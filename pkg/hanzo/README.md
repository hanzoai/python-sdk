# Hanzo AI - Complete AI Infrastructure Platform

The main SDK for the Hanzo AI ecosystem, providing unified access to all Hanzo tools and services.

## Installation

```bash
# Install base package with CLI
pip install hanzo

# Install with all components
pip install hanzo[all]

# Install specific components
pip install hanzo[ai]      # AI SDK (same as standalone hanzoai package)
pip install hanzo[router]  # LLM gateway router (replaces litellm)
pip install hanzo[mcp]     # Model Context Protocol server
pip install hanzo[agents]  # Agent runtime and orchestration
pip install hanzo[repl]    # Interactive REPL with AI chat
```

## Features

- **Unified LLM Gateway**: Use `hanzo.router` instead of litellm for 100+ LLM providers
- **MCP Integration**: Full Model Context Protocol support for AI tools
- **Agent Runtime**: Build and deploy AI agents with the agent framework
- **Interactive REPL**: Chat with AI models directly from the command line
- **Complete SDK**: Import all Hanzo components from a single package

## Quick Start

### Command Line
```bash
# Main CLI
hanzo --help

# Start MCP server
hanzo-mcp

# Interactive AI chat
hanzo-ai
hanzo-chat

# REPL interface
hanzo-repl
```

### Python SDK
```python
import hanzo

# Use router for LLM calls (replaces litellm)
from hanzo import router
response = router.completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Use agents
from hanzo import Agent, Network
agent = Agent(name="assistant")

# Use MCP tools
from hanzo import Tool, MCPServer

# Access AI SDK
from hanzo import Client
client = Client(api_key="...")
```

## Components

- **hanzo.router**: Unified LLM gateway (replaces litellm)
- **hanzo.mcp**: Model Context Protocol server and tools
- **hanzo.agents**: Agent runtime and orchestration
- **hanzo.memory**: Memory systems for agents
- **hanzo.Client**: Main AI SDK client

## Documentation

- [Hanzo AI Docs](https://docs.hanzo.ai)
- [Router Documentation](https://docs.hanzo.ai/router)
- [MCP Documentation](https://docs.hanzo.ai/mcp)
- [Agent Documentation](https://docs.hanzo.ai/agents)