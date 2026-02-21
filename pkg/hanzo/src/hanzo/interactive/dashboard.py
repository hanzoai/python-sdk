"""Dashboard interface for Hanzo CLI."""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.console import Console


def _get_cluster_status() -> Optional[Dict[str, Any]]:
    """Get cluster status from API. Returns None if not connected."""
    try:
        import json
        import urllib.request

        endpoint = os.getenv("HANZO_CLUSTER_URL", "http://localhost:8000")
        req = urllib.request.urlopen(f"{endpoint}/health", timeout=2)  # noqa: S310
        return json.loads(req.read().decode())
    except Exception:
        return None


def _get_agents() -> List[Dict[str, Any]]:
    """Get agents from registry. Returns empty list if not available."""
    try:
        from hanzoai.agents import list_agents

        return list_agents() or []
    except Exception:
        return []


def _get_jobs() -> List[Dict[str, Any]]:
    """Get recent jobs. Returns empty list if not available."""
    try:
        import json
        import urllib.request

        endpoint = os.getenv("HANZO_CLUSTER_URL", "http://localhost:8000")
        req = urllib.request.urlopen(f"{endpoint}/jobs?limit=5", timeout=2)  # noqa: S310
        return json.loads(req.read().decode()).get("jobs", [])
    except Exception:
        return []


def _get_logs() -> List[str]:
    """Get recent logs. Returns empty list if not available."""
    try:
        import json
        import urllib.request

        endpoint = os.getenv("HANZO_CLUSTER_URL", "http://localhost:8000")
        req = urllib.request.urlopen(f"{endpoint}/logs?limit=5", timeout=2)  # noqa: S310
        return json.loads(req.read().decode()).get("logs", [])
    except Exception:
        return []


def run_dashboard(refresh_rate: float = 1.0):
    """Run the interactive dashboard."""
    console = Console()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )

    layout["body"].split_row(Layout(name="left"), Layout(name="right"))
    layout["left"].split_column(Layout(name="cluster", size=10), Layout(name="agents"))
    layout["right"].split_column(Layout(name="jobs", size=15), Layout(name="logs"))

    def get_header() -> Panel:
        """Get header with connection status."""
        cluster = _get_cluster_status()
        header_text = Text()
        header_text.append("Hanzo AI Dashboard", style="bold cyan")

        if cluster:
            header_text.append("  [CONNECTED]", style="bold green")
            border = "green"
        else:
            header_text.append("  [DISCONNECTED]", style="bold red")
            border = "red"

        return Panel(header_text, border_style=border)

    def get_cluster_panel() -> Panel:
        """Get cluster status panel."""
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        cluster = _get_cluster_status()
        if cluster:
            table.add_row("Status", f"[green]{cluster.get('status', 'unknown')}[/green]")
            table.add_row("Nodes", str(cluster.get("nodes", 0)))
            table.add_row("Models", ", ".join(cluster.get("models", [])) or "none")
            table.add_row("Port", str(cluster.get("port", "-")))
            border = "green"
        else:
            table.add_row("Status", "[red]Not connected[/red]")
            table.add_row("", "[dim]Set HANZO_CLUSTER_URL[/dim]")
            border = "dim"

        return Panel(table, title="Cluster", border_style=border)

    def get_agents_panel() -> Panel:
        """Get agents panel."""
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Jobs", style="magenta")

        agents = _get_agents()
        if agents:
            for agent in agents[:5]:
                table.add_row(
                    agent.get("id", "-")[:4],
                    agent.get("name", "unknown"),
                    agent.get("status", "unknown"),
                    str(agent.get("jobs", 0)),
                )
            border = "blue"
        else:
            table.add_row("-", "[dim]No agents[/dim]", "-", "-")
            border = "dim"

        return Panel(table, title="Agents", border_style=border)

    def get_jobs_panel() -> Panel:
        """Get jobs panel."""
        table = Table()
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")

        jobs = _get_jobs()
        if jobs:
            for job in jobs[:5]:
                table.add_row(
                    job.get("id", "-")[:6],
                    job.get("type", "unknown"),
                    job.get("status", "unknown"),
                )
            border = "yellow"
        else:
            table.add_row("-", "[dim]No jobs[/dim]", "-")
            border = "dim"

        return Panel(table, title="Recent Jobs", border_style=border)

    def get_logs_panel() -> Panel:
        """Get logs panel."""
        logs = _get_logs()
        if logs:
            log_text = "\n".join(f"[dim]{log.get('time', '')}[/dim] {log.get('message', '')}" for log in logs[:5])
            border = "dim"
        else:
            log_text = "[dim]No logs available[/dim]"
            border = "dim"

        return Panel(log_text, title="Logs", border_style=border)

    layout["footer"].update(
        Panel(
            "[bold]Q[/bold] Quit  [bold]R[/bold] Refresh  [bold]C[/bold] Clear",
            border_style="dim",
        )
    )

    # Initial update
    layout["header"].update(get_header())
    layout["cluster"].update(get_cluster_panel())
    layout["agents"].update(get_agents_panel())
    layout["jobs"].update(get_jobs_panel())
    layout["logs"].update(get_logs_panel())

    try:
        with Live(layout, refresh_per_second=1 / refresh_rate, screen=True):
            while True:
                import time

                time.sleep(refresh_rate)

                # Update all panels with real data
                layout["header"].update(get_header())
                layout["cluster"].update(get_cluster_panel())
                layout["agents"].update(get_agents_panel())
                layout["jobs"].update(get_jobs_panel())
                layout["logs"].update(get_logs_panel())

    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard closed[/yellow]")
