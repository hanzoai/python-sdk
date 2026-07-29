"""Tests for the canonical IAM_* environment variable contract.

There is exactly one prefix — ``IAM_``. No upstream-brand aliases, no
per-org variants. See ~/work/hanzo/iam/CLAUDE.md "Configuration".
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

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
        monkeypatch.setenv("IAM_ORG", "acme")
        monkeypatch.setenv("HANZO_IAM_CLIENT_ID", "legacy")
        monkeypatch.setenv("HANZO_IAM_CLIENT_SECRET", "legacy-secret")
        monkeypatch.setenv("HANZO_IAM_ENDPOINT", "https://legacy.example")

        cfg = IAMConfig.from_env()
        assert cfg.client_id == ""
        assert cfg.client_secret == ""
        assert cfg.server_url == ""

    def test_ignores_org_prefixed_legacy(self, monkeypatch):
        # {ORG}_IAM_* aliases must NOT be honored.
        monkeypatch.setenv("IAM_ORG", "acme")
        monkeypatch.setenv("LUX_IAM_CLIENT_ID", "leak")
        monkeypatch.setenv("ZOO_IAM_CLIENT_SECRET", "leak2")

        cfg = IAMConfig.from_env()
        assert cfg.client_id == ""
        assert cfg.client_secret == ""

    def test_unset_org_refuses(self, monkeypatch):
        """An unset IAM_ORG must RAISE, never resolve to somebody else's org.

        The default was the literal "hanzo". A Lux or Zoo deployment that
        forgot IAM_ORG did not fail — it silently addressed the hanzo tenant
        and reported hanzo's users as its own. Refusing is the only safe
        answer: the process cannot guess which tenant it serves.
        """
        with pytest.raises(ValueError, match="IAM_ORG"):
            IAMConfig.from_env()

    def test_unset_org_refuses_under_a_custom_prefix(self, monkeypatch):
        monkeypatch.setenv("OTHER_ENDPOINT", "https://iam.example")
        with pytest.raises(ValueError, match="OTHER_ORG"):
            IAMConfig.from_env(prefix="OTHER_")

    def test_other_fields_still_default_when_empty(self, monkeypatch):
        monkeypatch.setenv("IAM_ORG", "acme")
        cfg = IAMConfig.from_env()
        assert cfg.server_url == ""
        assert cfg.client_id == ""
        assert cfg.application == "app"


class TestOrganizationIsNeverAssumed:
    """No construction path may invent a tenant."""

    def test_config_requires_an_organization(self):
        with pytest.raises(ValidationError):
            IAMConfig(server_url="https://hanzo.id", client_id="cid")

    def test_organization_enum_still_names_one_explicitly(self):
        cfg = IAMConfig(
            server_url=Organization.ZOO.iam_url,
            client_id="cid",
            organization=Organization.ZOO.value,
        )
        assert cfg.server_url == "https://zoo.id"
        assert cfg.organization == "zoo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
