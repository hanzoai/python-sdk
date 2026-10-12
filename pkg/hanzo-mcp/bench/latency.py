"""What an agent pays for hanzo-mcp, measured through a real MCP client over stdio.

    python bench/latency.py --out bench/latency-after.json [--runs 5] [--calls 30]

Cold start: spawn -> initialize -> tools/list, wall seconds and the server's CPU seconds (wall moves with the
machine's load, CPU does not). The tools/list payload, in bytes and estimated tokens (4 bytes a token), is
what every prompt of an agent carries. Per call: p50 / p95 milliseconds of the common tools after a warm-up.
The load average is recorded beside every number."""
import argparse, asyncio, json, os, resource, statistics, sys, tempfile, time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PAGE = """<!doctype html><title>bench</title><h1>bench</h1>
<button id=go onclick="document.getElementById('o').textContent='clicked'">Go</button>
<input id=q aria-label=query><p id=o>idle</p>"""


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def params(root):
    cwd = ARGS.cwd
    return StdioServerParameters(command=sys.executable, args=["-m", "hanzo_mcp", "--transport", "stdio", "--allow-path", "/home/z"],
                                 env={**os.environ, "HANZO_MCP_TRANSPORT": "stdio"}, cwd=cwd)


async def cold(root):
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.perf_counter()
    async with stdio_client(params(root)) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            t1 = time.perf_counter()
            tools = (await s.list_tools()).tools
            t2 = time.perf_counter()
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    blob = json.dumps([t.model_dump(exclude_none=True) for t in tools], separators=(",", ":"))
    return {"initialize_s": t1 - t0, "list_s": t2 - t1, "ready_s": t2 - t0, "cpu_s": (r1.ru_utime + r1.ru_stime) - (r0.ru_utime + r0.ru_stime),
            "tools": len(tools), "bytes": len(blob), "tokens_est": len(blob) // 4, "load": os.getloadavg()[0],
            "per_tool_bytes": {t.name: len(json.dumps(t.model_dump(exclude_none=True), separators=(",", ":"))) for t in tools}}


async def call(s, name, args):
    t = time.perf_counter()
    res = await s.call_tool(name, args)
    ms = (time.perf_counter() - t) * 1000.0
    text = "".join(getattr(c, "text", "") for c in res.content)
    return ms, bool(res.isError), text


async def warm(root, repo, calls):
    page = os.path.join(root, "page.html")
    with open(page, "w") as f:
        f.write(PAGE)
    big = os.path.join(repo, "pkg", "hanzo-mcp", "hanzo_mcp", "server.py")
    cases = [
        ("fs.read", "fs", {"action": "read", "uri": big}),
        ("fs.search_text", "fs", {"action": "search_text", "pattern": "def main", "uri": os.path.join(repo, "pkg", "hanzo-mcp", "hanzo_mcp")}),
        ("zsh.echo", "zsh", {"command": "echo hi"}),
        ("git.status", "git", {"action": "status", "cwd": repo}),
        ("playwright.snapshot", "playwright", {"action": "snapshot"}),
        ("playwright.click", "playwright", {"action": "click", "selector": "#go"}),
        ("playwright.fill", "playwright", {"action": "fill", "selector": "#q", "text": "hello"}),
    ]
    out = {}
    async with stdio_client(params(root)) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            await s.list_tools()
            nav = await call(s, "playwright", {"action": "navigate", "url": "file://" + page})
            out["playwright.navigate_first"] = {"ms": nav[0], "error": nav[1]}
            for label, tool, args in cases:
                n = calls if not label.startswith("playwright") else max(10, calls // 2)
                for _ in range(3):
                    await call(s, tool, args)
                ms, errs, last = [], 0, ""
                for _ in range(n):
                    m, e, last = await call(s, tool, args)
                    ms.append(m)
                    errs += e
                out[label] = {"p50_ms": statistics.median(ms), "p95_ms": pct(ms, 0.95), "n": n, "errors": errs, "load": os.getloadavg()[0], "sample": last[:80]}
    return out


ARGS = None


async def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--calls", type=int, default=30)
    ap.add_argument("--cwd", help="where the server starts: `python -m` imports hanzo_mcp from here first")
    ap.add_argument("--repo", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    a = ARGS = ap.parse_args()
    with tempfile.TemporaryDirectory(dir=os.path.expanduser("~/.cache")) as root:
        runs = [await cold(root) for _ in range(a.runs)]
        calls = await warm(root, a.repo, a.calls)
    ready = [r["ready_s"] for r in runs]
    summary = {"cold": {"ready_s_p50": statistics.median(ready), "ready_s_max": max(ready), "cpu_s_p50": statistics.median(r["cpu_s"] for r in runs),
                        "tools": runs[0]["tools"], "bytes": runs[0]["bytes"], "tokens_est": runs[0]["tokens_est"], "runs": runs},
               "calls": calls, "python": sys.version.split()[0]}
    with open(a.out, "w") as f:
        json.dump(summary, f, indent=1)
    c = summary["cold"]
    print("cold ready p50 %.2fs max %.2fs, cpu p50 %.2fs; tools/list %d tools %d bytes ~%d tokens" % (c["ready_s_p50"], c["ready_s_max"], c["cpu_s_p50"], c["tools"], c["bytes"], c["tokens_est"]))
    for k, v in calls.items():
        print("%-26s %s" % (k, ("p50 %.1f p95 %.1f ms (n=%d, errors %d) %s" % (v["p50_ms"], v["p95_ms"], v["n"], v["errors"], v["sample"])) if "p50_ms" in v else v))


asyncio.run(main())
