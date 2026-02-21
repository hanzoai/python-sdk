"""Configuration for Hanzo IAM client."""

from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class IAMConfig(BaseModel):
    """Configuration for Hanzo IAM client.

    Can be initialized directly or from environment variables via from_env().
    """

    model_config = ConfigDict(frozen=True)

    # Environment variable prefix
    ENV_PREFIX: ClassVar[str] = "HANZO_IAM_"

    server_url: str = Field(description="IAM server URL (e.g., https://hanzo.id)")
    client_id: str = Field(description="OAuth2 client ID")
    client_secret: str = Field(default="", description="OAuth2 client secret")
    organization: str = Field(default="hanzo", description="IAM organization name")
    application: str = Field(default="app", description="IAM application name")
    certificate: str = Field(default="", description="JWT verification certificate (PEM)")

    @classmethod
    def from_env(cls, prefix: str | None = None) -> IAMConfig:
        """Create config from environment variables.

        Environment variables:
            {prefix}ENDPOINT or {prefix}SERVER_URL - IAM server URL
            {prefix}CLIENT_ID - OAuth2 client ID
            {prefix}CLIENT_SECRET - OAuth2 client secret
            {prefix}ORG_NAME or {prefix}ORGANIZATION - Organization name
            {prefix}APP_NAME or {prefix}APPLICATION - Application name
            {prefix}CERTIFICATE - JWT certificate (PEM content or file path)
        """
        p = prefix or cls.ENV_PREFIX

        server_url = os.environ.get(f"{p}ENDPOINT") or os.environ.get(f"{p}SERVER_URL", "")
        client_id = os.environ.get(f"{p}CLIENT_ID", "")
        client_secret = os.environ.get(f"{p}CLIENT_SECRET", "")
        organization = os.environ.get(f"{p}ORG_NAME") or os.environ.get(f"{p}ORGANIZATION", "hanzo")
        application = os.environ.get(f"{p}APP_NAME") or os.environ.get(f"{p}APPLICATION", "app")

        # Certificate can be content or file path
        cert_val = os.environ.get(f"{p}CERTIFICATE", "")
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
        return f"{self.server_url}/api/login/oauth/access_token"

    @property
    def authorize_endpoint(self) -> str:
        """OAuth2 authorization endpoint URL."""
        return f"{self.server_url}/login/oauth/authorize"

    @property
    def userinfo_endpoint(self) -> str:
        """OIDC UserInfo endpoint URL."""
        return f"{self.server_url}/api/userinfo"

    @property
    def api_base(self) -> str:
        """Base URL for API calls."""
        return f"{self.server_url}/api"
