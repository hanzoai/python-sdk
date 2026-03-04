"""DNS provider abstraction and registry."""

from __future__ import annotations

import sys
import json
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path
from dataclasses import field, dataclass

CREDENTIALS_FILE = Path.home() / ".hanzo" / "credentials.json"


@dataclass
class DNSRecord:
    """Normalized DNS record across all providers."""

    id: str
    zone: str
    type: str
    name: str
    content: str
    ttl: int = 1
    proxied: bool = False
    provider: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def ttl_display(self) -> str:
        return "Auto" if self.ttl == 1 else str(self.ttl)


@dataclass
class DNSZone:
    """Normalized DNS zone across all providers."""

    id: str
    name: str
    status: str = ""
    plan: str = ""
    provider: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class DNSProvider(ABC):
    """Abstract DNS provider interface."""

    name: str = "unknown"

    @abstractmethod
    def list_zones(self) -> list[DNSZone]:
        """List all DNS zones."""

    @abstractmethod
    def list_records(
        self, zone: str, record_type: str | None = None
    ) -> list[DNSRecord]:
        """List DNS records for a zone."""

    @abstractmethod
    def add_record(
        self,
        zone: str,
        name: str,
        content: str,
        record_type: str = "A",
        proxied: bool = True,
        ttl: int = 1,
    ) -> DNSRecord | None:
        """Add a DNS record. Returns the created record or None on failure."""

    @abstractmethod
    def remove_records(
        self, zone: str, name: str, record_type: str | None = None
    ) -> int:
        """Remove DNS records matching name. Returns count deleted."""

    @abstractmethod
    def update_records(
        self, zone: str, old_content: str, new_content: str, record_type: str = "A"
    ) -> tuple[int, int]:
        """Batch update records. Returns (updated, failed) counts."""


# ── Provider registry ────────────────────────────────────────────────


_REGISTRY: dict[str, type[DNSProvider]] = {}


def register_provider(name: str, cls: type[DNSProvider]) -> None:
    _REGISTRY[name] = cls


def get_provider(name: str, config: dict[str, Any]) -> DNSProvider:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown DNS provider: {name}. "
            f"Available: {', '.join(sorted(_REGISTRY.keys()))}"
        )
    return cls(config)


def list_providers() -> list[str]:
    return sorted(_REGISTRY.keys())


# ── Config loading ───────────────────────────────────────────────────


def load_dns_config() -> dict[str, dict[str, Any]]:
    """Load all DNS provider configs from ~/.hanzo/credentials.json.

    Supports both legacy format and new multi-provider format:

    Legacy:
        {"cloudflare": {"email": "...", "api_key": "..."}}

    Multi-provider:
        {"dns": {"cloudflare": {...}, "coredns": {...}, "route53": {...}}}

    Both can coexist — legacy cloudflare key is merged into dns.cloudflare.
    """
    if not CREDENTIALS_FILE.exists():
        return {}

    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    providers: dict[str, dict[str, Any]] = {}

    # New format: dns.{provider}
    dns_section = data.get("dns", {})
    if isinstance(dns_section, dict):
        for name, cfg in dns_section.items():
            if isinstance(cfg, dict) and cfg:
                providers[name] = cfg

    # Legacy: top-level cloudflare key
    cf_legacy = data.get("cloudflare", {})
    if isinstance(cf_legacy, dict) and cf_legacy.get("email") and cf_legacy.get("api_key"):
        providers.setdefault("cloudflare", {}).update(cf_legacy)

    return providers


def get_active_providers() -> list[DNSProvider]:
    """Load and instantiate all configured DNS providers."""
    configs = load_dns_config()
    providers = []

    for name, cfg in configs.items():
        if name not in _REGISTRY:
            continue
        try:
            providers.append(get_provider(name, cfg))
        except Exception:
            pass

    return providers


def require_providers() -> list[DNSProvider]:
    """Like get_active_providers but exits if none configured."""
    from ...utils.output import console

    providers = get_active_providers()
    if not providers:
        console.print(
            "[red]No DNS providers configured.[/red]\n"
            f"Add credentials to {CREDENTIALS_FILE}:\n\n"
            '  {{"dns": {{"cloudflare": {{"email": "...", "api_key": "..."}}}}}}\n\n'
            "Or legacy format:\n"
            '  {{"cloudflare": {{"email": "...", "api_key": "..."}}}}\n\n'
            f"Supported providers: {', '.join(list_providers())}"
        )
        sys.exit(1)

    return providers
