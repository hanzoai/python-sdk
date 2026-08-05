# hanzo-tools-net

Network tools for Hanzo AI MCP (HIP-0300).

## Tools

- `fetch` — the web, one door per verb:
  - `search` — query → [url, title, snippet]
  - `web_read` — url → clean markdown
  - `research` — question → cited answer + sources (search + read + synthesize)
  - `fetch` / `download` / `crawl` / `head` / `request` / `open`
- `vision` — image (+ prompt) → text answer

## Installation

```bash
pip install hanzo-tools-net
```

## Usage

```python
from hanzo_tools.net import TOOLS, register_tools

# Register with MCP server
register_tools(mcp_server)
```

## Part of hanzo-tools

This package is part of the modular [hanzo-tools](../hanzo-tools) ecosystem.
