"""The devserver tool on a real FastMCP registry, beside a stand-in `browser` tool."""

import json

import pytest
from mcp.server.fastmcp import FastMCP
from hanzo_tools.devserver import DevServer, DevserverTool, discovery, devserver_tool
from hanzo_tools.devserver.devserver_tool import since, payload, structured


def test_description_is_three_lines_at_most():
    assert len(DevserverTool().description.splitlines()) <= 3


async def test_help_lists_the_actions():
    envelope = await DevserverTool().call(None, action="help")
    assert set(envelope["data"]["actions"]) == {"index", "call", "errors"}
    assert "index" in envelope["data"]["workflow"]


def test_payload():
    assert payload({"structuredContent": {"a": 1}, "content": []}) == {"a": 1}
    assert payload({"content": [{"type": "text", "text": '{"e":"\\u001b[31mred\\u001b[0m"}'}]}) == {"e": "red"}
    assert payload({"content": [{"type": "text", "text": "\x1b[1mplain\x1b[0m"}]}) == "plain"
    image = {"type": "image", "data": "AA==", "mimeType": "image/png"}
    assert payload({"content": [{"type": "text", "text": "[1]"}, image]}) == [[1], image]
    assert payload({"content": []}) == []


def test_since_keeps_only_entries_counted_after_the_baseline():
    assert since({"messages": [1, 2, 3, 4], "count": 9}, "messages", 7) == [3, 4]
    assert since({"messages": [1, 2], "count": 9}, "messages", 2) == [1, 2]
    assert since({"messages": [1, 2], "count": 2}, "messages", 2) == []
    assert since({"errors": ["x"]}, "errors", 0) == ["x"]
    assert since({"error": "no browser"}, "errors", 0) == []


def test_structured():
    class Text:
        def __init__(self, text):
            self.text = text

    assert structured(([], {"a": 1})) == {"a": 1}
    assert structured([Text('{"a": 1}')]) == {"a": 1}
    assert structured([Text("not json")]) == {"text": "not json"}
    assert structured([Text('{"ok": true, "data": {"a": 1}, "error": null}')]) == {"a": 1}
    assert structured([Text('{"ok": false, "data": null, "error": {"code": "X"}}')]) == {"error": {"code": "X"}}


def registry(pages: list[dict]):
    """A FastMCP with devserver and a `browser` that records calls and answers from `pages` in order."""
    server = FastMCP("test")
    calls = []

    @server.tool(name="browser")
    async def browser(action: str, url: str = "", state: str = "", level: str = "", code: str = "") -> dict:
        calls.append({k: v for k, v in dict(action=action, url=url, state=state, level=level).items() if v})
        return pages.pop(0)

    DevserverTool().register(server)
    return server, calls


async def run(server: FastMCP, **args) -> dict:
    [block] = await server.call_tool("devserver", args)
    return json.loads(block.text)


async def test_errors_opens_the_app_then_asks_the_servers_mcp(monkeypatch, next_mcp):
    monkeypatch.setattr(discovery, "scan", lambda: [])
    server, calls = registry([{"success": True}])
    out = await run(server, action="errors", port=next_mcp, path="dashboard")
    assert out["ok"], out
    assert calls == [{"action": "navigate", "url": f"http://localhost:{next_mcp}/dashboard", "state": "networkidle"}]
    data = out["data"]
    assert data["source"] == "mcp"
    assert data["result"] == {"sessionErrors": [{"url": "/", "buildError": "./app/page.jsx:3:1 Expected '>'"}]}
    assert "browser" not in data


async def test_errors_from_the_mcp_stands_when_the_browser_fails(monkeypatch, next_mcp):
    monkeypatch.setattr(discovery, "scan", lambda: [])
    server, _ = registry([{"error": "no browser"}])
    data = (await run(server, action="errors", port=next_mcp))["data"]
    assert data["browser"] == "no browser"
    assert data["result"]["sessionErrors"]


async def test_errors_reads_the_page_without_mcp(monkeypatch):
    vite = DevServer(port=5174, url="http://localhost:5174", framework="vite")

    async def one(port=None, cwd=None):
        return [vite]

    monkeypatch.setattr(devserver_tool, "discover", one)
    overlay = {"plugin": "[plugin:vite:oxc]", "message": "Transform failed", "file": "/app/src/label.ts"}
    server, calls = registry(
        [
            {"success": True, "messages": [{"text": "old"}], "count": 1},
            {"success": True, "errors": ["old"], "count": 1},
            {"success": True},
            {"success": True, "result": overlay},
            {"success": True, "messages": [{"text": "old"}, {"text": "500"}], "count": 2},
            {"success": True, "errors": ["old"], "count": 1},
        ]
    )
    data = (await run(server, action="errors"))["data"]
    assert [c["action"] for c in calls] == ["console", "errors", "navigate", "evaluate", "console", "errors"]
    assert calls[2]["state"] == "networkidle"
    assert data == {
        "server": "http://localhost:5174",
        "source": "browser",
        "overlay": overlay,
        "console": [{"text": "500"}],
        "errors": [],
    }


async def test_call_runs_a_listed_tool(monkeypatch, next_mcp):
    monkeypatch.setattr(discovery, "scan", lambda: [])
    server, _ = registry([])
    data = (await run(server, action="call", port=next_mcp, tool="get_routes"))["data"]
    assert data["result"] == {"appRouter": ["/"]}
    assert data["is_error"] is False
    missing = await run(server, action="call", port=next_mcp, tool="get_nothing")
    assert missing["error"]["code"] == "NOT_FOUND"


async def test_call_goes_to_the_one_server_listing_the_tool(monkeypatch, next_mcp):
    next_like = DevServer(port=next_mcp, framework="next", mcp=f"http://localhost:{next_mcp}/_next/mcp")
    next_like.tools = [{"name": "get_routes"}]
    vite = DevServer(port=5180, framework="vite", mcp="http://localhost:5180/__mcp/sse")
    vite.tools = [{"name": "get-vite-config"}]

    async def both(port=None, cwd=None):
        return [vite, next_like]

    monkeypatch.setattr(devserver_tool, "discover", both)
    server, _ = registry([])
    data = (await run(server, action="call", tool="get_routes"))["data"]
    assert data["server"] == next_like.mcp
    assert data["result"] == {"appRouter": ["/"]}


async def test_ambiguous_servers_ask_for_a_port(monkeypatch):
    async def two(port=None, cwd=None):
        return [DevServer(port=3000, framework="next"), DevServer(port=5173, framework="vite")]

    monkeypatch.setattr(devserver_tool, "discover", two)
    server, _ = registry([])
    out = await run(server, action="errors")
    assert out["error"]["code"] == "INVALID_PARAMS"
    assert "3000 (next), 5173 (vite)" in out["error"]["message"]
