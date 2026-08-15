# LLM.md — hanzoai/python-sdk

**What this is:** the flagship, most-complete Hanzo SDK — a `uv` workspace of 65
packages: the typed cloud client (`hanzoai`), agents, MCP server + tools, memory,
distributed compute, and the `hanzo` CLI. `pip install hanzo`.

**Canonical role (one-way SDK model):** Hanzo ships two SDK lines per language —
(1) the full cloud SDK generated from OpenAPI, (2) the AI/agents library. This repo
is the Python flagship of line 2, the reference for every other language.
Completeness: Python → Rust → C++ → Go. One impl, one place; discovery repos link
OUT, never duplicate. Full spec: `~/work/hanzo/SDK-ARCHITECTURE.md`.

## Install / run
```bash
pip install hanzoai==3.2.13  # the current client
pip install hanzo            # agents + MCP + orchestration helpers
uv sync --all-packages       # dev: whole workspace
uv run pytest tests/ -v      # tests
```

**PyPI serves this tree again.** `hanzoai` had sat at **3.2.1** while v3.2.3 …
v3.2.12 were tagged with nothing published, and the gap was not cosmetic: 3.2.1
predates the default version leaving the operation ids, so it carries
`get_v1_keys`/`get_v1_tools` (182 api modules, 2172 models) plus the retired flat
`hanzoai/api` tree. **3.2.13** carries `get_keys`/`get_tools` and is what the
README's quickstart runs on. The same tag published 13 sibling packages that had
also drifted behind — `hanzo-mcp` 0.15.14, `hanzo-tools` 0.3.5, `hanzo-kms`
1.1.1, `hanzo-network` 0.1.4, seven `hanzo-tools-*`, and first releases of
`hanzo-flags` and `hanzo-research`.

**What had stopped every one of them** is worth keeping, because it reads like a
missing secret and is not one. The job asked KMS for
`/v1/kms/orgs/hanzo/secrets/<path>/<key>` and parsed `.secret.value`. KMS serves
`GET /v1/kms/secrets/<path>/<key>?env=<env>` and answers `{"env","name","value"}`,
taking the org from the caller's own token claim. A wrong route 404s exactly like
an unseeded path, so the log said "KMS holds no PyPI token" about a token that was
sitting at `hanzo`/`prod`/`python-sdk-publish`/`PYPI_TOKEN` the whole time. The
route the kms-operator uses is the one that answers; check a read against a secret
known to exist before believing a 404.

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
hanzoai/cloud    emits its own router spec    -> cloud/openapi.yaml  [the ONE SDK input]
hanzoai/openapi  generate.py + sdks.yaml      -> the invocation, as data
this repo        owns its test + bump + release, and pins what it projected
```
The client is a projection of **cloud's document directly**, and `.spec-lock`
names the commit and sha256 it was cut from. `generate.py` passes
`--skip-validate-spec`, so the 1012 missing-`responses` errors that once made
cloud's emission write zero files no longer stop it; `hanzo.yaml` is out of this
SDK's path (it still feeds the doc site and the skills plane). Regenerate with
the document by value:
```bash
cd ~/work/hanzo/openapi && uv run --with pyyaml python3 generate.py python \
  --repo ~/work/hanzo/python-sdk --spec ~/work/hanzo/cloud/openapi.yaml
```
Current `pkg/hanzoai/cloud/` is **1814 paths / 2479 operations** → 192 api
modules + 2460 model modules, 2659 importable modules in total. The document
carries 191 tags; the 192nd module is `default_api`, which holds the 50
operations that carry no tag (`/`, `/.well-known/agent-skills/*`, …).

**834 of the 2479 operations model no response body** — 716 declare no
`responses` at all and 118 declare responses with no `content` — so those methods
are typed `-> None` and the payload is reachable only through the generated
`*_without_preload_content` variant. `examples/money` is the worked example of
reading one honestly, including the part that is easy to miss: the raw variant
does not raise on a 4xx, because raising is part of the typed deserialization
those operations do not have.

**Two renamings arrived with the lineage, and neither is a defect to undo.**
IAM's types are namespace-qualified — `iam.Role`, `iam.Application`, 95 of them
— because a bare `Role` had been two unrelated shapes under one name (IAM's
14-property role, and a 2-property `{role, user}` row from another service).
Both exist now and each says which it is. And the `<svc>_` operationId prefix is
gone, so every method lost it: `cloud_get_v1_tools` → `get_v1_tools` → `get_tools` (the default version
left the id at 3.2.10; the wire never carried it),
`AIApi`/`APIKeysApi`/`MCPApi` → `AiApi`/`KeysApi`/`McpApi`,
`AdminApi.plugin_admin_plugins` → `admin_plugins`.
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
document this tree is pinned to: **191 tags → 191 api modules, 1:1**, plus `default_api`
for the untagged 50, so nothing collapses, and `generate.py python --check` reports
`[python] clean` with no local strip of any kind.

## The client authenticates itself — CLOSED, and it was fixed in the document

`Configuration(access_token=…)` sends the credential. cloud's document declares
`components.securitySchemes.bearer` (`type: http`, `scheme: bearer`) and applies
it document-wide with `security: [{bearer: []}]`, so openapi-generator wrote a
populated `Configuration.auth_settings()` —

    auth['bearer'] = {'type': 'bearer', 'in': 'header',
                      'key': 'Authorization', 'value': 'Bearer ' + self.access_token}

— and `_auth_settings: List[str] = ['bearer']` into **2498 call sites**.
`ApiClient._apply_auth_params` reads that and sets the header. Four call sites
carry an empty list instead, and they are exactly the operations the document
marks `security: []`: `get_models`, `get_models_providers`, `get_commands`,
`get_openapi_json`.

Before this, the document declared no scheme at all: `auth_settings()` returned
`{}`, `update_params_for_auth` returned on its first line, and a Configuration
built with `access_token="sk-test"` produced a request with **no `Authorization`
header**. `examples/client.py` compensated with `ApiClient`'s
`header_name`/`header_value` pair. That compensation is gone — the flows pass
`access_token` and nothing else, which is the shape a reader of any other
openapi-generator client already expects.

Proven on the wire, not by reading: `python -m examples.hello` against
api.hanzo.ai returns the caller's keys with a real `sk-`, and the same command
with a bogus one returns `HTTP 403 {"code":"forbidden","error":"sign in to
manage API keys"}`. Two different answers to the same code means the credential
is reaching the server.

## A `pk-` is not a read key

`cloud.APIKeyPrefixes` is `{"pk-", "sk-"}`, and it is tempting to read that pair
as a permission split — publishable for reads, secret for writes. It is not one.
`middleware_identity.go` returns nil for **any** `pk-` before it ever consults the
key store: "a key meant for a browser bundle must not read … resolvable, not
authenticating". A `pk-` resolves to an org so an analytics beacon can be
attributed to a tenant, and that is the whole of it.

So every route these examples use refuses a valid `pk-` exactly as it refuses no
key at all — `/v1/tools` says why in as many words, `"a validated principal is
required"` — and the 403 that comes back reads like a revoked key rather than the
wrong shape of key. `examples/client.py` rejects a `pk-` up front for that reason:
an unauthenticating credential produces the same misleading refusal as a revoked
one, so it is caught before the request goes out.

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

## Examples — six flows, and nothing loose beside them

`examples/{models,hello,money,store,agent,tools}`, one directory each, plus
`examples/client.py` as the single place a base URL or an env var is resolved. Run one with
`python -m examples.hello` from the repo root.

`models` is the one that needs no credential — `GET /v1/models` is one of the four
operations the document marks `security: []` — so it is the install check a reader can run
before they have a key, and the flow that proves the package reaches api.hanzo.ai at all.
`client.py` exposes it as `public()` beside the credentialled `client()`.

`chat` is absent by measurement, not by choice: `POST /v1/chat/completions` is declared with
no `requestBody` and no `responses`, so the generated method takes no arguments and returns
`None` — the one call the flow exists to make cannot be expressed. It returns the day the
document describes the body; `hanzo.yml` carries the one-line test for that.

Five loose scripts used to sit beside the flows (`using_grok.py`, `unified_ai_example.py`,
`self_learning_agent.py`, `parallel_ai_doc_editing.py`, `worktree_orchestration.py`) and all
five were dead: they imported `hanzoai.Hanzo`, `hanzoai.cluster`, `hanzoai.agents`,
`hanzoai.completion` — none of which exist — or were dict-literal sketches captioned "in
practice this would be called through the MCP interface". `compileall` passed them all,
because syntax is not a claim. They are deleted. `examples/` is the flows.

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
`.hanzo/workflows/cicd.yml` importing `hanzoai/ci`. The gate is three blocks — import every
generated module (for generated code that IS the build step; there is no compiler to catch a
bad `$ref`), read the syntax tree for duplicate fields the import cannot see, then resolve
and import the six flows. Each provisions an interpreter with `uv` when the runner lacks
one. There is no `.github/workflows/` here: the label these callers ask for is served by the
git-runner fleet on git.hanzo.ai and by nothing on github.com.

Scope is deliberate: the cloud client and its flows, not all 65 packages. A red gate should
mean "the client the spec just produced is broken", not "something, somewhere".

**Publishing is not here.** `.hanzo/workflows/publish-pypi.yml` on our own runners stays the
canonical path because it reads the PyPI token from KMS like every other publish credential
in the fleet. `hanzo.yml` gates only; a second publish path would be one too many.

The `examples` step used to import the flows and stop there, and the comment beside it said
so honestly — a method name is looked up at call time, so a renamed operation passed the
import and failed in a user's app. It now resolves them: the syntax tree gives every
attribute access on a `*Api`-bound name, and the class is asked whether it has it. Ten names
resolve today, and a stale `get_v1_tools` fails the step in the same second the import
passes.

## Prose is checked the same way as code

Three docs under `docs/` were fabrication, not drift: `FEATURES.md`
(`from hanzoai import cluster/agents/mcp` — none exist), `QUICKSTART.md` and
`GPT5_ORCHESTRATION.md` (invented console output for CLI flags and models that were never
ours). None were in the mkdocs nav, so nothing rendered them and nothing checked them.
Deleted. `pkg/hanzo-agent` told the reader to `pip install hanzoai` and
`from hanzoai import Agent, Runner` — the cloud client has no `Agent` — and its own `full`
extra resolved to `hanzoai[web3,tee,marketplace,cli]`, extras the cloud client does not
declare, so it installed the client and none of the extensions. Both corrected to
`hanzo-agent` / `from agents import`.

`pyproject.toml` said `BSD-3-Clause` while `LICENSE` is the Apache 2.0 text, so the wheel's
metadata contradicted the file inside it. Metadata now matches the file: `Apache-2.0`.

`tests/test_smoke.py` imported `hanzoai.cloud.api.tracker_api`; no `/v1/tracker` path is
emitted any more, so the suite had a failing test that named a module the client does not
have. It reads `analytics_api` now, off the client.

## Key entry points
- `pkg/hanzoai/` — the client (`ApiClient`, `Configuration`, `*Api`) under `cloud/`, plus
  seven hand-written modules beside it (`config`, `mcp`, `protocols`, `session`, `zap`, …).
  `pkg/hanzoai/{api,models}` is GONE from git; if a checkout still shows `resources/` or
  `types/` on disk they are untracked leftovers of that surface, and the wheel excludes them
  — the published 3.2.13 wheel is 2667 files of `hanzoai/cloud/` and those seven modules,
  nothing else.
- `pkg/hanzo/src/hanzo/cli.py` — the `hanzo` CLI command tree.
- `pkg/hanzo-mcp/` — MCP server; tools via `[project.entry-points."hanzo.tools"]`.
- `pkg/hanzo-tools-*/` — one concern each; 37 of the 38 register a `TOOLS` list under the
  `hanzo.tools` entry point (`hanzo-tools-core` is the shared base, so it registers none).
- `pkg/hanzo-{agents,agent,network,memory}/` — agent/compute/memory libraries.
- `pkg/hanzo-kms/` — KMS client. The server is **luxfi/kms** (`kms.hanzo.ai`,
  `kms.lux.cloud`) and its whole surface is `/v1/kms/auth/login` plus
  `/v1/kms/orgs/{org}/secrets[/{path}/{name}]`. `/api/*` is Infisical's and was
  never served — it looked like a decode error rather than a 404 only because old
  builds answered every unmatched path with the console SPA (200 text/html).
  A secret is (org, path, name, env), one value each — no versions. The server
  splits the trailing URL at its LAST slash into (path, name), so escape each
  segment individually. `pkg/hanzo-kms/tests/` pins all of it.

**Rules for agents:** update THIS file with significant discoveries; never write
random summary files; keep the README cross-link block intact.
