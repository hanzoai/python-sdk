# hanzo-tools-cloud

The Hanzo Cloud surface, offered as the fleet publishes it: one entry per
subsystem carrying that subsystem's operation names, plus `describe`.

Nothing here is hand-written. `catalog.json` is generated from cloud's own typed
operations, and it is the same file the TypeScript (`@hanzo/mcp`) and Rust
(`hanzo-mcp`) runtimes embed — so the three cannot disagree about what the API
offers.

```python
from hanzo_tools.cloud import call, services, operations

services()              # every subsystem the fleet serves
operations("iam")       # that subsystem's operations
call("iam", "get_iam_users")
```

Every call goes to `api.hanzo.ai/v1/mcp`. Set `HANZO_API_KEY`; point elsewhere
with `HANZO_API_URL`.

Refresh the catalog from the repo root: `pnpm sync:catalog` in `hanzoai/mcp`, or
`go run ./plugin/gen-mcp-catalog .` in `hanzoai/cloud`.
