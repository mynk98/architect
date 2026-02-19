import ollama
import json
import sys
import os
import re
from ..memory.manager import MemoryManager
from ..tools.base import ToolRegistry
from ..planning.planner import Planner

class ArchitectEngine:
    def __init__(self, primary_model=None, specialist_model=None):
        # 1. Load config if exists
        self.config_file = "data/state/config.json"
        config = self._load_config()
        
        # 2. Priority: Argument > Config > Default
        self.primary_model = primary_model or config.get("primary_model", "deepseek-v3.1:671b-cloud")
        self.specialist_model = specialist_model or config.get("specialist_model", "qwen2.5:0.5b")
        
        self.memory = MemoryManager()
        self.tools = ToolRegistry(memory_manager=self.memory)
        self.planner = Planner(primary_model=self.primary_model, fallback_model=self.specialist_model)
        self.state_file = "data/state/active_plan.json"
        os.makedirs("data/state", exist_ok=True)
        self.system_prompt = self._load_system_prompt()
        self.primary_online = True

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _load_system_prompt(self):
        return """You are a component of a Multi-Model Chained Architect.
        Focus ONLY on the current SUB-TASK provided. Use your tools to complete it and verify it.
        FORMAT: Output valid JSON tool calls.
        """

    def run(self, initial_prompt=None, mode="serial"):
        print(f"--- Multi-Model Architect Online ---")
        print(f"Primary: {self.primary_model} | Specialist: {self.specialist_model}")
        
        while True:
            try:
                goal = initial_prompt if initial_prompt else input("\nOverall Goal: ")
                if not goal or goal.lower() in ['exit', 'quit']: break
                
                plan = self.planner.decompose(goal)
                self._save_state(goal, plan)
                self._run_serial(goal, plan)
                
                print("\n[Engine] Overall Goal Accomplished.")
                if initial_prompt: break
                initial_prompt = None
            except KeyboardInterrupt: break

    def _run_serial(self, goal, plan):
        results = []
        i = 0
        while i < len(plan):
            item = plan[i]
            task = item['task']
            task_type = item['type']
            model = self.specialist_model if (task_type == "SPECIALIST" or not self.primary_online) else self.primary_model
            
            print(f"\n>>> Task {i+1}/{len(plan)} [{task_type}]: {task} (Model: {model})")
            
            history = [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'system', 'content': f"OVERALL GOAL: {goal}\nPROGRESS: {json.dumps([r['task'] for r in results])}"},
                {'role': 'user', 'content': f"YOUR CURRENT TASK: {task}"}
            ]
            
            try:
                sub_result = self._process_task(model, history)
                results.append({"task": task, "result": sub_result})
                i += 1 
            except Exception as e:
                if model == self.primary_model:
                    print(f"[!] Primary model {model} failed. PIVOTING TO LOCAL RECOVERY...")
                    self.primary_online = False
                    recovery_tasks = self._recover_decompose(task)
                    plan = plan[:i] + recovery_tasks + plan[i+1:]
                else:
                    print(f"[!!] Local failure: {e}")
                    results.append({"task": task, "result": f"FAILED: {e}"})
                    i += 1

    def _recover_decompose(self, complex_task):
        prompt = f"""Break this complex task into 2-3 SMALLER steps.
        TASK: {complex_task}
        Output JSON list of objects with 'task' and 'type': 'SPECIALIST'."""
        try:
            response = ollama.chat(model=self.specialist_model, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content']
            if "[" in content and "]" in content:
                return json.loads(content[content.find("["):content.rfind("]")+1])
        except: pass
        return [{"task": complex_task, "type": "SPECIALIST"}]

    def _process_task(self, model, history):
        max_turns = 5
        last_out = ""
        for turn in range(max_turns):
            response = ollama.chat(model=model, messages=history, tools=self.tools.get_definitions())
            msg = response['message']
            history.append(msg)
            content = msg.get('content', '')
            if content: print(f"[{model}]: {content[:150]}...")
            tool_calls = msg.get('tool_calls') or self._fallback_parse(content)
            if tool_calls:
                for tool in tool_calls:
                    fn_name = tool['function']['name']
                    args = tool['function']['arguments']
                    print(f"[*] Tool Call: {fn_name}")
                    res = self.tools.execute(fn_name, args)
                    history.append({'role': 'tool', 'content': json.dumps(res)})
            else:
                last_out = content
                break
        return last_out

    def _save_state(self, goal, plan):
        state = {"goal": goal, "plan": plan, "completed": 0, "results": []}
        with open(self.state_file, 'w') as f: json.dump(state, f, indent=2)

    def _fallback_parse(self, content):
        if not content: return None
        calls = []
        # Try to find JSON objects that look like tool calls
        # This pattern looks for {"name": "...", "arguments": {...}}
        pattern = r'\{\s*"name":\s*"[^"]+",\s*"arguments":\s*\{.*?\}(?=\s*\}|$\s*)\s*\}'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match.group(0))
                if 'name' in data and 'arguments' in data:
                    calls.append({'function': data})
            except Exception as e:
                # Try a more aggressive approach if direct JSON load fails
                try:
                    # Sometimes models output extra braces or missing ones
                    text = match.group(0)
                    # Count braces to find a balanced object
                    brace_count = 0
                    for idx, char in enumerate(text):
                        if char == '{': brace_count += 1
                        elif char == '}': brace_count -= 1
                        if brace_count == 0 and idx > 0:
                            data = json.loads(text[:idx+1])
                            if 'name' in data and 'arguments' in data:
                                calls.append({'function': data})
                                break
                except: continue
        
        if not calls:
            # Last resort: check if the entire content is a JSON object
            try:
                clean_content = content.strip()
                if clean_content.startswith("```json"):
                    clean_content = clean_content[7:]
                if clean_content.endswith("```"):
                    clean_content = clean_content[:-3]
                clean_content = clean_content.strip()
                data = json.loads(clean_content)
                if 'name' in data and 'arguments' in data:
                    calls.append({'function': data})
                elif isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
                    for item in data:
                        calls.append({'function': item})
            except: pass

        return calls if calls else None
