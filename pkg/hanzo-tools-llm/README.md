# hanzo-tools-llm

LLM interaction tools for Hanzo AI MCP.

## Tools

- `llm` - Core LLM interaction with multiple providers
- `unified_llm` - Unified LLM interface
- `consensus` - Multi-model consensus for higher accuracy
- `llm_manage` - Model management and provider configuration

## Installation

```bash
pip install hanzo-tools-llm

# With all LLM providers
pip install hanzo-tools-llm[full]
```

## Supported Providers

- OpenAI (GPT-4, GPT-4o, etc.)
- Anthropic (Claude 4, Claude 3.5)
- Together AI
- Ollama (local models)

## Usage

```python
from hanzo_tools.llm import TOOLS, LLM_AVAILABLE, register_tools

if LLM_AVAILABLE:
    register_tools(mcp_server)
```

## Part of hanzo-tools

This package is part of the modular [hanzo-tools](../hanzo-tools) ecosystem.
