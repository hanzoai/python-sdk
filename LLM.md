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

## Codegen — this repo PULLS, it never pushes
```
hanzoai/cloud    emits its own router spec    -> cloud/openapi.yaml (984 paths)
hanzoai/openapi  merges 69 per-service specs  -> hanzo.yaml (1885 paths)  [the ONE SDK input]
hanzoai/openapi  generate.py + sdks.yaml      -> projects hanzo.yaml into each SDK repo
this repo        owns its test + PATCH bump + release
```
`pkg/hanzoai/cloud/` is **generated — never hand-edit it.** `generate.py` does
`rmtree(dst) + copytree(src)`, so anything written there dies on the next run. Regenerate
only from hanzoai/openapi (`python3 generate.py python`) — never from here. The old
`scripts/generate.sh` was a second, destructive driver (`rm -rf pkg/hanzoai`, which would
have eaten the hand-written `config/mcp/protocols/session/zap` modules); it is deleted.
Consumed at 3.1.2: cloud `8143fc0e`, openapi `f581a0e`.

**Upstream spec defect — open, fix in the per-service specs.** `hanzo.yaml` carries 23 tag
groups that differ only by case (`AI`/`ai`, `Users`/`users`, `flows`/`Flows`, …).
openapi-generator maps both spellings onto one module, so the second overwrites the first:
**127 of the 411 operations in those groups are missing from the generated client.** Three
groups (`AI`/`ai`, `API Keys`/`api-keys`, `MCP`/`mcp`) also yield divergent class names
(`AiApi` vs `AIApi`), which made `import hanzoai.cloud` raise ImportError; those 9 dead
lines are stripped and `tests/test_smoke.py` locks the import. One spelling per tag upstream
fixes both symptoms and the fix survives regeneration — the local strip does not.

## Key entry points
- `pkg/hanzoai/` — typed OpenAPI client (`ApiClient`, `Configuration`, `Ai*Api`). Two
  surfaces live here: `pkg/hanzoai/{api,models}` (older, frozen — nothing regenerates it
  now) and `pkg/hanzoai/cloud/` (current, spec-driven). New work targets `cloud/`.
- `pkg/hanzo/src/hanzo/cli.py` — the `hanzo` CLI command tree.
- `pkg/hanzo-mcp/` — MCP server; tools via `[project.entry-points."hanzo.tools"]`.
- `pkg/hanzo-tools-*/` — one concern each, exports a `TOOLS` list.
- `pkg/hanzo-{agents,agent,network,memory}/` — agent/compute/memory libraries.
- `pkg/hanzo-kms/` — KMS client. The server is **luxfi/kms** (`kms.hanzo.ai`,
  `kms.lux.network`) and its whole surface is `/v1/kms/auth/login` plus
  `/v1/kms/orgs/{org}/secrets[/{path}/{name}]`. `/api/*` is Infisical's and was
  never served — it looked like a decode error rather than a 404 only because old
  builds answered every unmatched path with the console SPA (200 text/html).
  A secret is (org, path, name, env), one value each — no versions. The server
  splits the trailing URL at its LAST slash into (path, name), so escape each
  segment individually. `pkg/hanzo-kms/tests/` pins all of it.

**Rules for agents:** update THIS file with significant discoveries; never write
random summary files; keep the README cross-link block intact.
