"""Authentication module for Hanzo AI.

Supports multiple authentication methods:
1. API Key (HANZO_API_KEY environment variable)
2. Email/Password via IAM (iam.hanzo.ai - Casdoor)
3. SSO authentication
4. MCP flow authentication
"""

import os
import json
import asyncio
import webbrowser
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urlencode

import httpx


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

    async def login_with_sso(self) -> Dict[str, Any]:
        """Login with SSO (browser-based).

        Returns:
            User information and tokens
        """
        # Generate state for security
        import secrets

        state = secrets.token_urlsafe(32)

        # Build SSO URL
        params = {
            "client_id": "app-hanzo",
            "redirect_uri": "http://localhost:8899/callback",
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
        }

        sso_url = f"{self.base_url}/login/oauth/authorize?{urlencode(params)}"

        # Open browser
        webbrowser.open(sso_url)

        # Start local server to receive callback
        from aiohttp import web

        auth_code = None

        async def callback_handler(request):
            nonlocal auth_code

            # Verify state
            if request.query.get("state") != state:
                return web.Response(text="Invalid state", status=400)

            auth_code = request.query.get("code")

            return web.Response(
                text="Authentication successful! You can close this window.",
                content_type="text/html",
            )

        app = web.Application()
        app.router.add_get("/callback", callback_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8899)
        await site.start()

        # Wait for callback
        while auth_code is None:
            await asyncio.sleep(0.1)

        await runner.cleanup()

        # Exchange code for token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/login/oauth/access_token",
                json={
                    "client_id": "app-hanzo",
                    "client_secret": "hanzo-cli-secret",  # Public client
                    "code": auth_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:8899/callback",
                },
            )
            response.raise_for_status()

            data = response.json()
            self._token = data.get("access_token")

            # Get user info
            user_info = await self.get_user_info()

            return {"token": self._token, **user_info}

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

        # Set restrictive permissions
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
