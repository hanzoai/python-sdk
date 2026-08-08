# hanzo-flags

Feature flags + A/B testing for Python, on the Hanzo native flags engine.

The Python client for cloud `/v1/flags` — the same PostHog-compatible evaluation
endpoint the Rust core, Go binding, and `@hanzo/flags` (TypeScript) all speak. One
flag definition, evaluated identically in every language.

**Zero runtime dependencies** — stdlib `urllib` only. A flag check must never drag
a dependency tree into a service.

## Install

```bash
pip install hanzo-flags     # or: uv add hanzo-flags
```

## Use

```python
from hanzo_flags import HanzoFlags

flags = HanzoFlags("https://api.hanzo.ai", token="sk-...")
flags.load("user-123", person_properties={"plan": "pro"})

if flags.is_enabled("checkout-exp"):
    ...

variant = flags.variant("pricing-test")   # "control" | "b" | None
payload = flags.payload("pricing-test")   # the flag's JSON payload, or None
```

Group targeting (orgs/teams):

```python
from hanzo_flags import Group

flags.load(
    "user-123",
    groups={"0": Group(key="acme", properties={"tier": "gold"})},
)
```

Async (asyncio services):

```python
from hanzo_flags import AsyncHanzoFlags

flags = AsyncHanzoFlags("https://api.hanzo.ai", token="sk-...")
await flags.load("user-123")
if flags.is_enabled("checkout-exp"):
    ...
```

One-shot:

```python
from hanzo_flags import evaluate
res = evaluate("https://api.hanzo.ai", "user-123", token="sk-...")
res.is_enabled("checkout-exp")
```

## Guarantees

- **Fail-open.** A transport or decode error returns the last good (or empty)
  result with `errors_while_computing` set — `load()` never raises on the hot path.
- **Cached by context + TTL** (default 15s). Re-evaluating the same context inside
  the TTL is free, so a hot path may call `load()` freely.

## The family

| Language   | Package               | Mode                                   |
|------------|-----------------------|----------------------------------------|
| Rust       | `hanzo-flags` crate   | native (the evaluation core)           |
| Go         | `cloud/clients/flags` | in-process via FFI to the Rust core    |
| TypeScript | `@hanzo/flags`        | HTTP to `/v1/flags` (browser + node)   |
| Python     | `hanzo-flags`         | HTTP to `/v1/flags` (this package)     |

All four resolve the same flag to the same value: the definitions live once in the
cloud flags cockpit (`/v1/flags/defs`), and every client evaluates against them.
