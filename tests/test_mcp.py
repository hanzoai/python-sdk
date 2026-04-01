"""Tests for MCP client implementation."""

import asyncio
import json
import sys
import textwrap

import pytest

from hanzoai.mcp import (
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
    MCPClient,
    MCPClientError,
    MCPHttpClient,
    mcp_tool_name,
    normalize_mcp_name,
)


# --- Name normalization tests ---


class TestNormalizeMcpName:
    def test_passthrough(self):
        assert normalize_mcp_name("hello") == "hello"

    def test_hyphens_kept(self):
        # Rust parity: hyphens are valid chars and kept as-is
        assert normalize_mcp_name("my-tool") == "my-tool"

    def test_dots_to_underscores(self):
        assert normalize_mcp_name("my.tool") == "my_tool"

    def test_slashes_to_underscores(self):
        assert normalize_mcp_name("my/tool") == "my_tool"

    def test_mixed_keeps_hyphens(self):
        assert normalize_mcp_name("my-tool.v2/action") == "my-tool_v2_action"

    def test_non_claude_keeps_consecutive_underscores(self):
        # Non-claude.ai names do NOT collapse underscores
        assert normalize_mcp_name("my--tool") == "my--tool"

    def test_non_claude_keeps_leading_trailing(self):
        # Non-claude.ai names do NOT strip leading/trailing
        assert normalize_mcp_name("-tool-") == "-tool-"

    def test_non_claude_trailing_underscore(self):
        assert normalize_mcp_name("tool name!") == "tool_name_"

    def test_github_dot_com(self):
        assert normalize_mcp_name("github.com") == "github_com"

    def test_claude_ai_collapses_and_strips(self):
        # claude.ai names get underscore collapsing + strip
        assert normalize_mcp_name("claude.ai Example   Server!!") == "claude_ai_Example_Server"

    def test_claude_ai_simple(self):
        assert normalize_mcp_name("claude.ai My Tool") == "claude_ai_My_Tool"


class TestMcpToolName:
    def test_basic(self):
        assert mcp_tool_name("server", "tool") == "mcp__server__tool"

    def test_normalizes_both(self):
        # Hyphens kept, so my-server stays my-server
        assert mcp_tool_name("my-server", "my-tool") == "mcp__my-server__my-tool"

    def test_claude_ai_server(self):
        assert mcp_tool_name("claude.ai Example Server", "weather tool") == "mcp__claude_ai_Example_Server__weather_tool"


# --- Protocol types tests ---


class TestJsonRpcRequest:
    def test_to_json(self):
        req = JsonRpcRequest(method="initialize", params={"a": 1}, id=1)
        d = req.to_dict()
        assert d["jsonrpc"] == "2.0"
        assert d["method"] == "initialize"
        assert d["params"] == {"a": 1}
        assert d["id"] == 1

    def test_to_line(self):
        req = JsonRpcRequest(method="test", params={}, id=42)
        line = req.to_line()
        assert line.endswith(b"\n")
        parsed = json.loads(line)
        assert parsed["id"] == 42


class TestJsonRpcResponse:
    def test_from_dict_success(self):
        resp = JsonRpcResponse.from_dict({"jsonrpc": "2.0", "result": {"ok": True}, "id": 1})
        assert resp.result == {"ok": True}
        assert resp.error is None
        assert resp.id == 1

    def test_from_dict_error(self):
        resp = JsonRpcResponse.from_dict({
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": 1,
        })
        assert resp.result is None
        assert resp.error is not None
        assert resp.error.code == -32600
        assert resp.error.message == "Invalid Request"


# --- Stdio MCPClient tests ---

# A minimal MCP server script that we spawn as a subprocess.
# It reads JSON-RPC from stdin and responds on stdout.
MOCK_SERVER_SCRIPT = textwrap.dedent("""\
    import json
    import sys

    def respond(id, result):
        msg = json.dumps({"jsonrpc": "2.0", "result": result, "id": id})
        sys.stdout.write(msg + "\\n")
        sys.stdout.flush()

    def respond_error(id, code, message):
        msg = json.dumps({"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": id})
        sys.stdout.write(msg + "\\n")
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        method = req["method"]
        rid = req["id"]

        if method == "initialize":
            respond(rid, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "mock", "version": "0.1.0"},
            })
        elif method == "tools/list":
            respond(rid, {
                "tools": [
                    {"name": "echo", "description": "echoes input", "inputSchema": {"type": "object"}},
                ],
            })
        elif method == "tools/call":
            tool_name = req["params"]["name"]
            args = req["params"].get("arguments", {})
            if tool_name == "echo":
                respond(rid, {"content": [{"type": "text", "text": json.dumps(args)}]})
            elif tool_name == "fail":
                respond_error(rid, -32000, "tool failed")
            else:
                respond_error(rid, -32601, f"unknown tool: {tool_name}")
        elif method == "resources/list":
            respond(rid, {"resources": [{"uri": "file:///test.txt", "name": "test.txt"}]})
        else:
            respond_error(rid, -32601, f"unknown method: {method}")
""")


class TestMCPClientStdio:
    @pytest.fixture
    async def client(self, tmp_path):
        script = tmp_path / "mock_server.py"
        script.write_text(MOCK_SERVER_SCRIPT)
        c = MCPClient(server_command=[sys.executable, str(script)])
        await c.connect()
        yield c
        await c.disconnect()

    async def test_connect_initializes(self, client):
        assert client.server_info is not None
        assert client.server_info["name"] == "mock"

    async def test_list_tools(self, client):
        tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "echo"

    async def test_call_tool(self, client):
        result = await client.call_tool("echo", arguments={"msg": "hello"})
        assert result["content"][0]["text"] == '{"msg": "hello"}'

    async def test_call_tool_error(self, client):
        with pytest.raises(MCPClientError, match="tool failed"):
            await client.call_tool("fail")

    async def test_list_resources(self, client):
        resources = await client.list_resources()
        assert len(resources) == 1
        assert resources[0]["uri"] == "file:///test.txt"

    async def test_context_manager(self, tmp_path):
        script = tmp_path / "mock_server.py"
        script.write_text(MOCK_SERVER_SCRIPT)
        async with MCPClient(server_command=[sys.executable, str(script)]) as c:
            tools = await c.list_tools()
            assert len(tools) == 1

    async def test_request_ids_increment(self, client):
        # Each call increments the request id
        id_before = client._next_id
        await client.list_tools()
        assert client._next_id == id_before + 1

    async def test_disconnect_kills_process(self, tmp_path):
        script = tmp_path / "mock_server.py"
        script.write_text(MOCK_SERVER_SCRIPT)
        c = MCPClient(server_command=[sys.executable, str(script)])
        await c.connect()
        proc = c._process
        await c.disconnect()
        assert c._process is None
        # Process should be terminated
        assert proc.returncode is not None


class TestMCPClientNotConnected:
    async def test_list_tools_without_connect(self):
        c = MCPClient(server_command=["true"])
        with pytest.raises(MCPClientError, match="not connected"):
            await c.list_tools()

    async def test_call_tool_without_connect(self):
        c = MCPClient(server_command=["true"])
        with pytest.raises(MCPClientError, match="not connected"):
            await c.call_tool("x")


class TestMCPClientBadProcess:
    async def test_connect_to_nonexistent_binary(self):
        c = MCPClient(server_command=["__nonexistent_binary_xyz__"])
        with pytest.raises(MCPClientError):
            await c.connect()
