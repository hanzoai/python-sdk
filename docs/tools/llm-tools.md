# hanzo-tools-llm

Unified LLM interface with multi-model consensus. Access 100+ models through a single tool.

## Installation

```bash
pip install hanzo-tools-llm[full]
```

Note: This package requires `litellm` which is a heavy dependency. It's disabled by default in hanzo-mcp.

## Overview

`hanzo-tools-llm` provides:

- **llm** - Unified LLM interface (query, consensus, model management)
- **consensus** - Multi-model consensus protocol

## Quick Start

```python
# Simple query
llm(action="query", prompt="Explain quantum computing", model="gpt-4")

# Multi-model consensus
llm(
    action="consensus",
    prompt="Best approach for distributed caching?",
    models=["gpt-4", "claude-3-opus", "gemini-pro"]
)

# List available models
llm(action="list")

# Enable/disable providers
llm(action="enable", provider="anthropic")
llm(action="disable", provider="openai")
```

## Actions Reference

### query

Send a prompt to an LLM.

```python
# Basic query
llm(action="query", prompt="Hello, world!", model="gpt-4")

# With system prompt
llm(
    action="query",
    prompt="Explain this code",
    model="claude-3-opus-20240229",
    system_prompt="You are a senior software engineer"
)

# With temperature control
llm(
    action="query",
    prompt="Generate creative names",
    model="gpt-4",
    temperature=0.9
)

# JSON mode
llm(
    action="query",
    prompt="List 5 programming languages with pros/cons",
    model="gpt-4",
    json_mode=True
)

# Streaming
llm(
    action="query",
    prompt="Write a long story",
    model="gpt-4",
    stream=True
)
```

**Parameters:**
- `prompt` (required): The prompt to send
- `model`: Model name (default: auto-select)
- `system_prompt`: System context
- `temperature`: Response randomness (0-2, default: 0.7)
- `max_tokens`: Maximum response tokens
- `json_mode`: Request JSON output (default: false)
- `stream`: Stream response (default: false)

### consensus

Get consensus from multiple models.

```python
llm(
    action="consensus",
    prompt="What's the best way to handle errors in Go?",
    models=["gpt-4", "claude-3-opus", "gemini-pro"],
    include_raw=True,        # Include individual responses
    judge_model="gpt-4",     # Model to synthesize consensus
    devils_advocate=True     # Add critical analysis
)
```

**Parameters:**
- `prompt` (required): Question for consensus
- `models`: List of models to query (default: auto-select 3)
- `consensus_size`: Number of models if not specifying (default: 3)
- `include_raw`: Include raw responses (default: false)
- `judge_model`: Model to aggregate responses
- `devils_advocate`: Add 10th model for critique (default: false)

**Response:**
```json
{
  "consensus": "The agreed-upon answer synthesized from all models...",
  "confidence": 0.85,
  "models_queried": ["gpt-4", "claude-3-opus", "gemini-pro"],
  "agreement_level": "high",
  "raw_responses": [...]  // if include_raw=true
}
```

### list

List available models and providers.

```python
llm(action="list")
```

**Response:**
```json
{
  "providers": {
    "openai": {"enabled": true, "models": ["gpt-4", "gpt-3.5-turbo"]},
    "anthropic": {"enabled": true, "models": ["claude-3-opus", "claude-3-sonnet"]},
    "google": {"enabled": false, "models": ["gemini-pro"]}
  }
}
```

### models

List models for a specific provider.

```python
llm(action="models", provider="openai")
```

### enable / disable

Enable or disable a provider.

```python
# Enable a provider
llm(action="enable", provider="anthropic")

# Disable a provider
llm(action="disable", provider="openai")
```

### test

Test connectivity to a model.

```python
llm(action="test", model="gpt-4")
```

## Supported Providers

The LLM tool uses [LiteLLM](https://github.com/BerriAI/litellm) to support 100+ models:

| Provider | Models | API Key Env |
|----------|--------|-------------|
| OpenAI | gpt-4, gpt-3.5-turbo | `OPENAI_API_KEY` |
| Anthropic | claude-3-opus, claude-3-sonnet | `ANTHROPIC_API_KEY` |
| Google | gemini-pro, gemini-ultra | `GOOGLE_API_KEY` |
| Azure | All Azure OpenAI models | `AZURE_API_KEY` |
| AWS Bedrock | claude, titan | AWS credentials |
| Cohere | command, command-r | `COHERE_API_KEY` |
| Together | Various open models | `TOGETHER_API_KEY` |
| Ollama | Local models | - |
| And more... | | |

## ConsensusTool

Dedicated tool for multi-model consensus:

```python
consensus(
    prompt="Should we use microservices or monolith?",
    models=["gpt-4", "claude-3-opus", "gemini-pro"],
    rounds=3
)
```

## Examples

### Code Review with Consensus

```python
# Get multiple perspectives on code
llm(
    action="consensus",
    prompt="""Review this function for issues:
    
    def process(data):
        result = []
        for item in data:
            if item > 0:
                result.append(item * 2)
        return result
    """,
    models=["gpt-4", "claude-3-opus", "gemini-pro"],
    devils_advocate=True
)
```

### Choosing Best Model for Task

```python
# List available models
models = llm(action="list")

# Test specific model
llm(action="test", model="claude-3-opus-20240229")

# Query with best model
llm(
    action="query",
    prompt="Complex reasoning task",
    model="claude-3-opus-20240229"
)
```

### JSON Output

```python
# Get structured data
response = llm(
    action="query",
    prompt="List 3 Python web frameworks with their pros and cons",
    model="gpt-4",
    json_mode=True
)

# Response will be valid JSON
```

### Creative vs Deterministic

```python
# Creative task (high temperature)
llm(
    action="query",
    prompt="Write a poem about coding",
    model="gpt-4",
    temperature=0.9
)

# Deterministic task (low temperature)
llm(
    action="query",
    prompt="Convert this SQL to Python",
    model="gpt-4",
    temperature=0.1
)
```

## Configuration

### API Keys

Set API keys via environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

### Default Model

Set default model via environment:

```bash
export HANZO_DEFAULT_LLM_MODEL="gpt-4"
```

### Model Aliases

Configure model aliases in `~/.hanzo/llm/aliases.json`:

```json
{
  "smart": "gpt-4",
  "fast": "gpt-3.5-turbo",
  "creative": "claude-3-opus-20240229"
}
```

## Performance Tips

1. **Use streaming for long responses** - Better UX for users
2. **Cache responses when appropriate** - Same prompt = same response
3. **Choose model based on task** - GPT-3.5 for simple, GPT-4 for complex
4. **Set max_tokens** - Avoid unnecessarily long responses
5. **Use consensus for important decisions** - Multiple perspectives reduce errors

## Best Practices

1. **Set appropriate temperature** - Low for factual, high for creative
2. **Use system prompts** - Provide context for better responses
3. **Validate JSON output** - Even with json_mode, validate responses
4. **Handle rate limits** - LiteLLM handles retries automatically
5. **Monitor costs** - Different models have different pricing
