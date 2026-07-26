"""Hanzo KMS client — asynchronous.

Mirror image of :class:`hanzo_kms.client.KMSClient`: same methods, same
arguments, same shared pure functions from :mod:`hanzo_kms.routes` — only the
I/O differs.
"""

import os
import time
from typing import Any, Optional

import httpx

from . import routes
from .models import ClientSettings, TokenResponse, settings_from_env


class AsyncKMSClient:
    """Async Hanzo KMS client for secret management.

    Example:
        async with AsyncKMSClient() as client:
            names = await client.list_secrets("providers/lux", env="prod")
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
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
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

    async def _token(self) -> str:
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

        response = await self.http.post(
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

    async def _headers(self) -> dict[str, str]:
        """Bearer header. The org is carried by the URL and the JWT `owner`
        claim — the server reads no org header."""
        return {"Authorization": f"Bearer {await self._token()}"}

    # =========================================================================
    # Secrets
    # =========================================================================

    async def list_secrets(
        self, path: str = "", env: str = routes.DEFAULT_ENV
    ) -> list[str]:
        """List the secret names stored at ``path``.

        Names only: the server's list route returns ``{"names": [...]}`` with
        no values, so reading a value takes a :meth:`get_secret` per name.
        """
        response = await self.http.get(
            routes.secrets_url(self.settings.org),
            params=routes.list_params(path, env),
            headers=await self._headers(),
        )
        response.raise_for_status()
        return routes.names_of(response.json())

    async def get_secret(
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
        response = await self.http.get(
            routes.secret_url(self.settings.org, path, name),
            params=routes.env_params(env),
            headers=await self._headers(),
        )
        response.raise_for_status()
        return routes.value_of(response.json())

    async def put_secret(
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
        response = await self.http.post(
            routes.secrets_url(self.settings.org),
            json=routes.upsert_body(path, name, value, env),
            headers=await self._headers(),
        )
        response.raise_for_status()

    async def delete_secret(
        self,
        path: str,
        name: str,
        env: str = routes.DEFAULT_ENV,
    ) -> None:
        """Delete a secret."""
        response = await self.http.delete(
            routes.secret_url(self.settings.org, path, name),
            params=routes.env_params(env),
            headers=await self._headers(),
        )
        response.raise_for_status()

    async def health(self) -> dict[str, Any]:
        """Probe the server: ``{"service": "kms", "status": "ok"}``. No auth."""
        response = await self.http.get(routes.HEALTH)
        response.raise_for_status()
        return response.json()

    async def inject_env(
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
        for name in await self.list_secrets(path, env):
            if overwrite or name not in os.environ:
                os.environ[name] = await self.get_secret(path, name, env)
                count += 1
        return count

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "AsyncKMSClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
