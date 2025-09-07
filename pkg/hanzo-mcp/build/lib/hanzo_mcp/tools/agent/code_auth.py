"""Claude Code and OpenAI Codex authentication management.

This module provides tools to manage API keys and authentication for
Claude Code CLI and OpenAI Codex, allowing separate accounts for swarm agents.
"""

import os
import json
import getpass
import subprocess
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

import keyring


@dataclass
class APICredential:
    """API credential information."""

    provider: str
    api_key: str
    model: Optional[str] = None
    base_url: Optional[str] = None
    org_id: Optional[str] = None
    description: Optional[str] = None


class CodeAuthManager:
    """Manages authentication for Claude Code and other AI coding tools."""

    # Configuration paths
    CONFIG_DIR = Path.home() / ".hanzo" / "auth"
    ACCOUNTS_FILE = CONFIG_DIR / "accounts.json"
    ACTIVE_ACCOUNT_FILE = CONFIG_DIR / "active_account"

    # Environment variable mappings
    ENV_VARS = {
        "claude": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "azure": ["AZURE_OPENAI_API_KEY", "AZURE_API_KEY"],
        "deepseek": ["DEEPSEEK_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "groq": ["GROQ_API_KEY"],
    }

    # Default models
    DEFAULT_MODELS = {
        "claude": "claude-3-5-sonnet-20241022",  # Latest Sonnet
        "openai": "gpt-4o",
        "azure": "gpt-4",
        "deepseek": "deepseek-coder",
        "google": "gemini-1.5-pro",
        "groq": "llama3-70b-8192",
    }

    def __init__(self):
        """Initialize auth manager."""
        self.ensure_config_dir()
        self._env_backup = {}

    def ensure_config_dir(self):
        """Ensure config directory exists."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def get_active_account(self) -> Optional[str]:
        """Get the currently active account."""
        if self.ACTIVE_ACCOUNT_FILE.exists():
            return self.ACTIVE_ACCOUNT_FILE.read_text().strip()
        return "default"

    def set_active_account(self, account: str):
        """Set the active account."""
        self.ACTIVE_ACCOUNT_FILE.write_text(account)

    def _load_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Load all accounts."""
        if not self.ACCOUNTS_FILE.exists():
            return {}

        try:
            with open(self.ACCOUNTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_accounts(self, accounts: Dict[str, Dict[str, Any]]):
        """Save accounts."""
        with open(self.ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, indent=2)

    def list_accounts(self) -> List[str]:
        """List all available accounts."""
        accounts = self._load_accounts()
        return list(accounts.keys())

    def get_account_info(self, account: str) -> Optional[Dict[str, Any]]:
        """Get information about an account."""
        accounts = self._load_accounts()
        return accounts.get(account)

    def create_account(
        self,
        account: str,
        provider: str = "claude",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Create a new account.

        Args:
            account: Account name
            provider: Provider (claude, openai, etc.)
            api_key: API key (will prompt if not provided)
            model: Model to use (defaults to provider default)
            description: Account description

        Returns:
            Tuple of (success, message)
        """
        accounts = self._load_accounts()

        if account in accounts:
            return False, f"Account '{account}' already exists"

        # Get API key if not provided
        if not api_key:
            api_key = self._prompt_for_api_key(provider)
            if not api_key:
                return False, "No API key provided"

        # Use default model if not specified
        if not model:
            model = self.DEFAULT_MODELS.get(provider)

        # Store in keyring for security
        try:
            keyring.set_password(f"hanzo-{provider}", account, api_key)
        except Exception:
            # Fallback to file storage (less secure)
            pass

        # Save account info
        accounts[account] = {
            "provider": provider,
            "model": model,
            "description": description or f"{provider} account",
            "created_at": os.path.getmtime(__file__),
            "has_keyring": self._has_keyring_support(),
        }

        self._save_accounts(accounts)
        return True, f"Created account '{account}' for {provider}"

    def _prompt_for_api_key(self, provider: str) -> Optional[str]:
        """Prompt user for API key."""
        prompt = f"Enter {provider.upper()} API key: "
        try:
            return getpass.getpass(prompt)
        except KeyboardInterrupt:
            return None

    def _has_keyring_support(self) -> bool:
        """Check if keyring is available."""
        try:
            keyring.get_keyring()
            return True
        except Exception:
            return False

    def login(self, account: str = "default") -> Tuple[bool, str]:
        """Login to an account by setting environment variables.

        Args:
            account: Account name to login to

        Returns:
            Tuple of (success, message)
        """
        accounts = self._load_accounts()

        if account not in accounts:
            return False, f"Account '{account}' not found"

        account_info = accounts[account]
        provider = account_info["provider"]

        # Get API key from keyring or prompt
        api_key = None
        if account_info.get("has_keyring"):
            try:
                api_key = keyring.get_password(f"hanzo-{provider}", account)
            except Exception:
                pass

        if not api_key:
            # Try environment variable
            for env_var in self.ENV_VARS.get(provider, []):
                if env_var in os.environ:
                    api_key = os.environ[env_var]
                    break

        if not api_key:
            api_key = self._prompt_for_api_key(provider)
            if not api_key:
                return False, "No API key available"

        # Backup current environment
        self._backup_environment(provider)

        # Set environment variables
        for env_var in self.ENV_VARS.get(provider, []):
            os.environ[env_var] = api_key

        # Set active account
        self.set_active_account(account)

        # Update shell if using claude command
        self._update_claude_command(account_info)

        return True, f"Logged in as '{account}' ({provider})"

    def logout(self) -> Tuple[bool, str]:
        """Logout by clearing environment variables."""
        current = self.get_active_account()

        if not current or current == "default":
            return False, "No active session"

        accounts = self._load_accounts()
        if current not in accounts:
            return False, f"Unknown account: {current}"

        provider = accounts[current]["provider"]

        # Clear environment variables
        for env_var in self.ENV_VARS.get(provider, []):
            if env_var in os.environ:
                del os.environ[env_var]

        # Restore backed up environment if any
        self._restore_environment(provider)

        # Clear active account
        if self.ACTIVE_ACCOUNT_FILE.exists():
            self.ACTIVE_ACCOUNT_FILE.unlink()

        return True, f"Logged out from '{current}'"

    def _backup_environment(self, provider: str):
        """Backup current environment variables."""
        for env_var in self.ENV_VARS.get(provider, []):
            if env_var in os.environ:
                self._env_backup[env_var] = os.environ[env_var]

    def _restore_environment(self, provider: str):
        """Restore backed up environment variables."""
        for env_var in self.ENV_VARS.get(provider, []):
            if env_var in self._env_backup:
                os.environ[env_var] = self._env_backup[env_var]
                del self._env_backup[env_var]

    def _update_claude_command(self, account_info: Dict[str, Any]):
        """Update claude command configuration if needed."""
        # Check if claude command exists
        try:
            result = subprocess.run(["which", "claude"], capture_output=True, text=True)
            if result.returncode == 0:
                # Claude command exists, update its config
                claude_config = Path.home() / ".claude" / "config.json"
                if claude_config.exists():
                    try:
                        with open(claude_config, "r") as f:
                            config = json.load(f)

                        # Update model if specified
                        if account_info.get("model"):
                            config["default_model"] = account_info["model"]

                        with open(claude_config, "w") as f:
                            json.dump(config, f, indent=2)
                    except Exception:
                        pass
        except Exception:
            pass

    def switch_account(self, account: str) -> Tuple[bool, str]:
        """Switch to a different account."""
        # Logout current
        self.logout()

        # Login to new account
        return self.login(account)

    def create_agent_account(
        self,
        agent_id: str,
        provider: str = "claude",
        parent_account: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Create an account for a swarm agent.

        Args:
            agent_id: Unique agent identifier
            provider: AI provider
            parent_account: Parent account to clone from

        Returns:
            Tuple of (success, account_name)
        """
        agent_account = f"agent_{agent_id}"

        # If parent account specified, clone its credentials
        if parent_account:
            parent_info = self.get_account_info(parent_account)
            if not parent_info:
                return False, f"Parent account '{parent_account}' not found"

            # Get parent API key
            api_key = None
            if parent_info.get("has_keyring"):
                try:
                    api_key = keyring.get_password(
                        f"hanzo-{parent_info['provider']}", parent_account
                    )
                except Exception:
                    pass

            if api_key:
                success, msg = self.create_account(
                    agent_account,
                    provider=parent_info["provider"],
                    api_key=api_key,
                    model=parent_info.get("model"),
                    description=f"Agent account (parent: {parent_account})",
                )
                if success:
                    return True, agent_account

        # Create with current environment
        for env_var in self.ENV_VARS.get(provider, []):
            if env_var in os.environ:
                success, msg = self.create_account(
                    agent_account,
                    provider=provider,
                    api_key=os.environ[env_var],
                    model=self.DEFAULT_MODELS.get(provider),
                    description=f"Agent account for {agent_id}",
                )
                if success:
                    return True, agent_account

        return False, "No credentials available for agent"

    def get_agent_credentials(self, agent_id: str) -> Optional[APICredential]:
        """Get credentials for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            APICredential if found
        """
        agent_account = f"agent_{agent_id}"
        account_info = self.get_account_info(agent_account)

        if not account_info:
            return None

        # Get API key
        api_key = None
        provider = account_info["provider"]

        if account_info.get("has_keyring"):
            try:
                api_key = keyring.get_password(f"hanzo-{provider}", agent_account)
            except Exception:
                pass

        if not api_key:
            # Try current environment
            for env_var in self.ENV_VARS.get(provider, []):
                if env_var in os.environ:
                    api_key = os.environ[env_var]
                    break

        if not api_key:
            return None

        return APICredential(
            provider=provider,
            api_key=api_key,
            model=account_info.get("model"),
            description=account_info.get("description"),
        )


# Update swarm tool to use latest Sonnet
def get_latest_claude_model() -> str:
    """Get the latest Claude model identifier."""
    # As of the knowledge cutoff, this is the latest Sonnet
    # In production, this could query an API for the latest model
    return "claude-3-5-sonnet-20241022"


# Token counting using tiktoken (same as current implementation)
def count_tokens_streaming(text_stream) -> int:
    """Count tokens in a streaming fashion.

    This uses the same tiktoken approach as the truncate module,
    but processes text as it streams.
    """
    import tiktoken

    try:
        # Use cl100k_base encoding (Claude/GPT-4 compatible)
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback to simple estimation
        return len(text_stream) // 4

    total_tokens = 0
    for chunk in text_stream:
        if isinstance(chunk, str):
            total_tokens += len(encoding.encode(chunk))
        elif isinstance(chunk, bytes):
            total_tokens += len(encoding.encode(chunk.decode("utf-8", errors="ignore")))

    return total_tokens
