import ollama
import subprocess
import os
import sys
import json
import re
import datetime

# Ensure we can import from local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from core.memory_manager import MemoryManager
except ImportError:
    # Fallback if running from a different directory
    sys.path.append(os.path.join(current_dir, 'core'))
    from memory_manager import MemoryManager

# Optional: Web Search
try:
    from tools.web import web_search
    HAS_WEB = True
except ImportError:
    HAS_WEB = False
    def web_search(query): return "Web search module not available."

# --- Configuration ---
DEFAULT_MODEL = "qwen2.5:7b"
SPECIALIST_MODEL = "qwen2.5-coder:7b"
PERSONALITY_DIR = os.path.abspath(os.path.join(current_dir, '../../personality'))
IDENTITY_FILE = os.path.join(PERSONALITY_DIR, 'identity.json')

# --- Initialization ---
memory = MemoryManager()

def load_identity():
    """Loads the core identity to seed the system prompt."""
    if os.path.exists(IDENTITY_FILE):
        try:
            with open(IDENTITY_FILE, 'r') as f:
                data = json.load(f)
                return f"You are Lyra. Core Traits: {', '.join(data.get('coreTraits', []))}. Principles: {'; '.join(data.get('principles', []))}."
        except:
            pass
    return "You are Lyra, an advanced AI architect."

SYSTEM_PROMPT = load_identity() + """
You have access to a persistent memory graph. Use 'update_memory' to store important facts and 'recall_memory' to retrieve them. 
You can also search the web and delegate coding tasks to a specialist.

IMPORTANT: When using 'update_memory', you must provide ALL three arguments:
- subject: The entity the fact is about (e.g., "Mayank").
- relation: The relationship (e.g., "likes", "is_a", "has").
- target: The object of the relationship (e.g., "Rust", "Game Developer", "High Expertise").
Example: update_memory("Mayank", "likes", "Rust") -> Correct
Example: update_memory("Mayank", "is a Game Developer", "") -> INCORRECT. Use ("Mayank", "is_a", "Game Developer")
"""

# --- Tools ---
def run_shell_command(command):
    print(f"[*] Executing Terminal: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 60 seconds"}
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

def write_file(path, content):
    print(f"[*] Writing File: {path}")
    try:
        with open(path, 'w') as f:
            f.write(content)
        return {"status": "success", "message": f"Wrote to {path}"}
    except Exception as e:
        return {"error": str(e)}

def update_memory(subject, relation, target):
    """Adds a fact to the memory graph (Subject -> Relation -> Target)."""
    if not target or target.strip() == "":
        return {"error": "Target cannot be empty. Please split the fact into Relation and Target. E.g., 'is a Developer' -> relation='is_a', target='Developer'."}
        
    print(f"[*] Updating Memory: {subject} {relation} {target}")
    try:
        s_node = memory.add_node(subject.lower().replace(" ", "_"), "entity", subject)
        t_node = memory.add_node(target.lower().replace(" ", "_"), "entity", target)
        memory.add_edge(s_node['id'], t_node['id'], relation)
        return {"status": "success", "message": f"Learned: {subject} {relation} {target}"}
    except Exception as e:
        return {"error": str(e)}

def recall_memory(concept):
    """Finds related concepts in the memory graph."""
    print(f"[*] Recalling: {concept}")
    try:
        node = memory.find_node(concept)
        if not node:
            return {"found": False, "message": "Concept not found in memory."}
        
        related = memory.get_related(node['id'])
        return {"found": True, "node": node, "related": related}
    except Exception as e:
        return {"error": str(e)}

def ask_specialist(prompt):
    """Delegates a task to a specialized coding model."""
    print(f"[*] Delegating to Specialist ({SPECIALIST_MODEL})...")
    try:
        response = ollama.chat(
            model=SPECIALIST_MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        return f"Error calling specialist: {str(e)}"

# Tool definitions
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
            'name': 'write_file',
            'description': 'Write content to a file',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'The path to the file to write'},
                    'content': {'type': 'string', 'description': 'The content to write'},
                },
                'required': ['path', 'content'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'update_memory',
            'description': 'Save a fact to long-term memory. Requires subject, relation, and target.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'subject': {'type': 'string', 'description': 'The subject entity (e.g. "Mayank")'},
                    'relation': {'type': 'string', 'description': 'The relationship (e.g. "likes", "is_a")'},
                    'target': {'type': 'string', 'description': 'The object entity (e.g. "Rust")'},
                },
                'required': ['subject', 'relation', 'target'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'recall_memory',
            'description': 'Query long-term memory for a concept.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'concept': {'type': 'string', 'description': 'The concept to search for'},
                },
                'required': ['concept'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'ask_specialist',
            'description': 'Delegate a complex coding task to a specialist model.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': 'The task description'},
                },
                'required': ['prompt'],
            },
        },
    }
]

if HAS_WEB:
    tools.append({
        'type': 'function',
        'function': {
            'name': 'web_search',
            'description': 'Search the web for information.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'The search query'},
                },
                'required': ['query'],
            },
        },
    })

def extract_json_objects(text):
    """Robustly extracts JSON objects from text using bracket counting."""
    objects = []
    stack = []
    start_index = -1
    
    for i, char in enumerate(text):
        if char == '{':
            if not stack:
                start_index = i
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    # Full object found
                    json_str = text[start_index:i+1]
                    try:
                        obj = json.loads(json_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass # Ignore invalid JSON
    return objects

def agent_loop(model_name=DEFAULT_MODEL, initial_prompt=None):
    print(f"--- Architect Agent v2.4 (Model: {model_name}) ---")
    print(f"System: {SYSTEM_PROMPT}")

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    
    if initial_prompt:
        messages.append({'role': 'user', 'content': initial_prompt})
        print(f"User (Auto): {initial_prompt}")
    else:
        user_input = input("User: ")
        messages.append({'role': 'user', 'content': user_input})
    
    while True:
        try:
            response = ollama.chat(
                model=model_name,
                messages=messages,
                tools=tools,
            )
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            break

        msg = response['message']
        messages.append(msg)
        tool_calls = msg.get('tool_calls')
        content = msg.get('content', '')

        # Enhanced Fallback: Parse multiple JSON blocks from content
        if not tool_calls:
            json_objects = extract_json_objects(content)
            parsed_calls = []
            
            for data in json_objects:
                if 'name' in data and 'arguments' in data:
                     parsed_calls.append({'function': data})
                elif 'function' in data and 'name' in data['function']:
                     parsed_calls.append(data)
            
            if parsed_calls:
                tool_calls = parsed_calls

        if not tool_calls:
            print(f"Lyra: {content}")
            if initial_prompt: # One-shot mode if auto
                break
            
            user_input = input("User: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            messages.append({'role': 'user', 'content': user_input})
            continue

        # Process tool calls
        for tool in tool_calls:
            fname = tool['function']['name']
            args = tool['function']['arguments']
            
            if fname == 'run_shell_command':
                res = run_shell_command(args['command'])
            elif fname == 'read_file':
                res = read_file(args['path'])
            elif fname == 'write_file':
                res = write_file(args['path'], args['content'])
            elif fname == 'update_memory':
                res = update_memory(args.get('subject'), args.get('relation'), args.get('target'))
            elif fname == 'recall_memory':
                res = recall_memory(args['concept'])
            elif fname == 'ask_specialist':
                res = ask_specialist(args['prompt'])
            elif fname == 'web_search' and HAS_WEB:
                res = web_search(args['query'])
            else:
                res = {"error": "Unknown tool"}
            
            messages.append({
                'role': 'tool',
                'content': json.dumps(res),
            })

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
    agent_loop(model, prompt)
