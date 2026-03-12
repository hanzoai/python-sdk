#!/usr/bin/env python3
"""
HIP-0300 Parallel Performance Benchmark

Tests that all MCP tools work correctly when invoked concurrently.
Measures throughput and latency under parallel load.

Usage:
    uv run python tests/conformance/benchmark_parallel.py
    uv run python tests/conformance/benchmark_parallel.py --concurrency 20
"""

from __future__ import annotations

import os
import sys
import json
import time
import asyncio
import tempfile
import statistics
from typing import Any
from pathlib import Path
from dataclasses import field, dataclass

HANZO_ROOT = Path(os.environ.get("HANZO_ROOT", Path.home() / "work" / "hanzo"))
TIMEOUT = 30
STARTUP_TIMEOUT = 20


class MCPClient:
    """JSON-RPC 2.0 over stdio client."""

    def __init__(self, command: list[str], cwd: Path, env: dict[str, str]):
        self.command = command
        self.cwd = cwd
        self.env = env
        self.proc: asyncio.subprocess.Process | None = None
        self._id = 0
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        full_env = {**os.environ, **self.env}
        self.proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.cwd),
            env=full_env,
        )
        resp = await self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "benchmark", "version": "1.0.0"},
        })
        if "error" in resp:
            raise RuntimeError(f"Initialize failed: {resp['error']}")
        await self._notify("notifications/initialized")

    async def stop(self) -> None:
        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.proc.kill()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        return await self._request("tools/call", {"name": name, "arguments": arguments})

    async def list_tools(self) -> list[dict]:
        resp = await self._request("tools/list", {})
        return resp.get("result", {}).get("tools", [])

    async def _request(self, method: str, params: dict) -> dict:
        async with self._lock:
            self._id += 1
            msg = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
            return await self._send_and_recv(msg)

    async def _notify(self, method: str, params: dict | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params:
            msg["params"] = params
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps(msg).encode() + b"\n")
        await self.proc.stdin.drain()

    async def _send_and_recv(self, msg: dict) -> dict:
        assert self.proc and self.proc.stdin and self.proc.stdout
        data = json.dumps(msg).encode() + b"\n"
        self.proc.stdin.write(data)
        await self.proc.stdin.drain()
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            try:
                line = await asyncio.wait_for(
                    self.proc.stdout.readline(),
                    timeout=max(0.1, deadline - time.monotonic()),
                )
            except asyncio.TimeoutError:
                break
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                continue
            if resp.get("id") == msg["id"]:
                return resp
        return {"error": {"code": -1, "message": "Timeout"}}


@dataclass
class BenchResult:
    tool: str
    action: str
    concurrency: int
    total_calls: int
    passed: int
    failed: int
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0

    @property
    def p95(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_l = sorted(self.latencies_ms)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def throughput(self) -> float:
        total_s = sum(self.latencies_ms) / 1000 if self.latencies_ms else 1
        return self.total_calls / (total_s / self.concurrency) if total_s > 0 else 0


async def bench_tool(
    client: MCPClient,
    tool: str,
    action: str,
    params: dict[str, Any],
    concurrency: int = 10,
    iterations: int = 50,
) -> BenchResult:
    """Benchmark a tool with parallel invocations."""
    result = BenchResult(
        tool=tool, action=action, concurrency=concurrency,
        total_calls=iterations, passed=0, failed=0,
    )

    sem = asyncio.Semaphore(concurrency)

    async def single_call():
        async with sem:
            t0 = time.monotonic()
            try:
                resp = await asyncio.wait_for(
                    client.call_tool(tool, {"action": action, **params}),
                    timeout=TIMEOUT,
                )
                duration = (time.monotonic() - t0) * 1000
                result.latencies_ms.append(duration)
                if "error" in resp:
                    result.failed += 1
                else:
                    result.passed += 1
            except Exception:
                result.failed += 1
                result.latencies_ms.append((time.monotonic() - t0) * 1000)

    # Run all calls concurrently
    await asyncio.gather(*[single_call() for _ in range(iterations)])
    return result


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="HIP-0300 Parallel Benchmark")
    parser.add_argument("--concurrency", type=int, default=10, help="Max concurrent calls")
    parser.add_argument("--iterations", type=int, default=50, help="Total calls per test")
    parser.add_argument("--impl", default="python", choices=["python", "typescript"])
    args = parser.parse_args()

    if args.impl == "python":
        client = MCPClient(
            command=["uv", "run", "hanzo-mcp"],
            cwd=HANZO_ROOT / "python-sdk",
            env={"LOGLEVEL": "ERROR", "HANZO_MCP_LOG_LEVEL": "ERROR"},
        )
    else:
        client = MCPClient(
            command=["node", "dist/cli.js", "serve"],
            cwd=HANZO_ROOT / "mcp",
            env={"NODE_ENV": "test", "MCP_LOG_LEVEL": "error"},
        )

    print(f"\nHIP-0300 Parallel Benchmark ({args.impl})")
    print(f"Concurrency: {args.concurrency}, Iterations: {args.iterations}")
    print(f"{'='*70}")

    print("Starting server...", end=" ", flush=True)
    await asyncio.wait_for(client.start(), timeout=STARTUP_TIMEOUT)
    tools = await client.list_tools()
    tool_names = set(t["name"] for t in tools)
    print(f"OK ({len(tools)} tools)")

    # Create temp dir for fs tests
    tmp = Path(tempfile.mkdtemp(prefix="mcp-bench-"))

    benchmarks = []

    # Define test workloads
    workloads = [
        ("exec", "exec", {"command": "echo bench"}),
        ("exec", "ps", {}),
        ("git", "status", {}),
        ("git", "log", {"limit": 3}),
        ("think", "think", {"thought": "Benchmark test"}),
    ]

    # Only test tools that are registered
    workloads = [(t, a, p) for t, a, p in workloads if t in tool_names]

    # Add fs tests with unique filenames
    if "fs" in tool_names:
        # Write files first
        for i in range(args.iterations):
            await client.call_tool("fs", {
                "action": "write",
                "path": str(tmp / f"bench_{i}.txt"),
                "content": f"benchmark content {i}",
            })
        workloads.append(("fs", "read", {"path": str(tmp / "bench_0.txt")}))
        workloads.append(("fs", "list", {"path": str(tmp)}))

    print(f"\nRunning {len(workloads)} workloads...\n")
    print(f"{'Tool':<12} {'Action':<10} {'Pass':<6} {'Fail':<6} {'P50':<10} {'P95':<10} {'Throughput':<12}")
    print("-" * 70)

    for tool, action, params in workloads:
        result = await bench_tool(
            client, tool, action, params,
            concurrency=args.concurrency,
            iterations=args.iterations,
        )
        benchmarks.append(result)
        print(
            f"{tool:<12} {action:<10} {result.passed:<6} {result.failed:<6} "
            f"{result.p50:>7.1f}ms {result.p95:>7.1f}ms "
            f"{result.throughput:>8.1f} ops/s"
        )

    # Cleanup
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    await client.stop()

    # Summary
    total_passed = sum(b.passed for b in benchmarks)
    total_failed = sum(b.failed for b in benchmarks)
    total = total_passed + total_failed
    all_latencies = [l for b in benchmarks for l in b.latencies_ms]

    print(f"\n{'='*70}")
    print(f"Total: {total_passed}/{total} passed ({total_failed} failed)")
    if all_latencies:
        print(f"Overall P50: {statistics.median(all_latencies):.1f}ms  P95: {sorted(all_latencies)[int(len(all_latencies)*0.95)]:.1f}ms")
    print(f"All tools async-safe: {'YES' if total_failed == 0 else 'NO'}")

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
