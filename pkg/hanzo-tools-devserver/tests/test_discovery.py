"""Discovery: argv, package.json and port parsing, and MCP protocol probing."""

import sys
import json
import threading
import subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import pytest
from conftest import free_port
from hanzo_tools.devserver import discovery
from hanzo_tools.devserver.discovery import (
    NEXT_MCP,
    VITE_MCP,
    scan,
    probe,
    binary,
    within,
    answers,
    discover,
    identify,
    mcp_paths,
)


@pytest.mark.parametrize(
    "argv,framework",
    [
        (["next-server (v16.3.7)", "", ""], "next"),
        (["node", "/app/node_modules/next/dist/bin/next", "dev"], "next"),
        (["node", "./node_modules/.bin/../vite/bin/vite.js", "--config", "plain.config.js"], "vite"),
        (["node", "/app/node_modules/.pnpm/vite@8.3.1/node_modules/vite/bin/vite.js"], "vite"),
        (["bun", "/app/node_modules/.bin/vite"], "vite"),
        (["node", "/app/node_modules/nuxi/bin/nuxi.mjs", "dev"], "nuxt"),
        (["node", "/app/node_modules/.bin/react-router", "dev"], "react-router"),
        (["node", "/app/node_modules/.bin/remix", "vite:dev"], "remix"),
        (["node", "/app/node_modules/astro/astro.js", "dev"], "astro"),
        (["node", "scripts/serve.mjs", "out", "5173"], None),
        (["node", "/home/z/next/server.js"], None),
        (["python3", "-m", "http.server"], None),
        ([], None),
    ],
)
def test_binary(argv, framework):
    assert binary(argv) == framework


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_identify_prefers_the_framework_over_vite_and_reads_the_hoisted_version(tmp_path):
    app = tmp_path / "apps" / "web"
    write(app / "package.json", {"devDependencies": {"vite": "^8.0.0", "@sveltejs/kit": "^2.0.0"}})
    write(tmp_path / "node_modules" / "@sveltejs" / "kit" / "package.json", {"version": "2.5.1"})
    (app / "src").mkdir()
    assert identify(str(app / "src")) == ("sveltekit", "2.5.1", str(app))


def test_identify_skips_manifests_without_a_framework(tmp_path):
    write(tmp_path / "package.json", {"dependencies": {"next": "16.3.7"}})
    write(tmp_path / "packages" / "ui" / "package.json", {"dependencies": {"react": "19"}})
    assert identify(str(tmp_path / "packages" / "ui")) == ("next", "16.3.7", str(tmp_path))


def test_identify_none_outside_a_project(tmp_path):
    assert identify(str(tmp_path)) is None


def test_mcp_paths():
    assert mcp_paths("next") == (NEXT_MCP,)
    assert mcp_paths("astro") == (VITE_MCP,)
    assert mcp_paths(None) == (NEXT_MCP, VITE_MCP)


def test_within(tmp_path):
    assert within(str(tmp_path / "app"), str(tmp_path))
    assert within(str(tmp_path), str(tmp_path / "app" / "src"))
    assert not within(str(tmp_path / "a"), str(tmp_path / "b"))
    assert not within(None, str(tmp_path))


LISTENER = """
import socket
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
sock.listen()
print(sock.getsockname()[1], flush=True)
input()
"""


def test_scan_reads_argv_cwd_and_listening_ports(tmp_path):
    write(tmp_path / "package.json", {"devDependencies": {"vite": "^8.0.0"}})
    write(tmp_path / "node_modules" / "vite" / "package.json", {"version": "8.3.1"})
    bin = tmp_path / "node_modules" / ".bin" / "vite"
    bin.parent.mkdir()
    bin.write_text(LISTENER)
    proc = subprocess.Popen(
        [sys.executable, str(bin)], cwd=tmp_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    try:
        port = int(proc.stdout.readline())
        [server] = [s for s in scan() if s.pid == proc.pid]
    finally:
        proc.communicate("")
    assert (server.port, server.framework, server.version, server.root) == (port, "vite", "8.3.1", str(tmp_path))
    assert server.url == f"http://localhost:{port}"


class Endpoints(BaseHTTPRequestHandler):
    """Answers like the servers a probe meets."""

    ROUTES = {
        ("POST", "/_next/mcp"): (200, "text/event-stream"),  # Next 16
        ("POST", "/stateful"): (400, "application/json"),  # needs a session: still MCP
        ("GET", "/__mcp/sse"): (200, "text/event-stream"),  # vite-plugin-mcp
        ("GET", "/spa/sse"): (200, "text/html"),  # an SPA fallback page
        ("POST", "/spa"): (200, "text/html"),
        ("POST", "/missing"): (404, "application/json"),
    }

    def answer(self, method):
        status, kind = self.ROUTES.get((method, self.path), (404, "text/html"))
        body = b"event: endpoint\ndata: /x\n\n" if kind == "text/event-stream" else b"{}"
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.answer("GET")

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.answer("POST")

    def log_message(self, *args):
        pass


@pytest.fixture
def endpoints():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Endpoints)
    server.block_on_close = False
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


@pytest.mark.parametrize(
    "path,speaks",
    [
        ("/_next/mcp", True),
        ("/stateful", True),
        ("/__mcp/sse", True),
        ("/spa/sse", False),
        ("/spa", False),
        ("/missing", False),
    ],
)
async def test_answers(endpoints, path, speaks):
    assert await answers(f"http://localhost:{endpoints}{path}") is speaks


async def test_answers_false_when_nothing_listens():
    assert await answers(f"http://localhost:{free_port()}/_next/mcp") is False


async def test_probe_finds_http_and_caches_it(endpoints):
    assert await probe(endpoints, NEXT_MCP) == f"http://localhost:{endpoints}{NEXT_MCP}"
    assert discovery._schemes[endpoints] == "http"
    assert await probe(endpoints, "/spa") is None


async def test_probe_tries_the_cached_scheme_first(monkeypatch):
    tried = []

    async def only_https(url):
        tried.append(url.split(":")[0])
        return url.startswith("https")

    monkeypatch.setattr(discovery, "answers", only_https)
    assert await probe(3000, NEXT_MCP) == f"https://localhost:3000{NEXT_MCP}"
    assert tried == ["http", "https"]
    tried.clear()
    await probe(3000, NEXT_MCP)
    assert tried == ["https"]


async def test_discover_probes_a_port_no_process_claims(monkeypatch, next_mcp):
    monkeypatch.setattr(discovery, "scan", lambda: [])
    [server] = await discover(port=next_mcp)
    assert server.mcp == f"http://localhost:{next_mcp}{NEXT_MCP}"
    assert server.url == f"http://localhost:{next_mcp}"
    assert [t["name"] for t in server.tools] == ["get_errors", "get_routes"]
    assert await discover(port=free_port()) == []
