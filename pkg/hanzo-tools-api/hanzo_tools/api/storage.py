"""Pluggable credential storage interface.

Provides abstractions for storing and retrieving credentials,
with built-in implementations for file storage and environment variables.

Custom implementations can integrate with KMS, 1Password, OS keychain, etc.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import aiofiles

from .models import Credential

logger = logging.getLogger(__name__)


class CredentialStorage(ABC):
    """Abstract interface for credential storage.

    Implement this interface to integrate custom secret stores
    (e.g., AWS Secrets Manager, HashiCorp Vault, 1Password, OS keychain).
    """

    @abstractmethod
    async def get(self, provider: str) -> Optional[Credential]:
        """Retrieve credential for a provider.

        Args:
            provider: Provider name

        Returns:
            Credential if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, credential: Credential) -> None:
        """Store a credential.

        Args:
            credential: Credential to store
        """
        pass

    @abstractmethod
    async def delete(self, provider: str) -> bool:
        """Delete a stored credential.

        Args:
            provider: Provider name

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list(self) -> list[str]:
        """List all stored provider names.

        Returns:
            List of provider names with stored credentials
        """
        pass


class FileCredentialStorage(CredentialStorage):
    """File-based credential storage with obfuscation.

    Stores credentials in a JSON file with basic base64 obfuscation
    and restrictive file permissions (0600).

    Note: This is NOT encryption. For production use with sensitive
    credentials, consider using a proper secrets manager.
    """

    def __init__(self, path: Optional[Path] = None):
        """Initialize file storage.

        Args:
            path: Path to credentials file. Defaults to ~/.hanzo/api/credentials.json
        """
        self.path = path or Path.home() / ".hanzo" / "api" / "credentials.json"
        self._cache: dict[str, Credential] = {}
        self._loaded = False

    def _ensure_dir(self) -> None:
        """Ensure parent directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _obfuscate(value: str) -> str:
        """Basic obfuscation for at-rest storage."""
        return base64.b64encode(value.encode()).decode()

    @staticmethod
    def _deobfuscate(value: str) -> str:
        """Reverse obfuscation."""
        try:
            return base64.b64decode(value.encode()).decode()
        except Exception:
            return value

    async def _load(self) -> None:
        """Load credentials from file."""
        if self._loaded:
            return

        self._ensure_dir()

        if self.path.exists():
            try:
                async with aiofiles.open(self.path, "r") as f:
                    content = await f.read()
                    data = json.loads(content)

                for name, cred_data in data.items():
                    # Deobfuscate sensitive fields
                    if cred_data.get("api_key"):
                        cred_data["api_key"] = self._deobfuscate(cred_data["api_key"])
                    if cred_data.get("api_secret"):
                        cred_data["api_secret"] = self._deobfuscate(cred_data["api_secret"])
                    self._cache[name] = Credential(**cred_data)

            except Exception as e:
                logger.warning(f"Failed to load credentials: {e}")

        self._loaded = True

    async def _save(self) -> None:
        """Save credentials to file."""
        self._ensure_dir()

        data = {}
        for name, cred in self._cache.items():
            cred_dict = cred.model_dump()
            # Obfuscate sensitive fields
            if cred_dict.get("api_key"):
                cred_dict["api_key"] = self._obfuscate(cred_dict["api_key"])
            if cred_dict.get("api_secret"):
                cred_dict["api_secret"] = self._obfuscate(cred_dict["api_secret"])
            data[name] = cred_dict

        async with aiofiles.open(self.path, "w") as f:
            await f.write(json.dumps(data, indent=2))

        # Set restrictive permissions
        self.path.chmod(0o600)

    async def get(self, provider: str) -> Optional[Credential]:
        await self._load()
        return self._cache.get(provider)

    async def set(self, credential: Credential) -> None:
        await self._load()
        self._cache[credential.provider] = credential
        await self._save()

    async def delete(self, provider: str) -> bool:
        await self._load()
        if provider in self._cache:
            del self._cache[provider]
            await self._save()
            return True
        return False

    async def list(self) -> list[str]:
        await self._load()
        return list(self._cache.keys())


class EnvironmentCredentialStorage(CredentialStorage):
    """Environment variable credential storage (read-only).

    Looks up credentials from environment variables based on
    provider-specific mappings.
    """

    def __init__(self, env_mappings: Optional[dict[str, list[str]]] = None):
        """Initialize environment storage.

        Args:
            env_mappings: Mapping of provider names to environment variable names
        """
        from .providers import ENV_VAR_MAPPINGS

        self.env_mappings = env_mappings or ENV_VAR_MAPPINGS

    async def get(self, provider: str) -> Optional[Credential]:
        env_vars = self.env_mappings.get(provider, [])

        for var in env_vars:
            value = os.environ.get(var)
            if value:
                logger.debug(f"Found credential for {provider} from env var {var}")
                return Credential(provider=provider, api_key=value)

        return None

    async def set(self, credential: Credential) -> None:
        """Environment storage is read-only."""
        raise NotImplementedError("Cannot write to environment storage")

    async def delete(self, provider: str) -> bool:
        """Environment storage is read-only."""
        raise NotImplementedError("Cannot delete from environment storage")

    async def list(self) -> list[str]:
        """List providers with credentials in environment."""
        result = []
        for provider, env_vars in self.env_mappings.items():
            for var in env_vars:
                if os.environ.get(var):
                    result.append(provider)
                    break
        return result


class MemoryCredentialStorage(CredentialStorage):
    """In-memory credential storage.

    Useful for per-call overrides and testing.
    Credentials are lost when the process exits.
    """

    def __init__(self):
        self._credentials: dict[str, Credential] = {}

    async def get(self, provider: str) -> Optional[Credential]:
        return self._credentials.get(provider)

    async def set(self, credential: Credential) -> None:
        self._credentials[credential.provider] = credential

    async def delete(self, provider: str) -> bool:
        if provider in self._credentials:
            del self._credentials[provider]
            return True
        return False

    async def list(self) -> list[str]:
        return list(self._credentials.keys())


class ChainedCredentialStorage(CredentialStorage):
    """Chains multiple credential stores with priority.

    Checks stores in order and returns the first match.
    Writes go to the first writable store.

    Default order:
    1. Memory (per-call overrides)
    2. File storage
    3. Environment variables
    """

    def __init__(self, stores: Optional[list[CredentialStorage]] = None):
        """Initialize chained storage.

        Args:
            stores: List of storage backends in priority order.
                   Defaults to [Memory, File, Environment].
        """
        if stores is None:
            stores = [
                MemoryCredentialStorage(),
                FileCredentialStorage(),
                EnvironmentCredentialStorage(),
            ]
        self.stores = stores

    async def get(self, provider: str) -> Optional[Credential]:
        """Get credential from first store that has it."""
        for store in self.stores:
            cred = await store.get(provider)
            if cred and cred.has_credentials:
                return cred
        return None

    async def get_with_source(self, provider: str) -> tuple[Optional[Credential], Optional[CredentialStorage]]:
        """Get credential and its source store."""
        for store in self.stores:
            cred = await store.get(provider)
            if cred and cred.has_credentials:
                return cred, store
        return None, None

    async def set(self, credential: Credential) -> None:
        """Store credential in first writable store."""
        for store in self.stores:
            try:
                await store.set(credential)
                return
            except NotImplementedError:
                continue
        raise RuntimeError("No writable credential store available")

    async def delete(self, provider: str) -> bool:
        """Delete from all writable stores."""
        deleted = False
        for store in self.stores:
            try:
                if await store.delete(provider):
                    deleted = True
            except NotImplementedError:
                continue
        return deleted

    async def list(self) -> list[str]:
        """List providers from all stores."""
        providers = set()
        for store in self.stores:
            providers.update(await store.list())
        return list(providers)
