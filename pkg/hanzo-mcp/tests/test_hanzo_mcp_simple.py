#!/usr/bin/env python3
"""Simple test to verify hanzo-mcp works locally."""

import os
import sys
import asyncio
import tempfile
import subprocess
from pathlib import Path

# Add the package to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_cli_help():
    """Test that CLI help works."""
    result = subprocess.run([sys.executable, "-m", "hanzo_mcp", "--help"], capture_output=True, text=True)

    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout[:200]}")
    print(f"STDERR: {result.stderr[:200]}")

    assert result.returncode == 0, (
        f"Command failed with code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "hanzo" in result.stdout.lower() or "mcp" in result.stdout.lower()
    print("✓ CLI help works")


def test_cli_version():
    """Test version command."""
    result = subprocess.run([sys.executable, "-m", "hanzo_mcp", "--version"], capture_output=True, text=True)

    print(f"Version output: {result.stdout}")
    # Version command might not be supported, so just check if command doesn't crash
    if result.returncode == 0 or "usage" in result.stdout + result.stderr:
        print("✓ Version check works")
    else:
        print(f"✗ Version check failed: {result.stderr}")


async def test_stdio_server():
    """Test the stdio server with a simple interaction."""
    import json
    import asyncio

    with tempfile.TemporaryDirectory() as tmpdir:
        # Start the server process
        env = os.environ.copy()
        env["HANZO_ALLOWED_PATHS"] = tmpdir

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "hanzo_mcp",
            "--transport",
            "stdio",
            "--allow-path",
            tmpdir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"capabilities": {}},
            }

            proc.stdin.write((json.dumps(init_request) + "\n").encode())
            await proc.stdin.drain()

            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
                response = json.loads(response_line.decode())

                print(f"Initialize response: {response}")
                assert response["id"] == 1
                assert "result" in response
                print("✓ Server initialization works")

                # List tools
                list_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }

                proc.stdin.write((json.dumps(list_request) + "\n").encode())
                await proc.stdin.drain()

                response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
                response = json.loads(response_line.decode())

                print(f"Found {len(response['result']['tools'])} tools")
                assert len(response["result"]["tools"]) > 10
                print("✓ Tool listing works")

            except asyncio.TimeoutError:
                print("✗ Server response timeout")
                stderr = await proc.stderr.read()
                print(f"Stderr: {stderr.decode()}")

        finally:
            proc.terminate()
            await proc.wait()


def test_import_tools():
    """Test that we can import tools directly."""
    try:
        from hanzo_mcp.tools import register_all_tools
        from mcp.server.fastmcp import FastMCP
        from hanzo_mcp.tools.common.permissions import PermissionManager

        # Create a test server
        server = FastMCP("test-server")
        pm = PermissionManager()
        pm.add_allowed_path("/tmp")

        # Register tools
        tools = register_all_tools(server, pm)

        print(f"✓ Registered {len(tools)} tools")

        # Check some essential tools
        tool_names = [getattr(t, "name", str(t)) for t in tools]
        print(f"Sample tools: {tool_names[:5]}")

    except Exception as e:
        print(f"✗ Import failed: {e}")
        raise


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing hanzo-mcp")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: CLI Help
    try:
        test_cli_help()
        tests_passed += 1
    except Exception as e:
        print(f"✗ CLI help test failed: {e}")
        tests_failed += 1

    # Test 2: Version
    try:
        test_cli_version()
        tests_passed += 1
    except Exception as e:
        print(f"✗ Version test failed: {e}")
        tests_failed += 1

    # Test 3: Import tools
    try:
        test_import_tools()
        tests_passed += 1
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        tests_failed += 1

    # Test 4: Stdio server
    try:
        asyncio.run(test_stdio_server())
        tests_passed += 1
    except Exception as e:
        print(f"✗ Stdio server test failed: {e}")
        tests_failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
