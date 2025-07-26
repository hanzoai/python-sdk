"""Authentication module for Hanzo AI.

Supports multiple authentication methods:
1. API Key (HANZO_API_KEY environment variable)
2. Email/Password via IAM (iam.hanzo.ai - Casdoor)
3. SSO authentication
4. MCP flow authentication
"""

import asyncio
import json
import os
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

import httpx


class HanzoAuth:
    """Hanzo authentication client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://iam.hanzo.ai",
        api_base_url: str = "https://api.hanzo.ai"
    ):
        """Initialize authentication client.
        
        Args:
            api_key: API key (defaults to HANZO_API_KEY env var)
            base_url: IAM service URL
            api_base_url: API service URL
        """
        self.api_key = api_key or os.environ.get("HANZO_API_KEY")
        self.base_url = base_url
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
            except:
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
                    "application": "hanzo-cli"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data.get("token")
            
            # Get user info
            user_info = await self.get_user_info()
            
            return {
                "token": self._token,
                "email": email,
                **user_info
            }
    
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
        
        return {
            "api_key": api_key,
            **user_info
        }
    
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
            "client_id": "hanzo-cli",
            "redirect_uri": "http://localhost:8899/callback",
            "response_type": "code",
            "scope": "openid profile email",
            "state": state
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
                content_type="text/html"
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
                    "client_id": "hanzo-cli",
                    "client_secret": "hanzo-cli-secret",  # Public client
                    "code": auth_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:8899/callback"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data.get("access_token")
            
            # Get user info
            user_info = await self.get_user_info()
            
            return {
                "token": self._token,
                **user_info
            }
    
    async def logout(self):
        """Logout and clear credentials."""
        if self._token:
            # Revoke token
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/logout",
                    headers=self._get_headers()
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
                f"{self.api_base_url}/v1/user",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            self._user_info = response.json()
            return self._user_info
    
    async def create_api_key(
        self,
        name: str,
        permissions: Optional[List[str]] = None,
        expires: Optional[str] = None
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
                    "expires": expires or "1y"
                }
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
                f"{self.api_base_url}/v1/api-keys",
                headers=self._get_headers()
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
                f"{self.api_base_url}/v1/api-keys/{name}",
                headers=self._get_headers()
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
            "user_info": self._user_info
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
    server_name: str = "hanzo-mcp",
    permissions: List[str] = None
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
            raise PermissionError(
                f"Missing permissions: {required_perms - user_perms}"
            )
        
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
        except:
            pass
    
    return None