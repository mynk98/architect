#!/bin/bash
# Agent Launcher
# Usage: qwen "prompt" [model_name]

cd "/Users/abhisheksonkar/Project/qwen"
source ollama_agent_env/bin/activate

# Default to qwen local if no model provided
MODEL=${2:-"qwen2.5:0.5b"}

python3 run_agent.py "$1" "$MODEL"
