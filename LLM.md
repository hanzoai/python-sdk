# LLM.md — hanzoai/python-sdk

**What this is:** the flagship, most-complete Hanzo SDK — a `uv` workspace of 60+
packages: the typed cloud client (`hanzoai`), agents, MCP server + tools, memory,
distributed compute, and the `hanzo` CLI. `pip install hanzo`.

**Canonical role (one-way SDK model):** Hanzo ships two SDK lines per language —
(1) the full cloud SDK generated from OpenAPI, (2) the AI/agents library. This repo
is the Python flagship of line 2, the reference for every other language.
Completeness: Python → Rust → C++ → Go. One impl, one place; discovery repos link
OUT, never duplicate. Full spec: `~/work/hanzo/SDK-ARCHITECTURE.md`.

## Install / run
```bash
pip install hanzo            # CLI + agents + MCP + client
uv sync --all-packages       # dev: whole workspace
uv run pytest tests/ -v      # tests
```

## Brand rules (hard — enforce in all docs)
- Never "LLM gateway"; never position against LiteLLM. Hanzo is a full AI SDK / AI
  cloud, not a proxy.
- Zen models are our own family — never name upstream models.
- Paths are `/v1/…`, never `/api/…`. Base host: `https://api.hanzo.ai`.
- Voice: "Hanzo — the Open AI Cloud." Crisp, developer-first, no emoji-spam.

## Key entry points
- `pkg/hanzoai/` — typed OpenAPI client (`ApiClient`, `Configuration`, `Ai*Api`).
- `pkg/hanzo/src/hanzo/cli.py` — the `hanzo` CLI command tree.
- `pkg/hanzo-mcp/` — MCP server; tools via `[project.entry-points."hanzo.tools"]`.
- `pkg/hanzo-tools-*/` — one concern each, exports a `TOOLS` list.
- `pkg/hanzo-{agents,agent,network,memory}/` — agent/compute/memory libraries.

**Rules for agents:** update THIS file with significant discoveries; never write
random summary files; keep the README cross-link block intact.
