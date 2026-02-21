import warnings
# Suppress noisy warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

import ollama
import subprocess
import os
import sys
import json
import datetime
import platform

# Import custom tools
from agent.tools.shell import run_shell_command
from agent.tools.filesystem import read_file, write_file, list_directory
from agent.tools.web import web_search
from agent.tools.info import get_system_info

def ask_specialist(prompt, specialist_model="mistral:7b"):
    print(f"\n--- Calling Specialist ({specialist_model}) ---\n")
    full_response = ""
    try:
        # Use streaming for the specialist call so the user sees progress
        stream = ollama.chat(
            model=specialist_model,
            messages=[
                {'role': 'system', 'content': 'You are a technical specialist. Provide precise, expert code or technical solutions.'},
                {'role': 'user', 'content': prompt}
            ],
            stream=True
        )
        
        for chunk in stream:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            full_response += content
        
        print(f"\n\n--- Specialist Task Complete ---\n")
        return full_response
    except Exception as e:
        return f"Error calling specialist: {str(e)}"

# --- Tool Definitions ---

tools_schema = [
    {
        'type': 'function',
        'function': {
            'name': 'run_shell_command',
            'description': 'Execute a shell command.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string'},
                },
                'required': ['command'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'read_file',
            'description': 'Read a file.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                },
                'required': ['path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'write_file',
            'description': 'Write to a file.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                    'content': {'type': 'string'},
                },
                'required': ['path', 'content'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_directory',
            'description': 'List directory.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                },
                'required': ['path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'web_search',
            'description': 'Search the web for information.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'The search query.'},
                },
                'required': ['query'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_system_info',
            'description': 'Gather a concise report on the filesystem size, OS, and structure of the project.',
            'parameters': {'type': 'object', 'properties': {}},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'ask_specialist',
            'description': 'Delegate technical/coding tasks to Qwen. Use this for generating entire games, complex logic, or boilerplate.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': 'The detailed technical task.'},
                },
                'required': ['prompt'],
            },
        },
    }
]

def run_agent_loop(initial_prompt=None, primary_model="deepseek-v3.1:671b-cloud", specialist_model="qwen2.5-coder:7b"):
    # Detect OS and Environment for context
    current_os = platform.system()
    home_dir = os.path.expanduser("~")
    desktop_dir = os.path.join(home_dir, "Desktop")
    project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    today = datetime.date.today().strftime("%B %d, %Y")
    
    system_message = (
        f"You are the 'Architect,' a high-authority execution agent on {current_os}.\n"
        f"Current Date: {today}\n"
        f"Project Root: {project_root}\n\n"
        "### IDENTITY ###\n"
        "You are Gemini CLI's 'Architect' sub-agent. You use local models (Mistral/Qwen) and tools to execute tasks. "
        "You are NOT just a chatbot; you are a system orchestrator.\n\n"
        "### OPERATIONAL RIGOR ###\n"
        "1. NO HALLUCINATIONS: Never output 'Result: {...}' or pretend a tool has finished. Wait for the 'tool' role.\n"
        "2. NO MARKDOWN CODE BLOCKS FOR TOOLS: Output raw JSON only for the tool call. Do NOT wrap tool calls in ```json or any other markers.\n"
        "3. CONCISE RESPONSES: When tools return large amounts of data (like web search), extract ONLY the relevant facts. Do not dump raw links unless asked.\n"
        "4. SINGLE PURPOSE: Do not call the same tool multiple times with slightly different queries in one turn. Pick the best query.\n"
        "5. VALID JSON: Tool calls must be valid JSON: {\"name\": \"tool_name\", \"arguments\": {...}}\n\n"
        "### WORKFLOW ###\n"
        "THINK -> ACT -> WAIT.\n"
        "Stop immediately after the JSON block. Do not provide 'expected' output."
    )
    
    messages = [
        {'role': 'system', 'content': system_message}
    ]

    print(f"\n--- Architect REPL (Streaming Mode) | Primary: {primary_model} | Specialist: {specialist_model} ---")
    print("Commands: '/model <name>' to switch primary, '/list' to see models, 'exit' to stop\n")

    current_prompt = initial_prompt
    active_primary = primary_model

    while True:
        if not current_prompt:
            if initial_prompt: # If we started with a prompt, exit after the first complete turn
                break
            try:
                current_prompt = input(f"[{active_primary}] User: ")
            except EOFError:
                break
        else:
            print(f"User: {current_prompt}")

        if not current_prompt.strip():
            continue

        if current_prompt.lower() in ['exit', 'quit']:
            break
        
        if current_prompt.startswith('/model '):
            new_model = current_prompt.split(' ', 1)[1].strip()
            print(f"[*] Switching primary model to: {new_model}")
            active_primary = new_model
            current_prompt = None
            continue
        
        if current_prompt.strip() == '/list':
            try:
                model_list = ollama.list()
                if hasattr(model_list, 'models'):
                    models = [m.model for m in model_list.models]
                elif isinstance(model_list, dict):
                    models = [m['name'] for m in model_list.get('models', [])]
                else:
                    models = [str(m) for m in model_list]
                print(f"[*] Installed Models: {', '.join(models)}")
            except Exception as e:
                print(f"[!] Could not list models: {e}")
            current_prompt = None
            continue

        messages.append({'role': 'user', 'content': current_prompt})
        current_prompt = None 

        tool_turn = 0
        max_tool_turns = 10
        
        while tool_turn < max_tool_turns:
            tool_turn += 1
            try:
                print(f"[*] Calling {active_primary} (Turn {tool_turn})...")
                stream = ollama.chat(model=active_primary, messages=messages, tools=tools_schema, stream=True)
                
                full_content = ""
                tool_calls = []
                
                for chunk in stream:
                    msg = chunk.get('message', {})
                    if msg.get('content'):
                        content_chunk = msg.get('content')
                        print(content_chunk, end='', flush=True)
                        full_content += content_chunk
                    
                    if msg.get('tool_calls'):
                        for call in msg['tool_calls']:
                            tool_calls.append(call)
                
                print() 

                if not tool_calls and ('{' in full_content or '(' in full_content):
                    import re
                    import uuid
                    new_full_content = full_content
                    
                    list_calls = re.findall(r'\[\s*"(\w+)"\s*,\s*(\{[^{}]*\})\s*\]', full_content)
                    for fn_name, args_json in list_calls:
                        try:
                            args = json.loads(args_json)
                            tool_calls.append({
                                'id': f"call_ls_{uuid.uuid4().hex[:8]}",
                                'type': 'function',
                                'function': {'name': fn_name, 'arguments': args}
                            })
                            print(f"[*] Detected list-format call: {fn_name}(...)")
                        except: pass

                    pseudo_calls = re.findall(r'(\w+)\s*\(\s*(\{.*?\})\s*\)', full_content, re.DOTALL)
                    for fn_name, args_json in pseudo_calls:
                        try:
                            args = json.loads(args_json)
                            tool_calls.append({
                                'id': f"call_ps_{uuid.uuid4().hex[:8]}",
                                'type': 'function',
                                'function': {'name': fn_name, 'arguments': args}
                            })
                            print(f"[*] Detected pseudo-code call: {fn_name}(...)")
                        except: pass

                    json_blocks = re.findall(r'(\{(?:[^{}]|\{[^{}]*\})*\})', new_full_content)
                    found_tool_call = False
                    first_json_pos = 1000000
                    
                    for block in json_blocks:
                        try:
                            potential_call = json.loads(block)
                            is_tool = False
                            if ('name' in potential_call and 'arguments' in potential_call):
                                is_tool = True
                            elif ('function' in potential_call and 'name' in potential_call['function']):
                                is_tool = True
                            
                            if is_tool:
                                found_tool_call = True
                                pos = full_content.find(block)
                                if pos != -1 and pos < first_json_pos:
                                    first_json_pos = pos
                                    
                                if 'name' in potential_call:
                                    tool_calls.append({
                                        'id': f"call_{uuid.uuid4().hex[:8]}",
                                        'type': 'function',
                                        'function': potential_call
                                    })
                                else:
                                    if 'id' not in potential_call:
                                        potential_call['id'] = f"call_{uuid.uuid4().hex[:8]}"
                                    tool_calls.append(potential_call)
                        except: pass
                    
                    if found_tool_call:
                        new_full_content = full_content[:first_json_pos].strip()
                        if not new_full_content:
                            new_full_content = "[Executing Tool...]"
                    full_content = new_full_content
                
                assistant_msg = {'role': 'assistant', 'content': full_content}
                if tool_calls:
                    assistant_msg['tool_calls'] = tool_calls
                messages.append(assistant_msg)

                if tool_calls:
                    if len(messages) >= 3:
                        prev_assistant = messages[-3]
                        if prev_assistant.get('role') == 'assistant' and prev_assistant.get('tool_calls') == tool_calls:
                            print("[!] Loop detected. Stopping.")
                            messages.pop()
                            break

                    for tool in tool_calls:
                        fn = tool['function']['name']
                        args = tool['function']['arguments']
                        call_id = tool.get('id')

                        print(f"[*] Executing tool: {fn}")
                        res = None
                        if fn == 'run_shell_command': res = run_shell_command(args.get('command'))
                        elif fn == 'read_file': res = read_file(args.get('path'))
                        elif fn == 'write_file': res = write_file(args.get('path'), args.get('content'))
                        elif fn == 'list_directory': res = list_directory(args.get('path'))
                        elif fn == 'web_search': res = web_search(args.get('query'))
                        elif fn == 'get_system_info': res = get_system_info()
                        elif fn == 'ask_specialist': res = ask_specialist(args.get('prompt'), specialist_model)
                        
                        print(f"[*] Tool {fn} completed.")
                        tool_msg = {'role': 'tool', 'content': str(res)}
                        if call_id: tool_msg['tool_call_id'] = call_id
                        tool_msg['name'] = fn
                        messages.append(tool_msg)
                else:
                    if full_content:
                        print(f"\nArch: {full_content}\n")
                    break
            except Exception as e:
                print(f"Error in agent loop: {e}")
                break
        if initial_prompt: break

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    primary = sys.argv[2] if len(sys.argv) > 2 else "mistral:7b"
    specialist = sys.argv[3] if len(sys.argv) > 3 else "mistral:7b"
    run_agent_loop(prompt, primary, specialist)
