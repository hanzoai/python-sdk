# hanzo-tools-config

Configuration tools for Hanzo AI MCP.

## Tools

- `config` - Git-style configuration management
- `mode` - Development mode switching

## Installation

```bash
pip install hanzo-tools-config
```

## Usage

```python
from hanzo_tools.config import TOOLS, register_tools

# Register with MCP server
register_tools(mcp_server)
```

## Part of hanzo-tools

This package is part of the modular [hanzo-tools](../hanzo-tools) ecosystem.
