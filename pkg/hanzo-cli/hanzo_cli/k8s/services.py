"""Service status and rollout management for Hanzo K8s CLI.

Uses kubectl to query pod and deployment status and displays results
in rich tables.

Usage:
    hanzo k8s services                     # List pods in default namespace
    hanzo k8s services --namespace kube-system
    hanzo k8s rollout <deployment>         # Restart a deployment
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _find_kubectl() -> str:
    """Locate kubectl or exit."""
    path = shutil.which("kubectl")
    if not path:
        console.print(
            "[red]kubectl not found.[/red] "
            "Install: https://kubernetes.io/docs/tasks/tools/"
        )
        sys.exit(1)
    return path


def _kubectl_json(args: list[str]) -> dict | list:
    """Run kubectl with -o json and return parsed output."""
    kubectl = _find_kubectl()
    cmd = [kubectl] + args + ["-o", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip()
        raise click.ClickException(f"kubectl failed: {err}")
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def _parse_age(timestamp: str) -> str:
    """Convert an ISO timestamp to a human-readable age string."""
    try:
        created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - created
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s"
        if total_seconds < 3600:
            return f"{total_seconds // 60}m"
        if total_seconds < 86400:
            return f"{total_seconds // 3600}h"
        days = total_seconds // 86400
        if days < 30:
            return f"{days}d"
        return f"{days // 30}mo"
    except (ValueError, TypeError):
        return "?"


def _status_style(phase: str) -> str:
    """Return rich style for a pod phase."""
    phase_lower = phase.lower()
    if phase_lower == "running":
        return "green"
    if phase_lower in ("pending", "containercreating"):
        return "yellow"
    if "error" in phase_lower or "crash" in phase_lower or "backoff" in phase_lower:
        return "red"
    if phase_lower in ("succeeded", "completed"):
        return "cyan"
    return "white"


@click.command("services")
@click.option(
    "--namespace",
    "-n",
    default=None,
    help="Kubernetes namespace (default: current cluster namespace).",
)
def services(namespace: str | None) -> None:
    """Show service status from pod information.

    Lists pods grouped by service (app label), showing replica counts,
    status, age, and restart counts.
    """
    if namespace is None:
        from hanzo_cli.k8s.clusters import get_current_cluster

        _, cluster_info = get_current_cluster()
        namespace = cluster_info.get("namespace", "hanzo")

    try:
        data = _kubectl_json(["get", "pods", "-n", namespace])
    except click.ClickException as e:
        console.print(f"[red]{e.message}[/red]")
        return

    items = data.get("items", [])
    if not items:
        console.print(f"[yellow]No pods found in namespace '{namespace}'.[/yellow]")
        return

    # Group pods by service name (app label)
    svc_map: dict[str, list[dict]] = {}
    for pod in items:
        labels = pod.get("metadata", {}).get("labels", {})
        svc_name = (
            labels.get("app")
            or labels.get("app.kubernetes.io/name")
            or labels.get("name")
            or pod.get("metadata", {}).get("name", "unknown")
        )
        svc_map.setdefault(svc_name, []).append(pod)

    table = Table(title=f"Services — {namespace}")
    table.add_column("Service", style="cyan", min_width=20)
    table.add_column("Ready", justify="center", min_width=8)
    table.add_column("Status", justify="center", min_width=14)
    table.add_column("Age", justify="right", min_width=6)
    table.add_column("Restarts", justify="right", min_width=9)

    for svc_name in sorted(svc_map.keys()):
        pods = svc_map[svc_name]
        total = len(pods)
        ready = 0
        total_restarts = 0
        worst_phase = "Running"

        for pod in pods:
            status = pod.get("status", {})
            phase = status.get("phase", "Unknown")

            # Check container statuses for more detail
            container_statuses = status.get("containerStatuses", [])
            pod_ready = True
            for cs in container_statuses:
                total_restarts += cs.get("restartCount", 0)
                if not cs.get("ready", False):
                    pod_ready = False
                # Detect CrashLoopBackOff
                waiting = cs.get("state", {}).get("waiting", {})
                reason = waiting.get("reason", "")
                if reason:
                    phase = reason

            if pod_ready and phase == "Running":
                ready += 1

            # Track worst phase for display
            if phase != "Running":
                worst_phase = phase

        # Pick display phase
        if ready == total:
            display_phase = "Running"
        elif ready > 0:
            display_phase = f"{worst_phase}" if worst_phase != "Running" else "Partial"
        else:
            display_phase = worst_phase

        style = _status_style(display_phase)
        ready_str = f"{ready}/{total}"

        # Age from oldest pod
        oldest = min(
            (
                p.get("metadata", {}).get("creationTimestamp", "")
                for p in pods
            ),
            default="",
        )
        age_str = _parse_age(oldest) if oldest else "?"

        restart_style = "red" if total_restarts > 10 else "yellow" if total_restarts > 0 else "dim"

        table.add_row(
            svc_name,
            ready_str,
            f"[{style}]{display_phase}[/{style}]",
            age_str,
            f"[{restart_style}]{total_restarts}[/{restart_style}]",
        )

    console.print(table)
    console.print(f"\n{len(svc_map)} service(s), {len(items)} pod(s)")


@click.command("rollout")
@click.argument("deployment")
@click.option(
    "--namespace",
    "-n",
    default=None,
    help="Kubernetes namespace (default: current cluster namespace).",
)
def rollout(deployment: str, namespace: str | None) -> None:
    """Trigger a rolling restart of a deployment.

    Runs `kubectl rollout restart deployment/<name>` in the specified
    namespace.
    """
    if namespace is None:
        from hanzo_cli.k8s.clusters import get_current_cluster

        _, cluster_info = get_current_cluster()
        namespace = cluster_info.get("namespace", "hanzo")

    kubectl = _find_kubectl()
    resource = deployment if "/" in deployment else f"deployment/{deployment}"

    console.print(
        f"Restarting [cyan]{resource}[/cyan] in namespace [cyan]{namespace}[/cyan]..."
    )

    result = subprocess.run(
        [kubectl, "rollout", "restart", resource, "-n", namespace],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        console.print(f"[red]Failed:[/red] {result.stderr.strip()}")
        raise SystemExit(1)

    console.print(f"[green]{result.stdout.strip()}[/green]")
