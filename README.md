# Hanzo Python SDK

`hanzoai` is the Python client for the Hanzo API, generated from the API's own
OpenAPI document — 1814 paths, 2479 operations, 192 API classes over 2460 models.
Every `/v1` route is in it, and the names it exposes are the document's operation
ids rather than a hand-picked subset. [`.spec-lock`](.spec-lock) names the commit
and sha256 of the document this tree was cut from.

[![PyPI](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Python](https://img.shields.io/pypi/pyversions/hanzoai.svg)](https://pypi.org/project/hanzoai/)

## Install

```bash
uv pip install "hanzoai @ git+https://github.com/hanzoai/python-sdk"
```

Install from source, not from PyPI, until this version reaches it. PyPI serves
**3.2.1**; this tree is **3.2.11**, and in between the API document dropped the
default version from its operation ids. 3.2.1's methods are `get_v1_keys` and
`get_v1_tools`; the current ones are `get_keys` and `get_tools`, so
`pip install hanzoai` gets you a client that works and a set of names that
matches nothing below.

Check the install without a key — `GET /v1/models` is public:

```python
import json
from hanzoai.cloud import ApiClient, Configuration, ModelsApi

body = ModelsApi(ApiClient(Configuration())).get_models_without_preload_content().read()
print(len(json.loads(body)["data"]), "models")     # e.g. 112 models
```

## Quickstart

```python
import os
from hanzoai.cloud import ApiClient, Configuration, KeysApi

client = ApiClient(
    Configuration(host="https://api.hanzo.ai"),
    "Authorization", f"Bearer {os.environ['HANZO_API_KEY']}",
)

with client as api:
    for key in KeysApi(api).get_keys().keys or []:
        print(key.prefix, key.type, key.created_at)
```

Every route follows that shape: one `*Api` class per tag, one method per
operation, typed models in and out. Keys come from
[cloud.hanzo.ai](https://cloud.hanzo.ai) or `hanzo login` in two shapes, and only
one of them works here. Use an `sk-`: it carries a principal, which every call
above needs. A `pk-` is publishable — it is safe in a browser bundle precisely
because it names an org and authenticates nobody, so cloud refuses it at the
identity boundary and it reads nothing.

## Auth

The header is `Authorization: Bearer <key>`, and you set it on the `ApiClient` as
above — **not** through `Configuration(access_token=…)`. The document declares no
security scheme, so the generator wrote an empty `auth_settings` into every
operation and nothing ever reads `access_token`. A client built that way sends no
`Authorization` header at all: every call goes out anonymous, and the refusal
that comes back reads like a bad key rather than an unsent header.

No generated code reads the environment — not one `os.environ` in all of
`hanzoai.cloud`, so no variable you export reaches a request on its own. (The
hand-written `hanzoai.zap` and `hanzoai.config` read `HANZO_ZAP_ENDPOINT` and
`HANZO_CONFIG_HOME`; neither is a credential.) [`examples/client.py`](examples/client.py)
is where `HANZO_API_KEY` and `HANZO_BASE_URL` get resolved — one place, for all
five flows.

## Examples

`examples/` carries one directory per flow. Each is a whole path through one part
of the API. On every push CI imports all five and resolves every method name they
call against the client, which is what keeps them from rotting into pseudocode.

| flow | what it does | routes |
|---|---|---|
| [`hello`](examples/hello) | prove the key works | `GET /v1/keys` |
| [`money`](examples/money) | balance + usage | `GET /v1/billing/balance`, `GET /v1/billing/usage` |
| [`store`](examples/store) | KV round-trip | `POST /v1/kv`, `GET`/`DELETE /v1/kv/{name}` |
| [`agent`](examples/agent) | create, run, read the runs | `POST /v1/agents`, `POST /v1/agents/{ref}/run`, `GET /v1/agents/{ref}/runs` |
| [`tools`](examples/tools) | the tool catalog | `GET /v1/tools` |

```bash
export HANZO_API_KEY=sk-...
python -m examples.hello
```

There is no `chat` flow because there is nothing to generate one from:
`POST /v1/chat/completions` is declared with no `requestBody` and no `responses`,
so the method takes no arguments and returns `None`. Hand-rolling the request
inside a generated client is the drift these SDKs exist to prevent. It comes back
the day the document describes the body.

The same gap shows up in `money`, which reads its two payloads through the
generated `*_without_preload_content` variant: of 2479 operations, 716 declare no
`responses` and another 118 declare no response content, so 834 of them model no
body to deserialize. Those become ordinary typed calls when the schemas land, and
nothing else about them changes.

Reference for the routes themselves: [api.hanzo.ai/docs](https://api.hanzo.ai/docs),
served from the same document — [api.hanzo.ai/v1/openapi.json](https://api.hanzo.ai/v1/openapi.json).

## The rest of the repo

This is a `uv` workspace. `pkg/hanzoai` is the client above; the other 64
packages are hand-written, ship separately, and mostly carry their own README:

| Package | Install | Purpose |
|---|---|---|
| `pkg/hanzoai` | `hanzoai` | the client above |
| `pkg/hanzo-mcp` | `hanzo-mcp` | Model Context Protocol server |
| `pkg/hanzo-agent` | `hanzo-agent` | agent framework (import path `agents`) |
| `pkg/hanzo-agents` | `hanzo-agents` | agent networks and swarms |
| `pkg/hanzo-memory` | `hanzo-memory` | persistent memory + RAG over SQLite |
| `pkg/hanzo-network` | `hanzo-network` | distributed compute nodes |
| `pkg/hanzo-tools-*` | one each | 37 single-concern tool packages, each registering a `TOOLS` list under the `hanzo.tools` entry point, which is how `hanzo-mcp` finds them |

The `hanzo` **command** is a native binary, not a Python package:
`curl -fsSL https://hanzo.sh | sh`. `pip install hanzo` ships the older Python CLI
under the name `hanzo-py`, so the two never fight over one name on a PATH.

## Development

```bash
git clone https://github.com/hanzoai/python-sdk && cd python-sdk
uv sync --all-packages
uv run pytest tests/ -v
```

`pkg/hanzoai/cloud/` is generated and is never edited by hand — a regeneration
does `rmtree` then `copytree`, so an edit there is gone on the next run. It comes
from [hanzoai/openapi](https://github.com/hanzoai/openapi):

```bash
cd ../openapi && uv run --with pyyaml python3 generate.py python \
  --repo ../python-sdk --spec ../cloud/openapi.yaml
```

A defect found in generated code is fixed in the document, where every other
language gets the fix too. See [LLM.md](LLM.md) for how the lane works.

## License

Apache 2.0 — see [LICENSE](LICENSE). Report vulnerabilities to security@hanzo.ai
([SECURITY.md](SECURITY.md)).

## Hanzo — the Open AI Cloud

[hanzo.ai](https://hanzo.ai) · [docs.hanzo.ai](https://docs.hanzo.ai) ·
same client in other languages:
[TypeScript](https://github.com/hanzoai/js-sdk) ·
[Go](https://github.com/hanzoai/go-sdk) ·
[Java](https://github.com/hanzoai/java-sdk) ·
[Kotlin](https://github.com/hanzoai/kotlin-sdk) ·
[umbrella](https://github.com/hanzoai/sdk)
