"""Multi-cluster management for Hanzo K8s CLI.

Stores known clusters in ~/.hanzo/k8s/clusters.json and manages
the current active cluster context for kubectl operations.

Usage:
    hanzo k8s clusters          # List all clusters
    hanzo k8s use <name>        # Switch to a cluster
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

CLUSTERS_FILE = Path.home() / ".hanzo" / "k8s" / "clusters.json"

DEFAULT_CLUSTERS: dict = {
    "clusters": {
        "hanzo": {
            "context": "do-sfo3-hanzo-k8s",
            "namespace": "hanzo",
            "ip": "209.38.69.69",
        },
        "adnexus": {
            "context": "do-sfo3-adnexus-k8s",
            "namespace": "adnexus",
            "ip": "134.199.141.68",
        },
        "lux": {
            "context": "do-sfo3-lux-k8s",
            "namespace": "lux",
        },
        "pars": {
            "context": "do-sfo3-pars-k8s",
            "namespace": "pars",
        },
        "zoo": {
            "context": "do-sfo3-zoo-k8s",
            "namespace": "zoo",
        },
        "bootnode": {
            "context": "do-sfo3-bootnode-k8s",
            "namespace": "bootnode",
        },
    },
    "current": "hanzo",
}


def _load_clusters() -> dict:
    """Load clusters config, auto-creating with defaults on first use."""
    if CLUSTERS_FILE.exists():
        try:
            return json.loads(CLUSTERS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    _save_clusters(DEFAULT_CLUSTERS)
    return DEFAULT_CLUSTERS


def _save_clusters(data: dict) -> None:
    """Persist clusters config to disk."""
    CLUSTERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLUSTERS_FILE.write_text(json.dumps(data, indent=2))


def get_current_cluster() -> tuple[str, dict]:
    """Return (name, cluster_info) for the current active cluster."""
    config = _load_clusters()
    name = config.get("current", "hanzo")
    cluster = config.get("clusters", {}).get(name, {})
    return name, cluster


@click.command("clusters")
def clusters() -> None:
    """List all known Kubernetes clusters."""
    config = _load_clusters()
    current = config.get("current", "")
    cluster_map = config.get("clusters", {})

    if not cluster_map:
        console.print("[yellow]No clusters configured.[/yellow]")
        return

    table = Table(title="Kubernetes Clusters")
    table.add_column("", width=2)
    table.add_column("Name", style="cyan")
    table.add_column("Context", style="white")
    table.add_column("Namespace", style="green")
    table.add_column("IP", style="dim")

    for name, info in sorted(cluster_map.items()):
        marker = "[bold green]*[/bold green]" if name == current else ""
        table.add_row(
            marker,
            name,
            info.get("context", ""),
            info.get("namespace", ""),
            info.get("ip", ""),
        )

    console.print(table)
    console.print(f"\nCurrent: [bold cyan]{current}[/bold cyan]")


@click.command("use")
@click.argument("name")
def use(name: str) -> None:
    """Set the current Kubernetes cluster.

    Switches kubectl context and updates the default namespace for
    subsequent hanzo k8s commands.
    """
    config = _load_clusters()
    cluster_map = config.get("clusters", {})

    if name not in cluster_map:
        available = ", ".join(sorted(cluster_map.keys()))
        console.print(f"[red]Unknown cluster:[/red] {name}")
        console.print(f"Available: {available}")
        raise SystemExit(1)

    info = cluster_map[name]
    context = info.get("context", "")

    # Switch kubectl context
    if context:
        kubectl = shutil.which("kubectl")
        if kubectl:
            result = subprocess.run(
                [kubectl, "config", "use-context", context],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print(
                    f"[yellow]Warning:[/yellow] kubectl context switch failed: "
                    f"{result.stderr.strip()}"
                )
                console.print(
                    "You may need to add this context first with "
                    "'doctl kubernetes cluster kubeconfig save'"
                )
            else:
                console.print(f"Switched kubectl context to [cyan]{context}[/cyan]")
        else:
            console.print("[yellow]kubectl not found, skipping context switch.[/yellow]")

    # Update current cluster in config
    config["current"] = name
    _save_clusters(config)

    ns = info.get("namespace", name)
    console.print(f"Active cluster: [bold green]{name}[/bold green] (namespace: {ns})")
