"""Authentication module for Hanzo AI.

Supports multiple authentication methods:
1. API Key (HANZO_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY)
2. Email/Password via IAM (iam.hanzo.ai - Casdoor)
3. SSO authentication
4. Anthropic OAuth (PKCE via console.anthropic.com)
5. OpenAI/ChatGPT OAuth (device code via auth.openai.com)
6. MCP flow authentication
7. Auto-detect (login_auto)
"""

import base64
import hashlib
import os
import sys
import json
import asyncio
import webbrowser
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

import httpx


# ---------------------------------------------------------------------------
# PKCE (Proof Key for Code Exchange) with S256
# ---------------------------------------------------------------------------

def _base64url_encode(data: bytes) -> str:
    """Base64url encode with no padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class PkceCodePair:
    """PKCE verifier/challenge pair."""
    verifier: str
    challenge: str
    challenge_method: str = "S256"


def generate_pkce_pair() -> PkceCodePair:
    """Generate a PKCE code verifier and S256 challenge.

    Uses 32 bytes of os.urandom for the verifier, SHA-256 for the challenge.
    Both are base64url encoded with no padding.
    """
    verifier = _base64url_encode(os.urandom(32))
    challenge = _base64url_encode(hashlib.sha256(verifier.encode("ascii")).digest())
    return PkceCodePair(verifier=verifier, challenge=challenge)


def generate_state() -> str:
    """Generate a random state token (32 bytes, base64url, no padding)."""
    return _base64url_encode(os.urandom(32))


@dataclass(frozen=True)
class OAuthAuthorizationRequest:
    """OAuth authorization request with PKCE parameters."""
    authorize_url: str
    client_id: str
    redirect_uri: str
    scopes: List[str]
    state: str
    code_challenge: str
    code_challenge_method: str

    def build_url(self) -> str:
        """Build the full authorization URL with query parameters."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": self.state,
            "code_challenge": self.code_challenge,
            "code_challenge_method": self.code_challenge_method,
        }
        return f"{self.authorize_url}?{urlencode(params)}"


@dataclass(frozen=True)
class OAuthTokenExchangeRequest:
    """OAuth token exchange request with PKCE code_verifier."""
    code: str
    redirect_uri: str
    client_id: str
    code_verifier: str
    state: str
    grant_type: str = "authorization_code"

    def form_params(self) -> Dict[str, str]:
        """Return parameters for the token exchange POST body."""
        return {
            "grant_type": self.grant_type,
            "code": self.code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": self.code_verifier,
            "state": self.state,
        }


@dataclass
class OAuthTokenSet:
    """OAuth token set returned from token exchange."""
    access_token: str
    scopes: List[str]
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None


class OAuthCredentialStore:
    """Manages OAuth credentials in ~/.hanzo/credentials.json.

    Respects HANZO_CONFIG_HOME env var. Uses atomic writes.
    Preserves other keys in the credentials file.

    Supports multiple providers via the `provider` parameter:
      - "hanzo"     -> stored under "oauth" key (backwards compatible)
      - "anthropic" -> stored under "oauth_anthropic" key
      - "openai"    -> stored under "oauth_openai" key
    """

    # Map provider names to JSON keys. Default "hanzo" uses "oauth"
    # for backwards compatibility with existing credentials files.
    _PROVIDER_KEYS = {
        "hanzo": "oauth",
        "anthropic": "oauth_anthropic",
        "openai": "oauth_openai",
    }

    def __init__(self, config_home: Optional[str] = None):
        self._config_home = config_home

    def _get_config_home(self) -> Path:
        if self._config_home:
            return Path(self._config_home)
        env = os.environ.get("HANZO_CONFIG_HOME")
        if env:
            return Path(env)
        return Path.home() / ".hanzo"

    def _key_for(self, provider: str) -> str:
        key = self._PROVIDER_KEYS.get(provider)
        if key is None:
            raise ValueError(f"unknown provider: {provider!r}")
        return key

    def credentials_path(self) -> Path:
        return self._get_config_home() / "credentials.json"

    def _read_file(self) -> Dict[str, Any]:
        path = self.credentials_path()
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def _write_file(self, data: Dict[str, Any]) -> None:
        path = self.credentials_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
        if sys.platform != "win32":
            os.chmod(path, 0o600)

    def save(self, token_set: OAuthTokenSet, provider: str = "hanzo") -> None:
        """Save OAuth token set. Atomic write, preserves other keys."""
        key = self._key_for(provider)
        existing = self._read_file()
        existing[key] = {
            "access_token": token_set.access_token,
            "refresh_token": token_set.refresh_token,
            "expires_at": token_set.expires_at,
            "scopes": token_set.scopes,
        }
        self._write_file(existing)

    def load(self, provider: str = "hanzo") -> Optional[OAuthTokenSet]:
        """Load OAuth token set from credentials file. Returns None if absent."""
        key = self._key_for(provider)
        data = self._read_file()
        oauth = data.get(key)
        if not oauth:
            return None
        return OAuthTokenSet(
            access_token=oauth["access_token"],
            refresh_token=oauth.get("refresh_token"),
            expires_at=oauth.get("expires_at"),
            scopes=oauth.get("scopes", []),
        )

    def clear(self, provider: str = "hanzo") -> None:
        """Remove provider's oauth key from credentials, preserving other keys."""
        key = self._key_for(provider)
        path = self.credentials_path()
        if not path.exists():
            return
        data = self._read_file()
        data.pop(key, None)
        self._write_file(data)


# ---------------------------------------------------------------------------
# Provider constants (matching codex-rs/login/src/auth/manager.rs)
# ---------------------------------------------------------------------------

# OpenAI / ChatGPT
OPENAI_ISSUER = "https://auth.openai.com"
OPENAI_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"

# Anthropic / Claude
ANTHROPIC_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
ANTHROPIC_ISSUER = "https://claude.ai"
ANTHROPIC_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
ANTHROPIC_AUTHORIZE_URL = "https://claude.ai/oauth/authorize"

# Hanzo IAM
HANZO_CLIENT_ID = "hanzo-dev"


class HanzoAuth:
    """Hanzo authentication client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://hanzo.id",
        api_base_url: str = "https://api.hanzo.ai",
    ):
        """Initialize authentication client.

        Args:
            api_key: API key (defaults to HANZO_API_KEY env var)
            base_url: IAM service URL (default: https://hanzo.id)
            api_base_url: API service URL
        """
        self.api_key = api_key or os.environ.get("HANZO_API_KEY")
        self.base_url = os.environ.get(
            "HANZO_IAM_URL", os.environ.get("IAM_URL", base_url)
        )
        self.api_base_url = api_base_url
        self._token = None
        self._user_info = None

    async def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        if self.api_key:
            return True
        if self._token:
            # Verify token is still valid
            try:
                await self.get_user_info()
                return True
            except Exception:
                self._token = None
                return False
        return False

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            User information and tokens
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/login",
                json={
                    "username": email,
                    "password": password,
                    "application": "app-hanzo",
                },
            )
            response.raise_for_status()

            data = response.json()
            self._token = data.get("token")

            # Get user info
            user_info = await self.get_user_info()

            return {"token": self._token, "email": email, **user_info}

    async def login_with_api_key(self, api_key: str) -> Dict[str, Any]:
        """Login with API key.

        Args:
            api_key: Hanzo API key

        Returns:
            User information
        """
        self.api_key = api_key

        # Verify key is valid
        user_info = await self.get_user_info()

        return {"api_key": api_key, **user_info}

    async def login_with_device_code(
        self,
        open_browser: bool = True,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """Login with Device Code flow (works on remote/headless systems).

        This is the recommended auth method for CLI tools. User visits a URL
        and enters a code, no local server required.

        Args:
            open_browser: Whether to automatically open browser (default True)
            poll_interval: Seconds between polling attempts (default 5)
            timeout: Max seconds to wait for auth (default 300)

        Returns:
            User information and tokens
        """
        import time

        async with httpx.AsyncClient() as client:
            # Step 1: Request device code
            response = await client.post(
                f"{self.base_url}/api/device/code",
                json={
                    "client_id": "app-hanzo",
                    "scope": "openid profile email",
                },
            )
            response.raise_for_status()

            data = response.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_url = data.get("verification_uri", f"{self.base_url}/device")
            verification_url_complete = data.get(
                "verification_uri_complete", f"{verification_url}?user_code={user_code}"
            )
            expires_in = data.get("expires_in", timeout)
            interval = data.get("interval", poll_interval)

            # Step 2: Display instructions to user
            print(f"\n\033[1;36mTo sign in, visit:\033[0m {verification_url}")
            print(f"\033[1;33mEnter code:\033[0m {user_code}\n")

            # Optionally open browser
            if open_browser:
                try:
                    webbrowser.open(verification_url_complete)
                    print("\033[2m(Browser opened automatically)\033[0m\n")
                except Exception:
                    pass

            # Step 3: Poll for completion
            start_time = time.time()
            while time.time() - start_time < min(expires_in, timeout):
                await asyncio.sleep(interval)

                try:
                    token_response = await client.post(
                        f"{self.base_url}/api/device/token",
                        json={
                            "client_id": "app-hanzo",
                            "device_code": device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        },
                    )

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        self._token = token_data.get("access_token")

                        # Get user info
                        user_info = await self.get_user_info()
                        print("\033[1;32m✓ Authentication successful!\033[0m\n")

                        return {"token": self._token, **user_info}

                    elif token_response.status_code == 400:
                        error_data = token_response.json()
                        error = error_data.get("error")

                        if error == "authorization_pending":
                            # User hasn't completed auth yet, keep polling
                            continue
                        elif error == "slow_down":
                            # Server asking us to slow down
                            interval += 5
                            continue
                        elif error == "expired_token":
                            raise RuntimeError("Device code expired. Please try again.")
                        elif error == "access_denied":
                            raise RuntimeError("Authentication denied by user.")
                        else:
                            raise RuntimeError(f"Authentication error: {error}")

                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 400:
                        raise

            raise RuntimeError("Authentication timed out. Please try again.")

    async def login_with_sso(self) -> OAuthTokenSet:
        """Login with SSO (browser-based).

        Delegates to login_with_pkce with the SSO redirect port.

        Returns:
            OAuthTokenSet with access token and metadata
        """
        return await self.login_with_pkce(redirect_port=8899)

    async def login_with_pkce(
        self,
        authorize_url: Optional[str] = None,
        token_url: Optional[str] = None,
        client_id: str = "app-hanzo",
        scopes: Optional[List[str]] = None,
        redirect_port: int = 4545,
    ) -> OAuthTokenSet:
        """Login with PKCE (Proof Key for Code Exchange) flow.

        Generates a PKCE pair, opens the browser, catches the callback
        on a local HTTP server, exchanges the code for tokens, and saves
        credentials.

        Args:
            authorize_url: Authorization endpoint (default: {base_url}/oauth/authorize)
            token_url: Token endpoint (default: {base_url}/oauth/token)
            client_id: OAuth client ID
            scopes: OAuth scopes
            redirect_port: Local port for the redirect callback server

        Returns:
            OAuthTokenSet with access token and metadata
        """
        if authorize_url is None:
            authorize_url = f"{self.base_url}/oauth/authorize"
        if token_url is None:
            token_url = f"{self.base_url}/oauth/token"
        if scopes is None:
            scopes = ["openid", "profile", "email"]

        pkce = generate_pkce_pair()
        state = generate_state()
        redirect_uri = f"http://localhost:{redirect_port}/callback"

        auth_req = OAuthAuthorizationRequest(
            authorize_url=authorize_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            state=state,
            code_challenge=pkce.challenge,
            code_challenge_method=pkce.challenge_method,
        )

        # Capture the auth code from the callback
        result: Dict[str, Optional[str]] = {"code": None, "error": None}

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                qs = parse_qs(urlparse(self.path).query)

                cb_state = qs.get("state", [None])[0]
                if cb_state != state:
                    self.send_response(400)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Invalid state parameter.")
                    result["error"] = "state mismatch"
                    return

                if "error" in qs:
                    self.send_response(400)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    msg = qs["error"][0]
                    self.wfile.write(f"Authorization error: {msg}".encode())
                    result["error"] = msg
                    return

                result["code"] = qs.get("code", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"Authentication successful. You can close this window.")

            def log_message(self, format, *args):
                pass  # Silence request logs

        server = HTTPServer(("127.0.0.1", redirect_port), CallbackHandler)

        # Open browser
        url = auth_req.build_url()
        try:
            webbrowser.open(url)
        except Exception:
            pass
        print(f"\nOpen this URL to authenticate:\n  {url}\n")

        # Serve one request to catch the callback
        def serve_once():
            server.handle_request()
            server.server_close()

        thread = Thread(target=serve_once, daemon=True)
        thread.start()
        # Wait for the callback (runs in background thread)
        await asyncio.get_event_loop().run_in_executor(None, thread.join, 300)

        if result["error"]:
            raise RuntimeError(f"PKCE authorization failed: {result['error']}")
        if not result["code"]:
            raise RuntimeError("No authorization code received.")

        # Exchange code for tokens
        exchange_req = OAuthTokenExchangeRequest(
            code=result["code"],
            redirect_uri=redirect_uri,
            client_id=client_id,
            code_verifier=pkce.verifier,
            state=state,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=exchange_req.form_params(),
            )
            response.raise_for_status()
            data = response.json()

        token_set = OAuthTokenSet(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at"),
            scopes=data.get("scope", " ".join(scopes)).split(),
        )

        self._token = token_set.access_token

        # Save credentials
        store = OAuthCredentialStore()
        store.save(token_set)

        return token_set

    async def login_with_anthropic(
        self,
        redirect_port: int = 4545,
    ) -> OAuthTokenSet:
        """Login with Anthropic console OAuth (PKCE flow).

        Opens browser to claude.ai/oauth/authorize, catches callback,
        exchanges code for tokens via platform.claude.com.

        Args:
            redirect_port: Local port for redirect callback (default 4545)

        Returns:
            OAuthTokenSet with access token
        """
        token_set = await self.login_with_pkce(
            authorize_url=ANTHROPIC_AUTHORIZE_URL,
            token_url=ANTHROPIC_TOKEN_URL,
            client_id=ANTHROPIC_CLIENT_ID,
            scopes=["openid", "profile", "email"],
            redirect_port=redirect_port,
        )

        # Also save under anthropic provider key
        store = OAuthCredentialStore()
        store.save(token_set, provider="anthropic")

        return token_set

    async def login_with_openai(
        self,
        open_browser: bool = True,
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ) -> OAuthTokenSet:
        """Login with OpenAI/ChatGPT device code flow.

        Requests a device code from auth.openai.com, displays a user code,
        and polls until the user completes authentication.

        Args:
            open_browser: Whether to open browser automatically
            poll_interval: Seconds between poll attempts (default 5)
            timeout: Max seconds to wait (default 900 / 15 min)

        Returns:
            OAuthTokenSet with access token
        """
        import time

        base_url = OPENAI_ISSUER.rstrip("/")
        api_url = f"{base_url}/api/accounts"

        async with httpx.AsyncClient() as client:
            # Step 1: Request device code
            response = await client.post(
                f"{api_url}/deviceauth/usercode",
                json={"client_id": OPENAI_CLIENT_ID},
            )
            response.raise_for_status()
            data = response.json()

            device_auth_id = data["device_auth_id"]
            user_code = data["user_code"]
            interval = float(data.get("interval", poll_interval))
            verification_url = f"{base_url}/codex/device"

            # Step 2: Display instructions
            print(f"\nTo sign in with ChatGPT, visit:")
            print(f"  {verification_url}")
            print(f"\nEnter code: {user_code}")
            print(f"(expires in 15 minutes)\n")

            if open_browser:
                try:
                    webbrowser.open(verification_url)
                except Exception:
                    pass

            # Step 3: Poll for completion
            start_time = time.time()
            while time.time() - start_time < timeout:
                await asyncio.sleep(interval)

                poll_resp = await client.post(
                    f"{api_url}/deviceauth/token",
                    json={
                        "device_auth_id": device_auth_id,
                        "user_code": user_code,
                    },
                )

                if poll_resp.status_code == 200:
                    code_data = poll_resp.json()

                    # Exchange the authorization code for tokens
                    pkce = PkceCodePair(
                        verifier=code_data["code_verifier"],
                        challenge=code_data["code_challenge"],
                    )
                    redirect_uri = f"{base_url}/deviceauth/callback"

                    exchange_resp = await client.post(
                        f"{base_url}/oauth/token",
                        data={
                            "grant_type": "authorization_code",
                            "code": code_data["authorization_code"],
                            "redirect_uri": redirect_uri,
                            "client_id": OPENAI_CLIENT_ID,
                            "code_verifier": pkce.verifier,
                        },
                    )
                    exchange_resp.raise_for_status()
                    token_data = exchange_resp.json()

                    token_set = OAuthTokenSet(
                        access_token=token_data["access_token"],
                        refresh_token=token_data.get("refresh_token"),
                        expires_at=token_data.get("expires_at"),
                        scopes=token_data.get("scope", "openid profile email").split(),
                    )

                    self._token = token_set.access_token

                    store = OAuthCredentialStore()
                    store.save(token_set, provider="openai")

                    print("Authentication successful.\n")
                    return token_set

                if poll_resp.status_code in (403, 404):
                    # User hasn't completed auth yet
                    continue

                # Unexpected error
                poll_resp.raise_for_status()

            raise RuntimeError("OpenAI device code authentication timed out.")

    async def login_auto(self) -> Dict[str, Any]:
        """Auto-detect authentication provider.

        Priority:
        1. HANZO_API_KEY env var
        2. ANTHROPIC_API_KEY env var
        3. OPENAI_API_KEY env var
        4. Interactive prompt to choose provider

        Returns:
            Dict with auth info (token or api_key, and provider name)
        """
        # Check env vars in priority order
        if api_key := os.environ.get("HANZO_API_KEY"):
            self.api_key = api_key
            return {"provider": "hanzo", "api_key": api_key}

        if api_key := os.environ.get("ANTHROPIC_API_KEY"):
            self.api_key = api_key
            return {"provider": "anthropic", "api_key": api_key}

        if api_key := os.environ.get("OPENAI_API_KEY"):
            self.api_key = api_key
            return {"provider": "openai", "api_key": api_key}

        # Check saved credentials
        store = OAuthCredentialStore()
        for provider in ("hanzo", "anthropic", "openai"):
            token_set = store.load(provider=provider)
            if token_set:
                self._token = token_set.access_token
                return {"provider": provider, "token": token_set.access_token}

        # Interactive: prompt user to choose
        print("\nNo API key or saved credentials found.")
        print("Choose authentication provider:")
        print("  1. Hanzo (hanzo.id)")
        print("  2. Anthropic (console.anthropic.com)")
        print("  3. OpenAI (ChatGPT)")

        choice = input("\nEnter choice [1/2/3]: ").strip()

        if choice == "1":
            token_set = await self.login_with_pkce()
            return {"provider": "hanzo", "token": token_set.access_token}
        elif choice == "2":
            token_set = await self.login_with_anthropic()
            return {"provider": "anthropic", "token": token_set.access_token}
        elif choice == "3":
            token_set = await self.login_with_openai()
            return {"provider": "openai", "token": token_set.access_token}
        else:
            raise ValueError(f"invalid choice: {choice!r}")

    async def logout(self):
        """Logout and clear credentials."""
        if self._token:
            # Revoke token
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/logout", headers=self._get_headers()
                )

        self._token = None
        self.api_key = None
        self._user_info = None

    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information.

        Returns:
            User details including permissions
        """
        if self._user_info:
            return self._user_info

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/v1/user", headers=self._get_headers()
            )
            response.raise_for_status()

            self._user_info = response.json()
            return self._user_info

    async def create_api_key(
        self,
        name: str,
        permissions: Optional[List[str]] = None,
        expires: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new API key.

        Args:
            name: Key name
            permissions: List of permissions
            expires: Expiration (e.g., "30d", "1y", "never")

        Returns:
            API key information
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/v1/api-keys",
                headers=self._get_headers(),
                json={
                    "name": name,
                    "permissions": permissions or ["read"],
                    "expires": expires or "1y",
                },
            )
            response.raise_for_status()

            return response.json()

    async def list_api_keys(self) -> List[Dict[str, Any]]:
        """List user's API keys.

        Returns:
            List of API key information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/v1/api-keys", headers=self._get_headers()
            )
            response.raise_for_status()

            return response.json().get("keys", [])

    async def revoke_api_key(self, name: str):
        """Revoke an API key.

        Args:
            name: Key name to revoke
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_base_url}/v1/api-keys/{name}", headers=self._get_headers()
            )
            response.raise_for_status()

    async def save_credentials(self, path: Path):
        """Save credentials to file.

        Args:
            path: File path to save credentials
        """
        creds = {
            "api_key": self.api_key,
            "token": self._token,
            "user_info": self._user_info,
        }

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(creds, f, indent=2)

        # Set restrictive permissions (no-op on Windows, but harmless)
        if sys.platform != "win32":
            os.chmod(path, 0o600)

    async def load_credentials(self, path: Path) -> Dict[str, Any]:
        """Load credentials from file.

        Args:
            path: File path to load credentials

        Returns:
            Saved credentials
        """
        if not path.exists():
            raise FileNotFoundError(f"Credentials file not found: {path}")

        with open(path, "r") as f:
            creds = json.load(f)

        self.api_key = creds.get("api_key")
        self._token = creds.get("token")
        self._user_info = creds.get("user_info")

        return creds

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers.

        Returns:
            Headers with authentication
        """
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        return headers


# MCP Authentication Flow
async def authenticate_for_mcp(
    server_name: str = "hanzo-mcp", permissions: List[str] = None
) -> str:
    """Authenticate and get token for MCP server.

    Args:
        server_name: MCP server name
        permissions: Required permissions

    Returns:
        Authentication token for MCP
    """
    auth = HanzoAuth()

    # Check existing authentication
    if await auth.is_authenticated():
        # Get or create MCP-specific token
        user_info = await auth.get_user_info()

        # Check if user has required permissions
        user_perms = set(user_info.get("permissions", []))
        required_perms = set(permissions or ["mcp.connect"])

        if not required_perms.issubset(user_perms):
            raise PermissionError(f"Missing permissions: {required_perms - user_perms}")

        # Return API key or token
        return auth.api_key or auth._token

    # Not authenticated - prompt for login
    raise RuntimeError("Not authenticated. Run 'hanzo auth login' first.")


# Convenience function for environment setup
def setup_auth_from_env():
    """Setup authentication from environment variables.

    Checks for:
    - HANZO_API_KEY
    - HANZO_AUTH_TOKEN
    """
    if api_key := os.environ.get("HANZO_API_KEY"):
        return HanzoAuth(api_key=api_key)

    if token := os.environ.get("HANZO_AUTH_TOKEN"):
        auth = HanzoAuth()
        auth._token = token
        return auth

    # Check for saved credentials
    config_file = Path.home() / ".hanzo" / "auth.json"
    if config_file.exists():
        auth = HanzoAuth()
        try:
            import asyncio

            asyncio.run(auth.load_credentials(config_file))
            return auth
        except Exception:
            pass

    return None


# Agent Runtime Authentication
class AgentAuth:
    """Authentication helper for agent runtime environments.

    Provides seamless auth for agents running in:
    - Local development
    - Remote VMs
    - Docker containers (Operative, etc.)
    - Kubernetes pods
    """

    def __init__(self):
        self._hanzo_auth = None

    async def ensure_authenticated(
        self,
        require_interactive: bool = False,
        headless: bool = True,
    ) -> HanzoAuth:
        """Ensure agent is authenticated, prompting if necessary.

        Args:
            require_interactive: Force device code flow even if token exists
            headless: Don't try to open browser (for containers)

        Returns:
            Authenticated HanzoAuth instance

        Raises:
            RuntimeError: If authentication fails
        """
        # 1. Check environment variables first (highest priority)
        if api_key := os.environ.get("HANZO_API_KEY"):
            self._hanzo_auth = HanzoAuth(api_key=api_key)
            return self._hanzo_auth

        if token := os.environ.get("HANZO_AUTH_TOKEN"):
            self._hanzo_auth = HanzoAuth()
            self._hanzo_auth._token = token
            return self._hanzo_auth

        # 2. Check saved credentials
        config_file = Path.home() / ".hanzo" / "auth.json"
        if config_file.exists() and not require_interactive:
            try:
                self._hanzo_auth = HanzoAuth()
                await self._hanzo_auth.load_credentials(config_file)
                if await self._hanzo_auth.is_authenticated():
                    return self._hanzo_auth
            except Exception:
                pass  # Fall through to device code flow

        # 3. Device code flow for interactive authentication
        self._hanzo_auth = HanzoAuth()
        result = await self._hanzo_auth.login_with_device_code(
            open_browser=not headless
        )

        # Save credentials for future use
        await self._hanzo_auth.save_credentials(config_file)

        return self._hanzo_auth

    @property
    def token(self) -> Optional[str]:
        """Get current auth token."""
        if self._hanzo_auth:
            return self._hanzo_auth.api_key or self._hanzo_auth._token
        return None

    def get_headers(self) -> Dict[str, str]:
        """Get auth headers for API requests."""
        if self._hanzo_auth:
            return self._hanzo_auth._get_headers()
        return {}


async def authenticate_agent(
    headless: bool = True,
    require_interactive: bool = False,
) -> AgentAuth:
    """Authenticate an agent in any environment.

    This is the recommended entry point for agent authentication.
    Works in:
    - Local CLI (opens browser for device code)
    - Remote SSH (displays device code)
    - Docker containers (uses HANZO_API_KEY or device code)
    - Kubernetes pods (uses service account or device code)

    Args:
        headless: Don't try to open browser (True for containers)
        require_interactive: Force device code even if cached token exists

    Returns:
        AgentAuth instance with authenticated session

    Example:
        async def main():
            auth = await authenticate_agent()
            # Agent is now authenticated
            headers = auth.get_headers()
            # Use headers for API requests
    """
    agent_auth = AgentAuth()
    await agent_auth.ensure_authenticated(
        require_interactive=require_interactive,
        headless=headless,
    )
    return agent_auth


def sync_authenticate_agent(
    headless: bool = True,
    require_interactive: bool = False,
) -> AgentAuth:
    """Synchronous wrapper for authenticate_agent.

    For use in non-async contexts.
    """
    return asyncio.run(
        authenticate_agent(
            headless=headless,
            require_interactive=require_interactive,
        )
    )
