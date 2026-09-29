"""A Next-shaped MCP server for the suite: streamable HTTP at /_next/mcp, whose
get_errors answers the way Next 16 does — a JSON text block with ANSI colour.

It runs in its own process: the SDK's streamable HTTP server leaves memory
streams unclosed, and in-process that would fail warnings-as-errors on the
server's account rather than the client's.
"""

import sys
import time
import socket
import subprocess

import pytest
from hanzo_tools.devserver import discovery

SERVER = """
import json, socket, uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("next", stateless_http=True, streamable_http_path="/_next/mcp")

@mcp.tool()
def get_errors():
    \"\"\"Current errors.\"\"\"
    return json.dumps({"sessionErrors": [{"url": "/", "buildError": "\\x1b[31m./app/page.jsx:3:1\\x1b[0m Expected '>'"}]})

@mcp.tool()
def get_routes():
    \"\"\"Routes.\"\"\"
    return json.dumps({"appRouter": ["/"]})

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1], flush=True)
uvicorn.Server(uvicorn.Config(mcp.streamable_http_app(), log_level="error")).run(sockets=[sock])
"""


def wait_listening(port: int) -> None:
    deadline = time.monotonic() + 10
    while True:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.05)


@pytest.fixture
def next_mcp():
    """Port of a running Next-shaped MCP server."""
    proc = subprocess.Popen([sys.executable, "-c", SERVER], stdout=subprocess.PIPE, text=True)
    try:
        port = int(proc.stdout.readline())
        wait_listening(port)
        yield port
    finally:
        proc.terminate()
        proc.wait()
        proc.stdout.close()


@pytest.fixture(autouse=True)
def fresh_schemes():
    discovery._schemes.clear()
    yield
    discovery._schemes.clear()


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port
