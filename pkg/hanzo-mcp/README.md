# hanzo-mcp

[![PyPI](https://img.shields.io/pypi/v/hanzo-mcp.svg)](https://pypi.org/project/hanzo-mcp/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzo-mcp.svg)](https://pypi.org/project/hanzo-mcp/)

A Model Context Protocol server. It gives an MCP client — Claude Desktop, an
editor, an agent — filesystem, shell, search and agent tools over one
connection.

## Install

```bash
pip install hanzo-mcp
```

## Run

```bash
hanzo-mcp                                   # stdio, the transport clients speak
hanzo-mcp --transport sse --host 127.0.0.1 --port 8888
hanzo-mcp --install                         # write the config into Claude Desktop
```

Point it at what it may touch, and nothing else:

```bash
hanzo-mcp --allow-path ~/work/project --project-dir ~/work/project
```

`--allow-path` may be repeated. Every filesystem tool refuses a path outside the
set, and `..` and `~` are refused before resolution.

## Flags

| flag | what it does |
|---|---|
| `--transport {stdio,sse}` | how the client connects; `stdio` by default |
| `--allow-path PATH` | grant access to a path; repeatable |
| `--project-dir DIR` | the project root, also granted |
| `--enable-agent` | let the server delegate to sub-agents |
| `--agent-model`, `--agent-api-key`, `--agent-base-url` | which model the agent tool calls |
| `--disable-write-tools` | read-only: no write, edit or shell mutation |
| `--disable-search-tools` | drop the search family |
| `--command-timeout`, `--search-timeout`, `--find-timeout`, `--ast-timeout` | per-family limits, in seconds |
| `--shell`, `--force-shell`, `--all-shells` | which shell the shell tools use |
| `--log-level LEVEL` | server logging |

`hanzo-mcp --help` prints the whole set; `--version` prints the build.

## Tools

The server registers what the installed `hanzo-tools-*` packages provide — each
one publishes a `TOOLS` list under the `hanzo.tools` entry point, and the server
loads every package it finds. `hanzo-tools-fs`, `hanzo-tools-shell` and
`hanzo-tools-core` come with this package; install another and its tools appear
on the next start.

```bash
pip install hanzo-tools-git hanzo-tools-sql
```

## In a client

Claude Desktop, `claude_desktop_config.json` — or `hanzo-mcp --install`, which
writes it for you:

```json
{
  "mcpServers": {
    "hanzo": {
      "command": "hanzo-mcp",
      "args": ["--allow-path", "/Users/you/work"]
    }
  }
}
```

## Embedding it

```python
from hanzo_mcp.server import HanzoMCPServer

server = HanzoMCPServer(name="hanzo", allowed_paths=["/Users/you/work"])
server.run(transport="stdio")
```

`run` blocks, and takes the transport. The rest of what the CLI accepts —
`allowed_paths`, `project_dir`, `enable_agent_tool`, `disable_write_tools`,
`disable_search_tools`, the timeouts — are constructor keywords.

## Development

```bash
uv sync
uv run pytest tests/ -v
```

## License

Apache-2.0.
