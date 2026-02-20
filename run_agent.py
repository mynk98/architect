import ollama
import subprocess
import os
import sys
import json

# --- Tool Implementations ---

def run_shell_command(command):
    print(f"[*] Tool: run_shell_command -> {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(path):
    print(f"[*] Tool: read_file -> {path}")
    try:
        if not os.path.exists(path):
            return f"Error: File not found at {path}"
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(path, content):
    print(f"[*] Tool: write_file -> {path}")
    try:
        full_path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_directory(path):
    print(f"[*] Tool: list_directory -> {path}")
    try:
        if not os.path.exists(path):
            return f"Error: Directory not found at {path}"
        return str(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def ask_specialist(prompt, specialist_model="qwen2.5-coder:7b"):
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
    messages = [
        {'role': 'system', 'content': f'You are a direct execution agent. Do not over-plan. Execute user requests using tools. You can delegate technical tasks to a specialist using the ask_specialist tool (model: {specialist_model}). If no tool is needed, respond directly.'}
    ]

    print(f"\n--- Architect REPL (Streaming Mode) | Primary: {primary_model} | Specialist: {specialist_model} ---")
    print("Commands: '/model <name>' to switch primary, '/list' to see models, 'exit' to stop\n")

    current_prompt = initial_prompt
    active_primary = primary_model

    while True:
        if not current_prompt:
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
                models = [m['name'] for m in ollama.list().get('models', [])]
                print(f"[*] Installed Models: {', '.join(models)}")
            except:
                print("[!] Could not list models.")
            current_prompt = None
            continue

        messages.append({'role': 'user', 'content': current_prompt})
        current_prompt = None 

        # Internal tool loop for the current user turn
        while True:
            try:
                # We call without stream=True first to check for tool calls
                # Ollama library handles tool calling best in non-streaming responses
                response = ollama.chat(model=active_primary, messages=messages, tools=tools_schema)
            except Exception as e:
                print(f"Error: {e}")
                break

            msg = response['message']
            messages.append(msg)

            if msg.get('tool_calls'):
                for tool in msg['tool_calls']:
                    fn = tool['function']['name']
                    args = tool['function']['arguments']
                    
                    res = None
                    if fn == 'run_shell_command': res = run_shell_command(args.get('command'))
                    elif fn == 'read_file': res = read_file(args.get('path'))
                    elif fn == 'write_file': res = write_file(args.get('path'), args.get('content'))
                    elif fn == 'list_directory': res = list_directory(args.get('path'))
                    elif fn == 'ask_specialist': res = ask_specialist(args.get('prompt'), specialist_model)
                    
                    messages.append({'role': 'tool', 'content': str(res)})
            else:
                if msg['content']:
                    print(f"\nArch: {msg['content']}\n")
                break

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    primary = sys.argv[2] if len(sys.argv) > 2 else "deepseek-v3.1:671b-cloud"
    specialist = sys.argv[3] if len(sys.argv) > 3 else "qwen2.5-coder:7b"
    run_agent_loop(prompt, primary, specialist)
