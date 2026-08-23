"""Tests for the canonical IAM_* environment variable contract.

There is exactly one prefix — ``IAM_``. No upstream-brand aliases, no
per-org variants. See ~/work/hanzo/iam/CLAUDE.md "Configuration".
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hanzo_iam.client import IAMClient
from hanzo_iam.config import IAMConfig
from hanzo_iam.models import Organization

_IAM_VARS = (
    "IAM_ENDPOINT",
    "IAM_CLIENT_ID",
    "IAM_CLIENT_SECRET",
    "IAM_ORG",
    "IAM_APP",
    "IAM_CERT",
)
_LEGACY_VARS = (
    "HANZO_IAM_ENDPOINT",
    "HANZO_IAM_CLIENT_ID",
    "HANZO_IAM_CLIENT_SECRET",
    "HANZO_IAM_ORG",
    "HANZO_IAM_APP",
    "HANZO_IAM_CERT",
    "HANZO_IAM_URL",
    "HANZO_IAM_SERVER_URL",
    "HANZO_CLIENT_ID",
    "HANZO_CLIENT_SECRET",
    "HANZO_IAM_ORGANIZATION",
    "HANZO_IAM_APP_NAME",
    "HANZO_IAM_ORG_NAME",
    "HANZO_IAM_CERTIFICATE",
    "LUX_IAM_CLIENT_ID",
    "ZOO_IAM_CLIENT_ID",
    "PARS_IAM_CLIENT_ID",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Strip every legacy + canonical IAM env var before each test."""
    for v in (*_IAM_VARS, *_LEGACY_VARS):
        monkeypatch.delenv(v, raising=False)


class TestCanonicalPrefix:
    """IAMConfig.ENV_PREFIX must be 'IAM_' — never an upstream-brand prefix."""

    def test_env_prefix_is_iam(self):
        assert IAMConfig.ENV_PREFIX == "IAM_"


class TestConfigFromEnv:
    """IAMConfig.from_env is the one reader of the environment."""

    def test_reads_iam_vars(self, monkeypatch):
        monkeypatch.setenv("IAM_ENDPOINT", "https://iam.example")
        monkeypatch.setenv("IAM_CLIENT_ID", "cid")
        monkeypatch.setenv("IAM_CLIENT_SECRET", "csec")
        monkeypatch.setenv("IAM_ORG", "acme")
        monkeypatch.setenv("IAM_APP", "myapp")

        cfg = IAMConfig.from_env()
        assert cfg.server_url == "https://iam.example"
        assert cfg.client_id == "cid"
        assert cfg.client_secret == "csec"
        assert cfg.organization == "acme"
        assert cfg.application == "myapp"

    def test_org_seeds_the_endpoint_and_the_tenant(self):
        """A process that exports nothing still reaches its own org.

        This is why from_env takes an org: the default is not a literal.
        """
        assert IAMConfig.from_env(Organization.ZOO).server_url == "https://zoo.id"
        assert IAMConfig.from_env(Organization.ZOO).organization == "zoo"
        assert IAMConfig.from_env(Organization.LUX).server_url == "https://lux.id"
        assert IAMConfig.from_env(Organization.LUX).organization == "lux"

    def test_the_environment_beats_the_seed(self, monkeypatch):
        monkeypatch.setenv("IAM_ENDPOINT", "https://iam.example")
        monkeypatch.setenv("IAM_ORG", "acme")

        cfg = IAMConfig.from_env(Organization.ZOO)
        assert cfg.server_url == "https://iam.example"
        assert cfg.organization == "acme"

    @pytest.mark.parametrize(
        "name",
        [
            "HANZO_IAM_CLIENT_ID",
            "HANZO_IAM_CLIENT_SECRET",
            "HANZO_IAM_ENDPOINT",
            "HANZO_IAM_URL",
            "LUX_IAM_CLIENT_ID",
            "ZOO_IAM_CLIENT_SECRET",
        ],
    )
    def test_no_alias_is_honoured(self, monkeypatch, name):
        """IAM_ is the prefix. A brand alias or an org prefix reads as nothing."""
        monkeypatch.setenv(name, "leak")

        cfg = IAMConfig.from_env(Organization.LUX)
        assert cfg.client_id == ""
        assert cfg.client_secret == ""
        assert cfg.server_url == "https://lux.id"

    def test_it_is_the_only_reader(self):
        """No module but config.py reads the environment.

        Three readers disagreed about the tenant once: two defaulted the org to
        the literal "hanzo", so a Lux or Zoo process that forgot IAM_ORG did not
        fail — it addressed the hanzo tenant and reported hanzo's users as its
        own.
        """
        pkg = Path(__file__).resolve().parent.parent / "hanzo_iam"
        readers = [
            f.name
            for f in pkg.glob("*.py")
            if ("os.getenv" in f.read_text() or "os.environ" in f.read_text())
        ]
        assert readers == ["config.py"], readers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_the_tenant_has_no_default():
    """IAMConfig will not guess a tenant.

    It defaulted to the literal "hanzo", so a Lux or Zoo service that forgot
    IAM_ORG addressed the hanzo tenant and reported hanzo's users as its own.
    """
    with pytest.raises(Exception):
        IAMConfig(server_url="https://lux.id", client_id="app")

    assert IAMConfig(server_url="https://lux.id", client_id="app", organization="lux").organization == "lux"
