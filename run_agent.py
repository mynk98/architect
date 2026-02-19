import sys
import os

# Ensure the architect directory is in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from agent.core.architect_engine import ArchitectEngine

if __name__ == "__main__":
    # Ensure we run from the correct directory
    os.chdir(current_dir)
    
    # Args
    initial_prompt = sys.argv[1] if len(sys.argv) > 1 else None
    # If args are passed, they override config
    primary = sys.argv[2] if len(sys.argv) > 2 else None
    specialist = sys.argv[3] if len(sys.argv) > 3 else None
    mode = sys.argv[4] if len(sys.argv) > 4 else "serial"
    
    agent = ArchitectEngine(primary_model=primary, specialist_model=specialist)
    agent.run(initial_prompt=initial_prompt, mode=mode)
