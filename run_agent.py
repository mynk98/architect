import ollama
import subprocess
import os
import sys
import json

# --- Tool Implementations ---

def run_shell_command(command):
    print(f"
[Tool] Executing: {command}")
    try:
        # Use shell=True for flexibility, but be careful with input
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        print(f"[Tool Output]: {output[:200]}...")
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(path):
    print(f"
[Tool] Reading: {path}")
    try:
        if not os.path.exists(path):
            return f"Error: File not found at {path}"
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(path, content):
    print(f"
[Tool] Writing to: {path}")
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_directory(path):
    print(f"
[Tool] Listing: {path}")
    try:
        if not os.path.exists(path):
            return f"Error: Directory not found at {path}"
        return str(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {str(e)}"

# --- Tool Definitions for Ollama ---

tools_schema = [
    {
        'type': 'function',
        'function': {
            'name': 'run_shell_command',
            'description': 'Execute a shell command. Use this for system operations, moving files, git commands, etc.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': 'The command to run.'},
                },
                'required': ['command'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'read_file',
            'description': 'Read the content of a file.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Path to the file.'},
                },
                'required': ['path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'write_file',
            'description': 'Write content to a file. Overwrites if exists.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Path to the file.'},
                    'content': {'type': 'string', 'description': 'Content to write.'},
                },
                'required': ['path', 'content'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_directory',
            'description': 'List files in a directory.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Directory path.'},
                },
                'required': ['path'],
            },
        },
    }
]

# --- Main Agent Loop ---

def run_simple_agent(prompt, model="qwen2.5-coder:7b"):
    messages = [
        {'role': 'system', 'content': 'You are a helpful AI assistant. You have access to tools to interact with the file system and shell. Execute the user's request directly. Do not plan, just do.'},
        {'role': 'user', 'content': prompt}
    ]

    print(f"
--- Arch (Simple Mode) | Model: {model} ---")
    print(f"User: {prompt}
")

    max_turns = 10
    for i in range(max_turns):
        try:
            response = ollama.chat(model=model, messages=messages, tools=tools_schema)
        except Exception as e:
            print(f"Ollama API Error: {e}")
            return

        message = response['message']
        messages.append(message) # Add assistant response to history

        if message.get('tool_calls'):
            for tool in message['tool_calls']:
                fn_name = tool['function']['name']
                args = tool['function']['arguments']
                
                result = None
                if fn_name == 'run_shell_command':
                    result = run_shell_command(args.get('command'))
                elif fn_name == 'read_file':
                    result = read_file(args.get('path'))
                elif fn_name == 'write_file':
                    result = write_file(args.get('path'), args.get('content'))
                elif fn_name == 'list_directory':
                    result = list_directory(args.get('path'))
                
                # Add tool output to history
                messages.append({
                    'role': 'tool',
                    'content': str(result),
                })
        else:
            # No tools called, final response
            print(f"
Arch: {message['content']}")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_agent.py "<prompt>" [model]")
        sys.exit(1)
    
    user_prompt = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "qwen2.5-coder:7b"
    
    run_simple_agent(user_prompt, model_name)
