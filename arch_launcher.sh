#!/bin/bash
# Multi-Model Architect Launcher
# Default Model: deepseek-v3.1:671b-cloud
# Usage: arch "prompt" [model_name]

cd "/Users/abhisheksonkar/Project/architect"
source ollama_agent_env/bin/activate

MODEL=${2:-"deepseek-v3.1:671b-cloud"}

python3 run_agent.py "$1" "$MODEL"
