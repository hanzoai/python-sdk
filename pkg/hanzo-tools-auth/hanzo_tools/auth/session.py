"""Hanzo authentication session — shared auth bridge for MCP platform tools.

Loads IAM tokens from disk or environment, auto-refreshes expired tokens,
and provides authenticated service clients (KMS, PaaS, IAM).

Token resolution order:
1. HANZO_AUTH_TOKEN env var (explicit override)
2. HANZO_API_KEY env var (API key auth)
3. ~/.hanzo/auth/token.json (from `hanzo login`)
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".hanzo" / "auth"
TOKEN_FILE = TOKEN_DIR / "token.json"

# IAM defaults (same as hanzo-cli)
DEFAULT_IAM_URL = "https://hanzo.id"
DEFAULT_ORG = "hanzo"
DEFAULT_APP = "app-hanzo"
DEFAULT_CLIENT_ID = "hanzo-app-client-id"


def _env(name: str) -> str:
    """Read env var, accepting both IAM_ and HANZO_IAM_ prefixes."""
    return os.getenv(name) or os.getenv(f"HANZO_{name}") or ""


class HanzoSession:
    """Singleton session providing authenticated clients to platform tools."""

    _instance: HanzoSession | None = None

    def __init__(self) -> None:
        self._token_data: dict[str, Any] | None = None
        self._iam_client: Any | None = None
        self._kms_client: Any | None = None

    @classmethod
    def get(cls) -> HanzoSession:
        """Get or create the singleton session."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        if cls._instance:
            cls._instance.close()
        cls._instance = None

    # -- Token loading -------------------------------------------------------

    def _load_token_from_disk(self) -> dict[str, Any] | None:
        """Load stored token from ~/.hanzo/auth/token.json."""
        if not TOKEN_FILE.exists():
            return None
        try:
            return json.loads(TOKEN_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _save_token(self, data: dict[str, Any]) -> None:
        """Save token data to disk."""
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(data, indent=2))
        TOKEN_FILE.chmod(0o600)

    def load_token(self) -> dict[str, Any] | None:
        """Load token using the resolution chain.

        Returns token data dict or None if not authenticated.
        """
        if self._token_data:
            return self._token_data

        # 1. Explicit token override
        auth_token = os.getenv("HANZO_AUTH_TOKEN")
        if auth_token:
            self._token_data = {
                "access_token": auth_token,
                "source": "env:HANZO_AUTH_TOKEN",
            }
            return self._token_data

        # 2. API key
        api_key = os.getenv("HANZO_API_KEY")
        if api_key:
            self._token_data = {
                "access_token": api_key,
                "source": "env:HANZO_API_KEY",
            }
            return self._token_data

        # 3. Stored token from `hanzo login`
        token_data = self._load_token_from_disk()
        if token_data and token_data.get("access_token"):
            token_data["source"] = "disk:~/.hanzo/auth/token.json"
            self._token_data = token_data
            return self._token_data

        return None

    # -- Token state ---------------------------------------------------------

    def is_authenticated(self) -> bool:
        """Check if we have a valid token."""
        return self.load_token() is not None

    def get_iam_token(self) -> str | None:
        """Get the current IAM access token."""
        token_data = self.load_token()
        if token_data:
            return token_data.get("access_token")
        return None

    def get_token_info(self) -> dict[str, Any]:
        """Get info about the current auth state."""
        token_data = self.load_token()
        if not token_data:
            return {"authenticated": False}

        info: dict[str, Any] = {
            "authenticated": True,
            "source": token_data.get("source", "unknown"),
        }

        # Check expiry
        login_time = token_data.get("login_time", 0)
        expires_in = token_data.get("expires_in", 0)
        if login_time and expires_in:
            expires_at = login_time + expires_in
            info["expires_at"] = expires_at
            info["expired"] = time.time() > expires_at

        # Add org/app info if available
        if token_data.get("organization"):
            info["organization"] = token_data["organization"]
        if token_data.get("application"):
            info["application"] = token_data["application"]
        if token_data.get("server_url"):
            info["server_url"] = token_data["server_url"]

        return info

    # -- Token refresh -------------------------------------------------------

    def refresh_token(self) -> bool:
        """Attempt to refresh an expired token.

        Returns True if refresh succeeded.
        """
        token_data = self._load_token_from_disk()
        if not token_data or not token_data.get("refresh_token"):
            return False

        try:
            from hanzo_iam import IAMClient, IAMConfig

            config = IAMConfig(
                server_url=token_data.get("server_url", DEFAULT_IAM_URL),
                client_id=token_data.get("client_id", DEFAULT_CLIENT_ID),
                client_secret="",
                organization=token_data.get("organization", DEFAULT_ORG),
                application=token_data.get("application", DEFAULT_APP),
            )
            client = IAMClient(config=config)

            tokens = client.refresh_token(token_data["refresh_token"])
            client.close()

            new_data = {
                **token_data,
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token or token_data["refresh_token"],
                "id_token": getattr(tokens, "id_token", ""),
                "expires_in": tokens.expires_in,
                "login_time": int(time.time()),
            }

            self._save_token(new_data)
            self._token_data = new_data
            self._token_data["source"] = "disk:~/.hanzo/auth/token.json"
            logger.info("Token refreshed successfully")
            return True

        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            return False

    # -- Service clients -----------------------------------------------------

    def get_iam_client(self) -> Any:
        """Get an authenticated IAMClient."""
        if self._iam_client:
            return self._iam_client

        from hanzo_iam import IAMClient, IAMConfig

        token_data = self.load_token()
        if not token_data:
            raise RuntimeError("Not authenticated. Run 'hanzo login' first.")

        # If we have M2M credentials
        client_id = _env("IAM_CLIENT_ID")
        client_secret = _env("IAM_CLIENT_SECRET")

        if client_id and client_secret:
            config = IAMConfig(
                server_url=_env("IAM_URL") or DEFAULT_IAM_URL,
                client_id=client_id,
                client_secret=client_secret,
                organization=_env("IAM_ORG") or DEFAULT_ORG,
                application=_env("IAM_APP") or DEFAULT_APP,
            )
            self._iam_client = IAMClient(config=config)
        else:
            config = IAMConfig(
                server_url=token_data.get("server_url", DEFAULT_IAM_URL),
                client_id=token_data.get("client_id", ""),
                client_secret="",
                organization=token_data.get("organization", DEFAULT_ORG),
                application=token_data.get("application", DEFAULT_APP),
            )
            self._iam_client = IAMClient(
                config=config,
                bearer_token=token_data["access_token"],
            )

        return self._iam_client

    def get_kms_client(self) -> Any:
        """Get an authenticated KMSClient."""
        if self._kms_client:
            return self._kms_client

        from hanzo_kms import ClientSettings, KMSClient

        kms_url = os.getenv("HANZO_KMS_URL", "https://kms.hanzo.ai")
        client_id = os.getenv("HANZO_KMS_CLIENT_ID", "")
        client_secret = os.getenv("HANZO_KMS_CLIENT_SECRET", "")

        if client_id and client_secret:
            from hanzo_kms import AuthenticationOptions, UniversalAuthMethod

            settings = ClientSettings(
                site_url=kms_url,
                auth=AuthenticationOptions(
                    universal_auth=UniversalAuthMethod(
                        client_id=client_id,
                        client_secret=client_secret,
                    )
                ),
            )
            self._kms_client = KMSClient(settings=settings)
        else:
            # Fall back to default env-based construction
            self._kms_client = KMSClient()

        return self._kms_client

    def get_paas_client(self) -> Any:
        """Get an authenticated PaaS client via IAM token exchange."""
        import httpx

        token_data = self.load_token()
        if not token_data:
            raise RuntimeError("Not authenticated. Run 'hanzo login' first.")

        base_url = os.getenv("HANZO_PAAS_URL", "https://platform.hanzo.ai").rstrip("/")
        iam_token = token_data["access_token"]

        # Check for cached PaaS session
        session_file = Path.home() / ".hanzo" / "paas" / "session.json"
        if session_file.exists():
            try:
                session = json.loads(session_file.read_text())
                if session.get("at"):
                    # Validate cached session
                    with httpx.Client(base_url=base_url, timeout=10.0) as tmp:
                        resp = tmp.get(
                            "/v1/org",
                            headers={"Authorization": session["at"]},
                        )
                        if resp.status_code != 401:
                            return _PaaSClientWrapper(base_url, session["at"], session.get("rt"))
            except Exception:
                pass

        # Exchange IAM token for PaaS session
        with httpx.Client(base_url=base_url, timeout=30.0) as tmp:
            resp = tmp.post(
                "/v1/auth/login",
                json={"provider": "hanzo", "accessToken": iam_token},
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 401:
                raise RuntimeError("IAM token rejected by PaaS. Try 'hanzo login' again.")
            resp.raise_for_status()
            data = resp.json()

        at = data.get("at", "")
        rt = data.get("rt", "")
        if not at:
            raise RuntimeError("PaaS login succeeded but no session token returned.")

        # Cache session
        session_dir = Path.home() / ".hanzo" / "paas"
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "session.json"
        session_file.write_text(json.dumps({"at": at, "rt": rt, "login_time": int(time.time())}, indent=2))
        session_file.chmod(0o600)

        return _PaaSClientWrapper(base_url, at, rt)

    # -- Lifecycle -----------------------------------------------------------

    def close(self) -> None:
        """Close all held clients."""
        if self._iam_client and hasattr(self._iam_client, "close"):
            self._iam_client.close()
        if self._kms_client and hasattr(self._kms_client, "close"):
            self._kms_client.close()
        self._iam_client = None
        self._kms_client = None
        self._token_data = None

    # -- Logout --------------------------------------------------------------

    @staticmethod
    def logout() -> None:
        """Clear stored credentials."""
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        session_file = Path.home() / ".hanzo" / "paas" / "session.json"
        if session_file.exists():
            session_file.unlink()


class _PaaSClientWrapper:
    """Lightweight async-friendly wrapper over PaaS REST API."""

    def __init__(self, base_url: str, access_token: str, refresh_token: str | None = None):
        self.base_url = base_url
        self._at = access_token
        self._rt = refresh_token

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": "hanzo-mcp/0.1"}
        if self._at:
            headers["Authorization"] = self._at
        if self._rt:
            headers["Refresh-Token"] = self._rt
        return headers

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an HTTP request to PaaS API."""
        import httpx

        with httpx.Client(base_url=self.base_url, timeout=30.0) as client:
            resp = client.request(method, path, headers=self._headers(), **kwargs)
            if resp.status_code >= 400:
                try:
                    err = resp.json()
                    msg = err.get("error", resp.text)
                except Exception:
                    msg = resp.text
                raise RuntimeError(f"PaaS error {resp.status_code}: {msg}")
            if not resp.content or resp.status_code == 204:
                return {}
            return resp.json()

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
