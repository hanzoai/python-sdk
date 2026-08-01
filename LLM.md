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
pip install hanzoai          # typed cloud client
pip install hanzo            # agents + MCP + orchestration helpers
uv sync --all-packages       # dev: whole workspace
uv run pytest tests/ -v      # tests
```

## Console-script law — only the native binary is called `hanzo`

The `hanzo` command is the Rust CLI (`curl -fsSL https://hanzo.sh | sh`). No
package in this workspace may declare a `hanzo` console script.

Both `hanzo` and `hanzo-cli` used to, and `hanzo` depends on `hanzo-cli`, so
`pip install hanzo` installed two distributions fighting over one name — whichever
landed last won. Measured on a clean venv at 0.4.3: `hanzo --help` printed
*hanzo-cli's* program (bot/deploy/iam/k8s/kms/login/logout/paas/s3/whoami), not
the one `pkg/hanzo/README.md` documented. And if the native CLI was already on
PATH, `hanzo login` meant one of three different things depending on install
order — the real CLI reads a bare `hanzo login` as an AI task, since the verb
there is `hanzo auth login`.

Now: `hanzo` ships `hanzo-py`, `hanzo-cli` ships `hanzo-cli`. Script named after
its distribution, one canonical `hanzo`.

`hanzo-node` on PyPI is also **not** the `hanzo-node` command. That command is a
symlink to the Hanzo CLI, installed by hanzo.sh. The PyPI package fetches a
different Rust binary from `hanzoai/node` — a private repo, so its release assets
404 for anyone outside the org. Both READMEs say so rather than implying one
product.

## Brand rules (hard — enforce in all docs)
- Never "LLM gateway"; never position against LiteLLM. Hanzo is a full AI SDK / AI
  cloud, not a proxy.
- Zen models are our own family — never name upstream models.
- Paths are `/v1/…`, never `/api/…`. Base host: `https://api.hanzo.ai`.
- Voice: "Hanzo — the Open AI Cloud." Crisp, developer-first, no emoji-spam.

## Codegen — this repo PULLS, it never pushes
```
hanzoai/cloud    emits its own router spec    -> cloud/openapi.yaml
hanzoai/openapi  merges 55 per-service specs  -> hanzo.yaml (1132 paths)  [the ONE SDK input]
hanzoai/openapi  generate.py + sdks.yaml      -> projects hanzo.yaml into each SDK repo
this repo        owns its test + PATCH bump + release
```
Current `pkg/hanzoai/cloud/` is **1132 paths / 1519 operations / 779 schemas** →
239 api modules + 1116 model modules. The path count dropped from 1885 because
the spec deleted 18 products it authored and served nowhere, not because
anything here was lost.
`pkg/hanzoai/cloud/` is **generated — never hand-edit it.** `generate.py` does
`rmtree(dst) + copytree(src)`, so anything written there dies on the next run. Regenerate
only from hanzoai/openapi (`python3 generate.py python`) — never from here. The old
`scripts/generate.sh` was a second, destructive driver (`rm -rf pkg/hanzoai`, which would
have eaten the hand-written `config/mcp/protocols/session/zap` modules); it is deleted.
Consumed at 3.1.3: cloud `8143fc0e`, openapi `2861089`. Regenerate whenever either moves —
openapi `3300cda` dropped `{org}` from the KMS secrets routes (`/v1/kms/orgs/{org}/secrets`
-> `/v1/kms/secrets`; the org is read from the token), which silently stranded 3.1.2 on a
path the server no longer serves.

**The case-variant tag defect is CLOSED.** `hanzo.yaml` used to carry 23 tag groups
differing only by case (`AI`/`ai`, `Users`/`users`, …); openapi-generator mapped both
spellings onto one module and 127 of the 411 operations in those groups never reached the
client. Fixed upstream in the per-service specs, as that note predicted. Verified on the
current spec: **239 distinct tags → 239 api modules, 1:1**, so nothing collapses, and
`generate.py python --check` reports `[python] clean` with no local strip of any kind.

**Two spec defects were found and fixed upstream while regenerating at 3.1.5.** Neither was
patched here; both are in `hanzoai/openapi` main:
- `fc0c17a` — 35 `/v1/platform` operations carried no `responses`. OAS 3.x requires it and
  openapi-generator aborts the entire document, so `hanzo.yaml` was producing no client in
  *any* language, not just Python.
- `07783f5` — `ChatCompletionResponse.choices` was `items: {type: object}`, so
  `choices[0].message.content` was `List[object]` and unusable without a cast. Now an
  `ai_ChatChoice` schema.

The rule holds in both directions: a generated tree is never hand-repaired, and a defect
found by generating is fixed in the spec, where every other language gets the fix too.

## Examples — the six canonical flows

`examples/{hello,chat,money,store,agent,tools}`, one directory each, plus
`examples/client.py` as the single place a base URL or an env var is resolved. The same six
exist in every Hanzo SDK. Run one with `python -m examples.hello` from the repo root.

Each flow's call sits behind `if __name__ == "__main__":` on purpose. That is what lets CI
*import* all six to prove every `from hanzoai.cloud import X` still resolves, without an API
key and without opening a socket — so a spec change that renames or drops an operation goes
red in the gate instead of in a user's app.

They are a gate, not decoration. The TypeScript twin of the `chat` flow is what surfaced the
`choices` defect above: the generated tree imported and built perfectly, because building
generated code only proves it is internally consistent. Only calling it proves the surface
is usable.

## CI

Fleet convention, added at 3.1.5: root `hanzo.yml` (the `test:` gate) plus a 7-line
`.github/workflows/cicd.yml` importing `hanzoai/ci`. The gate is two blocks — import every
generated module (for generated code that IS the build step; there is no compiler to catch a
bad `$ref`), then import the six flows. Both provision an interpreter with `uv` when the arc
runner lacks one.

Scope is deliberate: the cloud client and its flows, not all 65 packages. A red gate should
mean "the client the spec just produced is broken", not "something, somewhere".

**Publishing is not here.** `.hanzo/workflows/publish-pypi.yml` on our own runners stays the
canonical path because it reads the PyPI token from KMS like every other publish credential
in the fleet. `hanzo.yml` gates only; a second publish path would be one too many.

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
