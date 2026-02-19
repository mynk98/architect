import subprocess
import os

class ToolRegistry:
    def __init__(self, memory_manager=None):
        self.memory = memory_manager
        self.registry = {
            'run_shell_command': self.run_shell_command,
            'read_file': self.read_file,
            'write_file': self.write_file,
            'list_directory': self.list_directory,
            'save_memory': self.save_memory,
            'recall_memory': self.recall_memory,
            'web_search': self.web_search,
            'python_linter': self.python_linter
        }

    def get_definitions(self):
        return [
            # ... keep existing tools ...
            {
                'type': 'function',
                'function': {
                    'name': 'run_shell_command',
                    'description': 'Execute a bash command',
                    'parameters': {
                        'type': 'object',
                        'properties': {'command': {'type': 'string'}},
                        'required': ['command']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_file',
                    'description': 'Read file content',
                    'parameters': {
                        'type': 'object',
                        'properties': {'path': {'type': 'string'}},
                        'required': ['path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'write_file',
                    'description': 'Write content to file',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string'},
                            'content': {'type': 'string'}
                        },
                        'required': ['path', 'content']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'list_directory',
                    'description': 'List directory contents',
                    'parameters': {
                        'type': 'object',
                        'properties': {'path': {'type': 'string'}},
                        'required': ['path']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'save_memory',
                    'description': 'Save a fact to long-term memory',
                    'parameters': {
                        'type': 'object',
                        'properties': {'content': {'type': 'string'}},
                        'required': ['content']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'recall_memory',
                    'description': 'Search long-term memory',
                    'parameters': {
                        'type': 'object',
                        'properties': {'query': {'type': 'string'}},
                        'required': ['query']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'web_search',
                    'description': 'Search the internet for current information',
                    'parameters': {
                        'type': 'object',
                        'properties': {'query': {'type': 'string'}},
                        'required': ['query']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'python_linter',
                    'description': 'Check Python code for syntax errors',
                    'parameters': {
                        'type': 'object',
                        'properties': {'code': {'type': 'string'}},
                        'required': ['code']
                    }
                }
            }
        ]

    def python_linter(self, code):
        import ast
        try:
            ast.parse(code)
            return {"status": "success", "message": "Syntax is valid"}
        except SyntaxError as e:
            return {"status": "error", "message": str(e), "line": e.lineno}

    def web_search(self, query):
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n")
            return "\n---\n".join(results)
        except Exception as e:
            return {"error": str(e)}

    def save_memory(self, content):
        if self.memory:
            return self.memory.save(content)
        return {"error": "Memory manager not linked"}

    def recall_memory(self, query):
        if self.memory:
            return self.memory.retrieve_relevant(query)
        return {"error": "Memory manager not linked"}

    def execute(self, name, args):
        if name in self.registry:
            try:
                return self.registry[name](**args)
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Tool not found"}

    def run_shell_command(self, command):
        try:
            # Expand ~ in commands
            command = os.path.expanduser(command)
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"stdout": res.stdout, "stderr": res.stderr, "exit_code": res.returncode}
        except Exception as e:
            return {"error": str(e)}

    def read_file(self, path):
        path = os.path.expanduser(path)
        if not os.path.exists(path): return {"error": f"File not found: {path}"}
        with open(path, 'r') as f: return f.read()

    def write_file(self, path, content):
        path = os.path.expanduser(path)
        # Auto-create parent directories
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f: f.write(content)
        return {"status": "success", "path": path}

    def list_directory(self, path):
        path = os.path.expanduser(path)
        if not os.path.exists(path): return {"error": f"Path not found: {path}"}
        return os.listdir(path)
