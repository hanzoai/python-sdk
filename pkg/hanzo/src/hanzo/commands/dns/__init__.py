"""Hanzo DNS — Multi-provider DNS management.

Unified DNS interface that routes to any configured provider:
Cloudflare, CoreDNS, Route53, GoDaddy, DigitalOcean, etc.

All providers queried in parallel, results merged.
"""

from .cli import dns_group

__all__ = ["dns_group"]
