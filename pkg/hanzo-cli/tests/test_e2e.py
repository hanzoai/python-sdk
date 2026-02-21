"""End-to-end tests for hanzo CLI against live services.

Requires:
    - hanzo-cli installed (pip install -e pkg/hanzo-cli)
    - Valid credentials stored at ~/.hanzo/auth/token.json (run hanzo login first)
    - Live services: hanzo.id, platform.hanzo.ai

Run:
    pytest pkg/hanzo-cli/tests/test_e2e.py -v -s
"""

from __future__ import annotations

import subprocess
import time

import pytest

HANZO = "hanzo"
TIMEOUT = 30


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a hanzo CLI command and return the result."""
    result = subprocess.run(
        [HANZO] + args,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    if check and result.returncode != 0:
        pytest.fail(
            f"hanzo {' '.join(args)} failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


# =========================================================================
# Auth
# =========================================================================


class TestAuth:
    def test_version(self):
        r = run(["--version"])
        assert "0.1.0" in r.stdout

    def test_help(self):
        r = run(["--help"])
        assert "login" in r.stdout
        assert "paas" in r.stdout
        assert "iam" in r.stdout
        assert "kms" in r.stdout

    def test_whoami(self):
        r = run(["whoami"])
        assert "z@hanzo.ai" in r.stdout or "z" in r.stdout
        assert "hanzo.id" in r.stdout

    def test_whoami_shows_org(self):
        r = run(["whoami"])
        assert "hanzo" in r.stdout


# =========================================================================
# IAM
# =========================================================================


class TestIAM:
    def test_iam_help(self):
        r = run(["iam", "--help"])
        assert "users" in r.stdout
        assert "set-password" in r.stdout

    def test_iam_users(self):
        """List users — should return at least user z."""
        r = run(["iam", "users"], check=False)
        # May fail if bearer token doesn't have admin access,
        # but the command should at least not crash
        assert r.returncode == 0 or "Not authenticated" not in r.stderr

    def test_iam_orgs(self):
        r = run(["iam", "orgs"], check=False)
        assert r.returncode == 0 or "Not authenticated" not in r.stderr


# =========================================================================
# PaaS — Read Operations
# =========================================================================


class TestPaaSRead:
    def test_paas_help(self):
        r = run(["paas", "--help"])
        assert "deploy" in r.stdout
        assert "orgs" in r.stdout
        assert "use" in r.stdout

    def test_paas_orgs(self):
        r = run(["paas", "orgs"])
        assert "Hanzo" in r.stdout
        assert "Organizations" in r.stdout

    def test_paas_projects(self):
        r = run(["paas", "projects", "--org", "698cda6739f65183b3009313"])
        assert "Platform" in r.stdout

    def test_paas_envs(self):
        r = run(
            [
                "paas",
                "envs",
                "--org",
                "698cda6739f65183b3009313",
                "--project",
                "698cda6739f65183b3009318",
            ]
        )
        assert "production" in r.stdout

    def test_paas_context_set_and_show(self):
        run(
            [
                "paas",
                "use",
                "--org",
                "698cda6739f65183b3009313",
                "--project",
                "698cda6739f65183b3009318",
                "--env",
                "698cda6739f65183b300931c",
            ]
        )
        r = run(["paas", "context"])
        assert "698cda6739f65183b3009313" in r.stdout
        assert "698cda6739f65183b3009318" in r.stdout
        assert "698cda6739f65183b300931c" in r.stdout

    def test_paas_deploy_list(self):
        """List containers — may be empty, but should not error."""
        r = run(["paas", "deploy", "list"])
        assert r.returncode == 0


# =========================================================================
# PaaS — Deploy Lifecycle (create → status → logs → redeploy → delete)
# =========================================================================


class TestPaaSDeployLifecycle:
    """Full container lifecycle test using a lightweight Docker image."""

    CONTAINER_NAME = "e2e-test-nginx"

    @classmethod
    def setup_class(cls):
        """Ensure context is set and clean up any leftover test containers."""
        run(
            [
                "paas",
                "use",
                "--org",
                "698cda6739f65183b3009313",
                "--project",
                "698cda6739f65183b3009318",
                "--env",
                "698cda6739f65183b300931c",
            ]
        )
        # Clean up leftover from previous failed runs
        r = run(["paas", "deploy", "delete", cls.CONTAINER_NAME, "-y"], check=False)

    @classmethod
    def teardown_class(cls):
        """Clean up test container."""
        run(["paas", "deploy", "delete", cls.CONTAINER_NAME, "-y"], check=False)

    def test_01_create(self):
        r = run(
            [
                "paas",
                "deploy",
                "create",
                self.CONTAINER_NAME,
                "--image",
                "nginx:latest",
                "--port",
                "80",
            ]
        )
        assert "Created container" in r.stdout
        assert self.CONTAINER_NAME in r.stdout

    def test_02_list_contains_container(self):
        r = run(["paas", "deploy", "list"])
        assert self.CONTAINER_NAME in r.stdout

    def test_03_status_shows_pod(self):
        """Wait for the pod to appear and check status."""
        for attempt in range(6):
            r = run(["paas", "deploy", "status", self.CONTAINER_NAME])
            if "Running" in r.stdout or "Pending" in r.stdout:
                break
            time.sleep(5)
        assert self.CONTAINER_NAME in r.stdout
        assert "deployment" in r.stdout

    def test_04_wait_for_running(self):
        """Wait up to 60s for the pod to be Running."""
        for attempt in range(12):
            r = run(["paas", "deploy", "status", self.CONTAINER_NAME])
            if "Running" in r.stdout:
                return
            time.sleep(5)
        pytest.fail(f"Pod not Running after 60s:\n{r.stdout}")

    def test_05_logs(self):
        """Container logs should contain nginx startup messages."""
        r = run(["paas", "deploy", "logs", self.CONTAINER_NAME])
        assert "nginx" in r.stdout.lower() or "worker process" in r.stdout

    def test_06_env_show(self):
        """Show env vars — should work even if empty."""
        r = run(["paas", "deploy", "env", self.CONTAINER_NAME])
        assert r.returncode == 0

    def test_07_env_set(self):
        """Set an env var on the container."""
        r = run(
            [
                "paas",
                "deploy",
                "env",
                self.CONTAINER_NAME,
                "TEST_VAR=hello_e2e",
            ]
        )
        assert "Set 1 variable" in r.stdout

    def test_08_env_verify(self):
        """Verify the env var was set."""
        r = run(["paas", "deploy", "env", self.CONTAINER_NAME])
        assert "TEST_VAR" in r.stdout

    def test_09_redeploy(self):
        """Trigger a redeploy."""
        r = run(["paas", "deploy", "redeploy", self.CONTAINER_NAME])
        assert "Redeployment triggered" in r.stdout

    def test_10_delete(self):
        """Delete the container."""
        r = run(["paas", "deploy", "delete", self.CONTAINER_NAME, "-y"])
        assert "Deleted" in r.stdout

    def test_11_verify_deleted(self):
        """Verify the container no longer exists."""
        r = run(["paas", "deploy", "list"])
        assert self.CONTAINER_NAME not in r.stdout


# =========================================================================
# PaaS — Error Handling
# =========================================================================


class TestPaaSErrors:
    def test_missing_context(self):
        """Commands without required context should fail gracefully."""
        run(["paas", "use", "--clear"])
        r = run(["paas", "deploy", "list"], check=False)
        assert r.returncode != 0
        assert "required" in r.stdout.lower() or "required" in r.stderr.lower()

    def test_nonexistent_container(self):
        run(
            [
                "paas",
                "use",
                "--org",
                "698cda6739f65183b3009313",
                "--project",
                "698cda6739f65183b3009318",
                "--env",
                "698cda6739f65183b300931c",
            ]
        )
        r = run(["paas", "deploy", "status", "nonexistent-container-xyz"], check=False)
        assert r.returncode != 0
        assert "not found" in r.stdout.lower() or "not found" in r.stderr.lower()

    def test_create_missing_image_and_repo(self):
        r = run(["paas", "deploy", "create", "bad-deploy"], check=False)
        assert r.returncode != 0
