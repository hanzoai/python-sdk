"""MCPServerConnection over HTTP, against a real MCP server on loopback.

The server runs in its own process: the SDK's streamable HTTP server leaves
memory streams unclosed, and in-process that would fail this suite's
warnings-as-errors on the server's account rather than the client's.
"""

import sys
import time
import socket
import subprocess
from contextlib import contextmanager

import pytest
from hanzo_tools.mcp_tools.mcp_proxy import MCPServerConfig, MCPServerConnection

SERVER = """
import sys, socket, uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("echo", stateless_http=True)

@mcp.tool()
def echo(text: str) -> str:
    \"\"\"Say it back.\"\"\"
    return text

app = mcp.sse_app() if sys.argv[1] == "sse" else mcp.streamable_http_app()
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1], flush=True)
uvicorn.Server(uvicorn.Config(app, log_level="error")).run(sockets=[sock])
"""


@contextmanager
def serving(transport: str):
    """An echo MCP server on a free loopback port, for the length of the block."""
    proc = subprocess.Popen([sys.executable, "-c", SERVER, transport], stdout=subprocess.PIPE, text=True)
    try:
        port = int(proc.stdout.readline())
        deadline = time.monotonic() + 10
        while True:
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.05)
        yield port
    finally:
        proc.terminate()
        proc.wait()
        proc.stdout.close()


@pytest.mark.parametrize("transport,path", [("streamable", "/mcp"), ("sse", "/sse")])
async def test_lists_and_calls_over_http(transport, path):
    with serving(transport) as port:
        conn = MCPServerConnection(MCPServerConfig(name="echo", url=f"http://localhost:{port}{path}"))
        assert await conn.connect(), conn.error
        assert [t.name for t in conn.tools] == ["echo"]
        assert conn.tools[0].input_schema["required"] == ["text"]

        result = await conn.call_tool("echo", {"text": "hi"})
        assert result["content"] == [{"type": "text", "text": "hi"}]
        assert result["isError"] is False


async def test_unreachable_url_reports_why():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    conn = MCPServerConnection(MCPServerConfig(name="gone", url=f"http://localhost:{port}/mcp"))
    assert not await conn.connect()
    assert conn.error.startswith("ConnectError")
