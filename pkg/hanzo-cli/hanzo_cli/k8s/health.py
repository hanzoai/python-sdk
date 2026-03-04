"""Service health checks for Hanzo K8s CLI.

Runs concurrent HTTP health checks against known domains and displays
results in a rich table with color-coded status.

Usage:
    hanzo k8s health                        # Check default cluster domains
    hanzo k8s health --cluster adnexus      # Check a specific cluster
    hanzo k8s health --timeout 10           # Custom timeout
"""

from __future__ import annotations

import asyncio
import time

import click
import httpx
from rich.console import Console
from rich.table import Table

console = Console()

# Known domains per cluster
CLUSTER_DOMAINS: dict[str, list[str]] = {
    "hanzo": [
        "billing.hanzo.ai",
        "console.hanzo.ai",
        "api.hanzo.ai",
        "hanzo.chat",
        "kms.hanzo.ai",
        "models.hanzo.ai",
        "platform.hanzo.ai",
        "pricing.hanzo.ai",
        "status.hanzo.ai",
        "analytics.hanzo.ai",
        "hanzo.id",
        "hanzo.bot",
        "mpc.hanzo.ai",
        "cloud.hanzo.ai",
        "s3.hanzo.ai",
        "search.hanzo.ai",
        "gateway.hanzo.ai",
        "hanzo.space",
    ],
    "adnexus": [
        "ad.nexus",
        "api.ad.nexus",
        "api-ai.ad.nexus",
        "dsp.ad.nexus",
        "ssp.ad.nexus",
        "docs.ad.nexus",
        "grafana.ad.nexus",
        "id.ad.nexus",
    ],
    "lux": [
        "lux.network",
        "lux.id",
    ],
    "zoo": [
        "zoo.ngo",
        "zips.zoo.ngo",
    ],
}


async def _check_domain(
    client: httpx.AsyncClient, domain: str
) -> tuple[str, int, float, str]:
    """Check a single domain. Returns (domain, status, latency_ms, error)."""
    url = f"https://{domain}/"
    t0 = time.monotonic()
    try:
        resp = await client.get(url, follow_redirects=True)
        latency = (time.monotonic() - t0) * 1000
        return domain, resp.status_code, latency, ""
    except httpx.TimeoutException:
        latency = (time.monotonic() - t0) * 1000
        return domain, 0, latency, "timeout"
    except httpx.ConnectError as e:
        latency = (time.monotonic() - t0) * 1000
        return domain, 0, latency, f"connect: {e}"
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        return domain, 0, latency, str(e)


async def _run_checks(
    domains: list[str], timeout: float
) -> list[tuple[str, int, float, str]]:
    """Run health checks concurrently against all domains."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        verify=False,  # Some services may have cert issues
        headers={"User-Agent": "hanzo-cli/health"},
    ) as client:
        tasks = [_check_domain(client, d) for d in domains]
        return await asyncio.gather(*tasks)


def _status_style(code: int, error: str) -> str:
    """Return rich style string for a status code."""
    if error:
        return "bold red"
    if 200 <= code < 300:
        return "bold green"
    if 300 <= code < 400:
        return "yellow"
    if 400 <= code < 500:
        return "yellow"
    return "bold red"


def _status_text(code: int, error: str) -> str:
    """Return display text for status."""
    if error:
        return error[:30]
    return str(code)


@click.command("health")
@click.option(
    "--cluster",
    "-c",
    default=None,
    help="Cluster name (default: current cluster).",
)
@click.option(
    "--timeout",
    "-t",
    default=15.0,
    type=float,
    help="HTTP timeout in seconds (default: 15).",
)
def health(cluster: str | None, timeout: float) -> None:
    """Run HTTP health checks against cluster services.

    Checks all known domains for the specified cluster (or the current
    active cluster) and displays a table with status codes and latency.
    """
    # Resolve cluster name
    if cluster is None:
        from hanzo_cli.k8s.clusters import get_current_cluster

        cluster, _ = get_current_cluster()

    domains = CLUSTER_DOMAINS.get(cluster, [])
    if not domains:
        available = ", ".join(sorted(CLUSTER_DOMAINS.keys()))
        console.print(
            f"[yellow]No domains configured for cluster '{cluster}'.[/yellow]"
        )
        console.print(f"Known clusters with domains: {available}")
        return

    console.print(
        f"Checking [cyan]{len(domains)}[/cyan] domains for "
        f"[bold]{cluster}[/bold] (timeout: {timeout}s)...\n"
    )

    # Run async checks
    results = asyncio.run(_run_checks(domains, timeout))

    # Sort: errors first, then by status code descending, then by domain
    results.sort(key=lambda r: (r[3] == "", r[1], r[0]))

    # Build table
    table = Table(title=f"Health — {cluster}")
    table.add_column("Domain", style="cyan", min_width=25)
    table.add_column("Status", justify="center", min_width=8)
    table.add_column("Latency", justify="right", min_width=10)
    table.add_column("Note", style="dim")

    ok_count = 0
    for domain, code, latency_ms, error in results:
        style = _status_style(code, error)
        status_text = _status_text(code, error)

        if latency_ms >= 5000:
            latency_str = f"[red]{latency_ms:.0f}ms[/red]"
        elif latency_ms >= 1000:
            latency_str = f"[yellow]{latency_ms:.0f}ms[/yellow]"
        else:
            latency_str = f"{latency_ms:.0f}ms"

        note = ""
        if error:
            note = error[:50]
        elif code >= 400:
            note = "client/server error"

        if not error and 200 <= code < 400:
            ok_count += 1

        table.add_row(domain, f"[{style}]{status_text}[/{style}]", latency_str, note)

    console.print(table)

    total = len(results)
    if ok_count == total:
        console.print(f"\n[bold green]All {total} services healthy.[/bold green]")
    else:
        console.print(
            f"\n[bold]{ok_count}/{total}[/bold] healthy, "
            f"[red]{total - ok_count} issues[/red]"
        )
