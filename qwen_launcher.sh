#!/bin/bash
# Agent Launcher
# Usage: qwen "prompt" [model_name]

cd "/Users/abhisheksonkar/Project/qwen"
source ollama_agent_env/bin/activate

# Default to deepseek cloud if available, else fallback to qwen
MODEL=${2:-"deepseek-v3.1:671b-cloud"}

python3 run_agent.py "$1" "$MODEL"
