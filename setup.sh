#!/bin/bash

# --- Multi-Model Architect Setup Script ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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
    # Source for current shell
    export PATH="$HOME/.astral-uv/bin:$PATH"
fi
echo -e "${GREEN}[✓] uv detected.${NC}"

# 3. Model Management
echo -e "\n${BLUE}--- Model Configuration ---${NC}"
AVAILABLE_MODELS=$(ollama list | awk 'NR>1 {print $1}')

if [ -z "$AVAILABLE_MODELS" ]; then
    echo -e "${YELLOW}[!] No local models found in Ollama.${NC}"
    read -p "Enter a model name to download [default: qwen2.5-coder:7b]: " NEW_MODEL
    NEW_MODEL=${NEW_MODEL:-"qwen2.5-coder:7b"}
    echo -e "${BLUE}[*] Pulling $NEW_MODEL...${NC}"
    ollama pull "$NEW_MODEL"
    AVAILABLE_MODELS=$NEW_MODEL
fi

echo -e "Available local models:"
echo "$AVAILABLE_MODELS"
echo "-----------------------"

read -p "Enter PRIMARY model [default: deepseek-v3.1:671b-cloud]: " PRIMARY
PRIMARY=${PRIMARY:-"deepseek-v3.1:671b-cloud"}

read -p "Enter SPECIALIST model [default: qwen2.5-coder:7b]: " SPECIALIST
SPECIALIST=${SPECIALIST:-"qwen2.5-coder:7b"}

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
echo -e "\n${BLUE}--- Environment Setup ---${NC}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Create venv in the parent directory as per launcher expectation
cd "$PROJECT_ROOT"
uv venv ollama_agent_env
source ollama_agent_env/bin/activate
uv pip install ollama requests
echo -e "${GREEN}[✓] Virtual environment ready.${NC}"

# 6. Global Command Setup (arch)
echo -e "\n${BLUE}--- Global Command Setup ---${NC}"
ARCH_LAUNCHER="$(pwd)/architect/arch_launcher.sh"
# Escape spaces for the alias
ARCH_LAUNCHER_ESCAPED="${ARCH_LAUNCHER// /\\ }"

# Add alias to .zshrc
if ! grep -q "alias arch=" ~/.zshrc 2>/dev/null; then
    echo -e "[*] Adding 'arch' alias to ~/.zshrc..."
    echo "alias arch='$ARCH_LAUNCHER_ESCAPED'" >> ~/.zshrc
else
    echo -e "[*] Updating 'arch' alias in ~/.zshrc..."
    sed -i '' "s|alias arch=.*|alias arch='$ARCH_LAUNCHER_ESCAPED'|g" ~/.zshrc
fi

# Attempt to create symbolic link in Antigravity bin if it exists
ANTIGRAVITY_BIN="$HOME/.antigravity/antigravity/bin"
if [ -d "$ANTIGRAVITY_BIN" ]; then
    echo -e "[*] Antigravity detected. Creating symbolic link..."
    ln -sf "$ARCH_LAUNCHER" "$ANTIGRAVITY_BIN/arch"
    echo -e "${GREEN}[✓] Global binary linked to $ANTIGRAVITY_BIN/arch${NC}"
fi

# 7. Check for Lyra Context
if [ -f "$(pwd)/lyra_launcher.sh" ]; then
    echo -e "\n${BLUE}--- Lyra Personality Setup ---${NC}"
    LYRA_LAUNCHER="$(pwd)/lyra_launcher.sh"
    LYRA_LAUNCHER_ESCAPED="${LYRA_LAUNCHER// /\\ }"
    
    if ! grep -q "alias lyra=" ~/.zshrc 2>/dev/null; then
        echo "alias lyra='$LYRA_LAUNCHER_ESCAPED'" >> ~/.zshrc
    else
        sed -i '' "s|alias lyra=.*|alias lyra='$LYRA_LAUNCHER_ESCAPED'|g" ~/.zshrc
    fi
    
    if [ -d "$ANTIGRAVITY_BIN" ]; then
        ln -sf "$LYRA_LAUNCHER" "$ANTIGRAVITY_BIN/lyra"
    fi
    echo -e "${GREEN}[✓] 'lyra' command also configured.${NC}"
fi

echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo -e "1. Run ${YELLOW}source ~/.zshrc${NC} to activate commands."
echo -e "2. Type ${YELLOW}arch${NC} to start the AI agent (REPL)."
echo -e "3. Type ${YELLOW}arch \"your prompt\"${NC} for direct tasks."
