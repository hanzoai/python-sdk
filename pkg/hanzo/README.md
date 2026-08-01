# hanzo

[![PyPI](https://img.shields.io/pypi/v/hanzo.svg)](https://pypi.org/project/hanzo/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzo.svg)](https://pypi.org/project/hanzo/)

Python orchestration helpers for Hanzo AI, and the older Python implementation of
the Hanzo CLI.

## The `hanzo` command lives elsewhere now

The Hanzo CLI is a native binary. Install it with:

```bash
curl -fsSL https://hanzo.sh | sh
hanzo auth login
```

That gives you `hanzo` (and `hanzo-node`, a symlink to the same build) with one
command group per Hanzo Cloud product. This package's console script is
**`hanzo-py`** — deliberately not `hanzo`, so it cannot shadow the real CLI on
your PATH:

```bash
pip install hanzo
hanzo-py --help
```

Nothing here is being removed. If you have scripts on `hanzo-py`, they keep
working; new work should target the native CLI.

## What's still useful here

The Python library pieces, importable without touching the CLI:

```python
from hanzo.batch_orchestrator import BatchOrchestrator

orchestrator = BatchOrchestrator()
results = await orchestrator.run_batch([
    "Summarize the incident report",
    "Draft the follow-up email",
])
```

```python
from hanzo.memory_manager import MemoryManager

memory = MemoryManager()
memory.add_to_context("user", "What changed in the last deploy?")
context = memory.get_context()
```

```python
from hanzo.fallback_handler import FallbackHandler

handler = FallbackHandler()
result = await handler.handle_with_fallback(
    primary_fn=api_call,
    fallback_fn=local_inference,
)
```

For the typed Hanzo Cloud API client, install [`hanzoai`](https://pypi.org/project/hanzoai/).

## Configuration

```bash
HANZO_API_KEY=hk-...
HANZO_BASE_URL=https://api.hanzo.ai
```

Model ids come from the cloud catalog, not from this file — `zen5`,
`zen5-coder`, `zen5-flash`, `zen5-mini`, `zen5-pro`, `enso`, `enso-flash`,
`enso-ultra`. Ask the cloud rather than hardcoding: `hanzo models list`.

## Development

```bash
cd pkg/hanzo
uv sync --all-extras
uv build
```

## License

Apache 2.0
