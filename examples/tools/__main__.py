"""tools — list the MCP tools this key can reach.

``POST /v1/automations/mcp`` (operationId ``automations_mcp``) is the JSON-RPC
2.0 MCP surface in hanzo.yaml, and the only one with typed request/response
schemas — ``method`` is an enum the model validates, so ``tools/lst`` is a
pydantic ValidationError here rather than a -32601 at runtime.

JSON-RPC reports failure INSIDE a 200: a bad method comes back as
``error={code, message}``, not an HTTP 4xx, so no exception is raised. Check
``error`` before reading ``result``.

    python -m examples.tools
"""

from hanzoai.cloud import AutomationsMcpRequest, MCPApi

from examples.client import client, run


def main() -> None:
    with client() as api:
        response = MCPApi(api).automations_mcp(
            AutomationsMcpRequest(jsonrpc="2.0", id=1, method="tools/list")
        )

    if response.error:
        raise SystemExit(f"JSON-RPC {response.error.code}: {response.error.message}")

    tools = (response.result or {}).get("tools", [])
    print(f"{len(tools)} tools")
    for tool in tools:
        print(f"  {tool.get('name')} — {tool.get('description') or '(no description)'}")


if __name__ == "__main__":
    run(main)
