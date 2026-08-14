# Hanzo Python SDK

A workspace of 65 packages. Two things live here that people usually arrive for:
the API client, and the MCP server.

## The API client (`hanzoai`)

Generated from the Hanzo API's own OpenAPI document — 1814 paths, 2479
operations, 192 API classes over 2460 models. It is documented in the
[repository README](https://github.com/hanzoai/python-sdk#readme), which carries
the install line, the quickstart and the five runnable flows in `examples/`.

```python
import os
from hanzoai.cloud import ApiClient, Configuration, KeysApi

client = ApiClient(
    Configuration(host="https://api.hanzo.ai"),
    "Authorization", f"Bearer {os.environ['HANZO_API_KEY']}",
)

with client as api:
    for key in KeysApi(api).get_keys().keys or []:
        print(key.prefix, key.type, key.created_at)
```

The rest of this site is the MCP server, the agent framework and the tool
packages.

## Installation

=== "MCP server"
    ```bash
    pip install hanzo-mcp
    ```

=== "Agent SDK"
    ```bash
    pip install hanzo-agent
    ```

=== "Using uv"
    ```bash
    uv pip install hanzo-mcp
    ```

## Quick Start

### Using with Claude Code

The easiest way to use Hanzo MCP is with Claude Code:

```bash
# Install globally
uvx hanzo-mcp

# Or run directly
uvx hanzo-mcp --transport stdio
```

### Agent SDK Example

```python
from agents import Agent, Runner

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant."
)

result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
```

### MCP Tools Example

```python
from hanzo_mcp import create_mcp_server

# Create server with all tools
server = create_mcp_server()
server.run()
```

## Packages

| Package | Description | PyPI |
|---------|-------------|------|
| `hanzo-mcp` | MCP server with all tools | [![PyPI](https://img.shields.io/pypi/v/hanzo-mcp)](https://pypi.org/project/hanzo-mcp/) |
| `hanzo-agent` | Agent SDK | [![PyPI](https://img.shields.io/pypi/v/hanzo-agent)](https://pypi.org/project/hanzo-agent/) |
| `hanzo-tools-shell` | Shell/command tools | [![PyPI](https://img.shields.io/pypi/v/hanzo-tools-shell)](https://pypi.org/project/hanzo-tools-shell/) |
| `hanzo-tools-fs` | File system tools | [![PyPI](https://img.shields.io/pypi/v/hanzo-tools-fs)](https://pypi.org/project/hanzo-tools-fs/) |
| `hanzo-tools-browser` | Browser automation | [![PyPI](https://img.shields.io/pypi/v/hanzo-tools-browser)](https://pypi.org/project/hanzo-tools-browser/) |
| `hanzo-tools-memory` | Memory/knowledge tools | [![PyPI](https://img.shields.io/pypi/v/hanzo-tools-memory)](https://pypi.org/project/hanzo-tools-memory/) |

## Features

### 30+ MCP Tools

- **File System**: `read`, `write`, `edit`, `tree`, `find`, `search`, `ast`
- **Shell**: `cmd`, `zsh`, `bash`, `ps`, `npx`, `uvx`, `open`
- **Browser**: Full Playwright automation with 70+ actions
- **Memory**: Unified memory tool with recall, create, update, delete
- **Reasoning**: `think`, `critic` for structured AI reasoning
- **LSP**: Go-to-definition, find references, rename, hover
- **Refactor**: Advanced code refactoring with AST support
- **Agent**: Run external AI agents (Claude, Gemini, Codex, etc.)
- **LLM**: Direct LLM access and multi-model consensus

### Auto-Backgrounding

Long-running commands automatically background after 30 seconds:

```python
# This will auto-background if it takes too long
cmd("npm install")

# Check status
ps()  # List all background processes
ps(logs="cmd_xxx")  # View output
ps(kill="cmd_xxx")  # Stop process
```

### Multi-Backend Support

Use the MCP with any AI assistant:

- **Claude Code** - `uvx hanzo-mcp`
- **VS Code/Cursor** - Hanzo extension with auto-detection
- **Antigravity** - Full integration via Open VSX
- **Any MCP Client** - Standard MCP protocol

## Documentation

### Getting Started

- [Quickstart Guide](getting-started/quickstart.md)
- [MCP Quickstart](mcp/quickstart.md)
- [MCP Configuration](mcp/configuration.md)

### Reference

- [Tools Reference](tools/index.md) - All 30+ tool packages
- [Agent Reference](ref/agent/index.md) - Agent SDK documentation
- [MCP Reference](ref/mcp/index.md) - MCP server documentation
- [Core Libraries](lib/index.md) - Supporting packages (async, consensus, network)

### Tool Categories

- [Filesystem Tools](tools/fs.md) - File operations and AST analysis
- [Shell Tools](tools/shell.md) - Command execution and process management
- [Browser Tool](tools/browser.md) - Playwright automation
- [Memory Tools](tools/memory.md) - Persistent memory and knowledge bases
- [Reasoning Tools](tools/reasoning.md) - Structured thinking and analysis

## Links

- [GitHub Repository](https://github.com/hanzoai/python-sdk)
- [PyPI Package](https://pypi.org/project/hanzo-mcp/)
- [Discord Community](https://discord.gg/CJCyAsm9Vr)
- [Hanzo AI](https://hanzo.ai)
