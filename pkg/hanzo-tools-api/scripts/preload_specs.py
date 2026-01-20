#!/usr/bin/env python3
"""Pre-download and cache popular OpenAPI specs for faster startup.

Usage:
    python scripts/preload_specs.py              # Download top 50 specs
    python scripts/preload_specs.py --all        # Download all specs with URLs
    python scripts/preload_specs.py --list       # List available specs
    python scripts/preload_specs.py github stripe  # Download specific specs
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from hanzo_tools.api.client import APIClient
from hanzo_tools.api.providers import list_providers_with_specs, get_provider_config

# Top 50 most popular APIs to pre-cache
POPULAR_APIS = [
    # AI/ML
    "openai", "anthropic", "together", "groq", "mistral", "cohere", "replicate",
    # Developer
    "github", "gitlab", "bitbucket", "vercel", "netlify", "fly", "railway", "render",
    # Cloud
    "cloudflare", "digitalocean", "hetzner", "linode", "vultr",
    # Payment
    "stripe", "paypal", "adyen-com-accountservice", "square",
    # Communication
    "twilio", "sendgrid", "resend", "slack", "discord",
    # Databases
    "supabase", "neon", "planetscale", "mongodb", "redis",
    # Search
    "algolia", "elasticsearch", "meilisearch", "typesense",
    # Monitoring
    "datadog", "sentry", "newrelic",
    # Other popular
    "notion", "airtable", "hubspot", "shopify", "jira",
]


async def preload_specs(
    providers: list[str] | None = None,
    concurrent: int = 10,
    verbose: bool = True,
) -> dict[str, bool]:
    """Pre-download and cache OpenAPI specs.

    Args:
        providers: List of provider names, or None for POPULAR_APIS
        concurrent: Number of concurrent downloads
        verbose: Print progress

    Returns:
        Dict mapping provider name to success status
    """
    client = APIClient()

    if providers is None:
        providers = POPULAR_APIS

    # Filter to only those with spec URLs
    valid_providers = []
    for p in providers:
        config = get_provider_config(p)
        if config and config.spec_url:
            valid_providers.append(p)
        elif verbose:
            print(f"  ⚠ {p}: no spec URL configured")

    if verbose:
        print(f"Pre-loading {len(valid_providers)} OpenAPI specs...")
        print()

    results: dict[str, bool] = {}
    semaphore = asyncio.Semaphore(concurrent)

    async def fetch_one(provider: str) -> tuple[str, bool]:
        async with semaphore:
            try:
                await client.spec(provider)
                if verbose:
                    print(f"  ✓ {provider}")
                return provider, True
            except Exception as e:
                if verbose:
                    print(f"  ✗ {provider}: {e}")
                return provider, False

    tasks = [fetch_one(p) for p in valid_providers]
    for coro in asyncio.as_completed(tasks):
        provider, success = await coro
        results[provider] = success

    if verbose:
        success_count = sum(1 for v in results.values() if v)
        print()
        print(f"Downloaded {success_count}/{len(results)} specs")
        print(f"Cached at: {client._spec_cache.cache_dir}")

    return results


async def main():
    parser = argparse.ArgumentParser(description="Pre-download OpenAPI specs")
    parser.add_argument("providers", nargs="*", help="Specific providers to download")
    parser.add_argument("--all", action="store_true", help="Download all available specs")
    parser.add_argument("--list", action="store_true", help="List available specs")
    parser.add_argument("-n", "--concurrent", type=int, default=10, help="Concurrent downloads")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    if args.list:
        specs = list_providers_with_specs()
        print(f"Available specs ({len(specs)}):")
        for i, name in enumerate(specs, 1):
            config = get_provider_config(name)
            display = config.display_name if config else name
            print(f"  {i:4}. {name}: {display}")
        return

    providers = None
    if args.providers:
        providers = args.providers
    elif args.all:
        providers = list_providers_with_specs()

    await preload_specs(
        providers=providers,
        concurrent=args.concurrent,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    asyncio.run(main())
