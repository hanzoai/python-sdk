#!/usr/bin/env python
"""Simple test to check if stdio mode starts without logging interference."""

import sys
import json
import time
import subprocess


def test_stdio_simple():
    """Test stdio mode for logging interference."""
    # Start the server
    proc = subprocess.Popen(
        [sys.executable, "-m", "hanzo_mcp.cli", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
    )

    # Send initialize request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    print("Sending initialize request...")
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read response for 5 seconds
    start_time = time.time()
    output_lines = []
    error_lines = []

    while time.time() - start_time < 5:
        # Check for stdout
        try:
            proc.stdout.flush()
            line = proc.stdout.readline()
            if line:
                output_lines.append(line.strip())
        except Exception:
            pass

        # Check for stderr
        try:
            proc.stderr.flush()
            line = proc.stderr.readline()
            if line:
                error_lines.append(line.strip())
        except Exception:
            pass

        time.sleep(0.1)

    # Kill the process
    proc.terminate()
    proc.wait()

    # Analyze results
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Total stdout lines: {len(output_lines)}")
    print(f"Total stderr lines: {len(error_lines)}")

    # Check each stdout line for valid JSON
    violations = 0
    for i, line in enumerate(output_lines):
        try:
            data = json.loads(line)
            print(f"✓ Valid JSON response: {data.get('method', data.get('result', 'response'))}")
        except json.JSONDecodeError:
            print(f"✗ Line {i + 1} is not valid JSON: {line}")
            violations += 1

    # Show stderr if any
    if error_lines:
        print("\nSTDERR OUTPUT:")
        for line in error_lines:
            print(f"  {line}")

    if violations == 0 and output_lines:
        print("✅ All stdout output is valid JSON!")
    else:
        print(f"❌ Found {violations} protocol violations")

    return violations == 0


if __name__ == "__main__":
    success = test_stdio_simple()
    sys.exit(0 if success else 1)
