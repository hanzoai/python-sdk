"""ZAP protocol test suite.

Covers types, wire format encoding, server tool dispatch,
and full client-server integration over TCP.
"""

import asyncio
import json
import struct

import pytest
import pytest_asyncio

from hanzo_zap import (
    ApprovalPolicy,
    ClientInfo,
    MessageType,
    SandboxPolicy,
    ServerInfo,
    Tool,
    ToolCall,
    ToolResult,
    ZapClient,
    ZapServer,
)


# -- types -------------------------------------------------------------------

class TestMessageType:
    def test_handshake(self):
        assert MessageType.INIT == 0x01
        assert MessageType.INIT_ACK == 0x02

    def test_tools(self):
        assert MessageType.LIST_TOOLS == 0x10
        assert MessageType.LIST_TOOLS_RESPONSE == 0x11
        assert MessageType.CALL_TOOL == 0x12
        assert MessageType.CALL_TOOL_RESPONSE == 0x13

    def test_resources(self):
        assert MessageType.LIST_RESOURCES == 0x20
        assert MessageType.LIST_RESOURCES_RESPONSE == 0x21
        assert MessageType.READ_RESOURCE == 0x22
        assert MessageType.READ_RESOURCE_RESPONSE == 0x23

    def test_prompts(self):
        assert MessageType.LIST_PROMPTS == 0x30
        assert MessageType.LIST_PROMPTS_RESPONSE == 0x31
        assert MessageType.GET_PROMPT == 0x32
        assert MessageType.GET_PROMPT_RESPONSE == 0x33

    def test_control(self):
        assert MessageType.PING == 0xF0
        assert MessageType.PONG == 0xF1
        assert MessageType.ERROR == 0xFF

    def test_cast_from_int(self):
        assert MessageType(1) is MessageType.INIT
        assert MessageType(0xFF) is MessageType.ERROR

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            MessageType(0x99)

    def test_all_unique(self):
        values = [m.value for m in MessageType]
        assert len(values) == len(set(values))


class TestTool:
    def test_defaults(self):
        t = Tool(name="read", description="Read a file")
        assert t.name == "read"
        assert t.description == "Read a file"
        assert t.input_schema == {}

    def test_schema(self):
        schema = {"type": "object", "properties": {"path": {"type": "string"}}}
        t = Tool(name="read", description="Read", input_schema=schema)
        assert t.input_schema["properties"]["path"]["type"] == "string"

    def test_serializes(self):
        t = Tool(name="x", description="y")
        assert t.__dict__ == {"name": "x", "description": "y", "input_schema": {}}


class TestToolCall:
    def test_fields(self):
        tc = ToolCall(id="r-1", name="read", args={"path": "/tmp"})
        assert tc.id == "r-1"
        assert tc.name == "read"
        assert tc.args == {"path": "/tmp"}
        assert tc.metadata is None

    def test_defaults(self):
        tc = ToolCall(id="r-2", name="ping")
        assert tc.args == {}
        assert tc.metadata is None


class TestToolResult:
    def test_success(self):
        tr = ToolResult(id="r-1", content="hello")
        assert tr.content == "hello"
        assert tr.error is None

    def test_error(self):
        tr = ToolResult(id="r-1", error="boom")
        assert tr.error == "boom"
        assert tr.content is None

    def test_metadata(self):
        tr = ToolResult(id="r-1", content="ok", metadata={"latency_ms": 12})
        assert tr.metadata["latency_ms"] == 12


class TestServerInfo:
    def test_defaults(self):
        si = ServerInfo(name="test", version="1.0")
        assert si.capabilities == {"tools": True, "resources": False, "prompts": False}

    def test_custom_capabilities(self):
        si = ServerInfo(name="x", version="1", capabilities={"tools": True, "resources": True, "prompts": True})
        assert si.capabilities["resources"] is True


class TestClientInfo:
    def test_fields(self):
        ci = ClientInfo(name="hanzo-zap", version="0.6.1")
        assert ci.name == "hanzo-zap"
        assert ci.version == "0.6.1"


class TestApprovalPolicy:
    def test_all_values(self):
        assert ApprovalPolicy.UNLESS_TRUSTED == "unless-trusted"
        assert ApprovalPolicy.ON_FAILURE == "on-failure"
        assert ApprovalPolicy.ON_REQUEST == "on-request"
        assert ApprovalPolicy.NEVER == "never"


class TestSandboxPolicy:
    def test_danger_full_access(self):
        sp = SandboxPolicy.danger_full_access()
        assert sp.mode == "danger-full-access"
        assert sp.writable_roots == []
        assert sp.network_access is False

    def test_read_only(self):
        sp = SandboxPolicy.read_only()
        assert sp.mode == "read-only"

    def test_workspace_write(self):
        sp = SandboxPolicy.workspace_write(
            writable_roots=["/tmp", "/workspace"],
            network_access=True,
            allow_git_writes=True,
        )
        assert sp.mode == "workspace-write"
        assert len(sp.writable_roots) == 2
        assert sp.network_access is True
        assert sp.allow_git_writes is True

    def test_workspace_write_defaults(self):
        sp = SandboxPolicy.workspace_write()
        assert sp.writable_roots == []
        assert sp.network_access is False
        assert sp.allow_git_writes is False


# -- wire format -------------------------------------------------------------

class TestWireFormat:
    """Binary wire format: [4-byte LE length][1-byte type][JSON payload]."""

    def test_header_size(self):
        header = struct.pack("<IB", 42, MessageType.INIT)
        assert len(header) == 5

    def test_header_roundtrip(self):
        payload = b'{"key":"value"}'
        total_len = 1 + len(payload)
        header = struct.pack("<IB", total_len, MessageType.CALL_TOOL)
        dec_len, dec_type = struct.unpack("<IB", header)
        assert dec_len == total_len
        assert dec_type == MessageType.CALL_TOOL

    def test_empty_payload(self):
        header = struct.pack("<IB", 1, MessageType.PING)
        dec_len, _ = struct.unpack("<IB", header)
        assert dec_len == 1  # type byte only

    def test_full_message_roundtrip(self):
        data = {"tools": [{"name": "read", "description": "Read file"}]}
        payload = json.dumps(data).encode("utf-8")
        total_len = 1 + len(payload)
        msg = struct.pack("<IB", total_len, MessageType.LIST_TOOLS_RESPONSE) + payload

        dec_len, dec_type = struct.unpack("<IB", msg[:5])
        dec_payload = json.loads(msg[5 : 5 + dec_len - 1])
        assert dec_type == MessageType.LIST_TOOLS_RESPONSE
        assert dec_payload == data

    def test_max_encodable_length(self):
        # 4-byte LE unsigned int can hold up to 4GB, 16MB is the protocol limit
        payload = b"x" * (16 * 1024 * 1024)
        total_len = 1 + len(payload)
        header = struct.pack("<IB", total_len, MessageType.CALL_TOOL_RESPONSE)
        dec_len, _ = struct.unpack("<IB", header)
        assert dec_len == total_len

    def test_unicode_payload(self):
        data = {"text": "Hello, \u4e16\u754c\U0001f30d"}
        payload = json.dumps(data).encode("utf-8")
        total_len = 1 + len(payload)
        msg = struct.pack("<IB", total_len, MessageType.CALL_TOOL_RESPONSE) + payload
        dec_len, _ = struct.unpack("<IB", msg[:5])
        decoded = json.loads(msg[5 : 5 + dec_len - 1])
        assert decoded["text"] == data["text"]


# -- server unit tests -------------------------------------------------------

class TestZapServer:
    def test_init(self):
        server = ZapServer(name="test-server", version="1.0.0")
        assert server._info.name == "test-server"
        assert server._info.version == "1.0.0"
        assert server._info.capabilities["tools"] is True
        assert len(server._tools) == 0

    def test_register_tool(self):
        server = ZapServer(name="s", version="1")

        async def handler(name, args):
            return "ok"

        server.register_tool("greet", "Greet user", {"type": "object"}, handler)
        assert "greet" in server._tools
        tool, h = server._tools["greet"]
        assert tool.name == "greet"
        assert tool.description == "Greet user"
        assert h is handler

    def test_register_multiple(self):
        server = ZapServer(name="s", version="1")
        for i in range(10):
            server.register_tool(f"tool_{i}", f"Tool {i}", {}, lambda n, a: None)
        assert len(server._tools) == 10

    def test_decorator(self):
        server = ZapServer(name="s", version="1")

        @server.tool("echo", "Echo input")
        async def echo(name, args):
            return args.get("text", "")

        assert "echo" in server._tools
        tool, _ = server._tools["echo"]
        assert tool.description == "Echo input"

    def test_decorator_preserves_function(self):
        server = ZapServer(name="s", version="1")

        @server.tool("fn", "Fn")
        async def fn(name, args):
            return 42

        # decorator returns the original function
        assert asyncio.iscoroutinefunction(fn)

    @pytest.mark.asyncio
    async def test_execute_async_handler(self):
        server = ZapServer(name="s", version="1")

        async def adder(name, args):
            return args["a"] + args["b"]

        server.register_tool("add", "Add", {}, adder)
        result = await server._execute_tool({"name": "add", "args": {"a": 2, "b": 3}, "id": "t1"})
        assert result.content == 5
        assert result.error is None
        assert result.id == "t1"

    @pytest.mark.asyncio
    async def test_execute_sync_handler(self):
        server = ZapServer(name="s", version="1")

        def handler(name, args):
            return "sync-result"

        server.register_tool("sync", "Sync", {}, handler)
        result = await server._execute_tool({"name": "sync", "args": {}, "id": "t2"})
        assert result.content == "sync-result"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        server = ZapServer(name="s", version="1")
        result = await server._execute_tool({"name": "missing", "args": {}, "id": "t3"})
        assert "Unknown tool" in result.error
        assert result.content is None

    @pytest.mark.asyncio
    async def test_execute_handler_exception(self):
        server = ZapServer(name="s", version="1")

        async def bad(name, args):
            raise ValueError("broken")

        server.register_tool("bad", "Bad", {}, bad)
        result = await server._execute_tool({"name": "bad", "args": {}, "id": "t4"})
        assert result.error == "broken"
        assert result.content is None

    @pytest.mark.asyncio
    async def test_execute_returns_complex_types(self):
        server = ZapServer(name="s", version="1")

        async def handler(name, args):
            return {"nested": [1, 2, 3], "ok": True}

        server.register_tool("complex", "Complex", {}, handler)
        result = await server._execute_tool({"name": "complex", "args": {}, "id": "t5"})
        assert result.content == {"nested": [1, 2, 3], "ok": True}


# -- client-server integration -----------------------------------------------

async def _free_port() -> int:
    srv = await asyncio.start_server(lambda r, w: None, "127.0.0.1", 0)
    port = srv.sockets[0].getsockname()[1]
    srv.close()
    await srv.wait_closed()
    return port


@pytest_asyncio.fixture
async def zap_fixture():
    server = ZapServer(name="test-tools", version="0.1.0")

    @server.tool("greet", "Greet someone", {"type": "object", "properties": {"name": {"type": "string"}}})
    async def greet(tool_name, args):
        return f"Hello, {args.get('name', 'world')}!"

    @server.tool("add", "Add numbers")
    async def add(tool_name, args):
        return args["a"] + args["b"]

    @server.tool("fail", "Always fails")
    async def fail(tool_name, args):
        raise RuntimeError("intentional")

    @server.tool("echo", "Echo back")
    def echo(tool_name, args):
        return args.get("text", "")

    @server.tool("slow", "Simulate work")
    async def slow(tool_name, args):
        await asyncio.sleep(0.01)
        return "done"

    port = await _free_port()
    await server.start(port, "127.0.0.1")
    yield server, port
    await server.stop()


@pytest.mark.asyncio
class TestIntegration:

    async def test_handshake(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        assert client.server_info.name == "test-tools"
        assert client.server_info.version == "0.1.0"
        assert client.server_info.capabilities["tools"] is True
        await client.close()

    async def test_list_tools(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        tools = await client.list_tools()
        names = {t.name for t in tools}
        assert names == {"greet", "add", "fail", "echo", "slow"}
        for t in tools:
            assert isinstance(t.description, str)
            assert len(t.description) > 0
        await client.close()

    async def test_tool_schema_preserved(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        tools = await client.list_tools()
        greet = next(t for t in tools if t.name == "greet")
        assert greet.input_schema["type"] == "object"
        assert "name" in greet.input_schema["properties"]
        await client.close()

    async def test_call_tool(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("greet", {"name": "Hanzo"})
        assert result.content == "Hello, Hanzo!"
        assert result.error is None
        assert result.id.startswith("req-")
        await client.close()

    async def test_call_tool_numeric(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("add", {"a": 10, "b": 32})
        assert result.content == 42
        await client.close()

    async def test_call_tool_error(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("fail", {})
        assert result.error == "intentional"
        assert result.content is None
        await client.close()

    async def test_call_sync_handler(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("echo", {"text": "abc"})
        assert result.content == "abc"
        await client.close()

    async def test_call_slow_tool(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("slow", {})
        assert result.content == "done"
        await client.close()

    async def test_unknown_tool(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("nonexistent", {})
        assert "Unknown tool" in result.error
        await client.close()

    async def test_ping(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        await client.ping()
        await client.close()

    async def test_sequential_calls(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        for i in range(5):
            r = await client.call_tool("add", {"a": i, "b": i})
            assert r.content == i * 2
        await client.close()

    async def test_batch(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        results = await client.batch([
            {"name": "add", "args": {"a": 1, "b": 1}},
            {"name": "greet", "args": {"name": "batch"}},
            {"name": "echo", "args": {"text": "ok"}},
        ])
        assert len(results) == 3
        assert results[0].content == 2
        assert results[1].content == "Hello, batch!"
        assert results[2].content == "ok"
        await client.close()

    async def test_batch_with_error(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        results = await client.batch([
            {"name": "add", "args": {"a": 1, "b": 2}},
            {"name": "fail", "args": {}},
        ])
        assert results[0].content == 3
        assert results[0].error is None
        assert results[1].error == "intentional"
        await client.close()

    async def test_context_manager(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        async with client:
            result = await client.call_tool("greet", {"name": "ctx"})
            assert result.content == "Hello, ctx!"

    async def test_request_ids_increment(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        r1 = await client.call_tool("echo", {"text": "a"})
        r2 = await client.call_tool("echo", {"text": "b"})
        # IDs should be sequential
        id1 = int(r1.id.split("-")[1])
        id2 = int(r2.id.split("-")[1])
        assert id2 == id1 + 1
        await client.close()

    async def test_multiple_clients(self, zap_fixture):
        _, port = zap_fixture
        c1 = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        c2 = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        r1 = await c1.call_tool("add", {"a": 1, "b": 2})
        r2 = await c2.call_tool("add", {"a": 3, "b": 4})
        assert r1.content == 3
        assert r2.content == 7
        await c1.close()
        await c2.close()

    async def test_large_payload(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        big_text = "x" * 100_000
        result = await client.call_tool("echo", {"text": big_text})
        assert result.content == big_text
        await client.close()

    async def test_empty_args(self, zap_fixture):
        _, port = zap_fixture
        client = await ZapClient.connect(f"zap://127.0.0.1:{port}")
        result = await client.call_tool("greet", {})
        assert result.content == "Hello, world!"
        await client.close()
