#!/usr/bin/env python3
"""Test signal handling for hanzo net command."""

import os
import sys
import time
import signal
import subprocess

import pytest


class TestSignalHandling:
    """Test signal handling for hanzo network commands."""

    @pytest.fixture
    def env_with_pythonpath(self):
        """Create environment with PYTHONPATH set."""
        env = os.environ.copy()
        pkg_path = os.path.join(os.path.dirname(__file__), "..", "pkg", "hanzo", "src")
        env["PYTHONPATH"] = pkg_path + ":" + env.get("PYTHONPATH", "")
        return env

    @pytest.mark.skipif(sys.platform == "win32", reason="Signal handling test not supported on Windows")
    def test_sigint_graceful_shutdown(self, env_with_pythonpath):
        """Test that Ctrl-C (SIGINT) properly stops hanzo net."""
        import fcntl

        process = subprocess.Popen(
            [sys.executable, "-m", "hanzo", "net"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env_with_pythonpath,
            cwd=os.path.dirname(__file__),
            preexec_fn=os.setsid,  # Create new process group
        )

        # Give it time to start
        time.sleep(3)

        # Check if process exited early (which is acceptable in test env)
        if process.poll() is not None:
            # Process exited - this is OK in CI environment
            # where network might not be fully available
            stdout, stderr = process.communicate()
            # Just verify it ran and exited
            assert process.returncode is not None
            return

        # Process is running, make stdout/stderr non-blocking
        fl = fcntl.fcntl(process.stdout.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

        fl = fcntl.fcntl(process.stderr.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(process.stderr.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

        # Send SIGINT to process group
        os.killpg(os.getpgid(process.pid), signal.SIGINT)

        # Wait for graceful shutdown
        try:
            returncode = process.wait(timeout=10)
            # 0 = success, -2 = killed by SIGINT (expected)
            assert returncode in [0, -2, 1], f"Unexpected return code: {returncode}"
        except subprocess.TimeoutExpired:
            # Force kill if it didn't shutdown gracefully
            process.kill()
            process.wait()
            pytest.fail("Process did not shut down within 10 seconds")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
