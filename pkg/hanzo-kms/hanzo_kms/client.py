"""Hanzo KMS client — synchronous.

Speaks the canonical luxfi/kms surface; see :mod:`hanzo_kms.routes` for the
route table and for why the old ``/api/*`` paths never worked. This is the
mirror image of :class:`hanzo_kms.async_client.AsyncKMSClient`: same methods,
same arguments, same shared pure functions — only the I/O differs.
"""

import os
import time
from typing import Any, Optional

import httpx

from . import routes
from .models import ClientSettings, TokenResponse, settings_from_env


class KMSClient:
    """Hanzo KMS client for secret management.

    A secret is identified by (org, path, name, env). ``org`` comes from
    settings — it scopes both the URL and the JWT — and the rest are
    per-call.

    Example:
        client = KMSClient(ClientSettings(
            org="lux",
            client_id="...",
            client_secret="...",
        ))
        mnemonic = client.get_secret("providers/lux", "deploy-mnemonic", env="prod")

    With ``HANZO_KMS_ORG`` / ``HANZO_KMS_CLIENT_ID`` / ``HANZO_KMS_CLIENT_SECRET``
    set, ``KMSClient()`` configures itself.
    """

    def __init__(
        self,
        settings: Optional[ClientSettings] = None,
        *,
        debug: bool = False,
    ):
        """Initialize the client.

        Args:
            settings: Configuration; read from the environment when omitted.
            debug: Enable debug logging.
        """
        self.settings = settings or settings_from_env()
        self.debug = debug
        self._access_token = ""
        self._token_expires_at = 0.0
        self._http_client: Optional[httpx.Client] = None

    @property
    def http(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=self.settings.site_url.rstrip("/"),
                timeout=30.0,
                headers={
                    "User-Agent": self.settings.user_agent,
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    # =========================================================================
    # Auth
    # =========================================================================

    def _token(self) -> str:
        """Return a valid bearer token, logging in when needed."""
        if self.settings.access_token:
            return self.settings.access_token

        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        if not (self.settings.client_id and self.settings.client_secret):
            raise ValueError(
                "no KMS credentials: set access_token, or client_id and client_secret "
                "(HANZO_KMS_TOKEN, or HANZO_KMS_CLIENT_ID and HANZO_KMS_CLIENT_SECRET)"
            )

        response = self.http.post(
            routes.LOGIN,
            json={
                "clientId": self.settings.client_id,
                "clientSecret": self.settings.client_secret,
            },
        )
        response.raise_for_status()
        token = TokenResponse.model_validate(response.json())
        self._access_token = token.access_token
        self._token_expires_at = time.time() + token.expires_in
        return self._access_token

    def _headers(self) -> dict[str, str]:
        """Bearer header. The org is carried by the URL and the JWT `owner`
        claim — the server reads no org header."""
        return {"Authorization": f"Bearer {self._token()}"}

    # =========================================================================
    # Secrets
    # =========================================================================

    def list_secrets(self, path: str = "", env: str = routes.DEFAULT_ENV) -> list[str]:
        """List the secret names stored at ``path``.

        Names only: the server's list route returns ``{"names": [...]}`` with
        no values, so reading a value takes a :meth:`get_secret` per name.
        """
        response = self.http.get(
            routes.secrets_url(self.settings.org),
            params=routes.list_params(path, env),
            headers=self._headers(),
        )
        response.raise_for_status()
        return routes.names_of(response.json())

    def get_secret(
        self,
        path: str,
        name: str,
        env: str = routes.DEFAULT_ENV,
        version: Optional[int] = None,
    ) -> str:
        """Read the value of one secret.

        Args:
            path: Secret path, e.g. ``"providers/lux"``.
            name: Secret name, e.g. ``"deploy-mnemonic"``. May not contain ``/``.
            env: Environment bucket.
            version: Must be None — see :class:`~hanzo_kms.routes.VersionUnsupportedError`.
        """
        routes.check_version(version)
        response = self.http.get(
            routes.secret_url(self.settings.org, path, name),
            params=routes.env_params(env),
            headers=self._headers(),
        )
        response.raise_for_status()
        return routes.value_of(response.json())

    def put_secret(
        self,
        path: str,
        name: str,
        value: str,
        env: str = routes.DEFAULT_ENV,
    ) -> None:
        """Create or replace a secret.

        One upsert, not a create/update pair: luxfi/kms holds exactly one
        value per (path, name, env) and a write replaces it in place.
        """
        response = self.http.post(
            routes.secrets_url(self.settings.org),
            json=routes.upsert_body(path, name, value, env),
            headers=self._headers(),
        )
        response.raise_for_status()

    def delete_secret(
        self,
        path: str,
        name: str,
        env: str = routes.DEFAULT_ENV,
    ) -> None:
        """Delete a secret."""
        response = self.http.delete(
            routes.secret_url(self.settings.org, path, name),
            params=routes.env_params(env),
            headers=self._headers(),
        )
        response.raise_for_status()

    def health(self) -> dict[str, Any]:
        """Probe the server: ``{"service": "kms", "status": "ok"}``. No auth."""
        response = self.http.get(routes.HEALTH)
        response.raise_for_status()
        return response.json()

    def inject_env(
        self,
        path: str = "",
        env: str = routes.DEFAULT_ENV,
        overwrite: bool = False,
    ) -> int:
        """Load every secret at ``path`` into ``os.environ``, keyed by name.

        Costs one list request plus one read per secret — the list route
        returns names, not values.

        Returns:
            The number of variables set.
        """
        count = 0
        for name in self.list_secrets(path, env):
            if overwrite or name not in os.environ:
                os.environ[name] = self.get_secret(path, name, env)
                count += 1
        return count

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "KMSClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
