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

## Unified cloud surface (`hanzo` tool)
One `hanzo` tool fronts all Hanzo cloud services; the per-service tools (`api`, `auth`,
`billing`, `commerce`, `iam`, `ingress`, `kms`, `mpc`, `paas`, `team`) are hidden behind
it. `hanzo(service=…, action=…, args='{json}')`; `service="services"` lists them.
It is a pure dispatcher — `SERVICE_TOOL_PATHS` in `hanzo-tools-api/hanzo_tools/api/
hanzo_tool.py` maps a service to the tool class that already implements it. Adding a
service is one line there; never reimplement a service tool inside it.

It ships from `hanzo-tools-api` under its **own** `hanzo` entry point, separate from
`api` — the unified surface is not one of the services it dispatches to.

**The gate is conditional, deliberately.** `register_all_tools` hides the ten only when
`hanzo` is both installed and enabled by the active mode; otherwise the ten stay on and
the server logs a warning. Hiding them unconditionally is what took cloud control
offline once already: the gate shipped before any package provided `hanzo`, so ten tools
vanished and nothing replaced them. Keep both halves — presence *and* enablement.

Mode allowlists are a second, independent gate: a tool absent from the active
personality's `tools` list is off no matter what the loader says. New platform tools
belong in `PLATFORM_TOOLS` in `tools/common/personality.py`.

## Auth — loads, does not work
The tool surface is restored; the backends are mostly not reachable. `LoginTool` has no
login action (status/whoami/logout/refresh only) — real login lives in `hanzo-cli`, and
it targets `hanzo.id/oauth/*` while the IdP serves `/v1/iam/oauth/*`, so the loopback
flow hangs and token exchange parses an HTML SPA as JSON. `hanzo_iam/models.py` already
declares `IAM_ROUTE_PREFIX = "/v1/iam"`; it is simply not applied to token/authorize.
`iam` is the only service on a correct path, and only with `HANZO_AUTH_TOKEN` obtained
elsewhere. `HanzoSession.is_authenticated()` is a string-presence check — it reports
authenticated for any garbage token. PaaS moved to Better Auth (`/v1/auth`), so
`session.py`'s `POST /v1/auth/login` 404s, which also strands `mpc` and `ingress`. KMS
still calls Infisical-legacy `/api/v3/secrets/raw` instead of
`/v1/kms/orgs/{org}/secrets/…`. Tokens land plaintext in `~/.hanzo/auth/token.json`
(0600, but written then chmodded — briefly umask-wide); they belong in KMS.

## Vector search — not wired, on purpose
`hanzo-tools-vector` is not installed and must not be. `TOOLS` is empty (a relative
import of `index_config` that only exists in `hanzo-tools-config`), `_generate_embedding`
returns `random.random()` values, and the store silently falls back to `mock_infinity`,
which discards the query vector and scores with `random.uniform`. It returns confident
nonsense rather than failing. Full-text already ships: `fs`/`search` is ripgrep-backed.

## Common issues
Import error → `uv sync --all-packages`. Missing tool → check the entry point in the
package's `pyproject.toml`, **then** check the active mode's allowlist. Backend
unavailable → install the optional dep.
