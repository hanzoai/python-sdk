<p align="center"><img src=".github/hero.svg" alt="Hanzo Python SDK" width="880"></p>

# Hanzo Python SDK

**The flagship Python SDK for the Open AI Cloud — models, agents, tools, memory, and MCP in one install.**

[![CI](https://github.com/hanzoai/python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/hanzoai/python-sdk/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzoai.svg)](https://pypi.org/project/hanzoai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

This is the most complete Hanzo SDK — a `uv` workspace of 60+ composable packages
covering the full AI surface: the typed cloud client, an agent framework, the
Model Context Protocol server and tools, persistent memory + RAG, distributed
compute, and a batteries-included CLI. If you build AI in Python, start here.

## Install

```bash
pip install hanzoai        # the typed cloud API client
pip install hanzo          # orchestration helpers, agents, MCP
pip install "hanzo[all]"   # everything, including optional extras
```

The `hanzo` **command** is not a Python package — it is a native binary:

```bash
curl -fsSL https://hanzo.sh | sh
hanzo auth login
```

## Quickstart

```python
from hanzoai.cloud import ApiClient, Configuration, ChatApi

config = Configuration(host="https://api.hanzo.ai", access_token="sk-...")

with ApiClient(config) as client:
    print(ChatApi(client).post_v1_chat_completions())
```

`hanzoai.cloud` is the client, and it is the only one. Method and class names are
the document's operation ids, so they move when the document does — that is what
makes the client checkable against a release instead of against memory.

Every route is `https://api.hanzo.ai/v1/<service>/*`. Models come from the **Zen**
family (our own models) plus any provider you connect — one typed client, no proxy
in the middle.

## Examples — the six canonical flows

`examples/` carries one directory per flow. These are the same six in every
Hanzo SDK, so a reader who knows one language's set can navigate another's.

| flow | what it does | routes |
|---|---|---|
| [`hello`](examples/hello) | identity — prove the key works | `GET /v1/bot/auth/me` |
| [`chat`](examples/chat) | one completion | `POST /v1/chat/completions` |
| [`money`](examples/money) | balance + usage | `GET /v1/billing/balance`, `GET /v1/billing/usage` |
| [`store`](examples/store) | KV round-trip | `POST /v1/kv`, `GET`/`DELETE /v1/kv/{name}` |
| [`agent`](examples/agent) | create + run + read | `POST /v1/agents`, `POST /v1/agents/{ref}/run`, `GET /v1/agents/{ref}/runs` |
| [`tools`](examples/tools) | tool catalog | `GET /v1/tools` |

Each reads `HANZO_API_KEY` from the environment and talks to
`https://api.hanzo.ai` unless `HANZO_BASE_URL` says otherwise:

```bash
export HANZO_API_KEY=sk-...
uv run python -m examples.hello
```

They import from **`hanzoai.cloud`** — the client generated from
`https://api.hanzo.ai/v1/openapi.json`, which is where new work goes.
`examples/client.py` is the single place a base URL or an env var is resolved.
CI imports all six on every push, which is what keeps them from rotting into
pseudocode.

## Packages

The workspace splits cleanly by concern. The headline packages:

| Package | Purpose |
|---------|---------|
| `hanzoai` | Typed cloud API client (generated from the Hanzo OpenAPI surface). |
| `hanzo` | Orchestration helpers and the older Python CLI (console script `hanzo-py`). |
| `hanzo-mcp` | Model Context Protocol server — discovers tools via entry points. |
| `hanzo-agents` / `hanzo-agent` | Agent framework — build and orchestrate agents and swarms. |
| `hanzo-network` | Distributed AI compute and node orchestration. |
| `hanzo-memory` | Persistent memory + RAG (SQLite, optional vector backends). |
| `hanzo-tools-*` | 60+ single-concern tool packages (`shell`, `browser`, `fs`, `code`, `vector`, `iam`, …), each exposing a `TOOLS` list. |

```
python-sdk/
└── pkg/
    ├── hanzoai/          # typed cloud client (OpenAPI-generated)
    ├── hanzo/            # orchestration helpers + legacy Python CLI
    ├── hanzo-mcp/        # MCP server (entry-point tool discovery)
    ├── hanzo-agents/     # agent framework
    ├── hanzo-network/    # distributed compute
    ├── hanzo-memory/     # memory + RAG
    └── hanzo-tools-*/    # composable tool packages
```

## CLI

The Hanzo CLI is a native binary, not a Python package:

```bash
curl -fsSL https://hanzo.sh | sh
hanzo auth login
hanzo models list
hanzo "fix the failing test"
```

It carries one command group per Hanzo Cloud product, generated from the same
contract this SDK is generated from. `hanzo --help` prints the tree.

`pip install hanzo` still ships the older Python CLI as **`hanzo-py`**. It is
named that way on purpose: two programs called `hanzo` on one PATH is how
`hanzo login` came to mean different things to different people.

## Model Context Protocol (`hanzo-mcp`)

`hanzo-mcp` hosts the MCP server and discovers tools through
`[project.entry-points."hanzo.tools"]`, so any installed `hanzo-tools-*` package
lights up automatically.

```python
from hanzo_mcp import create_mcp_server

server = create_mcp_server()
server.register_tool(my_tool)
server.start()
```

## Agents (`hanzo-agents`)

```python
from hanzo_agents import Agent, Swarm

agent = Agent(
    name="researcher",
    model="zen5-coder",
    instructions="You are a research assistant.",
)

swarm = Swarm([agent])
result = await swarm.run("Research quantum computing.")
```

## Network (`hanzo-network`)

```python
from hanzo_network import LocalComputeNode, DistributedNetwork

node = LocalComputeNode(node_id="node-001")
network = DistributedNetwork()
network.register_node(node)
```

## Memory (`hanzo-memory`)

Persistent memory and RAG backed by SQLite, with optional vector search
(`sqlite-vec`, `lancedb`, `kuzu`). Global state lives in `~/.hanzo/`; per-project
state in `.hanzo/`.

```python
from hanzo_memory import MemoryService

memory = MemoryService()
await memory.store("key", "value")
result = await memory.retrieve("key")
```

## Development

This is a `uv` workspace.

```bash
git clone https://github.com/hanzoai/python-sdk.git
cd python-sdk
uv sync --all-packages       # install the whole workspace

uv run pytest tests/ -v      # run tests
make lint                    # ruff lint
make format                  # ruff format
make type-check              # mypy / pyright
```

Per-package work:

```bash
uv run pytest pkg/hanzo-mcp -v
cd pkg/hanzo && uv build
```

## Configuration

```bash
HANZO_API_KEY=your-api-key
HANZO_BASE_URL=https://api.hanzo.ai
HANZO_LOG_LEVEL=INFO
```

Or `~/.hanzo/config.yaml`:

```yaml
api:
  key: your-api-key
  base_url: https://api.hanzo.ai
logging:
  level: INFO
```

## Security

- Transport is TLS 1.3+. Secrets belong in a KMS, never in source or plaintext.
- SOC 2 audit in progress; HIPAA BAA available.

Report vulnerabilities to **security@hanzo.ai**. See [SECURITY.md](SECURITY.md).

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Use type hints,
add tests for new behavior, and run `make lint` before opening a PR.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Support

- Docs: [docs.hanzo.ai](https://docs.hanzo.ai)
- Issues: [github.com/hanzoai/python-sdk/issues](https://github.com/hanzoai/python-sdk/issues)
- Email: support@hanzo.ai

## Hanzo — the Open AI Cloud

Open source · every language · on-chain settlement. [hanzo.ai](https://hanzo.ai) · [docs.hanzo.ai](https://docs.hanzo.ai)

**SDKs in every language** — [Python](https://github.com/hanzoai/python-sdk) (flagship) · [TypeScript](https://github.com/hanzo-js/sdk) · [Go](https://github.com/hanzo-go/sdk) · [Rust](https://github.com/hanzo-rs/sdk) · [C++](https://github.com/hanzo-cpp/sdk) · [Swift](https://github.com/hanzo-swift/sdk) · [Kotlin](https://github.com/hanzo-kt/sdk) · [umbrella](https://github.com/hanzoai/sdk)
