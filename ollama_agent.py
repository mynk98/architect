import ollama
import subprocess
import os
import sys
import json

# Define the tools
def run_shell_command(command):
    print(f"[*] Executing Terminal: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"error": str(e)}

def read_file(path):
    print(f"[*] Reading File: {path}")
    try:
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return {"error": str(e)}

def list_directory(path):
    print(f"[*] Listing Directory: {path}")
    try:
        if not os.path.exists(path):
            return {"error": f"Directory not found: {path}"}
        return os.listdir(path)
    except Exception as e:
        return {"error": str(e)}

# Tool definitions for Ollama
tools = [
    {
        'type': 'function',
        'function': {
            'name': 'run_shell_command',
            'description': 'Execute a bash command in the terminal',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': 'The exact bash command to execute'},
                },
                'required': ['command'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'read_file',
            'description': 'Read the contents of a file',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'The path to the file to read'},
                },
                'required': ['path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_directory',
            'description': 'List the contents of a directory',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'The path to the directory to list'},
                },
                'required': ['path'],
            },
        },
    }
]

def agent_loop(model_name, initial_prompt=None):
    if initial_prompt:
        user_input = initial_prompt
        print(f"Agent User (Auto): {user_input}")
    else:
        user_input = input("Agent User: ")
        
    messages = [{'role': 'user', 'content': user_input}]
    
    while True:
        max_tool_turns = 5
        turn_count = 0
        
        while turn_count < max_tool_turns:
            response = ollama.chat(
                model=model_name,
                messages=messages,
                tools=tools,
            )
            
            messages.append(response['message'])
            tool_calls = response['message'].get('tool_calls')
            
            # Fallback: Parse JSON from content if model didn't use structured tool calls
            content = response['message'].get('content', '')
            if not tool_calls and content.strip().startswith('{'):
                try:
                    potential_call = json.loads(content)
                    if 'name' in potential_call and 'arguments' in potential_call:
                        tool_calls = [{'function': potential_call}]
                except: pass

            if not tool_calls:
                print(f"Agent: {content}")
                break # Exit tool loop to wait for user input

            # Process tool calls
            for tool in tool_calls:
                function_name = tool['function']['name']
                arguments = tool['function']['arguments']
                
                if function_name == 'run_shell_command':
                    result = run_shell_command(arguments['command'])
                elif function_name == 'read_file':
                    result = read_file(arguments['path'])
                elif function_name == 'list_directory':
                    result = list_directory(arguments['path'])
                else:
                    result = {"error": "Tool not found"}
                
                messages.append({
                    'role': 'tool',
                    'content': json.dumps(result),
                })
            
            turn_count += 1
            if turn_count >= max_tool_turns:
                print("[!] Tool turn limit reached to prevent infinite loops.")

        if initial_prompt:
            break
            
        user_input = input("Agent User: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        messages.append({'role': 'user', 'content': user_input})

if __name__ == "__main__":
    model = "qwen2.5:0.5b"
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"--- Starting Agent with {model} ---")
    agent_loop(model, prompt)
