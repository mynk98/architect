import os

def read_file(path):
    try:
        if not os.path.exists(path):
            return f"Error: File not found at {path}"
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(path, content):
    try:
        full_path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_directory(path):
    try:
        if not os.path.exists(path):
            return f"Error: Directory not found at {path}"
        return str(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {str(e)}"
