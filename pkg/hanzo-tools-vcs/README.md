# hanzo-tools-vcs

Version control tools for Hanzo AI MCP (HIP-0300).

## Tools

- `git` - Unified version control (status, diff, commit, branch, log, …)
- `repo` - Your repositories on Hanzo git and the GitHub links that feed them,
  through `api.hanzo.ai` with your Hanzo credential: `list` (`GET /v1/sync`; each
  link's id, scope, source, target, direction, trigger, status, branch, url and
  last sync; `search` and `status` narrow it) and `sync` (`POST /v1/sync/{id}/run`,
  sync one now).

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
