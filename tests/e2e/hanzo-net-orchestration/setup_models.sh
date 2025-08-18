#!/bin/bash

# Setup script for E2E test models
set -e

echo "================================================"
echo "Hanzo Net E2E Test - Model Setup"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create models directory
mkdir -p models

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to download model with Ollama
download_ollama_model() {
    local model=$1
    echo -e "${YELLOW}Downloading $model with Ollama...${NC}"
    
    if command_exists ollama; then
        ollama pull $model
        echo -e "${GREEN}✓ Downloaded $model${NC}"
    else
        echo -e "${RED}✗ Ollama not installed. Install from: https://ollama.ai${NC}"
        return 1
    fi
}

# Function to download Hugging Face model
download_hf_model() {
    local model_id=$1
    local model_name=$2
    
    echo -e "${YELLOW}Downloading $model_name from Hugging Face...${NC}"
    
    if command_exists huggingface-cli; then
        huggingface-cli download $model_id --local-dir ./models/$model_name
        echo -e "${GREEN}✓ Downloaded $model_name${NC}"
    else
        echo -e "${YELLOW}Installing huggingface-hub...${NC}"
        pip install huggingface-hub
        huggingface-cli download $model_id --local-dir ./models/$model_name
    fi
}

# Check for Docker
if ! command_exists docker; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check for Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

echo ""
echo "Setting up local models for testing..."
echo ""

# 1. Setup Ollama models (if Ollama is installed locally)
if command_exists ollama; then
    echo "Setting up Ollama models..."
    
    # Start Ollama service if not running
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting Ollama service..."
        ollama serve &
        sleep 5
    fi
    
    # Download models
    download_ollama_model "qwen2.5:3b"
    download_ollama_model "llama3.2:3b"
    download_ollama_model "mistral:7b"
    download_ollama_model "deepseek-coder:6.7b"
    
else
    echo -e "${YELLOW}Ollama not installed locally. Models will be downloaded in Docker container.${NC}"
fi

# 2. Download GGUF models for LocalAI
echo ""
echo "Downloading GGUF models for LocalAI..."

# Create models directory structure
mkdir -p models/gguf

# Download Qwen 3B GGUF
if [ ! -f "models/gguf/qwen2.5-3b-instruct.gguf" ]; then
    echo "Downloading Qwen 2.5 3B GGUF..."
    wget -O models/gguf/qwen2.5-3b-instruct.gguf \
        https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
fi

# Download Llama 3.2 3B GGUF
if [ ! -f "models/gguf/llama-3.2-3b.gguf" ]; then
    echo "Downloading Llama 3.2 3B GGUF..."
    wget -O models/gguf/llama-3.2-3b.gguf \
        https://huggingface.co/NousResearch/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
fi

# 3. Create LocalAI model configurations
echo ""
echo "Creating LocalAI model configurations..."

# Qwen config
cat > models/qwen3.yaml <<EOF
name: qwen3
parameters:
  model: /models/gguf/qwen2.5-3b-instruct.gguf
  temperature: 0.7
  top_k: 40
  top_p: 0.95
  threads: 8
  max_tokens: 2048
  stop:
    - "<|im_end|>"
    - "<|endoftext|>"
template:
  chat: |
    <|im_start|>system
    {{.System}}<|im_end|>
    <|im_start|>user
    {{.Input}}<|im_end|>
    <|im_start|>assistant
EOF

# Llama config
cat > models/llama32.yaml <<EOF
name: llama32
parameters:
  model: /models/gguf/llama-3.2-3b.gguf
  temperature: 0.7
  top_k: 40
  top_p: 0.95
  threads: 8
  max_tokens: 2048
  stop:
    - "</s>"
    - "<|eot_id|>"
template:
  chat: |
    <|begin_of_text|><|start_header_id|>system<|end_header_id|>
    {{.System}}<|eot_id|><|start_header_id|>user<|end_header_id|>
    {{.Input}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
EOF

# 4. Setup API keys check
echo ""
echo "Checking API keys..."

check_api_key() {
    local key_name=$1
    local service=$2
    
    if [ -z "${!key_name}" ]; then
        echo -e "${YELLOW}⚠ $key_name not set. $service will not be available.${NC}"
        echo "  Export it with: export $key_name='your-key-here'"
        return 1
    else
        echo -e "${GREEN}✓ $key_name is set for $service${NC}"
        return 0
    fi
}

check_api_key "OPENAI_API_KEY" "OpenAI (GPT-4/Codex)"
check_api_key "ANTHROPIC_API_KEY" "Anthropic (Claude)"
check_api_key "GOOGLE_API_KEY" "Google (Gemini)"

# 5. Create .env file for Docker Compose
echo ""
echo "Creating .env file..."

cat > .env <<EOF
# API Keys (add your keys here)
OPENAI_API_KEY=${OPENAI_API_KEY:-your-openai-key}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your-anthropic-key}
GOOGLE_API_KEY=${GOOGLE_API_KEY:-your-google-key}

# Model paths
MODELS_PATH=./models

# Resource limits
MEMORY_LIMIT=16G
CPU_LIMIT=8
EOF

echo -e "${GREEN}✓ Created .env file${NC}"

# 6. Start Docker services
echo ""
echo "Starting Docker services..."

# Use docker compose or docker-compose depending on what's available
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

$COMPOSE_CMD up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to start..."

wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $service on port $port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e " ${RED}✗ (timeout)${NC}"
    return 1
}

wait_for_service "Ollama" 11434
wait_for_service "LocalAI" 8080
wait_for_service "vLLM" 8000

# 7. Test model availability
echo ""
echo "Testing model availability..."

# Test Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is responding${NC}"
    
    # List available models
    echo "  Available Ollama models:"
    curl -s http://localhost:11434/api/tags | jq -r '.models[].name' | sed 's/^/    - /'
else
    echo -e "${RED}✗ Ollama is not responding${NC}"
fi

# Test LocalAI
if curl -s http://localhost:8080/v1/models >/dev/null 2>&1; then
    echo -e "${GREEN}✓ LocalAI is responding${NC}"
else
    echo -e "${RED}✗ LocalAI is not responding${NC}"
fi

# Test vLLM
if curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then
    echo -e "${GREEN}✓ vLLM is responding${NC}"
else
    echo -e "${YELLOW}⚠ vLLM may need GPU support${NC}"
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "You can now run the E2E test with:"
echo "  python test_local_ai_orchestration.py"
echo ""
echo "To stop services:"
echo "  $COMPOSE_CMD down"
echo ""
echo "To view logs:"
echo "  $COMPOSE_CMD logs -f"
echo ""