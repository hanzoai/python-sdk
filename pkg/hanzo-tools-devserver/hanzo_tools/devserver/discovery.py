"""Dev servers running on this machine, as plain records.

``discover()`` is the seam: each ``DevServer`` is one addressable node — a
framework's dev server and, where it serves one, its MCP endpoint and tools.
Identification reads three facts per process: its argv (which binary runs),
its cwd (the nearest package.json names the framework), and its listening
ports. Each port is then probed at the framework's MCP path.
"""

import json
import asyncio
from pathlib import Path
from dataclasses import field, dataclass

import httpx
import psutil

from hanzo_tools.mcp_tools.mcp_proxy import MCPServerConfig, MCPServerConnection

# The npm package that names each framework, most specific first: all but Next
# run on Vite, so a bare `vite` dependency is the last word, not the first.
FRAMEWORKS = (
    ("next", "next"),
    ("nuxt", "nuxt"),
    ("react-router", "@react-router/dev"),
    ("remix", "@remix-run/dev"),
    ("astro", "astro"),
    ("sveltekit", "@sveltejs/kit"),
    ("vite", "vite"),
)

# Binary a dev server runs as -> framework. Next renames its server process
# to "next-server (vX.Y.Z)"; the rest are the basename of a node_modules bin.
BINARIES = {
    "next": "next",
    "next-server": "next",
    "vite": "vite",
    "nuxi": "nuxt",
    "nuxt": "nuxt",
    "remix": "remix",
    "react-router": "react-router",
    "astro": "astro",
}

# Next 16 serves streamable HTTP MCP at /_next/mcp by default. The Vite family
# has none built in; vite-plugin-mcp (and nuxt-mcp-dev, which wraps it) serves
# SSE at /__mcp/sse.
NEXT_MCP = "/_next/mcp"
VITE_MCP = "/__mcp/sse"

PROBE_TIMEOUT = 1.0

# The scheme each port last answered on, tried first on the next probe.
_schemes: dict[int, str] = {}


@dataclass
class DevServer:
    """One dev server: where it listens, what it is, and the MCP it serves."""

    port: int
    url: str = ""
    pid: int | None = None
    framework: str | None = None
    version: str | None = None
    root: str | None = None
    command: str | None = None
    mcp: str | None = None
    tools: list[dict] = field(default_factory=list)
    error: str | None = None


def binary(argv: list[str]) -> str | None:
    """The framework whose dev binary this argv runs, or None."""
    for arg in argv[:3]:
        name = arg.replace("\\", "/")
        if name.startswith("next-server"):
            return "next"
        base = name.rsplit("/", 1)[-1].split(".")[0]
        if base in BINARIES:
            return BINARIES[base]
    return None


def installed(root: Path, package: str) -> str | None:
    """The version of `package` that node resolves from `root`."""
    for d in (root, *root.parents):
        try:
            return json.loads((d / "node_modules" / package / "package.json").read_text())["version"]
        except (OSError, ValueError, KeyError):
            continue
    return None


def identify(cwd: str) -> tuple[str, str, str] | None:
    """(framework, version, root) from the nearest package.json that depends on one."""
    start = Path(cwd)
    for d in (start, *start.parents):
        try:
            manifest = json.loads((d / "package.json").read_text())
        except (OSError, ValueError):
            continue
        deps = {**manifest.get("devDependencies", {}), **manifest.get("dependencies", {})}
        for framework, package in FRAMEWORKS:
            if package in deps:
                return framework, installed(d, package) or deps[package], str(d)
    return None


def scan() -> list[DevServer]:
    """Listening processes that run a dev-server binary, one record per port."""
    found = []
    for proc in psutil.process_iter(["pid", "cmdline", "cwd"]):
        argv = proc.info["cmdline"] or []
        framework = binary(argv)
        if framework is None:
            continue
        try:
            ports = sorted({c.laddr.port for c in proc.net_connections("tcp") if c.status == psutil.CONN_LISTEN})
        except psutil.Error:
            continue
        version = root = None
        project = identify(proc.info["cwd"]) if proc.info["cwd"] else None
        if project:
            framework, version, root = project
        command = " ".join(argv).strip()
        for port in ports:
            found.append(
                DevServer(
                    port=port,
                    url=f"http://localhost:{port}",
                    pid=proc.pid,
                    framework=framework,
                    version=version,
                    root=root,
                    command=command,
                )
            )
    return found


async def answers(url: str) -> bool:
    """Whether `url` speaks MCP. SSE answers a GET with an event stream;
    streamable HTTP answers a POSTed tools/list with JSON or an event stream,
    even a stateful server's 400 for the missing session."""
    # A probe only ever addresses localhost, where a dev server's certificate is self-signed.
    async with httpx.AsyncClient(verify=False, timeout=PROBE_TIMEOUT) as client:  # noqa: S501
        if url.endswith("/sse"):
            request = client.build_request("GET", url, headers={"Accept": "text/event-stream"})
        else:
            request = client.build_request(
                "POST",
                url,
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                headers={"Accept": "application/json, text/event-stream"},
            )
        try:
            response = await client.send(request, stream=True)
        except httpx.HTTPError:
            return False
        await response.aclose()
    kind = response.headers.get("content-type", "")
    return response.status_code != 404 and kind.startswith(("text/event-stream", "application/json"))


async def probe(port: int, path: str) -> str | None:
    """The MCP endpoint at localhost:`port``path`, over http or https, or None."""
    first = _schemes.get(port, "http")
    for scheme in (first, "https" if first == "http" else "http"):
        url = f"{scheme}://localhost:{port}{path}"
        if await answers(url):
            _schemes[port] = scheme
            return url
    return None


def mcp_paths(framework: str | None) -> tuple[str, ...]:
    """Where a framework's dev server would serve MCP; both when it is unknown."""
    if framework == "next":
        return (NEXT_MCP,)
    if framework is None:
        return (NEXT_MCP, VITE_MCP)
    return (VITE_MCP,)


async def attach(server: DevServer) -> None:
    """Find the server's MCP endpoint and list its tools."""
    for path in mcp_paths(server.framework):
        url = await probe(server.port, path)
        if url is None:
            continue
        server.url = url.removesuffix(path)
        server.mcp = url
        connection = MCPServerConnection(MCPServerConfig(name=f"{server.framework}:{server.port}", url=url))
        if await connection.connect():
            server.tools = [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in connection.tools
            ]
        else:
            server.error = connection.error
        return


def within(root: str | None, cwd: str) -> bool:
    """Whether a project root and a working directory contain one another."""
    if root is None:
        return False
    a, b = Path(root).resolve(), Path(cwd).expanduser().resolve()
    return a.is_relative_to(b) or b.is_relative_to(a)


async def discover(port: int | None = None, cwd: str | None = None) -> list[DevServer]:
    """Dev servers on this machine, narrowed to `port` and to projects around `cwd`,
    each probed for MCP. A `port` no process scan claims is probed as given and
    kept when an MCP endpoint answers there."""
    servers = [s for s in scan() if (port is None or s.port == port) and (cwd is None or within(s.root, cwd))]
    if port is not None and not servers:
        bare = DevServer(port=port, url=f"http://localhost:{port}")
        await attach(bare)
        return [bare] if bare.mcp else []
    await asyncio.gather(*(attach(s) for s in servers))
    return servers
