# hanzo-tools-vcs

Unified version control tool for Hanzo AI MCP (HIP-0300).

## Tools

- `git` - Unified version control (status, diff, commit, branch, log, …)

## Installation

```bash
pip install hanzo-tools-vcs
```

## Usage

```python
from hanzo_tools.vcs import TOOLS, register_tools

# Register with MCP server
register_tools(mcp_server)
```

## Part of hanzo-tools

This package is part of the modular [hanzo-tools](../hanzo-tools) ecosystem.
