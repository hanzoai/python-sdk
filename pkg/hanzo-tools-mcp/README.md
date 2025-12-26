# hanzo-tools-mcp

MCP server management tools for Hanzo AI.

## Tools

- `mcp` - Unified MCP server management (list, add, remove, enable, disable, restart)
- `mcp_add` - Add new MCP servers
- `mcp_remove` - Remove MCP servers
- `mcp_stats` - MCP server statistics

## Installation

```bash
pip install hanzo-tools-mcp
```

## Usage

```python
from hanzo_tools.mcp_tools import TOOLS, register_tools

# Register with MCP server
register_tools(mcp_server)
```

## Part of hanzo-tools

This package is part of the modular [hanzo-tools](../hanzo-tools) ecosystem.
