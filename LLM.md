# Hanzo Python SDK

uv workspace. `uv sync --all-packages`; `uv run pytest tests/ -v`.

## Packages

- **Core:** `hanzoai` (API client) · `hanzo-mcp` (MCP server — thin wrapper that
  discovers tools via `[project.entry-points."hanzo.tools"]`) · `hanzo-memory` ·
  `hanzo-repl` · `hanzo-agent`.
- **Tools** (each exports a `TOOLS` list via its entry point):
  `hanzo-tools-{shell,browser,fs,memory,reasoning,agent,api,lsp,refactor,llm,…}`.

```
hanzo-mcp  ──entry points──►  hanzo-tools-*   (each: a TOOLS list)
```

## Browser tools (hanzo-tools-browser) — zapd consumer

hanzo-mcp hosts **no** server. It connects to the shared local router
`~/.zap/run/zapd.sock` (see `~/work/zap`) as a *consumer*, lists providers, and routes
opaque CDP to a `browser:*` provider (the real Chrome/Firefox extension via its native
host). No in-process server, no mDNS, no port pool, no HTTP bridge, no Playwright
fallback in native-browser mode.

```python
from hanzo_tools.browser.zapd_consumer import get_consumer
c = get_consumer()                          # ~/.zap/run/zapd.sock
c.resolve_browser("chrome", None)           # -> browser:chrome/<host>/default
c.route(provider, "Target.getTargets", {})  # opaque command, raw result bytes
```

Two tools, one transport: `browser` (high-level verbs) + `cdp` (raw CDP method by
name). Files: `zapd_consumer.py` (envelope codec + consumer), `browser_tool.py`,
`cdp_tool.py`. Unit-tested in `tests/test_browser_tools.py` (zapd mocked) + against a
live zapd; the router (`zap-proto/zapd`) owns the transport tests.

`hanzo-mcp` pins `hanzo-tools-browser[playwright]>=0.5.8` (the zapd-consumer version);
the Claude Code MCP entry sources it from disk via
`uvx --from pkg/hanzo-mcp --with-editable pkg/hanzo-tools-browser`.

## Memory
SQLite + optional vector (sqlite-vec). `~/.hanzo/{memory,db}` global, `.hanzo/` per
project. Backends: local (default), sqlite, lancedb, kuzu.

## API tool (hanzo-tools-api)
Generic REST over OpenAPI specs (`~/work/hanzo/openapi/`). Auto-detects `GITHUB_TOKEN`,
`OPENAI_API_KEY`, etc. `api(action="list|config|call|spec|ops", provider=…)`. Hanzo
providers: `hanzo`, `hanzo-iam`, `hanzo-gateway`, `hanzo-commerce`, `hanzo-vector`,
`hanzo-cloud`, `hanzo-nexus`.

## Common issues
Import error → `uv sync --all-packages`. Missing tool → check the entry point in the
package's `pyproject.toml`. Backend unavailable → install the optional dep.
