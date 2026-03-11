#!/usr/bin/env python3
"""
HIP-0300 MCP Conformance Test Suite

Tests that all MCP implementations (TypeScript, Python, Rust) expose equivalent
tool functionality. Handles the fact that TS uses unified tool names (fs, exec)
while Python currently uses legacy names (read_file, run_command) by mapping both.

Speaks raw MCP JSON-RPC 2.0 over stdio to each server process.

Usage:
    # Test all enabled implementations
    uv run python tests/conformance/run_conformance.py

    # Test specific implementation
    uv run python tests/conformance/run_conformance.py --impl python
    uv run python tests/conformance/run_conformance.py --impl typescript

    # Test specific category
    uv run python tests/conformance/run_conformance.py --cat filesystem

    # Verbose output
    uv run python tests/conformance/run_conformance.py -v
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Configuration ─────────────────────────────────────────────────────────────

HANZO_ROOT = Path(os.environ.get("HANZO_ROOT", Path.home() / "work" / "hanzo"))
TIMEOUT = 30  # seconds per request
STARTUP_TIMEOUT = 20  # seconds to wait for server ready


@dataclass
class Implementation:
    id: str
    name: str
    command: list[str]
    cwd: Path
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    startup_timeout: int = STARTUP_TIMEOUT


IMPLEMENTATIONS: list[Implementation] = [
    Implementation(
        id="python",
        name="Hanzo MCP Python",
        command=["uv", "run", "hanzo-mcp"],
        cwd=HANZO_ROOT / "python-sdk",
        env={"LOGLEVEL": "ERROR", "HANZO_MCP_LOG_LEVEL": "ERROR"},
        enabled=True,
    ),
    Implementation(
        id="typescript",
        name="Hanzo MCP TypeScript",
        command=["node", "dist/cli.js", "serve"],
        cwd=HANZO_ROOT / "mcp",
        env={"NODE_ENV": "test", "MCP_LOG_LEVEL": "error"},
        enabled=(HANZO_ROOT / "mcp" / "dist" / "cli.js").exists(),
    ),
    Implementation(
        id="rust",
        name="Hanzo MCP Rust",
        command=["cargo", "run", "--release", "--bin", "hanzo-mcp-server", "--", "serve"],
        cwd=HANZO_ROOT / "rust-sdk",
        env={"RUST_LOG": "error"},
        enabled=False,
        startup_timeout=60,
    ),
]


# ── Tool Name Mapping ─────────────────────────────────────────────────────────
# Maps (category, action) → {impl_id: (tool_name, arguments)}
# This bridges unified (TS) and legacy (Python) tool surfaces.

def resolve_tool_call(
    impl_id: str,
    tool_names: set[str],
    category: str,
    action: str,
    params: dict[str, Any],
) -> tuple[str, dict[str, Any]] | None:
    """Resolve a logical test action to the correct tool name + args for an implementation.

    Returns (tool_name, arguments) or None if the tool isn't available.
    """
    # Unified names (TS default, Python future)
    unified_map: dict[tuple[str, str], tuple[str, dict]] = {
        ("filesystem", "read"):      ("fs", {"action": "read", **params}),
        ("filesystem", "write"):     ("fs", {"action": "write", **params}),
        ("filesystem", "stat"):      ("fs", {"action": "stat", **params}),
        ("filesystem", "list"):      ("fs", {"action": "list", **params}),
        ("filesystem", "search"):    ("fs", {"action": "search_text", **params}),
        ("filesystem", "mkdir"):     ("fs", {"action": "mkdir", **params}),
        ("filesystem", "rm"):        ("fs", {"action": "rm", **params}),
        ("shell", "exec"):           ("exec", {"action": "exec", **params}),
        ("shell", "ps"):             ("exec", {"action": "ps"}),
        ("vcs", "status"):           ("git", {"action": "status", **params}),
        ("vcs", "branch"):           ("git", {"action": "branch", **params}),
        ("vcs", "log"):              ("git", {"action": "log", **params}),
        ("vcs", "diff"):             ("git", {"action": "diff", **params}),
        ("code", "symbols"):         ("code", {"action": "symbols", **params}),
        ("code", "summarize"):       ("code", {"action": "summarize", **params}),
        ("network", "fetch"):        ("fetch", {"action": "fetch", **params}),
        ("network", "head"):         ("fetch", {"action": "head", **params}),
        ("reasoning", "think"):      ("think", {"action": "think", **params}),
        ("memory", "store"):         ("memory", {"action": "store", **params}),
        ("memory", "recall"):        ("memory", {"action": "recall", **params}),
        ("memory", "list"):          ("memory", {"action": "list", **params}),
        ("memory", "forget"):        ("memory", {"action": "forget", **params}),
        ("tasks", "add"):            ("tasks", {"action": "add", **params}),
        ("tasks", "list"):           ("tasks", {"action": "list", **params}),
        ("mode", "list"):            ("mode", {"action": "list"}),
    }

    # Legacy names (Python current)
    legacy_map: dict[tuple[str, str], tuple[str, dict]] = {
        ("filesystem", "read"):      ("read_file", params),
        ("filesystem", "write"):     ("write_file", params),
        ("filesystem", "stat"):      ("get_file_info", params),
        ("filesystem", "list"):      ("list_files", params),
        ("filesystem", "search"):    ("grep", params),
        ("filesystem", "mkdir"):     ("create_file", {**params, "content": ""}),
        ("filesystem", "rm"):        ("delete_file", params),
        ("shell", "exec"):           ("run_command", params),
        ("shell", "ps"):             ("list_processes", {}),
        ("vcs", "status"):           ("run_command", {"command": "git status"}),
        ("vcs", "branch"):           ("run_command", {"command": "git branch"}),
        ("vcs", "log"):              ("run_command", {"command": f"git log --oneline -n {params.get('limit', 5)}"}),
        ("vcs", "diff"):             ("run_command", {"command": "git diff"}),
        ("reasoning", "think"):      ("critic_agent", params),
    }

    key = (category, action)

    # Try unified name first
    if key in unified_map:
        tool, args = unified_map[key]
        if tool in tool_names:
            return tool, args

    # Fall back to legacy name
    if key in legacy_map:
        tool, args = legacy_map[key]
        if tool in tool_names:
            return tool, args

    return None


# ── MCP Protocol ──────────────────────────────────────────────────────────────


class MCPClient:
    """Speaks JSON-RPC 2.0 over stdio to an MCP server process."""

    def __init__(self, impl: Implementation):
        self.impl = impl
        self.proc: asyncio.subprocess.Process | None = None
        self._id = 0

    async def start(self) -> None:
        env = {**os.environ, **self.impl.env}
        self.proc = await asyncio.create_subprocess_exec(
            *self.impl.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.impl.cwd),
            env=env,
        )
        resp = await self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "conformance-test", "version": "1.0.0"},
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

    async def list_tools(self) -> list[dict]:
        resp = await self._request("tools/list", {})
        return resp.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        return await self._request("tools/call", {"name": name, "arguments": arguments})

    async def _request(self, method: str, params: dict) -> dict:
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
            if "id" not in resp:
                continue
            if resp.get("id") == msg["id"]:
                return resp
        return {"error": {"code": -1, "message": "Timeout waiting for response"}}


# ── Test Cases ────────────────────────────────────────────────────────────────


@dataclass
class TestCase:
    category: str
    action: str
    name: str
    params: dict[str, Any]
    expect_success: bool = True
    expect_pattern: str | None = None
    expect_error_pattern: str | None = None
    setup: Any = None
    cleanup: Any = None


def build_test_cases() -> list[TestCase]:
    """Build the HIP-0300 conformance test cases."""
    tmp = Path(tempfile.mkdtemp(prefix="mcp-conformance-"))
    cases: list[TestCase] = []

    def setup_fs():
        tmp.mkdir(parents=True, exist_ok=True)

    def cleanup_fs():
        shutil.rmtree(tmp, ignore_errors=True)

    # ── Filesystem ────────────────────────────────────────────────────────
    cases.extend([
        TestCase(
            category="filesystem", action="write", name="write creates file",
            params={"path": str(tmp / "hello.txt"), "content": "Hello HIP-0300!"},
            setup=setup_fs,
        ),
        TestCase(
            category="filesystem", action="read", name="read reads file back",
            params={"path": str(tmp / "hello.txt")},
            expect_pattern="Hello HIP-0300!",
        ),
        TestCase(
            category="filesystem", action="stat", name="stat gets metadata",
            params={"path": str(tmp / "hello.txt")},
            expect_pattern="(?i)size|bytes|modified|type|permission",
        ),
        TestCase(
            category="filesystem", action="list", name="list directory",
            params={"path": str(tmp)},
            expect_pattern="hello",
        ),
        TestCase(
            category="filesystem", action="rm", name="rm removes file",
            params={"path": str(tmp / "hello.txt"), "confirm": True},
            cleanup=cleanup_fs,
        ),
    ])

    # ── Shell / Execution ─────────────────────────────────────────────────
    cases.extend([
        TestCase(
            category="shell", action="exec", name="exec echo command",
            params={"command": 'echo "HIP-0300 OK"'},
            expect_pattern="HIP-0300 OK",
        ),
        TestCase(
            category="shell", action="exec", name="exec true succeeds",
            params={"command": "true"},
        ),
        TestCase(
            category="shell", action="ps", name="ps lists processes",
            params={},
        ),
    ])

    # ── Version Control ───────────────────────────────────────────────────
    cases.extend([
        TestCase(
            category="vcs", action="status", name="git status",
            params={},
        ),
        TestCase(
            category="vcs", action="branch", name="git branch lists branches",
            params={},
            expect_pattern="(?i)main|master|\\*",
        ),
        TestCase(
            category="vcs", action="log", name="git log shows history",
            params={"limit": 3},
        ),
    ])

    # ── Reasoning ─────────────────────────────────────────────────────────
    cases.append(
        TestCase(
            category="reasoning", action="think", name="think accepts thought",
            params={"action": "think", "thought": "Testing conformance across implementations."},
        ),
    )

    return cases


# ── Runner ────────────────────────────────────────────────────────────────────


@dataclass
class TestResult:
    impl: str
    category: str
    action: str
    name: str
    passed: bool
    duration_ms: float
    tool_used: str = ""
    error: str = ""
    skipped: bool = False


def extract_text(resp: dict) -> str:
    """Extract all text content from an MCP response."""
    result = resp.get("result", {})
    content = result.get("content", [])
    if isinstance(content, list):
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return " ".join(texts)
    if isinstance(result, str):
        return result
    return json.dumps(result)


def is_error_response(resp: dict) -> bool:
    """Check if response indicates an error."""
    if "error" in resp:
        return True
    result = resp.get("result", {})
    if isinstance(result, dict) and result.get("isError"):
        return True
    return False


async def run_tests(
    impls: list[Implementation],
    cases: list[TestCase],
    categories_filter: list[str] | None = None,
    verbose: bool = False,
) -> list[TestResult]:
    """Run conformance tests against all implementations."""
    results: list[TestResult] = []

    for impl in impls:
        if not impl.enabled:
            continue

        print(f"\n{'='*60}")
        print(f"  {impl.name} ({impl.id})")
        print(f"{'='*60}")

        client = MCPClient(impl)
        try:
            print(f"  Starting server...", end=" ", flush=True)
            await asyncio.wait_for(client.start(), timeout=impl.startup_timeout)
            print("OK")

            tools = await client.list_tools()
            tool_names = set(t["name"] for t in tools)
            print(f"  Tools registered: {len(tools)}")

            if verbose:
                for tn in sorted(tool_names):
                    print(f"    - {tn}")

            for tc in cases:
                if categories_filter and tc.category not in categories_filter:
                    continue

                resolved = resolve_tool_call(impl.id, tool_names, tc.category, tc.action, tc.params)
                if resolved is None:
                    print(f"  SKIP {tc.name} (no matching tool for {tc.category}.{tc.action})")
                    results.append(TestResult(
                        impl=impl.id, category=tc.category, action=tc.action,
                        name=tc.name, passed=False, duration_ms=0,
                        error=f"No tool for {tc.category}.{tc.action}", skipped=True,
                    ))
                    continue

                tool_name, arguments = resolved

                if tc.setup:
                    tc.setup()

                t0 = time.monotonic()
                try:
                    resp = await asyncio.wait_for(
                        client.call_tool(tool_name, arguments),
                        timeout=TIMEOUT,
                    )
                    duration = (time.monotonic() - t0) * 1000

                    is_err = is_error_response(resp)
                    text = extract_text(resp)
                    passed = True
                    error = ""

                    if tc.expect_success and is_err:
                        passed = False
                        err_msg = resp.get("error", {}).get("message", text)
                        error = f"Expected success, got error: {err_msg[:200]}"
                    elif not tc.expect_success and not is_err:
                        passed = False
                        error = f"Expected error, got success: {text[:100]}"

                    if passed and tc.expect_pattern:
                        if not re.search(tc.expect_pattern, text, re.IGNORECASE):
                            passed = False
                            error = f"Pattern /{tc.expect_pattern}/ not found in: {text[:200]}"

                    if passed and not tc.expect_success and tc.expect_error_pattern:
                        err_text = resp.get("error", {}).get("message", text)
                        if not re.search(tc.expect_error_pattern, err_text, re.IGNORECASE):
                            passed = False
                            error = f"Error pattern /{tc.expect_error_pattern}/ not found"

                    status = "PASS" if passed else "FAIL"
                    print(f"  {status} {tc.name} [{tool_name}] ({duration:.0f}ms)")
                    if not passed:
                        print(f"       {error}")
                    elif verbose:
                        print(f"       -> {text[:120]}")

                    results.append(TestResult(
                        impl=impl.id, category=tc.category, action=tc.action,
                        name=tc.name, passed=passed, duration_ms=duration,
                        tool_used=tool_name, error=error,
                    ))

                except asyncio.TimeoutError:
                    duration = (time.monotonic() - t0) * 1000
                    print(f"  FAIL {tc.name} [{tool_name}] (TIMEOUT {duration:.0f}ms)")
                    results.append(TestResult(
                        impl=impl.id, category=tc.category, action=tc.action,
                        name=tc.name, passed=False, duration_ms=duration,
                        tool_used=tool_name, error="Timeout",
                    ))
                except Exception as e:
                    duration = (time.monotonic() - t0) * 1000
                    print(f"  FAIL {tc.name} [{tool_name}] ({e})")
                    results.append(TestResult(
                        impl=impl.id, category=tc.category, action=tc.action,
                        name=tc.name, passed=False, duration_ms=duration,
                        tool_used=tool_name, error=str(e),
                    ))
                finally:
                    if tc.cleanup:
                        try:
                            tc.cleanup()
                        except Exception:
                            pass

        except Exception as e:
            print(f"FAILED to start: {e}")
            for tc in cases:
                if categories_filter and tc.category not in categories_filter:
                    continue
                results.append(TestResult(
                    impl=impl.id, category=tc.category, action=tc.action,
                    name=tc.name, passed=False, duration_ms=0,
                    error=f"Server start failed: {e}",
                ))
        finally:
            await client.stop()

    return results


def print_summary(results: list[TestResult]) -> None:
    """Print a summary table of results."""
    if not results:
        print("\nNo results.")
        return

    impls = sorted(set(r.impl for r in results))
    categories = sorted(set(r.category for r in results))

    print(f"\n{'='*70}")
    print("  HIP-0300 CONFORMANCE SUMMARY")
    print(f"{'='*70}\n")

    # Per-implementation breakdown
    for impl in impls:
        ir = [r for r in results if r.impl == impl and not r.skipped]
        passed = sum(1 for r in ir if r.passed)
        total = len(ir)
        skipped = sum(1 for r in results if r.impl == impl and r.skipped)
        pct = (passed / total * 100) if total else 0
        status = "PASS" if passed == total else "FAIL"
        print(f"  {impl:20s}  {passed}/{total} ({pct:.0f}%) [{status}]  ({skipped} skipped)")

        for cat in categories:
            cr = [r for r in ir if r.category == cat]
            if not cr:
                continue
            cp = sum(1 for r in cr if r.passed)
            ct = len(cr)
            marker = "+" if cp == ct else "X"
            # Show which tool names were used
            tool_names = sorted(set(r.tool_used for r in cr if r.tool_used))
            tools_str = ", ".join(tool_names) if tool_names else "?"
            print(f"    [{marker}] {cat:15s}  {cp}/{ct}  via: {tools_str}")

    # Cross-implementation parity
    if len(impls) > 1:
        print(f"\n  CROSS-IMPLEMENTATION PARITY:")
        for cat in categories:
            impl_status = {}
            for impl in impls:
                cr = [r for r in results if r.impl == impl and r.category == cat and not r.skipped]
                if cr:
                    impl_status[impl] = all(r.passed for r in cr)

            if len(impl_status) < 2:
                continue

            values = list(impl_status.values())
            if all(values):
                print(f"    {cat:15s}  PARITY OK")
            elif any(values):
                passing = [k for k, v in impl_status.items() if v]
                failing = [k for k, v in impl_status.items() if not v]
                print(f"    {cat:15s}  MISMATCH  pass={passing}  fail={failing}")
            else:
                print(f"    {cat:15s}  ALL FAIL")

    print()


async def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="HIP-0300 MCP Conformance Tests")
    parser.add_argument("--impl", "-i", action="append", help="Implementation ID(s)")
    parser.add_argument("--cat", "-c", action="append", help="Category filter")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--list", action="store_true", help="List implementations")
    args = parser.parse_args()

    if args.list:
        for impl in IMPLEMENTATIONS:
            status = "enabled" if impl.enabled else "disabled"
            exists = impl.cwd.exists()
            print(f"  {impl.id:15s}  {impl.name:30s}  [{status}]  {'exists' if exists else 'MISSING'}")
        return 0

    impls = IMPLEMENTATIONS
    if args.impl:
        impls = [i for i in impls if i.id in args.impl]
        for i in impls:
            i.enabled = True

    cases = build_test_cases()
    enabled = [i.id for i in impls if i.enabled]
    print(f"HIP-0300 Conformance Suite: {len(cases)} test cases")
    print(f"Implementations: {', '.join(enabled)}")

    results = await run_tests(impls, cases, categories_filter=args.cat, verbose=args.verbose)
    print_summary(results)

    non_skipped = [r for r in results if not r.skipped]
    if all(r.passed for r in non_skipped):
        print("ALL TESTS PASSED")
        return 0
    else:
        failed = sum(1 for r in non_skipped if not r.passed)
        print(f"{failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
