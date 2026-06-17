# hanzo-tools-gimp

Unified **GIMP automation** tool for Hanzo AI (HIP-0300).

Drives [GIMP](https://www.gimp.org/) 3.0 through the **Hanzo GIMP bridge** — a
clean-room, **BSD-3** GIMP plug-in (see `hanzo/gimp-mcp`) that exposes GIMP's
Procedural Database (PDB) over a line-oriented JSON TCP socket. This package is
the Python client for that bridge.

This is a clean-room implementation with **no GPL lineage**: both the bridge
and this client use GIMP's documented, public PDB / GObject-Introspection API.

## Install

```sh
pip install hanzo-tools-gimp
```

## Prerequisites

The Hanzo GIMP bridge plug-in must be running inside GIMP. Briefly:

1. Copy `hanzo_gimp_bridge.py` (from `hanzo/gimp-mcp`) into your GIMP 3.0
   plug-ins directory (one folder per plug-in, script made executable).
2. Start GIMP and run **Filters → Hanzo → Start Hanzo Bridge**.
3. The bridge listens on `127.0.0.1:9876` by default (override with
   `HANZO_GIMP_PORT` / `HANZO_GIMP_HOST`).

See the `gimp-mcp` repo's `README.md` and `PROTOCOL.md` for full details.

## Usage

```python
from hanzo_tools.gimp import GimpTool, register_tools, TOOLS

# Register with a FastMCP server
register_tools(mcp_server)            # optional host=..., port=...

# Or use the tool directly
tool = GimpTool(host="127.0.0.1", port=9876)
```

The tool exposes the same action surface as the Hanzo MCP TypeScript `gimp`
tool:

| Action            | Params                          | Result |
|-------------------|---------------------------------|--------|
| `version`         | —                               | `{bridge, gimp, protocol}` |
| `open`            | `path`                          | `{image_id, width, height}` |
| `export`          | `image_id`, `path`              | `{image_id, path, saved}` |
| `pdb_call`        | `procedure`, `args`             | the procedure's return value(s) |
| `new_image`       | `width`, `height`               | `{image_id, width, height}` |
| `image_info`      | `image_id`                      | `{image_id, width, height, ...}` |
| `list_procedures` | `prefix?`                       | `{count, procedures}` |
| `flatten`         | `image_id`                      | `{image_id, layer_id}` |

Every action also accepts `host` / `port` overrides.

`pdb_call` is the generic escape hatch — it can invoke **any** PDB procedure,
so anything GIMP can do is reachable.

## License

**BSD-3-Clause**. Copyright (c) 2026 Hanzo AI.
