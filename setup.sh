#!/bin/bash

# --- Multi-Model Architect Setup Script ---
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Architect Framework Setup ===${NC}"

# 1. Check for Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}[!] Ollama is not installed.${NC}"
    echo "Please download and install it from https://ollama.com/"
    exit 1
fi
echo -e "${GREEN}[✓] Ollama detected.${NC}"

# 2. Check for UV (faster dependency management)
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}[*] Installing uv for faster setup...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi
echo -e "${GREEN}[✓] uv detected.${NC}"

# 3. Model Management
echo -e "
${BLUE}--- Model Configuration ---${NC}"
AVAILABLE_MODELS=$(ollama list | awk 'NR>1 {print $1}')

if [ -z "$AVAILABLE_MODELS" ]; then
    echo -e "${RED}[!] No local models found in Ollama.${NC}"
    echo "Recommended for Specialist: qwen2.5-coder:7b"
    echo "Recommended for Architect: deepseek-v3.1:671b-cloud (if configured)"
    read -p "Enter a model name to download (e.g., qwen2.5-coder:7b): " NEW_MODEL
    echo -e "${BLUE}[*] Pulling $NEW_MODEL...${NC}"
    ollama pull "$NEW_MODEL"
    AVAILABLE_MODELS=$NEW_MODEL
fi

echo -e "Available local models:"
echo "$AVAILABLE_MODELS"
echo "-----------------------"

read -p "Enter name for PRIMARY (Architect) model [default: deepseek-v3.1:671b-cloud]: " PRIMARY
PRIMARY=${PRIMARY:-"deepseek-v3.1:671b-cloud"}

read -p "Enter name for SPECIALIST (Local) model: " SPECIALIST
while [ -z "$SPECIALIST" ]; do
    read -p "${RED}Specialist model is required. Enter name: ${NC}" SPECIALIST
done

# 4. Save Configuration
mkdir -p data/state
cat <<EOF > data/state/config.json
{
  "primary_model": "$PRIMARY",
  "specialist_model": "$SPECIALIST"
}
EOF
echo -e "${GREEN}[✓] Configuration saved to data/state/config.json${NC}"

# 5. Environment Setup
echo -e "
${BLUE}--- Environment Setup ---${NC}"
uv venv ollama_agent_env
source ollama_agent_env/bin/activate
uv pip install ollama duckduckgo-search requests
echo -e "${GREEN}[✓] Virtual environment ready.${NC}"

# 6. Alias Setup
ARCH_PATH="$(pwd)/arch_launcher.sh"
if ! grep -q "alias arch=" ~/.zshrc; then
    echo -e "
${BLUE}[*] Adding 'arch' alias to ~/.zshrc...${NC}"
    echo "alias arch='$ARCH_PATH'" >> ~/.zshrc
    echo -e "${GREEN}[✓] Alias added. Run 'source ~/.zshrc' to activate.${NC}"
else
    echo -e "
${BLUE}[*] Updating 'arch' alias in ~/.zshrc...${NC}"
    sed -i '' "s|alias arch=.*|alias arch='$ARCH_PATH'|g" ~/.zshrc
fi

echo -e "
${GREEN}=== Setup Complete! ===${NC}"
echo "You can now run the agent using: arch "your task""
