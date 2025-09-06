# Hanzo CLI and Orchestration Tools

[![PyPI](https://img.shields.io/pypi/v/hanzo.svg)](https://pypi.org/project/hanzo/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzo.svg)](https://pypi.org/project/hanzo/)

Core CLI and orchestration tools for the Hanzo AI platform.

## Installation

```bash
pip install hanzo
```

## Features

- **Interactive Chat**: Chat with AI models through CLI
- **Node Management**: Run local AI inference nodes
- **Router Control**: Manage LLM proxy router
- **REPL Interface**: Interactive Python REPL with AI
- **Batch Orchestration**: Orchestrate multiple AI tasks
- **Memory Management**: Persistent conversation memory

## Usage

### CLI Commands

```bash
# Interactive chat
hanzo chat

# Use specific model
hanzo chat --model gpt-4

# Use router (local proxy)
hanzo chat --router

# Use cloud API
hanzo chat --cloud
```

### Node Management

```bash
# Start local node
hanzo node start

# Check status
hanzo node status

# List available models
hanzo node models

# Load specific model
hanzo node load llama2:7b

# Stop node
hanzo node stop
```

### Router Management

```bash
# Start router proxy
hanzo router start

# Check router status
hanzo router status

# List available models
hanzo router models

# View configuration
hanzo router config

# Stop router
hanzo router stop
```

### Interactive REPL

```bash
# Start REPL
hanzo repl

# In REPL:
> /help              # Show help
> /models            # List models
> /model gpt-4       # Switch model
> /clear             # Clear context
> What is Python?    # Ask questions
```

## Python API

### Batch Orchestration

```python
from hanzo.batch_orchestrator import BatchOrchestrator

orchestrator = BatchOrchestrator()
results = await orchestrator.run_batch([
    "Summarize quantum computing",
    "Explain machine learning",
    "Define artificial intelligence"
])
```

### Memory Management

```python
from hanzo.memory_manager import MemoryManager

memory = MemoryManager()
memory.add_to_context("user", "What is Python?")
memory.add_to_context("assistant", "Python is...")
context = memory.get_context()
```

### Fallback Handling

```python
from hanzo.fallback_handler import FallbackHandler

handler = FallbackHandler()
result = await handler.handle_with_fallback(
    primary_fn=api_call,
    fallback_fn=local_inference
)
```

## Configuration

### Environment Variables

```bash
# API settings
HANZO_API_KEY=your-api-key
HANZO_BASE_URL=https://api.hanzo.ai

# Router settings
HANZO_ROUTER_URL=http://localhost:4000/v1

# Node settings
HANZO_NODE_URL=http://localhost:8000/v1
HANZO_NODE_WORKERS=4

# Model preferences
HANZO_DEFAULT_MODEL=gpt-4
HANZO_FALLBACK_MODEL=llama2:7b
```

### Configuration File

Create `~/.hanzo/config.yaml`:

```yaml
api:
  key: your-api-key
  base_url: https://api.hanzo.ai

router:
  url: http://localhost:4000/v1
  auto_start: true

node:
  url: http://localhost:8000/v1
  workers: 4
  models:
    - llama2:7b
    - mistral:7b

models:
  default: gpt-4
  fallback: llama2:7b
```

## Architecture

### Components

- **CLI**: Command-line interface (`cli.py`)
- **Chat**: Interactive chat interface (`commands/chat.py`)
- **Node**: Local AI node management (`commands/node.py`)
- **Router**: LLM proxy management (`commands/router.py`)
- **REPL**: Interactive Python REPL (`interactive/repl.py`)
- **Orchestrator**: Batch task orchestration (`batch_orchestrator.py`)
- **Memory**: Conversation memory (`memory_manager.py`)
- **Fallback**: Resilient API handling (`fallback_handler.py`)

### Port Allocation

- **4000**: Router (LLM proxy)
- **8000**: Node (local AI)
- **9550-9553**: Desktop app integration

## Development

### Setup

```bash
cd pkg/hanzo
uv sync --all-extras
```

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=hanzo
```

### Building

```bash
uv build
```

## License

Apache License 2.0