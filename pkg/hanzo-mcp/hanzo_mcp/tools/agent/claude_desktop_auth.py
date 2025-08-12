"""Claude Desktop authentication management.

This module provides tools to automate Claude Desktop login/logout,
manage separate accounts for swarm agents, and handle authentication flows.
"""

import os
import json
import time
import asyncio
import subprocess
import webbrowser
from typing import Any, Dict, Tuple, Optional
from pathlib import Path
from urllib.parse import parse_qs

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context


class ClaudeDesktopAuth:
    """Manages Claude Desktop authentication."""

    # Claude Desktop paths
    CLAUDE_APP_MAC = "/Applications/Claude.app"
    CLAUDE_CONFIG_DIR = Path.home() / ".claude"
    CLAUDE_SESSION_FILE = CLAUDE_CONFIG_DIR / "session.json"
    CLAUDE_ACCOUNTS_FILE = CLAUDE_CONFIG_DIR / "accounts.json"

    # Authentication endpoints
    CLAUDE_LOGIN_URL = "https://claude.ai/login"
    CLAUDE_API_URL = "https://api.claude.ai"

    def __init__(self):
        """Initialize Claude Desktop auth manager."""
        self.ensure_config_dir()

    def ensure_config_dir(self):
        """Ensure Claude config directory exists."""
        self.CLAUDE_CONFIG_DIR.mkdir(exist_ok=True)

    def is_claude_installed(self) -> bool:
        """Check if Claude Desktop is installed."""
        if os.path.exists(self.CLAUDE_APP_MAC):
            return True

        # Check if claude command is available
        try:
            result = subprocess.run(["which", "claude"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def is_logged_in(self, account: Optional[str] = None) -> bool:
        """Check if Claude Desktop is logged in.

        Args:
            account: Optional account identifier to check

        Returns:
            True if logged in
        """
        if not self.CLAUDE_SESSION_FILE.exists():
            return False

        try:
            with open(self.CLAUDE_SESSION_FILE, "r") as f:
                session = json.load(f)

            # Check if session is valid
            if not session.get("access_token"):
                return False

            # Check expiry if available
            if "expires_at" in session:
                if time.time() > session["expires_at"]:
                    return False

            # Check specific account if requested
            if account and session.get("account") != account:
                return False

            return True
        except Exception:
            return False

    def get_current_account(self) -> Optional[str]:
        """Get the currently logged in account."""
        if not self.is_logged_in():
            return None

        try:
            with open(self.CLAUDE_SESSION_FILE, "r") as f:
                session = json.load(f)
            return session.get("account", session.get("email"))
        except Exception:
            return None

    async def login_interactive(
        self, account: Optional[str] = None, headless: bool = False
    ) -> Tuple[bool, str]:
        """Login to Claude Desktop interactively.

        Args:
            account: Optional account email/identifier
            headless: Whether to run in headless mode

        Returns:
            Tuple of (success, message)
        """
        # Check if already logged in
        if self.is_logged_in(account):
            current = self.get_current_account()
            return True, f"Already logged in as {current}"

        # Start login flow
        if headless:
            return await self._login_headless(account)
        else:
            return await self._login_browser(account)

    async def _login_browser(self, account: Optional[str]) -> Tuple[bool, str]:
        """Login using browser flow."""
        # Generate state for OAuth-like flow
        state = os.urandom(16).hex()

        # Create callback server
        callback_port = 9876
        auth_code = None

        async def handle_callback(reader, writer):
            """Handle OAuth callback."""
            nonlocal auth_code

            # Read request
            request = await reader.read(1024)
            request_str = request.decode()

            # Extract code from query params
            if "GET /" in request_str:
                path = request_str.split(" ")[1]
                if "?code=" in path:
                    query = path.split("?")[1]
                    params = parse_qs(query)
                    if "code" in params:
                        auth_code = params["code"][0]

            # Send response
            response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            response += b"<html><body><h1>Authentication successful!</h1>"
            response += b"<p>You can close this window.</p></body></html>"
            writer.write(response)
            await writer.drain()
            writer.close()

        # Start callback server
        server = await asyncio.start_server(handle_callback, "localhost", callback_port)

        # Build login URL
        login_url = f"{self.CLAUDE_LOGIN_URL}?callback=http://localhost:{callback_port}&state={state}"
        if account:
            login_url += f"&login_hint={account}"

        # Open browser
        print(f"Opening browser for Claude login...")
        print(f"URL: {login_url}")
        webbrowser.open(login_url)

        # Wait for callback (timeout after 2 minutes)
        try:
            start_time = time.time()
            while not auth_code and (time.time() - start_time) < 120:
                await asyncio.sleep(0.5)

            if auth_code:
                # Exchange code for session
                success = await self._exchange_code_for_session(auth_code, account)
                if success:
                    return True, f"Successfully logged in as {account or 'default'}"
                else:
                    return False, "Failed to exchange auth code for session"
            else:
                return False, "Login timeout - no auth code received"

        finally:
            server.close()
            await server.wait_closed()

    async def _login_headless(self, account: Optional[str]) -> Tuple[bool, str]:
        """Login in headless mode using TTY automation."""
        # This would use expect/pexpect or similar to automate the CLI
        # For now, return a placeholder
        return False, "Headless login not yet implemented"

    async def _exchange_code_for_session(
        self, code: str, account: Optional[str]
    ) -> bool:
        """Exchange auth code for session token."""
        # This would make API calls to exchange the code
        # For now, create a mock session
        session = {
            "access_token": f"mock_token_{code[:8]}",
            "account": account or "default",
            "email": account,
            "expires_at": time.time() + 3600 * 24,  # 24 hours
            "created_at": time.time(),
        }

        try:
            with open(self.CLAUDE_SESSION_FILE, "w") as f:
                json.dump(session, f, indent=2)
            return True
        except Exception:
            return False

    async def logout(self, account: Optional[str] = None) -> Tuple[bool, str]:
        """Logout from Claude Desktop.

        Args:
            account: Optional account to logout (if multiple accounts)

        Returns:
            Tuple of (success, message)
        """
        current = self.get_current_account()

        if not current:
            return True, "No active session to logout"

        if account and current != account:
            return False, f"Not logged in as {account} (current: {current})"

        try:
            # Remove session file
            if self.CLAUDE_SESSION_FILE.exists():
                self.CLAUDE_SESSION_FILE.unlink()

            # Clear any cached credentials
            self._clear_credentials_cache()

            return True, f"Successfully logged out {current}"
        except Exception as e:
            return False, f"Logout failed: {str(e)}"

    def _clear_credentials_cache(self):
        """Clear any cached credentials."""
        # Clear keychain on macOS
        if os.path.exists("/usr/bin/security"):
            try:
                subprocess.run(
                    [
                        "/usr/bin/security",
                        "delete-generic-password",
                        "-s",
                        "claude.ai",
                        "-a",
                        "claude-desktop",
                    ],
                    capture_output=True,
                )
            except Exception:
                pass

    def switch_account(self, account: str) -> Tuple[bool, str]:
        """Switch to a different Claude account.

        Args:
            account: Account identifier to switch to

        Returns:
            Tuple of (success, message)
        """
        # Load accounts configuration
        accounts = self._load_accounts()

        if account not in accounts:
            return False, f"Unknown account: {account}"

        # Save current session if any
        current = self.get_current_account()
        if current and current != account:
            self._save_session_for_account(current)

        # Load session for new account
        if self._load_session_for_account(account):
            return True, f"Switched to account: {account}"
        else:
            return False, f"No saved session for account: {account}"

    def _load_accounts(self) -> Dict[str, Any]:
        """Load accounts configuration."""
        if not self.CLAUDE_ACCOUNTS_FILE.exists():
            return {}

        try:
            with open(self.CLAUDE_ACCOUNTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_accounts(self, accounts: Dict[str, Any]):
        """Save accounts configuration."""
        with open(self.CLAUDE_ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, indent=2)

    def _save_session_for_account(self, account: str):
        """Save current session for an account."""
        if not self.CLAUDE_SESSION_FILE.exists():
            return

        accounts = self._load_accounts()

        try:
            with open(self.CLAUDE_SESSION_FILE, "r") as f:
                session = json.load(f)

            accounts[account] = {"session": session, "saved_at": time.time()}

            self._save_accounts(accounts)
        except Exception:
            pass

    def _load_session_for_account(self, account: str) -> bool:
        """Load saved session for an account."""
        accounts = self._load_accounts()

        if account not in accounts:
            return False

        account_data = accounts[account]
        if "session" not in account_data:
            return False

        try:
            # Restore session
            session = account_data["session"]

            # Update account info
            session["account"] = account

            with open(self.CLAUDE_SESSION_FILE, "w") as f:
                json.dump(session, f, indent=2)

            return True
        except Exception:
            return False

    def create_agent_account(self, agent_id: str) -> str:
        """Create a unique account identifier for an agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Account identifier for the agent
        """
        # Generate agent-specific account
        return f"agent_{agent_id}@claude.local"

    async def ensure_agent_auth(
        self, agent_id: str, force_new: bool = False
    ) -> Tuple[bool, str]:
        """Ensure an agent is authenticated with its own account.

        Args:
            agent_id: Unique agent identifier
            force_new: Force new login even if cached

        Returns:
            Tuple of (success, message/account)
        """
        agent_account = self.create_agent_account(agent_id)

        # Check if agent already has a session
        if not force_new and self._has_saved_session(agent_account):
            # Try to switch to agent account
            success, msg = self.switch_account(agent_account)
            if success:
                return True, agent_account

        # Need to create new session for agent
        # For now, we'll use the main account
        # In production, this would create separate auth
        current = self.get_current_account()
        if current:
            # Clone current session for agent
            self._clone_session_for_agent(current, agent_account)
            return True, agent_account
        else:
            return False, "No active session to clone for agent"

    def _has_saved_session(self, account: str) -> bool:
        """Check if account has a saved session."""
        accounts = self._load_accounts()
        return account in accounts and "session" in accounts[account]

    def _clone_session_for_agent(self, source: str, agent_account: str):
        """Clone a session for an agent account."""
        # In a real implementation, this would create a sub-session
        # or use delegation tokens
        if self.CLAUDE_SESSION_FILE.exists():
            try:
                with open(self.CLAUDE_SESSION_FILE, "r") as f:
                    session = json.load(f)

                # Modify for agent
                session["account"] = agent_account
                session["parent_account"] = source
                session["is_agent"] = True

                # Save as agent session
                accounts = self._load_accounts()
                accounts[agent_account] = {
                    "session": session,
                    "saved_at": time.time(),
                    "parent": source,
                }
                self._save_accounts(accounts)
            except Exception:
                pass


class ClaudeDesktopAuthTool(BaseTool):
    """Tool for managing Claude Desktop authentication."""

    @property
    def name(self) -> str:
        return "claude_auth"

    @property
    def description(self) -> str:
        return """Manage Claude Desktop authentication.

Actions:
- status: Check login status
- login: Login to Claude Desktop
- logout: Logout from Claude Desktop
- switch: Switch between accounts
- ensure_agent: Ensure agent has auth

Usage:
claude_auth status
claude_auth login --account user@example.com
claude_auth logout
claude_auth switch agent_1
claude_auth ensure_agent swarm_agent_1"""

    def __init__(self):
        """Initialize the auth tool."""
        self.auth = ClaudeDesktopAuth()

    async def call(self, ctx, action: str = "status", **kwargs) -> str:
        """Execute auth action."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        if action == "status":
            if self.auth.is_logged_in():
                account = self.auth.get_current_account()
                return f"Logged in as: {account}"
            else:
                return "Not logged in"

        elif action == "login":
            account = kwargs.get("account")
            headless = kwargs.get("headless", False)
            success, msg = await self.auth.login_interactive(account, headless)
            return msg

        elif action == "logout":
            account = kwargs.get("account")
            success, msg = await self.auth.logout(account)
            return msg

        elif action == "switch":
            account = kwargs.get("account")
            if not account:
                return "Error: account required for switch"
            success, msg = self.auth.switch_account(account)
            return msg

        elif action == "ensure_agent":
            agent_id = kwargs.get("agent_id")
            if not agent_id:
                return "Error: agent_id required"
            force_new = kwargs.get("force_new", False)
            success, result = await self.auth.ensure_agent_auth(agent_id, force_new)
            if success:
                return f"Agent authenticated as: {result}"
            else:
                return f"Failed: {result}"

        else:
            return f"Unknown action: {action}"
