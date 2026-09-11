# Hanzo Python SDK

`hanzoai` is the Python client for the Hanzo API, generated from the API's own
OpenAPI document. Every `/v1` route is in it, and the names it exposes are the
document's operation ids. [`.spec-lock`](.spec-lock) names the commit and sha256
of the document this tree was cut from.

[![PyPI](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Python](https://img.shields.io/pypi/pyversions/hanzoai.svg)](https://pypi.org/project/hanzoai/)

## Install

Python 3.12 or newer.

```bash
pip install hanzoai
```

`Client` and the six capabilities below are newer than 8.5.156, the latest
release on PyPI; that release has the generated client under `hanzoai.cloud`
and not them. If `from hanzoai import Client` raises `ImportError`, install from
`main`:

```bash
pip install 'hanzoai @ git+https://github.com/hanzoai/python-sdk'
```

On Python 3.9, 3.10 and 3.11 pip installs the 2.1 line instead, without an
error. That is an older client with a different API (`from hanzoai import
Hanzo`, key in `HANZO_API_KEY`), and nothing below applies to it.

Check the install without a credential — `GET /v1/models` needs none:

```bash
python -c 'from hanzoai.cloud import AiApi, ApiClient, Configuration
print(len(AiApi(ApiClient(Configuration(retries=0))).get_models().data or []), "models")'
```

It prints the number of models in the catalogue. The import alone takes 15 to
35 seconds: the generated package is 68 MB.

Calls without a valid credential are limited per address in 8-hour windows.
Past the limit the answer is `429` with `Retry-After` in seconds, and
`retries=0` turns that into an `ApiException` at once. A plain
`Configuration()` sleeps for `Retry-After` and tries three more times, and the
server has sent `Retry-After: 23730`.

`examples/models` prints the same catalogue with prices and is in the sdist, not
the wheel — clone the repo to run it.

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
from hanzoai.cloud import AccountApi

with c as api:
    for key in AccountApi(api).get_account_keys().keys or []:
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

What each status becomes for the six:

| status | result |
|---|---|
| 2xx | `Ok`, body decoded as sent; a 200 carrying an error object is still `Ok` |
| 202 with `"status": "held"` | `Held` |
| 402, or 403 with code `insufficient_balance` or `spend_cap_exceeded` | `Denied` |
| 401 | the token is re-minted and the call sent once more; a second 401 raises `Fault` |
| anything else, including a 403 without those codes, 429 and 5xx | raises `Fault`, carrying `status`, `code`, `reason` and `request` |

Apart from that one replay on a 401, one of these calls is one request, and
`Retry-After` is not waited on. The generated operations are different: called
through `Client`, a 429 or 503 with `Retry-After` makes them sleep for it and
try three more times.

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
from hanzoai.cloud import AccountApi

try:
    AccountApi(acme).post_account_keys(key_type_in)
except Held as held:
    print(held.id, held.clause, held.reason)   # queued — nothing ran
```

The dozen long-running operations whose `202` means "accepted, working on it"
carry their own schema and pass straight through — the body is the
discriminator, not the status code.

## Examples

`examples/` carries one directory per flow. Each is a whole path through one part
of the API.

| flow | what it does | routes | credential |
|---|---|---|---|
| [`models`](examples/models) | the model catalog | `GET /v1/models` | none |
| [`six`](examples/six) | budget, policy, search, kb, graph and audit in one flow | `/v1/allowance`, `/v1/billing/balance`, `/v1/entitlement`, `/v1/authz/check`, `/v1/search`, `/v1/framework/kb.page`, `/v1/graph`, `/v1/audit` | IAM |
| [`hello`](examples/hello) | prove the credential works | `GET /v1/account/keys` | IAM |
| [`money`](examples/money) | balance + usage | `GET /v1/billing/balance`, `GET /v1/billing/usage` | IAM |
| [`store`](examples/store) | KV round-trip | `POST /v1/provisioning/kv`, `GET`/`DELETE /v1/provisioning/kv/{name}` | IAM |
| [`agent`](examples/agent) | create, run, read the runs | `POST /v1/agent`, `POST /v1/agent/{ref}/run`, `GET /v1/agent/runs` | IAM |
| [`tools`](examples/tools) | the tool catalog | `GET /v1/tool` | IAM |

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
are hand-written and released on their own. What PyPI has from this repo:

| install | import | Python | what it is |
|---|---|---|---|
| `hanzoai` | `hanzoai` | 3.12+ | the client above |
| `hanzo-mcp` | `hanzo_mcp` | 3.12+ | MCP server, command `hanzo-mcp` |
| `hanzo-tools` | `hanzo_tools` | 3.12+ | the base the tool packages build on |
| `hanzo-tools-<name>` | `hanzo_tools.<name>` | 3.12+ | one tool each, registered under the `hanzo.tools` entry point, which is how `hanzo-mcp` finds it |
| `hanzo-iam` | `hanzo_iam` | 3.12+ | Hanzo IAM client |
| `hanzo-kms` | `hanzo_kms` | 3.12+ | Hanzo KMS client, command `hanzo-kms` |
| `hanzo-memory` | `hanzo_memory` | 3.10+ | memory service with MCP, commands `hanzo-memory` and `hanzo-memory-server` |
| `hanzo-zap` | `hanzo_zap` | 3.10+ | ZAP protocol client |
| `hanzo-flags` | `hanzo_flags` | 3.9+ | feature flags over `/v1/flags` |
| `hanzo-research` | `hanzo_research` | 3.9+ | research records over `/v1/research` |
| `hanzo-train` | `hanzo_train` | 3.12+ | client for the Hanzo Engine training API |
| `hanzo-tasks` | `hanzo_tasks` | 3.12+ | durable workflows for agents |
| `hanzo-network` | `hanzo_network` | 3.12+ | agent networks |
| `hanzo-consensus` | `hanzo_consensus` | 3.11+ | agreement among several agents |
| `hanzo-flow` | `hanzo_flow` | 3.12+ | visual workflow builder |
| `hanzo-web3` | `hanzo_web3` | 3.12+ | blockchain SDK |
| `hanzo-async` | `hanzo_async` | 3.12+ | async I/O |
| `hanzo-hooks` | `hanzo_hooks` | 3.12+ | runs shell hooks before and after tool calls |
| `hanzo-lsp` | `hanzo_lsp` | 3.12+ | language server client |
| `hanzo-sandbox` | `hanzo_sandbox` | 3.12+ | Linux sandbox for agent runtimes |

The tool packages are agent, api, auth, billing, browser, code, commerce,
computer, config, database, editor, fs, gimp, iam, ide, ingress, jupyter, kms,
llm, lsp, mcp, memory, mpc, net, paas, plan, reasoning, refactor, repl, s3,
shell, team, test, todo, ui, vcs and vector. `hanzo-tools-core` is empty and
only installs `hanzo-tools`.

The `hanzo` **command** is a native binary, not a Python package:
`curl -fsSL https://hanzo.sh | sh`. It replaces `hanzo-cli` and `hanzo-node`,
which are still on PyPI. `pip install hanzo` ships the older Python CLI under the
name `hanzo-py`, so the two never fight over one name on a PATH.

`pkg/` also holds copies of `hanzo-agent`, `hanzo-agents`, `hanzo-aci`,
`hanzo-dev` and `hanzo-s3`. PyPI gets those from
[hanzoai/agent](https://github.com/hanzoai/agent),
[hanzoai/agents](https://github.com/hanzoai/agents),
[hanzoai/aci](https://github.com/hanzoai/aci),
[hanzoai/ide](https://github.com/hanzoai/ide) and
[hanzos3/py-sdk](https://github.com/hanzos3/py-sdk); read those repos, not the
copies here.

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
