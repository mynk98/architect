import os
import platform
import subprocess

def get_system_info():
    try:
        current_os = platform.system()
        project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
        
        # Filesystem report (Project size)
        du_res = subprocess.run(f"du -sh '{project_root}'", shell=True, capture_output=True, text=True)
        size = du_res.stdout.split()[0] if du_res.stdout else "Unknown"
        
        # Filesystem structure (top-level only to avoid spam)
        items = os.listdir(project_root)
        dirs = [i for i in items if os.path.isdir(os.path.join(project_root, i)) and not i.startswith('.')]
        files = [i for i in items if os.path.isfile(os.path.join(project_root, i)) and not i.startswith('.')]
        
        report = f"""
Architect System Report:
------------------------
OS: {current_os} {platform.release()}
Project Root: {project_root}
Project Size: {size}
Main Directories: {', '.join(dirs[:10])}
Main Files: {', '.join(files[:10])}
Status: Fully Operational (Optimized for JSON Signal)
        """.strip()
        return report
    except Exception as e:
        return f"Error gathering system info: {e}"
