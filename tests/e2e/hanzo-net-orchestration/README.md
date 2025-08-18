# Hanzo Net E2E Test - Local AI Orchestration

This end-to-end test demonstrates the complete local AI orchestration capability of Hanzo Dev, showcasing:

1. **Local AI as Orchestrator**: Using Qwen3, Llama 3.2, or other local models to orchestrate
2. **Hybrid Agent Networks**: Local orchestrator managing API-based agents (Claude, GPT-4, Gemini)
3. **Cost Optimization**: 90% cost reduction through intelligent routing
4. **Full MCP Integration**: All agents can use MCP tools and communicate

## Architecture

```
┌─────────────────────────────────────────┐
│     Local Orchestrator (Qwen3)          │
│         via hanzo/net                   │
│    (Strategic Planning & Routing)       │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Cost-Optimized Router              │
│   (Prefers local for simple tasks)      │
└──────┬──────────────┬──────────────────┘
       │              │
       ▼              ▼
┌──────────────┐  ┌──────────────────────┐
│ Local Workers│  │   API Workers        │
│  (Qwen3)     │  │ • Claude 3.5 Sonnet  │
│   Free/Fast  │  │ • GPT-4 Turbo        │
│              │  │ • Gemini Pro         │
└──────────────┘  └──────────────────────┘
```

## Quick Start

### 1. Basic Test (Recommended)

```bash
# Run quick test with default model (qwen3)
./run_test.sh --quick

# Run with specific model
./run_test.sh --model llama-3.2-3b --quick
```

### 2. Full Test with Docker Setup

```bash
# Setup models and run full test
./run_test.sh --setup

# This will:
# 1. Download required models
# 2. Start Docker containers
# 3. Run complete test suite
```

### 3. Manual Testing

```bash
# Step 1: Start hanzo net with local model
hanzo net --models qwen3 --network local

# Step 2: Run hanzo dev with local orchestrator
hanzo dev --orchestrator local:qwen3 --use-hanzo-net

# Step 3: The system will:
# - Use Qwen3 as the orchestrator
# - Create local workers for simple tasks
# - Use Claude/GPT-4/Gemini for complex tasks
# - Route intelligently to minimize costs
```

## Test Scenarios

### 1. Task Routing Test
Tests that tasks are routed correctly based on complexity:

- **Simple tasks** → Local workers (free)
  - File listing
  - JSON formatting
  - String validation

- **Complex tasks** → API workers (paid)
  - Implementation of algorithms
  - System design
  - Debugging complex issues

- **Review tasks** → Critics
  - Code security review
  - Performance analysis

### 2. Cost Optimization Test
Verifies that the system achieves >50% cost savings by:
- Using local models for majority of simple tasks
- Only calling APIs when truly needed
- Tracking task distribution

### 3. Integration Test
Tests the full `hanzo dev` command with:
- Local orchestrator startup
- Agent network creation
- MCP tool integration
- Graceful shutdown

## Supported Models

### Local Models (via hanzo/net)
- **Qwen 2.5/3**: Best for instruction following
- **Llama 3.2**: Good general performance
- **Mistral 7B**: Strong reasoning
- **DeepSeek V3**: Excellent for code

### API Models (when needed)
- **Claude 3.5 Sonnet**: Complex implementation
- **GPT-4 Turbo**: Analysis and design
- **Gemini Pro**: Multimodal tasks

## Configuration

### Environment Variables

```bash
# API Keys (optional - only for API workers)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Hanzo Net Configuration
export HANZO_NET_PORT=52415
export HANZO_NET_MODELS="qwen3,llama-3.2-3b"
```

### Docker Services

The test includes Docker Compose configuration for:

1. **Ollama**: General model serving
2. **LocalAI**: GGUF model support
3. **vLLM**: High-performance inference (GPU)
4. **Text Generation WebUI**: Interactive testing

Start services:
```bash
docker-compose up -d
```

Stop services:
```bash
docker-compose down
```

## Expected Results

### Successful Test Output

```
============================================
HANZO NET E2E TEST - LOCAL AI ORCHESTRATION
============================================

Testing with model: qwen3
============================================
✓ hanzo net started successfully on port 52415
✓ Created local qwen3 orchestrator via hanzo/net
✓ Agent network initialized with 7 agents

=== Testing Task Routing ===
✓ Simple task → local_worker_0
✓ Complex task → claude_worker
✓ Review task → local_critic

=== Testing Cost Optimization ===
Task Distribution:
  Local models: 5/8
  API models: 3/8
  Cost savings: ~62.5%

=== Testing Hanzo Dev Integration ===
✓ hanzo dev started successfully

TEST SUMMARY
============================================
qwen3:
  Routing: 5/5 passed
  Cost Optimization: ✓ (62.5% savings)
  Hanzo Dev Integration: ✓
```

### Cost Savings Analysis

With this setup, you can expect:

- **90% cost reduction** for simple tasks
- **60-70% overall cost reduction** in typical workflows
- **Full capability** maintained (complex tasks still use best models)

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :52415

# Kill the process or use different port
hanzo net --port 52416
```

### Model Download Issues
```bash
# Download models manually with Ollama
ollama pull qwen2.5:3b
ollama pull llama3.2:3b

# Or use Hugging Face CLI
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF
```

### API Key Issues
The test will work without API keys but with reduced functionality:
- Local orchestrator and workers will still function
- API-based workers will be skipped
- Cost optimization will show 100% local usage

### Memory Issues
Adjust memory limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Reduce if needed
```

## Advanced Usage

### Custom Model Configuration

Create a custom model config:
```yaml
# models/custom-model.yaml
name: custom-model
parameters:
  model: /path/to/model.gguf
  temperature: 0.7
  max_tokens: 2048
```

### Running Specific Tests

```python
# Run only routing test
python3 -c "
import asyncio
from test_local_ai_orchestration import HanzoNetE2ETest

async def test():
    t = HanzoNetE2ETest()
    await t.setup()
    await t.start_hanzo_net('qwen3')
    network = await t.create_agent_network('qwen3')
    await t.test_task_routing(network)

asyncio.run(test())
"
```

### Monitoring Performance

View real-time logs:
```bash
# Hanzo net logs
hanzo net --models qwen3 --network local --verbose

# Docker logs
docker-compose logs -f

# System monitoring
htop  # CPU/Memory usage
nvidia-smi  # GPU usage (if available)
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/e2e-test.yml
name: E2E Test - Local AI Orchestration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e pkg/hanzo/
        pip install -e pkg/hanzo-network/
    
    - name: Run E2E Test
      run: |
        cd tests/e2e/hanzo-net-orchestration
        ./run_test.sh --quick --model llama-3.2-3b
```

## Summary

This E2E test demonstrates that Hanzo Dev can:

1. **Use local AI models as orchestrators** via hanzo/net
2. **Manage hybrid networks** of local and API agents
3. **Optimize costs** by routing intelligently
4. **Maintain full capability** while reducing expenses
5. **Scale from laptop to cloud** seamlessly

The result is an AI coding assistant that:
- Runs primarily on local/private infrastructure
- Calls expensive APIs only when necessary
- Provides enterprise-grade capabilities
- Reduces costs by up to 90%