# Hanzo Python SDK

`hanzoai` is the Python client for the Hanzo API, generated from the API's own
OpenAPI document. Every `/v1` route is in it, and the names it exposes are the
document's operation ids. [`.spec-lock`](.spec-lock) names the commit and sha256
of the document this tree was cut from.

[![PyPI](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Python](https://img.shields.io/pypi/pyversions/hanzoai.svg)](https://pypi.org/project/hanzoai/)

## Install

```bash
pip install hanzoai
```

Check the install without a key — `GET /v1/models` is public:

```bash
python -c 'from hanzoai.cloud import AiApi, ApiClient, Configuration
print(len(AiApi(ApiClient(Configuration())).get_models().data), "models")'
```

```
481 models
```

If it prints a count, the package imports, the host resolves and the client
speaks the API. `examples/models` prints the same catalogue with prices and is
in the sdist, not the wheel — clone the repo to run it.

## Quickstart

```python
from hanzoai import Client

c = Client()                          # HANZO_CLIENT_ID / HANZO_CLIENT_SECRET

print(c.budget.left().left, "free calls left today")
print(c.policy.check("usr_7", "write", "graph:acme").allow)

a = c.search.find("q3 incident postmortems")
if a.denied:
    for cure in a.denied.cures:
        print(cure.kind, cure.url)
else:
    for hit in a.value.items:
        print(hit.score, hit.title)
```

`budget`, `policy`, `audit`, `search`, `kb` and `graph` hang off the client and
are the surface most callers want. They are the same six words, the same method
names and the same answer type in the
[Go](https://github.com/hanzoai/go-sdk) and
[TypeScript](https://github.com/hanzoai/js-sdk) SDKs.

Everything else is the generated client — one `*Api` class per tag, one method
per operation, typed models in and out. `Client` is the generated `ApiClient`, so
it goes anywhere an `ApiClient` goes and carries the same credential there:

```python
from hanzoai.cloud import KeysApi

with c as api:
    for key in KeysApi(api).get_keys().keys or []:
        print(key.prefix, key.type, key.created_at)
```

### Answers

A budget that says no and a policy that says no are answers, not exceptions.
Every capability call that can be refused returns one type with three arms:

```python
from hanzoai import Ok, Denied, Held

match c.graph.assert_(facts):
    case Ok(value=wrote):    print(wrote.recorded, "recorded")
    case Denied() as denied: print(denied.code, denied.reason, denied.cures)
    case Held() as held:     print("a person was asked:", held.id, held.clause)
```

`Ok` holds what ran, `Denied` names the code and the cures that would clear it,
`Held` names the approval a person still has to give. Reading `.value` off a
refusal raises it, so there is no member you can read off the wrong arm. Every
arm carries `request` — the `x-request-id` the server stamped — which is the same
word `audit.Event` uses, so the trail can be read back for a call you just made.

Reads no gate refuses answer their value directly: `budget.left`,
`budget.balance`, `budget.plan`, `audit.list`, `graph.read`, `graph.resolve`,
`kb.get`. `policy.check` answers a `Decision` carrying a boolean, because asking
whether you may is a question with an answer — being stopped mid-call is what
produces a refusal.

## Auth

IAM is the only authority. The client holds its own application's `clientId` and
`clientSecret`, exchanges them for a short-lived access token —
`POST https://hanzo.id/v1/iam/oauth/token`, `client_credentials`,
`client_secret_basic`, RFC 8707 `resource`-scoped to the endpoint it will call —
holds it until shortly before expiry, and re-mints once on a 401.

It takes no bearer. A credential handed to an SDK is a credential nobody
rotates, and it says nothing about who is calling, which is the one question
every gate in the estate exists to answer.

Five options, each falling back to an environment variable, so the
zero-argument constructor is the normal case:

| option | environment | default |
|---|---|---|
| `id` | `HANZO_CLIENT_ID` | — |
| `secret` | `HANZO_CLIENT_SECRET` | — |
| `base` | `HANZO_BASE_URL` | `https://api.hanzo.ai` |
| `issuer` | `HANZO_ISSUER_URL` | `https://hanzo.id` |
| `resource` | `HANZO_RESOURCE` | = `base` |

Four operations need no credential at all — `GET /v1/models`,
`GET /v1/models/providers`, `GET /v1/commands`, `GET /v1/openapi.json` — which is
why `examples/models` runs before you have one.

## Tenants

If you are building on top of Hanzo, you hold one key and your customers hold
none. `as_` binds a client to one of them:

```python
from hanzoai import Client

hanzo = Client()
acme = hanzo.as_("user_42")                 # a subject id, or your own externalId

acme.kb.put(doc)                            # written as that customer
```

IAM mints a short-lived token bound to that subject — `POST
https://hanzo.id/v1/iam/tokens/issue?id=user_42`, on IAM's own host, reading the
act grant off your own token — and the scoped client sends it on every call, the
six capabilities and the generated operations alike, keeps it until it nears
expiry, and re-mints once on a 401. Your own credential leaves with the scope:
two credentials on one request are two answers to who is calling. No method
takes a user id, so there is none to pass wrongly and none to forget.
`Client(issuer=...)` points the mint at a private estate.

The spelling is `as_` rather than `as` only because `as` is a keyword; the
trailing underscore is what PEP 8 prescribes, and it keeps the platform's one
word for this from growing a synonym in Python.

### Held calls

A generated operation your policy holds for a human decision answers `202` with
the approval — `{"status": "held", "id", "clause", "reason"}`. A 202 is a 2xx, so
a client that only checks for a raise reads a queued call as a completed one.
This one raises the same `Held` the six answer as an arm:

```python
from hanzoai import Held

try:
    fact = MemoryApi(acme).post_memory_remember(body)
except Held as held:
    print(held.id, held.clause, held.reason)   # queued — nothing ran
```

The dozen long-running operations whose `202` means "accepted, working on it"
carry their own schema and pass straight through — the body is the
discriminator, not the status code.

## Examples

`examples/` carries one directory per flow. Each is a whole path through one part
of the API. CI imports all six and resolves every method name they call against
the client.

| flow | what it does | routes | credential |
|---|---|---|---|
| [`models`](examples/models) | the model catalog | `GET /v1/models` | none |
| [`six`](examples/six) | budget, policy, search, kb, graph and audit in one flow | `/v1/allowance`, `/v1/billing/balance`, `/v1/entitlement`, `/v1/authz/check`, `/v1/search`, `/v1/framework/kb.page`, `/v1/graph`, `/v1/audit` | IAM |
| [`hello`](examples/hello) | prove the credential works | `GET /v1/keys` | IAM |
| [`money`](examples/money) | balance + usage | `GET /v1/billing/balance`, `GET /v1/billing/usage` | IAM |
| [`store`](examples/store) | KV round-trip | `POST /v1/kv`, `GET`/`DELETE /v1/kv/{name}` | IAM |
| [`agent`](examples/agent) | create, run, read the runs | `POST /v1/agents`, `POST /v1/agents/{ref}/run`, `GET /v1/agents/{ref}/runs` | IAM |
| [`tools`](examples/tools) | the tool catalog | `GET /v1/tools` | IAM |

One command each, from the repo root:

```bash
python -m examples.models                  # no credential

export HANZO_CLIENT_ID=... HANZO_CLIENT_SECRET=...
python -m examples.six
```

`six` is the one that shows the capabilities composing: it checks what it may
spend, asks whether it may write, searches the corpus, files a page, records a
fact, and then reads the audit trail back for the request ids the earlier calls
carried.

There is no `chat` flow: `POST /v1/chat/completions` is declared with no
`requestBody` and no `responses`, so the method takes no arguments and returns
`None`. It comes back the day the document describes the body.

`money` reads its two payloads through the generated
`*_without_preload_content` variant, for the same reason — an operation that
declares no `responses`, or a 2xx carrying no content, models no body to
deserialize.

Reference for the routes themselves: [api.hanzo.ai/docs](https://api.hanzo.ai/docs),
served from the same document — [api.hanzo.ai/v1/openapi.json](https://api.hanzo.ai/v1/openapi.json).

## The rest of the repo

This is a `uv` workspace. `pkg/hanzoai` is the client above; the other packages
are hand-written, ship separately, and mostly carry their own README:

| Package | Install | Purpose |
|---|---|---|
| `pkg/hanzoai` | `hanzoai` | the client above |
| `pkg/hanzo-mcp` | `hanzo-mcp` | Model Context Protocol server |
| `pkg/hanzo-agent` | `hanzo-agent` | agent framework (import path `agents`) |
| `pkg/hanzo-agents` | `hanzo-agents` | agent networks and swarms |
| `pkg/hanzo-memory` | `hanzo-memory` | persistent memory + RAG over SQLite |
| `pkg/hanzo-network` | `hanzo-network` | distributed compute nodes |
| `pkg/hanzo-tools-*` | one each | single-concern tool packages, each registering a `TOOLS` list under the `hanzo.tools` entry point, which is how `hanzo-mcp` finds them |

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

A defect in generated code is fixed in the document.

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
