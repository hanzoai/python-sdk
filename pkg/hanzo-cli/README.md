# Hanzo CLI

Unified command-line interface for Hanzo AI - Local, Private, Free AI Infrastructure.

## Features

- 🤖 **AI Chat** - Interactive chat with multiple LLM providers
- 🛠️ **MCP Tools** - Access to 70+ Model Context Protocol tools
- 🌐 **Agent Networks** - Distributed AI agent orchestration
- ⛏️ **Mining** - Contribute compute and earn rewards
- 🔐 **Authentication** - Secure access with Hanzo IAM
- 📊 **Monitoring** - Real-time cluster and agent status
- 🎨 **Beautiful UI** - Rich terminal interface with syntax highlighting

## Installation

```bash
# Basic installation
pip install hanzo

# With all features
pip install hanzo[all]

# With specific features
pip install hanzo[repl]     # Interactive REPL
pip install hanzo[cluster]  # Local AI cluster
pip install hanzo[network]  # Agent networks
```

## Quick Start

### Authentication

```bash
# Login with email/password
hanzo auth login

# Use API key
export HANZO_API_KEY=your-key
hanzo auth status
```

### AI Chat

```bash
# Interactive chat
hanzo chat

# Quick question
hanzo ask "What is the capital of France?"

# With specific model
hanzo chat --model claude-3.5-sonnet

# Start REPL (like Claude Code)
hanzo chat --repl
```

### Local AI Cluster

```bash
# Start local cluster
hanzo serve

# Or with options
hanzo cluster start --models llama-3.2-3b --port 8000

# Check status
hanzo cluster status

# Start as node
hanzo cluster node start --blockchain --network
```

### MCP Tools

```bash
# List available tools
hanzo mcp tools

# Run a tool
hanzo mcp run read_file --arg file_path=README.md

# Start MCP server
hanzo mcp serve

# Install in Claude Desktop
hanzo mcp install
```

### Agent Networks

```bash
# Dispatch work to network
hanzo network dispatch "Analyze this codebase and suggest improvements"

# Start local swarm
hanzo network swarm --agents 5

# List available agents
hanzo network agents
```

### Mining

```bash
# Start mining
hanzo miner start --wallet 0x... --models llama-3.2-3b

# Check earnings
hanzo miner earnings --wallet 0x...

# View leaderboard
hanzo miner leaderboard
```

## Configuration

### Environment Variables

```bash
# API Keys
export HANZO_API_KEY=your-hanzo-key
export ANTHROPIC_API_KEY=your-anthropic-key
export OPENAI_API_KEY=your-openai-key

# Preferences
export HANZO_DEFAULT_MODEL=claude-3.5-sonnet
export HANZO_USE_LOCAL=true
```

### Configuration File

```bash
# Initialize config
hanzo config init

# Set values
hanzo config set default_model claude-3.5-sonnet
hanzo config set mcp.allowed_paths /home/user/projects

# View config
hanzo config show
```

## Advanced Usage

### Interactive REPL

The REPL provides direct access to all MCP tools and AI capabilities:

```bash
# Start REPL
hanzo repl start

# With IPython interface
hanzo repl start --ipython

# With TUI interface
hanzo repl start --tui
```

In the REPL:
```python
# Direct tool access
>>> read_file(file_path="config.json")
>>> search(query="TODO", path=".")

# Chat with AI
>>> chat("Create a FastAPI server with authentication")

# AI uses tools automatically
>>> chat("Find all Python files and create a dependency graph")
```

### Tool Management

```bash
# Install custom tools
hanzo tools install my-tool

# Create new tool
hanzo tools create my-custom-tool

# List installed tools
hanzo tools list --installed
```

### Dashboard

```bash
# Start interactive dashboard
hanzo dashboard
```

## Command Reference

### Main Commands

- `hanzo auth` - Authentication management
- `hanzo chat` - Interactive AI chat
- `hanzo cluster` - Local AI cluster management
- `hanzo mcp` - Model Context Protocol tools
- `hanzo agent` - Agent management
- `hanzo network` - Agent network operations
- `hanzo miner` - Mining operations
- `hanzo tools` - Tool management
- `hanzo config` - Configuration management
- `hanzo repl` - Interactive REPL

### Quick Aliases

- `hanzo ask <question>` - Quick AI question
- `hanzo serve` - Start local cluster
- `hanzo dashboard` - Open dashboard

## Examples

### Complex Workflows

```bash
# Analyze project and create documentation
hanzo network dispatch "Analyze this Python project and create comprehensive documentation" --agents 3

# Start mining with specific configuration
hanzo miner start --wallet 0x123... --models "llama-3.2-3b,mistral-7b" --min-stake 100

# Create and deploy an agent
hanzo agent create researcher --model gpt-4
hanzo agent start researcher --task "Research best practices for API security"
```

### Integration with Other Tools

```bash
# Use with pipes
echo "Explain this error" | hanzo chat --once

# Process files
find . -name "*.py" | xargs hanzo mcp run analyze_code

# Combine with jq
hanzo network jobs --json | jq '.[] | select(.status=="completed")'
```

## Troubleshooting

### Common Issues

1. **No LLM provider configured**
   ```bash
   export ANTHROPIC_API_KEY=your-key
   # or
   hanzo auth login
   ```

2. **Local cluster not running**
   ```bash
   hanzo cluster start
   # or
   hanzo serve
   ```

3. **Permission denied for MCP tools**
   ```bash
   hanzo config set mcp.allowed_paths /path/to/allow
   ```

### Debug Mode

```bash
# Enable debug output
export HANZO_DEBUG=true
hanzo chat

# Verbose logging
hanzo --verbose chat
```

## Contributing

See the main [Hanzo Python SDK](https://github.com/hanzoai/python-sdk) repository.

## License

BSD-3-Clause - see LICENSE file for details.