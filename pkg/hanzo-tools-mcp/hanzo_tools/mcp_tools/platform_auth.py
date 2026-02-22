"""Platform authentication utilities for Hanzo Platform MCP.

This module provides utilities for authenticating with Hanzo Platform,
including:
- Getting API keys
- Getting deployment tokens
- Setting up CI/CD credentials

Usage:
    # Interactive login
    hanzo-platform login

    # Get deploy token for CI
    hanzo-platform deploy-token --app console

    # Check authentication status
    hanzo-platform status
"""

import os
import sys
import json
import asyncio
import webbrowser
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

import httpx


@dataclass
class PlatformConfig:
    """Configuration for Platform API."""

    base_url: str = "https://platform.hanzo.ai"
    api_key: Optional[str] = None
    org_id: Optional[str] = None

    @classmethod
    def load(cls) -> "PlatformConfig":
        """Load configuration from file and environment."""
        config = cls()

        # Load from file
        config_file = Path.home() / ".hanzo" / "platform" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    config.base_url = data.get("base_url", config.base_url)
                    config.api_key = data.get("api_key")
                    config.org_id = data.get("org_id")
            except Exception:
                pass

        # Environment overrides
        if os.environ.get("PLATFORM_URL"):
            config.base_url = os.environ["PLATFORM_URL"]
        if os.environ.get("PLATFORM_API_KEY"):
            config.api_key = os.environ["PLATFORM_API_KEY"]
        if os.environ.get("PLATFORM_ORG_ID"):
            config.org_id = os.environ["PLATFORM_ORG_ID"]

        return config

    def save(self):
        """Save configuration to file."""
        config_file = Path.home() / ".hanzo" / "platform" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "org_id": self.org_id,
        }

        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)

        # Set restrictive permissions
        try:
            import stat

            config_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except Exception:
            pass


class PlatformClient:
    """Client for Hanzo Platform API."""

    def __init__(self, config: Optional[PlatformConfig] = None):
        self.config = config or PlatformConfig.load()
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._get_headers(),
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        return headers

    async def check_auth(self) -> Dict[str, Any]:
        """Check if authentication is valid."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        try:
            response = await self._client.get("/api/v1/user/me")
            if response.status_code == 200:
                return {"authenticated": True, "user": response.json()}
            return {"authenticated": False, "error": "Invalid API key"}
        except Exception as e:
            return {"authenticated": False, "error": str(e)}

    async def list_projects(self) -> Dict[str, Any]:
        """List all projects."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.get("/api/v1/projects")
        return response.json()

    async def list_applications(self, project_id: str) -> Dict[str, Any]:
        """List applications in a project."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.get(f"/api/v1/projects/{project_id}/applications")
        return response.json()

    async def get_deploy_token(self, app_id: str) -> Optional[str]:
        """Get or create a deploy token for an application."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        # Get application details including refresh token
        response = await self._client.get(f"/api/v1/applications/{app_id}")
        if response.status_code != 200:
            return None

        app_data = response.json()
        return app_data.get("application", {}).get("refreshToken")

    async def create_api_key(self, name: str = "hanzo-mcp") -> Optional[str]:
        """Create a new API key."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.post(
            "/api/v1/api-keys",
            json={"name": name, "expiresAt": None},
        )

        if response.status_code == 201:
            data = response.json()
            return data.get("apiKey", {}).get("key")
        return None


async def interactive_login() -> bool:
    """Interactive login flow."""
    print("=== Hanzo Platform Login ===")
    print()

    config = PlatformConfig.load()

    # Check if already logged in
    if config.api_key:
        async with PlatformClient(config) as client:
            result = await client.check_auth()
            if result.get("authenticated"):
                user = result.get("user", {})
                print(f"Already logged in as: {user.get('email', 'Unknown')}")
                confirm = input("Re-authenticate? [y/N]: ").strip().lower()
                if confirm != "y":
                    return True

    print(f"Opening {config.base_url}/settings/api-keys in your browser...")
    print()

    # Try to open browser
    try:
        webbrowser.open(f"{config.base_url}/settings/api-keys")
    except Exception:
        print(
            f"Could not open browser. Please visit: {config.base_url}/settings/api-keys"
        )

    print("1. Create a new API key in the Platform dashboard")
    print("2. Copy the API key")
    print()

    api_key = input("Paste your API key here: ").strip()

    if not api_key:
        print("Error: No API key provided")
        return False

    # Validate the API key
    config.api_key = api_key

    async with PlatformClient(config) as client:
        result = await client.check_auth()

        if result.get("authenticated"):
            user = result.get("user", {})
            print(f"\n✅ Successfully authenticated as: {user.get('email')}")

            # Save the configuration
            config.save()

            # Also set in environment for current session
            os.environ["PLATFORM_API_KEY"] = api_key

            print(f"\nConfiguration saved to: ~/.hanzo/platform/config.json")
            print(f"For CI/CD, set: PLATFORM_API_KEY={api_key[:8]}...")
            return True
        else:
            print(f"\n❌ Authentication failed: {result.get('error')}")
            return False


async def get_deploy_token_cli(app_name: str) -> Optional[str]:
    """Get deploy token for an application."""
    config = PlatformConfig.load()

    if not config.api_key:
        print("Error: Not logged in. Run 'hanzo-platform login' first.")
        return None

    async with PlatformClient(config) as client:
        # List projects to find the app
        projects = await client.list_projects()

        for project in projects.get("projects", []):
            apps = await client.list_applications(project["id"])

            for app in apps.get("applications", []):
                if app.get("name") == app_name or app.get("id") == app_name:
                    token = await client.get_deploy_token(app["id"])
                    if token:
                        return token

    print(f"Error: Application '{app_name}' not found")
    return None


async def status() -> Dict[str, Any]:
    """Check authentication status and available resources."""
    config = PlatformConfig.load()

    result = {
        "configured": bool(config.api_key),
        "base_url": config.base_url,
        "authenticated": False,
        "user": None,
        "projects": [],
    }

    if not config.api_key:
        return result

    async with PlatformClient(config) as client:
        auth_result = await client.check_auth()
        result["authenticated"] = auth_result.get("authenticated", False)
        result["user"] = auth_result.get("user")

        if result["authenticated"]:
            try:
                projects = await client.list_projects()
                result["projects"] = projects.get("projects", [])
            except Exception:
                pass

    return result


def cli():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hanzo Platform authentication",
        prog="hanzo-platform",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Login command
    subparsers.add_parser("login", help="Interactive login")

    # Status command
    subparsers.add_parser("status", help="Check authentication status")

    # Deploy token command
    deploy_parser = subparsers.add_parser(
        "deploy-token", help="Get deploy token for app"
    )
    deploy_parser.add_argument("--app", required=True, help="Application name or ID")
    deploy_parser.add_argument("--output", choices=["plain", "json"], default="plain")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show/set configuration")
    config_parser.add_argument("--set-url", help="Set Platform URL")
    config_parser.add_argument("--set-key", help="Set API key")

    args = parser.parse_args()

    if args.command == "login":
        success = asyncio.run(interactive_login())
        sys.exit(0 if success else 1)

    elif args.command == "status":
        result = asyncio.run(status())

        if result["authenticated"]:
            user = result.get("user", {})
            print(f"✅ Authenticated as: {user.get('email', 'Unknown')}")
            print(f"   Platform: {result['base_url']}")
            print(f"   Projects: {len(result.get('projects', []))}")

            for project in result.get("projects", []):
                print(f"     - {project.get('name', 'Unknown')}")
        else:
            print("❌ Not authenticated")
            print(f"   Platform: {result['base_url']}")
            print("\nRun 'hanzo-platform login' to authenticate")
        sys.exit(0)

    elif args.command == "deploy-token":
        token = asyncio.run(get_deploy_token_cli(args.app))
        if token:
            if args.output == "json":
                print(json.dumps({"token": token}))
            else:
                print(token)
            sys.exit(0)
        sys.exit(1)

    elif args.command == "config":
        config = PlatformConfig.load()

        if args.set_url:
            config.base_url = args.set_url
            config.save()
            print(f"Set Platform URL to: {args.set_url}")

        if args.set_key:
            config.api_key = args.set_key
            config.save()
            print(f"Set API key: {args.set_key[:8]}...")

        if not args.set_url and not args.set_key:
            print(f"Platform URL: {config.base_url}")
            print(
                f"API Key: {'****' + config.api_key[-4:] if config.api_key else 'Not set'}"
            )
            print(f"Org ID: {config.org_id or 'Not set'}")

        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    cli()
