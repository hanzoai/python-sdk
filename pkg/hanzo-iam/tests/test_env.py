"""Tests for the canonical IAM_* environment variable contract.

There is exactly one prefix — ``IAM_``. No upstream-brand aliases, no
per-org variants. See ~/work/hanzo/iam/CLAUDE.md "Configuration".
"""

from __future__ import annotations

import os

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
    """IAMConfig.from_env reads only IAM_* vars."""

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

    def test_ignores_hanzo_iam_legacy(self, monkeypatch):
        # Legacy aliases must NOT be honored.
        monkeypatch.setenv("HANZO_IAM_CLIENT_ID", "legacy")
        monkeypatch.setenv("HANZO_IAM_CLIENT_SECRET", "legacy-secret")
        monkeypatch.setenv("HANZO_IAM_ENDPOINT", "https://legacy.example")

        cfg = IAMConfig.from_env()
        assert cfg.client_id == ""
        assert cfg.client_secret == ""
        assert cfg.server_url == ""

    def test_ignores_org_prefixed_legacy(self, monkeypatch):
        # {ORG}_IAM_* aliases must NOT be honored.
        monkeypatch.setenv("LUX_IAM_CLIENT_ID", "leak")
        monkeypatch.setenv("ZOO_IAM_CLIENT_SECRET", "leak2")

        cfg = IAMConfig.from_env()
        assert cfg.client_id == ""
        assert cfg.client_secret == ""

    def test_defaults_when_empty(self, monkeypatch):
        cfg = IAMConfig.from_env()
        assert cfg.server_url == ""
        assert cfg.client_id == ""
        assert cfg.organization == "hanzo"
        assert cfg.application == "app"


class TestClientConfigFromEnv:
    """IAMClient._config_from_env reads only IAM_* vars."""

    def test_reads_iam_vars(self, monkeypatch):
        monkeypatch.setenv("IAM_ENDPOINT", "https://iam.example")
        monkeypatch.setenv("IAM_CLIENT_ID", "cid")
        monkeypatch.setenv("IAM_CLIENT_SECRET", "csec")
        monkeypatch.setenv("IAM_ORG", "acme")
        monkeypatch.setenv("IAM_APP", "myapp")
        monkeypatch.setenv("IAM_CERT", "")

        cfg = IAMClient._config_from_env(Organization.HANZO)
        assert cfg.server_url == "https://iam.example"
        assert cfg.client_id == "cid"
        assert cfg.client_secret == "csec"
        assert cfg.organization == "acme"
        assert cfg.application == "myapp"

    def test_endpoint_defaults_to_org_url(self, monkeypatch):
        cfg = IAMClient._config_from_env(Organization.ZOO)
        assert cfg.server_url == "https://zoo.id"
        assert cfg.organization == "zoo"

    def test_ignores_hanzo_iam_legacy(self, monkeypatch):
        monkeypatch.setenv("HANZO_IAM_CLIENT_ID", "legacy")
        monkeypatch.setenv("HANZO_IAM_URL", "https://legacy.example")

        cfg = IAMClient._config_from_env(Organization.HANZO)
        assert cfg.client_id == ""
        assert cfg.server_url == "https://hanzo.id"  # org default, NOT legacy URL

    def test_ignores_org_prefixed_legacy(self, monkeypatch):
        monkeypatch.setenv("LUX_IAM_CLIENT_ID", "leak")
        monkeypatch.setenv("ZOO_IAM_CLIENT_ID", "leak2")

        cfg = IAMClient._config_from_env(Organization.LUX)
        assert cfg.client_id == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
