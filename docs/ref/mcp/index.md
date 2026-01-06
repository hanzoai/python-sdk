# MCP Reference

API reference for hanzo-mcp (Model Context Protocol).

## Overview

hanzo-mcp provides:

- 30+ tools for AI development
- FastMCP-based server
- Claude Code integration
- Entry-point based tool discovery

## Documentation

| Topic | Description |
|-------|-------------|
| [Quickstart](../../mcp/quickstart.md) | Getting started |
| [Configuration](../../mcp/configuration.md) | Server configuration |
| [VS Code Setup](../../mcp/vscode.md) | IDE integration |
| [Tool Parity](../../mcp/PARITY.md) | Feature comparison |

## Tool Categories

| Category | Docs |
|----------|------|
| [Shell](../../mcp/tools/shell.md) | Command execution |
| [Filesystem](../../mcp/tools/filesystem.md) | File operations |
| [Browser](../../mcp/tools/browser.md) | Web automation |
| [Memory](../../mcp/tools/memory.md) | Persistent memory |
| [Reasoning](../../mcp/tools/reasoning.md) | Thinking tools |
| [Agent](../../mcp/tools/agent.md) | Multi-agent |
| [LSP](../../mcp/tools/lsp.md) | Code intelligence |
| [LLM](../../mcp/tools/llm-tools.md) | LLM interface |

## Quick Start

```bash
# Install
pip install hanzo-mcp[tools-all]

# Run server
hanzo-mcp

# Or with specific tools
hanzo-mcp --tools shell,browser,memory
```

## Claude Code Integration

```json
{
  "mcpServers": {
    "hanzo": {
      "command": "hanzo-mcp",
      "args": ["--stdio"]
    }
  }
}
```

## See Also

- [Tools Reference](../tools/index.md) - Full tool documentation
- [Core Libraries](../../lib/index.md) - Supporting packages
