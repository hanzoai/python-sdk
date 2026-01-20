"""Credential manager with pluggable storage.

Provides unified credential management with:
- Explicit resolution order (override > memory > file > env)
- Pluggable storage backends
- Clear source introspection
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from .models import Credential, CredentialSource, EffectiveCredential, ProviderConfig, ProviderStatus
from .providers import PROVIDER_CONFIGS, ENV_VAR_MAPPINGS, get_env_vars, get_provider_config
from .storage import (
    CredentialStorage,
    ChainedCredentialStorage,
    FileCredentialStorage,
    EnvironmentCredentialStorage,
    MemoryCredentialStorage,
)
from .errors import CredentialError

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages API credentials with explicit resolution order.

    Resolution order:
    1. Per-call overrides (via override_for_provider)
    2. In-memory config (set at runtime)
    3. Stored file (~/.hanzo/api/credentials.json)
    4. Environment variables

    Example:
        manager = CredentialManager()

        # Check what credentials are available
        effective = await manager.get_effective_credentials("cloudflare")
        print(f"Source: {effective.source}")  # e.g., "environment"

        # Configure credentials
        await manager.set_credential("cloudflare", api_key="my-key")

        # Make a call with per-call override
        async with manager.override_for_provider("cloudflare", api_key="temp-key"):
            # Uses temp-key for this call only
            cred = await manager.get_credential("cloudflare")
    """

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        storage: Optional[CredentialStorage] = None,
    ):
        """Initialize credential manager.

        Args:
            config_dir: Directory for file storage. Defaults to ~/.hanzo/api/
            storage: Custom storage backend. If None, uses default chain.
        """
        self.config_dir = config_dir or Path.home() / ".hanzo" / "api"
        self.specs_dir = self.config_dir / "specs"

        # Set up storage chain
        # Note: MemoryCredentialStorage is NOT included here because
        # per-call overrides are handled separately by self._overrides
        if storage:
            self._storage = storage
        else:
            file_path = self.config_dir / "credentials.json"
            self._storage = ChainedCredentialStorage([
                FileCredentialStorage(file_path),  # Persistent storage
                EnvironmentCredentialStorage(ENV_VAR_MAPPINGS),  # Read-only fallback
            ])

        # Separate override storage for context manager
        self._overrides = MemoryCredentialStorage()

    async def get_credential(self, provider: str) -> Credential:
        """Get credential for a provider.

        Args:
            provider: Provider name

        Returns:
            Credential (may be empty if not found)
        """
        effective = await self.get_effective_credentials(provider)
        return effective.credential

    async def get_effective_credentials(self, provider: str) -> EffectiveCredential:
        """Get credential with full resolution info.

        Shows exactly where the credential came from and what
        alternatives are available.

        Args:
            provider: Provider name

        Returns:
            EffectiveCredential with source information
        """
        # Check overrides first
        override = await self._overrides.get(provider)
        if override and override.has_credentials:
            return EffectiveCredential(
                credential=override,
                source=CredentialSource.OVERRIDE,
            )

        # Check chained storage
        if isinstance(self._storage, ChainedCredentialStorage):
            cred, store = await self._storage.get_with_source(provider)
            if cred and cred.has_credentials:
                source = CredentialSource.NONE
                env_var = None

                if isinstance(store, MemoryCredentialStorage):
                    source = CredentialSource.MEMORY
                elif isinstance(store, FileCredentialStorage):
                    source = CredentialSource.STORED
                elif isinstance(store, EnvironmentCredentialStorage):
                    source = CredentialSource.ENVIRONMENT
                    # Find which env var was used
                    for var in get_env_vars(provider):
                        if os.environ.get(var):
                            env_var = var
                            break

                return EffectiveCredential(
                    credential=cred,
                    source=source,
                    env_var_used=env_var,
                )
        else:
            cred = await self._storage.get(provider)
            if cred and cred.has_credentials:
                return EffectiveCredential(
                    credential=cred,
                    source=CredentialSource.STORED,
                )

        # Check provider config for base URL
        config = get_provider_config(provider)
        base_url = config.base_url if config else None

        return EffectiveCredential(
            credential=Credential(provider=provider, base_url=base_url),
            source=CredentialSource.NONE,
        )

    async def set_credential(
        self,
        provider: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra,
    ) -> None:
        """Store a credential.

        Args:
            provider: Provider name
            api_key: API key or token
            api_secret: API secret (for providers that need it)
            account_id: Account/organization ID
            base_url: Custom base URL override
            **extra: Additional provider-specific fields
        """
        # Get existing to merge
        existing = await self._storage.get(provider)

        credential = Credential(
            provider=provider,
            api_key=api_key or (existing.api_key if existing else None),
            api_secret=api_secret or (existing.api_secret if existing else None),
            account_id=account_id or (existing.account_id if existing else None),
            base_url=base_url or (existing.base_url if existing else None),
            extra={**(existing.extra if existing else {}), **extra},
        )

        await self._storage.set(credential)

    async def delete_credential(self, provider: str) -> bool:
        """Delete a stored credential.

        Args:
            provider: Provider name

        Returns:
            True if deleted, False if not found
        """
        return await self._storage.delete(provider)

    async def list_credentials(self) -> list[str]:
        """List all providers with stored credentials."""
        return await self._storage.list()

    async def list_providers(self) -> list[ProviderStatus]:
        """List all providers and their status.

        Returns:
            List of provider status objects
        """
        result = []
        all_providers = set(PROVIDER_CONFIGS.keys()) | set(ENV_VAR_MAPPINGS.keys())

        # Add stored providers too
        stored = await self._storage.list()
        all_providers.update(stored)

        for provider in sorted(all_providers):
            effective = await self.get_effective_credentials(provider)
            config = get_provider_config(provider)

            # Check spec cache
            spec_cached = False
            spec_age = None
            spec_file = self.specs_dir / f"{provider}.json"
            if spec_file.exists():
                spec_cached = True
                import time

                spec_age = time.time() - spec_file.stat().st_mtime

            result.append(
                ProviderStatus(
                    name=provider,
                    display_name=config.display_name if config else provider.title(),
                    configured=effective.has_credentials,
                    source=effective.source if effective.has_credentials else None,
                    base_url=config.base_url if config else "",
                    has_spec=bool(config and config.spec_url),
                    spec_cached=spec_cached,
                    spec_age_seconds=spec_age,
                )
            )

        return result

    async def require_credential(self, provider: str) -> Credential:
        """Get credential or raise CredentialError.

        Args:
            provider: Provider name

        Returns:
            Credential with valid api_key

        Raises:
            CredentialError: If no credential is configured
        """
        effective = await self.get_effective_credentials(provider)

        if not effective.has_credentials:
            env_vars = get_env_vars(provider)
            raise CredentialError(
                message=f"No credentials configured for {provider}",
                provider=provider,
                env_vars=env_vars,
            )

        return effective.credential

    def get_provider_config(self, provider: str) -> Optional[ProviderConfig]:
        """Get provider configuration."""
        return get_provider_config(provider)


# Singleton instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def reset_credential_manager() -> None:
    """Reset the global credential manager (for testing)."""
    global _credential_manager
    _credential_manager = None


# Re-export for backwards compatibility
__all__ = [
    "CredentialManager",
    "get_credential_manager",
    "reset_credential_manager",
    "Credential",
    "EffectiveCredential",
    "CredentialSource",
    "ProviderConfig",
    "ProviderStatus",
    "PROVIDER_CONFIGS",
    "ENV_VAR_MAPPINGS",
]
