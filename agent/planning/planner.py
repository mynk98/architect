import ollama
import json

class Planner:
    def __init__(self, primary_model="deepseek-v3.1:671b-cloud", fallback_model="qwen2.5:0.5b"):
        self.primary_model = primary_model
        self.fallback_model = fallback_model

    def decompose(self, goal):
        prompt = f"""Break down the following complex AI engineering goal into a sequence of sub-tasks.
        Categorize each task based on its complexity:
        - 'SPECIALIST': Simple technical tasks like writing a single function, creating a file, or running a command.
        - 'ARCHITECT': Complex reasoning, multi-file integration, or high-level logic design.
        
        GOAL: {goal}
        
        Output your response strictly as a JSON list of objects:
        [
          {{"task": "Task description", "type": "SPECIALIST"}},
          {{"task": "Task description", "type": "ARCHITECT"}}
        ]
        """
        
        print(f"[Planner] Attempting decomposition with {self.primary_model}...")
        try:
            response = ollama.chat(
                model=self.primary_model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            plan = self._parse_plan(response['message']['content'])
            if plan: return plan
        except Exception as e:
            print(f"[!] Primary Planner Failed: {e}.")
        
        print(f"[*] Falling back to {self.fallback_model} for planning...")
        try:
            response = ollama.chat(
                model=self.fallback_model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            plan = self._parse_plan(response['message']['content'])
            if plan: return plan
        except Exception as fe:
            print(f"[!!] Total Planning Failure: {fe}")
        
        # Absolute fallback: treat the goal as a single specialist task
        return [{"task": goal, "type": "SPECIALIST"}]

    def _parse_plan(self, content):
        try:
            # Look for everything from the first [ to the last ]
            if "[" in content and "]" in content:
                json_str = content[content.find("["):content.rfind("]")+1]
                data = json.loads(json_str)
                if isinstance(data, list):
                    return data
        except:
            pass
        return None
