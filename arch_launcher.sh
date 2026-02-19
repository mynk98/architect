#!/bin/bash
# Multi-Model Architect Launcher
# Default Model: deepseek-v3.1:671b-cloud
# Usage: arch "prompt" [model_name]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source ollama_agent_env/bin/activate

MODEL=${2:-"deepseek-v3.1:671b-cloud"}

python3 run_agent.py "$1" "$MODEL"
