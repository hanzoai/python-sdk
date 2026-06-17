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

**hanzo-mcp is a `zapd` *consumer*** — it hosts NO server. It connects to the
one shared local router `~/.zap/run/zapd.sock` (see `~/work/zap`), lists
providers, and routes opaque commands to a `browser:*` provider (the real Chrome/
Firefox extension, connected via the native host). No in-process server, no mDNS,
no `9999-9995`, no `:9224` HTTP bridge, no `BROWSER_TRANSPORT`, no Playwright
fallback in native-browser mode. The old `zap_server.py`/`cdp_bridge_server.py`
in-process model is removed.

```python
from hanzo_tools.browser.zapd_consumer import ZapdConsumer, get_consumer
c = get_consumer()                          # connects to ~/.zap/run/zapd.sock
c.resolve_browser("chrome", None)           # -> "browser:chrome/<host>/default"
c.route(provider, "Target.getTargets", {})  # opaque command, raw result bytes
```

Key files:
- `hanzo_tools/browser/zapd_consumer.py` — the ZAP router-envelope codec +
  consumer (connect / hello / providers.list / route). Mirrors `zapd/src/frame.rs`.
- `hanzo_tools/browser/browser_tool.py` — `_extension_command` / `_check_extension`
  route via `zapd_consumer`. `register_browser_tools` no longer starts a server.
- `hanzo_tools/browser/cdp_tool.py` — the `cdp` tool, a method-oriented peer of
  `browser`. Sends a raw CDP method by name (`Target.getTargets`, `Page.navigate`)
  through the SAME `zapd_consumer` route — the method goes on the wire verbatim,
  so there is no `{"action":"cdp"}` envelope for the extension to reject.

Two tools, one transport: `browser` (high-level verbs) and `cdp` (raw methods).
Both are in `TOOLS` and resolve to the same zapd provider.

The router (`zapd`) is a separate always-on daemon — install/run it from
`zap-proto/zapd` (`curl … | sh` or `@hanzo/zapd`).

**MCP must be sourced from disk, not PyPI.** The published `hanzo-tools-browser`
wheel (≤0.5.7) still ships the removed in-process HTTP-bridge model and breaks
`cdp` with `Unknown method: cdp`. The Claude Code MCP entry in `~/.claude.json`
therefore uses `uvx --from pkg/hanzo-mcp --with-editable pkg/hanzo-tools-browser`
so the on-disk source (≥0.5.8) is authoritative. `--with <python-sdk root>` does
NOT work — uv ignores the workspace sources for `--from` deps and pulls the buggy
wheel from the index. `hanzo-mcp` pins `hanzo-tools-browser>=0.5.8` as a guard.

Router/transport tests live with the router (`zap-proto/zapd`: `cargo test` +
`tests/e2e.py`). The Python consumer + `cdp` routing are unit-tested in
`tests/test_browser_tools.py` (zapd mocked) and verified end-to-end against a
live `zapd`. The old `test_zap_server.py`/`zap_server.py` (in-process server,
leases, multi-MCP) and `cdp_bridge_server.py` are removed.

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
