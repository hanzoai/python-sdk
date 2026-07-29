"""Hanzo authentication session — shared auth bridge for MCP platform tools.

Resolves a credential, VERIFIES it, and hands out authenticated service
clients (KMS, PaaS, IAM).

Credential resolution order:
1. HANZO_AUTH_TOKEN env var (explicit override)
2. HANZO_API_KEY env var (opaque API key)
3. The token store (OS keyring, else ~/.hanzo/auth/token.json at 0600)
"""

from __future__ import annotations

import os
import json
import time
import logging
from typing import Any
from pathlib import Path

from hanzo_iam import store
from hanzo_iam.oauth import DEFAULT_CLIENT_ID, DEFAULT_IAM_URL, DEFAULT_ORG
from hanzo_iam.models import OIDC_JWKS_PATH, OIDC_USERINFO_PATH
from hanzo_iam.tokens import (
    BAD_SIGNATURE,
    JWKS_UNREACHABLE,
    NO_CREDENTIAL,
    OK,
    OPAQUE,
    Verification,
)
from hanzo_iam.tokens import verify as verify_jwt

logger = logging.getLogger(__name__)

DEFAULT_APP = "hanzo-app"

# Kept for callers that report where credentials live. The store owns writing.
TOKEN_DIR = store.TOKEN_DIR
TOKEN_FILE = store.TOKEN_FILE


def _env(name: str) -> str:
    """Read an IAM_* env var, normalising absence to the empty string."""
    return os.getenv(name) or ""


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
        """Load stored token from the credential store."""
        return store.load()

    def _save_token(self, data: dict[str, Any]) -> None:
        """Persist token data. The store picks keyring or an atomic 0600 file."""
        store.save(data)

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
            token_data["source"] = f"store:{store.backend()}"
            self._token_data = token_data
            return self._token_data

        return None

    # -- Token state ---------------------------------------------------------

    def has_credential(self) -> bool:
        """Report whether ANY credential is present. Says nothing about validity."""
        return self.load_token() is not None

    def verify(self) -> Verification:
        """Judge the held credential against the issuer's published keys.

        This is the real check. `is_authenticated()` used to be
        `load_token() is not None`, which returned True for the literal string
        "fake.not.a.real.jwt" and made every downstream authorization decision
        in this package meaningless.

        Fails CLOSED: if the JWKS cannot be fetched we do not know the token is
        good, so we do not claim it is. The reason code distinguishes that from
        an actually-bad token.
        """
        token_data = self.load_token()
        if not token_data:
            return Verification(False, NO_CREDENTIAL, "no credential found")

        token = token_data.get("access_token") or ""
        server_url = (token_data.get("server_url") or DEFAULT_IAM_URL).rstrip("/")
        result = verify_jwt(
            token,
            jwks_uri=f"{server_url}{OIDC_JWKS_PATH}",
            issuer=server_url,
        )
        if result.reason == OPAQUE:
            # An API key is a real credential that simply cannot be judged
            # offline. Ask the issuer instead of guessing.
            return self._verify_opaque(token, server_url)
        return result

    def _verify_opaque(self, token: str, server_url: str) -> Verification:
        """Confirm an opaque credential by calling userinfo — the authority."""
        import httpx

        try:
            resp = httpx.get(
                f"{server_url}{OIDC_USERINFO_PATH}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
        except httpx.HTTPError as e:
            return Verification(False, JWKS_UNREACHABLE, f"cannot reach {server_url}: {e}")
        if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
            return Verification(True, OK, claims=resp.json())
        return Verification(
            False,
            BAD_SIGNATURE,
            f"issuer rejected the credential ({resp.status_code})",
        )

    def is_authenticated(self) -> bool:
        """True only when the held credential actually verifies."""
        return self.verify().valid

    def get_iam_token(self) -> str | None:
        """Get the current IAM access token."""
        token_data = self.load_token()
        if token_data:
            return token_data.get("access_token")
        return None

    def get_token_info(self) -> dict[str, Any]:
        """Describe the current auth state. `authenticated` reflects VERIFICATION.

        It used to reflect credential presence, so `auth status` cheerfully
        reported a garbage token as a working login.
        """
        token_data = self.load_token()
        if not token_data:
            return {"authenticated": False, "reason": NO_CREDENTIAL}

        result = self.verify()
        info: dict[str, Any] = {
            "authenticated": result.valid,
            "reason": result.reason,
            "source": token_data.get("source", "unknown"),
            "store": store.backend(),
        }
        if not result.valid:
            info["detail"] = result.detail

        # Expiry, from the token's own exp when we could read it, else the
        # locally recorded issue time.
        exp = result.claims.get("exp")
        if exp:
            info["expires_at"] = int(exp)
            info["expired"] = time.time() > float(exp)
        else:
            login_time = token_data.get("login_time", 0)
            expires_in = token_data.get("expires_in", 0)
            if login_time and expires_in:
                info["expires_at"] = login_time + expires_in
                info["expired"] = time.time() > info["expires_at"]

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
            # The token endpoint has ONE owner: hanzo_iam.oauth. This used to
            # build a whole IAMConfig and an admin IAMClient to reach a second
            # copy of the refresh grant — an org, an application and a
            # client_secret named, none of which a refresh needs.
            from hanzo_iam import oauth

            tokens = oauth.refresh(
                server_url=token_data.get("server_url", DEFAULT_IAM_URL),
                client_id=token_data.get("client_id", DEFAULT_CLIENT_ID),
                refresh_token=token_data["refresh_token"],
            )

            new_data = {
                **token_data,
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token") or token_data["refresh_token"],
                "id_token": tokens.get("id_token", ""),
                "expires_in": tokens.get("expires_in"),
                "login_time": int(time.time()),
            }

            self._save_token(new_data)
            self._token_data = new_data
            self._token_data["source"] = f"store:{store.backend()}"
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

        from hanzo_kms import KMSClient

        # KMSClient() reads HANZO_KMS_URL / _ORG / _CLIENT_ID / _CLIENT_SECRET
        # / _TOKEN itself -- see hanzo_kms.settings_from_env.
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

        # Exchange IAM token for PaaS session.
        #
        # MEASURED, not assumed: platform.hanzo.ai answers POST /v1/auth/login
        # with a bodyless 404, while /v1/org and /v1/user answer 401 — so the
        # PaaS API is up and gated, but the token-exchange route in front of it
        # is not deployed. The paas repo does mount it (platform/server.js:62 →
        # routes/auth.js) and it expects {gitUser:{provider,providerUserId,...}},
        # not the {provider,accessToken} this client used to send. Two faults,
        # and the deployment one cannot be fixed from here.
        #
        # So: fail with the actual diagnosis. Guessing a payload against a route
        # that 404s would just move the confusion downstream.
        with httpx.Client(base_url=base_url, timeout=30.0) as tmp:
            resp = tmp.post(
                "/v1/auth/login",
                json={"provider": "hanzo", "accessToken": iam_token},
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 404:
                raise RuntimeError(
                    f"PaaS token exchange is not deployed: POST {base_url}/v1/auth/login"
                    " returned 404 while /v1/org returns 401. The route exists in the"
                    " paas repo (platform/server.js -> routes/auth.js) but is not"
                    " reachable at this edge. No client-side workaround exists."
                )
            if resp.status_code == 401:
                raise RuntimeError("IAM token rejected by PaaS. Sign in again.")
            resp.raise_for_status()
            if "json" not in resp.headers.get("content-type", ""):
                raise RuntimeError(
                    f"PaaS login returned {resp.headers.get('content-type')} instead of"
                    " JSON — the request reached a web page, not the API."
                )
            data = resp.json()

        at = data.get("at", "")
        rt = data.get("rt", "")
        if not at:
            raise RuntimeError("PaaS login succeeded but no session token returned.")

        # Cache session under the same 0600-atomic discipline as the IAM token —
        # a PaaS session cookie is a bearer credential too.
        session_file = Path.home() / ".hanzo" / "paas" / "session.json"
        store._write_private(
            session_file,
            json.dumps({"at": at, "rt": rt, "login_time": int(time.time())}, indent=2),
        )

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

    def login(self, **kwargs: Any) -> dict[str, Any]:
        """Run the interactive login, persist the result, and return its info.

        Verification happens BEFORE the token is stored: a token we cannot
        check is not one we should keep and later present as proof of identity.
        """
        from hanzo_iam import oauth

        token_data = oauth.login(**kwargs)
        server_url = token_data["server_url"]
        result = verify_jwt(
            token_data["access_token"],
            jwks_uri=f"{server_url}{OIDC_JWKS_PATH}",
            issuer=server_url,
        )
        if not result.valid:
            raise RuntimeError(
                f"IAM issued a token this client cannot verify ({result.reason}:"
                f" {result.detail}). Refusing to store it."
            )
        self._save_token(token_data)
        self.close()
        self._token_data = None
        return {"claims": result.claims, "store": store.backend()}

    @staticmethod
    def logout() -> None:
        """Clear stored credentials from every backend."""
        store.clear()
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
