import ollama
import json
import sys
import os

# Add current folder to path so we can import from qwen
sys.path.append(os.getcwd())
from agent.core.engine import QwenEngine

def autonomous_test():
    print("--- Starting Autonomous Validation of Qwen Agent ---")
    agent = QwenEngine()
    
    # Task: "Create a file named 'hello.txt' with content 'world', then save this action to your memory."
    user_input = "Create a file named 'hello.txt' with content 'world', then save this action to your memory."
    print(f"User: {user_input}")
    
    history = [
        {'role': 'system', 'content': agent.system_prompt},
        {'role': 'user', 'content': user_input}
    ]
    
    # Process turn
    max_turns = 10
    memory_updated = False
    file_created = False
    
    for i in range(max_turns):
        print(f"\n[Turn {i+1}] Thinking...")
        response = ollama.chat(
            model=agent.model,
            messages=history,
            tools=agent.tools.get_definitions()
        )
        
        msg = response['message']
        history.append(msg)
        
        tool_calls = msg.get('tool_calls')
        if not tool_calls:
            tool_calls = agent._fallback_parse(msg.get('content', ''))
        
        if tool_calls:
            for tool in tool_calls:
                fn_name = tool['function']['name']
                args = tool['function']['arguments']
                print(f"[Tool Call] {fn_name}: {args}")
                
                if fn_name == 'write_file' and args.get('path') == 'hello.txt':
                    file_created = True
                if fn_name == 'save_memory':
                    memory_updated = True
                
                result = agent.tools.execute(fn_name, args)
                print(f"[Tool Result] {result}")
                
                history.append({
                    'role': 'tool',
                    'content': json.dumps(result)
                })
        else:
            print(f"Qwen: {msg['content']}")
            break

    print("\n--- Validation Results ---")
    print(f"File Created: {'PASS' if file_created else 'FAIL'}")
    print(f"Memory Updated: {'PASS' if memory_updated else 'FAIL'}")
    print(f"Thinking Loop: {'PASS' if (file_created and memory_updated) else 'FAIL'}")

if __name__ == "__main__":
    autonomous_test()
