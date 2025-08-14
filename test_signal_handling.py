#!/usr/bin/env python3
"""Test signal handling for hanzo net command."""

import subprocess
import time
import signal
import sys

def test_signal_handling():
    """Test that Ctrl-C properly stops hanzo net."""
    print("Testing signal handling for 'hanzo net'...")
    print("Starting hanzo net process...")
    
    # Start hanzo net using the local module
    import os
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), 'pkg/hanzo/src') + ':' + env.get('PYTHONPATH', '')
    
    process = subprocess.Popen(
        [sys.executable, "-m", "hanzo", "net"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=os.path.dirname(__file__),
        preexec_fn=os.setsid  # Create new process group
    )
    
    # Give it time to start
    time.sleep(3)
    
    if process.poll() is not None:
        print(f"❌ Process exited early with code: {process.returncode}")
        stdout, stderr = process.communicate()
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        return False
    
    print("Process is running, checking output...")
    # Read any initial output without blocking
    import select
    import fcntl
    import os as os2
    
    # Make stdout non-blocking
    fl = fcntl.fcntl(process.stdout.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, fl | os2.O_NONBLOCK)
    
    # Try to read initial output
    try:
        initial_output = process.stdout.read()
        if initial_output:
            print(f"Initial stdout: {initial_output[:500]}")
    except:
        pass
    
    # Make stderr non-blocking too
    fl = fcntl.fcntl(process.stderr.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(process.stderr.fileno(), fcntl.F_SETFL, fl | os2.O_NONBLOCK)
    
    try:
        initial_stderr = process.stderr.read()
        if initial_stderr:
            print(f"Initial stderr: {initial_stderr[:500]}")
    except:
        pass
    
    print("Sending SIGINT (Ctrl-C) to process group...")
    # Send signal to the entire process group
    os.killpg(os.getpgid(process.pid), signal.SIGINT)
    
    # Wait for graceful shutdown (up to 10 seconds)
    try:
        returncode = process.wait(timeout=10)
        if returncode == 0 or returncode == -2:
            print("✅ Process shut down gracefully!")
            return True
        else:
            print(f"⚠️ Process exited with code: {returncode}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Process did not shut down within 10 seconds")
        print("Force killing...")
        process.kill()
        process.wait()
        return False

if __name__ == "__main__":
    success = test_signal_handling()
    sys.exit(0 if success else 1)