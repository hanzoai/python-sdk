"""tools — list the tools this key can reach.

``GET /v1/tools`` (operationId ``get_tools``), the catalog behind the
MCP surface: each entry is a tool name, its description and its input schema.

A note on the MCP door, because it is easy to pick the wrong one. There is a
live JSON-RPC endpoint at ``POST /v1/mcp`` that answers ``tools/list`` with the
same catalog (730 tools at the time of writing) — but it is NOT in hanzo.yaml,
so the generator emits no method for it and an example would have to bypass the
SDK to call it, which defeats the point of an SDK example. Of the MCP routes
that ARE declared, ``/v1/automations/mcp`` returns 405 at api.hanzo.ai. So this
catalog read is the one that is both generated and served. When ``/v1/mcp`` is
added to the spec, this flow should move to it.

    python -m examples.tools
"""

from hanzoai.cloud import ToolsApi

from examples.client import client, run


def main() -> None:
    with client() as api:
        catalog = ToolsApi(api).get_tools()

    tools = catalog.tools or []
    print(f"{len(tools)} tools")
    for tool in tools[:20]:
        print(f"  {tool.name} — {tool.description or '(no description)'}")
    if len(tools) > 20:
        print(f"  … and {len(tools) - 20} more")


if __name__ == "__main__":
    run(main)
