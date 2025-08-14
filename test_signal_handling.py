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
    
    # Start hanzo net
    process = subprocess.Popen(
        [sys.executable, "-m", "hanzo", "net"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    time.sleep(3)
    
    if process.poll() is not None:
        print(f"❌ Process exited early with code: {process.returncode}")
        stdout, stderr = process.communicate()
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        return False
    
    print("Sending SIGINT (Ctrl-C) to process...")
    process.send_signal(signal.SIGINT)
    
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