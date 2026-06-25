"""Configuration for Hanzo IAM client."""

from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from hanzo_iam.models import OIDC_USERINFO_PATH


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
    organization: str = Field(default="hanzo", description="IAM organization name")
    application: str = Field(default="app", description="IAM application name")
    certificate: str = Field(
        default="", description="JWT verification certificate (PEM)"
    )

    @classmethod
    def from_env(cls, prefix: str | None = None) -> IAMConfig:
        """Create config from environment variables.

        The canonical prefix is ``IAM_`` (no upstream-brand aliases, no
        per-org variants). The ``prefix`` argument exists for advanced
        callers that scope multiple IAM clients in a single process; new
        code should leave it at the default.

        Environment variables (with the default prefix):
            IAM_ENDPOINT - IAM server URL (preferred)
            IAM_CLIENT_ID - OAuth2 client ID
            IAM_CLIENT_SECRET - OAuth2 client secret
            IAM_ORG - Organization name
            IAM_APP - Application name
            IAM_CERT - JWT verification certificate (PEM content or file path)
        """
        p = prefix or cls.ENV_PREFIX

        server_url = os.environ.get(f"{p}ENDPOINT", "")
        client_id = os.environ.get(f"{p}CLIENT_ID", "")
        client_secret = os.environ.get(f"{p}CLIENT_SECRET", "")
        organization = os.environ.get(f"{p}ORG", "hanzo")
        application = os.environ.get(f"{p}APP", "app")

        # Certificate can be content or file path
        cert_val = os.environ.get(f"{p}CERT", "")
        if cert_val and not cert_val.startswith("-----BEGIN"):
            # Treat as file path
            cert_path = os.path.expanduser(cert_val)
            if os.path.isfile(cert_path):
                with open(cert_path) as f:
                    cert_val = f.read()

        return cls(
            server_url=server_url,
            client_id=client_id,
            client_secret=client_secret,
            organization=organization,
            application=application,
            certificate=cert_val,
        )

    @property
    def token_endpoint(self) -> str:
        """OAuth2 token endpoint URL."""
        return f"{self.server_url}/oauth/token"

    @property
    def authorize_endpoint(self) -> str:
        """OAuth2 authorization endpoint URL."""
        return f"{self.server_url}/oauth/authorize"

    @property
    def userinfo_endpoint(self) -> str:
        """OIDC UserInfo endpoint URL (HIP-0111 canonical path)."""
        return f"{self.server_url}{OIDC_USERINFO_PATH}"

    @property
    def api_base(self) -> str:
        """Base URL for API calls."""
        return f"{self.server_url}/api"
