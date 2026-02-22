"""Pydantic models for Hanzo IAM (Casdoor-based)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Organization(str, Enum):
    """Hanzo IAM organizations with their identity domains."""

    HANZO = "hanzo"
    ZOO = "zoo"
    LUX = "lux"
    PARS = "pars"

    @property
    def iam_url(self) -> str:
        """Return the IAM URL for this organization."""
        return f"https://{self.value}.id"


class IAMConfig(BaseModel):
    """Configuration for Hanzo IAM client."""

    model_config = ConfigDict(frozen=True)

    server_url: str = Field(description="IAM server URL (e.g., https://hanzo.id)")
    client_id: str = Field(description="OAuth2 client ID")
    client_secret: str = Field(default="", description="OAuth2 client secret")
    organization: str = Field(default="hanzo", description="IAM organization name")
    application: str = Field(default="app", description="IAM application name")
    certificate: str = Field(
        default="", description="JWT verification certificate (PEM)"
    )


class TokenResponse(BaseModel):
    """OAuth2 token response."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="access_token")
    token_type: str = Field(default="Bearer", alias="token_type")
    expires_in: int = Field(alias="expires_in")
    refresh_token: str | None = Field(default=None, alias="refresh_token")
    id_token: str | None = Field(default=None, alias="id_token")
    scope: str | None = Field(default=None)


class JWTClaims(BaseModel):
    """JWT claims with standard and Hanzo-specific fields."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Standard JWT claims
    iss: str | None = Field(default=None, description="Issuer")
    sub: str | None = Field(default=None, description="Subject (user ID)")
    aud: str | list[str] | None = Field(default=None, description="Audience")
    exp: int | None = Field(
        default=None, description="Expiration time (Unix timestamp)"
    )
    iat: int | None = Field(default=None, description="Issued at (Unix timestamp)")
    nbf: int | None = Field(default=None, description="Not before (Unix timestamp)")
    jti: str | None = Field(default=None, description="JWT ID")

    # Hanzo-specific claims
    name: str | None = Field(default=None, description="User display name")
    email: str | None = Field(default=None, description="User email")
    owner: str | None = Field(default=None, description="Organization owner")
    roles: list[str] = Field(default_factory=list, description="User roles")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.exp is None:
            return False
        return datetime.now().timestamp() > self.exp


class UserInfo(BaseModel):
    """OIDC UserInfo response with Hanzo extensions."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Standard OIDC claims
    sub: str = Field(description="Subject identifier")
    name: str | None = Field(default=None)
    given_name: str | None = Field(default=None, alias="given_name")
    family_name: str | None = Field(default=None, alias="family_name")
    preferred_username: str | None = Field(default=None, alias="preferred_username")
    email: str | None = Field(default=None)
    email_verified: bool = Field(default=False, alias="email_verified")
    picture: str | None = Field(default=None)
    locale: str | None = Field(default=None)
    updated_at: int | None = Field(default=None, alias="updated_at")

    # Hanzo extensions
    owner: str | None = Field(default=None, description="Organization owner")
    balance: float = Field(default=0.0, description="Account balance")
    is_admin: bool = Field(default=False, alias="isAdmin", description="Admin status")
    roles: list[str] = Field(default_factory=list, description="User roles")


class User(BaseModel):
    """Full user object from IAM API."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Identity
    id: str | None = Field(default=None)
    owner: str = Field(description="Organization owner")
    name: str = Field(description="Username")
    display_name: str = Field(default="", alias="displayName")

    # Contact
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    country_code: str | None = Field(default=None, alias="countryCode")

    # Profile
    avatar: str | None = Field(default=None)
    avatar_type: str | None = Field(default=None, alias="avatarType")
    bio: str | None = Field(default=None)
    location: str | None = Field(default=None)
    homepage: str | None = Field(default=None)

    # Status
    is_admin: bool = Field(default=False, alias="isAdmin")
    is_deleted: bool = Field(default=False, alias="isDeleted")
    is_forbidden: bool = Field(default=False, alias="isForbidden")
    is_online: bool = Field(default=False, alias="isOnline")

    # Account
    type: str | None = Field(default=None)
    password: str | None = Field(default=None)
    password_salt: str | None = Field(default=None, alias="passwordSalt")
    password_type: str | None = Field(default=None, alias="passwordType")

    # Verification
    email_verified: bool = Field(default=False, alias="emailVerified")
    phone_verified: bool = Field(default=False, alias="phoneVerified")

    # Hanzo extensions
    balance: float = Field(default=0.0)
    score: int = Field(default=0)
    karma: int = Field(default=0)
    ranking: int = Field(default=0)
    signup_application: str | None = Field(default=None, alias="signupApplication")

    # Permissions
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)

    # Timestamps
    created_time: str | None = Field(default=None, alias="createdTime")
    updated_time: str | None = Field(default=None, alias="updatedTime")

    # Additional properties
    properties: dict[str, Any] = Field(default_factory=dict)


class Application(BaseModel):
    """IAM application configuration."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Identity
    owner: str = Field(description="Organization owner")
    name: str = Field(description="Application name")
    display_name: str = Field(default="", alias="displayName")
    description: str = Field(default="")
    logo: str = Field(default="")
    homepage_url: str = Field(default="", alias="homepageUrl")

    # OAuth2 configuration
    client_id: str = Field(alias="clientId")
    client_secret: str = Field(default="", alias="clientSecret")
    redirect_uris: list[str] = Field(default_factory=list, alias="redirectUris")
    grant_types: list[str] = Field(default_factory=list, alias="grantTypes")
    response_types: list[str] = Field(default_factory=list, alias="responseTypes")

    # Token settings
    expire_in_hours: int = Field(default=168, alias="expireInHours")
    refresh_expire_in_hours: int = Field(default=0, alias="refreshExpireInHours")

    # Providers
    providers: list[dict[str, Any]] = Field(default_factory=list)
    signup_items: list[dict[str, Any]] = Field(
        default_factory=list, alias="signupItems"
    )

    # Features
    enable_password: bool = Field(default=True, alias="enablePassword")
    enable_signup: bool = Field(default=True, alias="enableSignUp")
    enable_signin_session: bool = Field(default=False, alias="enableSigninSession")
    enable_code_signin: bool = Field(default=False, alias="enableCodeSignin")

    # Organization
    organization: str = Field(default="")

    # Certificate for JWT verification
    cert: str = Field(default="")

    # Timestamps
    created_time: str | None = Field(default=None, alias="createdTime")
