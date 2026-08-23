"""Configuration for Hanzo IAM client."""

from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from hanzo_iam.models import (
    OIDC_AUTHORIZE_PATH,
    Organization,
    OIDC_DEVICE_PATH,
    OIDC_JWKS_PATH,
    OIDC_TOKEN_PATH,
    OIDC_USERINFO_PATH,
)


class IAMConfig(BaseModel):
    """Configuration for Hanzo IAM client.

    Can be initialized directly or from environment variables via from_env().
    """

    model_config = ConfigDict(frozen=True)

    # Canonical environment variable prefix. There is exactly one prefix —
    # no upstream-brand aliases, no per-org fallbacks. See
    # ~/work/hanzo/iam/CLAUDE.md "Configuration" section.
    ENV_PREFIX: ClassVar[str] = "IAM_"

    server_url: str = Field(description="IAM server URL (e.g., https://hanzo.id)")
    client_id: str = Field(description="OAuth2 client ID")
    client_secret: str = Field(default="", description="OAuth2 client secret")
    organization: str = Field(description="IAM organization name — the tenant this client acts in")
    application: str = Field(default="app", description="IAM application name")
    certificate: str = Field(
        default="", description="JWT verification certificate (PEM)"
    )

    @classmethod
    def from_env(cls, org: Organization = Organization.HANZO, prefix: str | None = None) -> IAMConfig:
        """Read configuration from the environment. The one reader.

        The canonical prefix is ``IAM_``: no upstream-brand aliases, no per-org
        variants. ``org`` seeds the endpoint and the tenant when the environment
        names neither, so a Zoo process that exports nothing reaches zoo.id as
        zoo rather than hanzo.id as hanzo. ``prefix`` exists for a process that
        scopes more than one IAM client; new code leaves it alone.

            IAM_ENDPOINT        server URL, default ``org.iam_url``
            IAM_CLIENT_ID       OAuth2 client id
            IAM_CLIENT_SECRET   OAuth2 client secret
            IAM_ORG             tenant, default ``org.value``
            IAM_APP             application, default ``app``
            IAM_CERT            JWT verification certificate, content or path
        """
        p = prefix or cls.ENV_PREFIX

        cert = os.environ.get(f"{p}CERT", "")
        if cert and not cert.startswith("-----BEGIN"):
            path = os.path.expanduser(cert)
            if os.path.isfile(path):
                cert = open(path).read()

        return cls(
            server_url=os.environ.get(f"{p}ENDPOINT", org.iam_url),
            client_id=os.environ.get(f"{p}CLIENT_ID", ""),
            client_secret=os.environ.get(f"{p}CLIENT_SECRET", ""),
            organization=os.environ.get(f"{p}ORG", org.value),
            application=os.environ.get(f"{p}APP", "app"),
            certificate=cert,
        )

    @property
    def base_url(self) -> str:
        """Server URL with any trailing slash removed."""
        return self.server_url.rstrip("/")

    @property
    def token_endpoint(self) -> str:
        """OAuth2 token endpoint URL."""
        return f"{self.base_url}{OIDC_TOKEN_PATH}"

    @property
    def authorize_endpoint(self) -> str:
        """OAuth2 authorization endpoint URL."""
        return f"{self.base_url}{OIDC_AUTHORIZE_PATH}"

    @property
    def device_endpoint(self) -> str:
        """RFC 8628 device authorization endpoint URL."""
        return f"{self.base_url}{OIDC_DEVICE_PATH}"

    @property
    def jwks_uri(self) -> str:
        """JWKS URL used to verify tokens this issuer signed."""
        return f"{self.base_url}{OIDC_JWKS_PATH}"

    @property
    def userinfo_endpoint(self) -> str:
        """OIDC UserInfo endpoint URL (HIP-0111 canonical path)."""
        return f"{self.base_url}{OIDC_USERINFO_PATH}"
