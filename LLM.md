# LLM.md - Hanzo Python SDK

## Quick Start

```bash
uv sync --all-packages
uv run python -c "from hanzoai import __version__; print(__version__)"
```

## Packages

### Core (Workspace Members)
| Package | Import | Description |
|---------|--------|-------------|
| hanzoai | `import hanzoai` | Official Hanzo API client |
| hanzo-mcp | `import hanzo_mcp` | MCP server with 39 tools |
| hanzo-memory | `import hanzo_memory` | Memory service with SQLite/vector |
| hanzo-repl | `import hanzo_repl` | Interactive REPL |
| hanzo-agent | `import hanzo_agent` | Agent framework |

### Tool Packages (Entry Points)
All tools discovered via `[project.entry-points."hanzo.tools"]`:

- `hanzo-tools-shell` - zsh, ps, open, npx, uvx
- `hanzo-tools-browser` - Playwright automation
- `hanzo-tools-fs` - read, write, edit, tree, find, search, ast
- `hanzo-tools-memory` - Unified memory tool
- `hanzo-tools-reasoning` - think, critic
- `hanzo-tools-agent` - CLI agent runner, iching, review
- `hanzo-tools-api` - Generic REST API via OpenAPI
- `hanzo-tools-lsp` - Language server protocol
- `hanzo-tools-refactor` - AST-based refactoring
- `hanzo-tools-llm` - LLM calls, consensus

## Architecture

```
hanzo-mcp (thin wrapper)
  └── discovers tools via entry points from hanzo-tools-* packages

hanzo-tools-*
  └── each exports TOOLS list via entry point
```

**Entry Point Pattern:**
```toml
[project.entry-points."hanzo.tools"]
shell = "hanzo_tools.shell:TOOLS"
```

## Key Patterns

### Tool Registration
```python
class MyTool(BaseTool):
    name = "my_tool"

    @property
    def description(self) -> str:
        return "Tool description"

    async def call(self, ctx, **params) -> str:
        pass
```

### Async (Non-blocking)
```python
# Use asyncio subprocess
proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

# Use aiofiles for file I/O
async with aiofiles.open(path) as f:
    content = await f.read()
```

### Auto-backgrounding
Commands auto-background after 45s. Use `ps` tool to monitor.

## Memory System

SQLite-based with optional vector search (sqlite-vec).

```
~/.hanzo/
├── memory/           # Global markdown files
└── db/
    └── global.db     # SQLite with FTS5

/project/.hanzo/
├── memory/           # Project memories
└── db/
    └── memory.db     # Project database
```

**Backends:** local (default), sqlite, lancedb (optional), kuzudb (optional)

## Browser Tool (hanzo-tools-browser)

Two-process architecture (since 0.5.0): `hanzo-tools-browser` hosts the
ZAP server directly inside the MCP process. Browser extensions discover
it on the lowest free port from `[9999, 9998, 9997, 9996, 9995]` (POSIX
flock ensures multi-MCP coexistence under one ext).

```python
from hanzo_tools.browser import (
    BrowserTool,            # the MCP tool
    ZapServer,              # raw server (for advanced use)
    get_or_start_server,    # bootstrap + return singleton
    get_server,             # return current singleton or None
)
```

Key files:
- `hanzo_tools/browser/zap_server.py` — wire format, server, leases,
  cluster registry (`~/.hanzo/extension/config.json:mcp_instances`).
- `hanzo_tools/browser/browser_tool.py` — `_extension_command` tries
  ZAP first, falls back to legacy HTTP bridge on `:9224`. New actions
  `list_mcp_instances`, `claim_browser`, `release_browser`.
- `hanzo_tools/browser/cdp_bridge_server.py` — legacy node-bridge
  replacement (kept for non-ZAP callers).

Env vars:
- `BROWSER_TRANSPORT=zap|http|auto` — pin transport (default auto).
- `HANZO_ZAP_DISABLED=1` — don't auto-start the ZAP server.
- `HANZO_ZAP_PORTS=9999,9998` — override the candidate port list.
- `HANZO_AGENT_LABEL=...` — attach to the cluster registry entry.
- `HANZO_CDP_BRIDGE_ENABLED=1` — opt back into the legacy HTTP bridge.

Tests live in `pkg/hanzo-tools-browser/tests/test_zap_server.py` (30
cases: wire format, lifecycle, RPC, leases, multi-MCP). Latency bench
in `test_zap_bench.py`. The full suite runs with:

```bash
cd pkg/hanzo-tools-browser
uv venv .venv --python 3.12
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest tests/ -v
```

## API Tool

Generic REST API tool with OpenAPI specs.

```python
api(action="list")                                    # List providers
api(action="config", provider="github", api_key="x") # Configure
api(action="call", provider="github", operation="listRepos")
```

Auto-detects: `GITHUB_TOKEN`, `CLOUDFLARE_API_TOKEN`, `OPENAI_API_KEY`, etc.

### Hanzo API Providers

All Hanzo services have unified OpenAPI specs at `/Users/z/work/hanzo/openapi/`:

| Provider | Service | Base URL | Spec |
|----------|---------|----------|------|
| `hanzo` | Unified API | api.hanzo.ai | `hanzo.yaml` |
| `hanzo-iam` | Identity/Auth | iam.hanzo.ai | `iam/openapi.yaml` |
| `hanzo-gateway` | LLM Gateway | gateway.hanzo.ai | `gateway/openapi.yaml` |
| `hanzo-commerce` | E-commerce | api.hanzo.ai/v1 | `commerce/openapi.yaml` |
| `hanzo-vector` | Vector DB | vector.hanzo.ai | `vector/openapi.yaml` |
| `hanzo-cloud` | AI Platform | cloud.hanzo.ai | `cloud/openapi.yaml` |
| `hanzo-nexus` | RAG/Knowledge | nexus.hanzo.ai | `nexus/openapi.yaml` |

```python
# Example: Call IAM API
api(action="spec", provider="hanzo-iam")
api(action="ops", provider="hanzo-iam", search="user")
api(action="call", provider="hanzo-iam", operation="getUser", params='{"id": "admin/user1"}')
```

## Testing

```bash
uv run pytest tests/ -v
uv run python -c "from hanzoai import __version__; print(__version__)"
```

## Common Issues

**Import error:** Run `uv sync --all-packages`

**Missing tool:** Check entry point in package's pyproject.toml

**Backend not available:** Install optional deps (lancedb, kuzu, sqlite-vec)
