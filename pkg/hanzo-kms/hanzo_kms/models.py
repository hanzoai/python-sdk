"""Settings and response models for the canonical luxfi/kms surface."""

import os

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_SITE_URL = "https://kms.hanzo.ai"
DEFAULT_ORG = "hanzo"


class ClientSettings(BaseModel):
    """KMS client configuration.

    Auth is one of exactly two things: a pre-issued IAM bearer token
    (``access_token``), or machine-identity client credentials that
    ``POST /v1/kms/auth/login`` exchanges for one. luxfi/kms has a single
    login route — the AWS / Azure / GCP / Kubernetes / SRP methods this SDK
    used to model were Infisical's, and none of them were ever served.
    """

    site_url: str = Field(DEFAULT_SITE_URL, description="KMS base URL")
    org: str = Field(
        DEFAULT_ORG,
        description="Organization — scopes both the secret path and the JWT `owner` claim",
    )
    client_id: str = Field("", description="Machine identity client ID")
    client_secret: str = Field("", description="Machine identity client secret")
    access_token: str = Field("", description="Pre-issued IAM bearer token; skips login")
    user_agent: str = Field("hanzo-kms-python", description="User agent string")


def settings_from_env() -> ClientSettings:
    """Build settings from the ``HANZO_KMS_*`` environment variables."""
    return ClientSettings(
        site_url=os.getenv("HANZO_KMS_URL", DEFAULT_SITE_URL),
        org=os.getenv("HANZO_KMS_ORG", DEFAULT_ORG),
        client_id=os.getenv("HANZO_KMS_CLIENT_ID", ""),
        client_secret=os.getenv("HANZO_KMS_CLIENT_SECRET", ""),
        access_token=os.getenv("HANZO_KMS_TOKEN", ""),
    )


class TokenResponse(BaseModel):
    """``POST /v1/kms/auth/login`` response."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(..., alias="accessToken")
    expires_in: int = Field(..., alias="expiresIn")
    token_type: str = Field("Bearer", alias="tokenType")
