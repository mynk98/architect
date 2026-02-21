#!/bin/bash
# Multi-Model Architect Launcher
# Default Model: deepseek-v3.1:671b-cloud
# Usage: arch "prompt" [model_name]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/../ollama_agent_env/bin/activate"

MODEL=${2:-"qwen2.5-coder:7b"}

python3 agent/main.py "$1" "$MODEL"
