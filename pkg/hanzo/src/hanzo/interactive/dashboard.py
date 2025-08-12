"""Dashboard interface for Hanzo CLI."""

from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.console import Console


def run_dashboard(refresh_rate: float = 1.0):
    """Run the interactive dashboard."""
    console = Console()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )

    layout["header"].update(
        Panel(
            Text("Hanzo AI Dashboard", style="bold cyan", justify="center"),
            border_style="cyan",
        )
    )

    layout["body"].split_row(Layout(name="left"), Layout(name="right"))

    layout["left"].split_column(Layout(name="cluster", size=10), Layout(name="agents"))

    layout["right"].split_column(Layout(name="jobs", size=15), Layout(name="logs"))

    def get_cluster_panel() -> Panel:
        """Get cluster status panel."""
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        # Mock data - would be real in production
        table.add_row("Status", "[green]Running[/green]")
        table.add_row("Nodes", "3")
        table.add_row("Models", "llama-3.2-3b, gpt-4")
        table.add_row("Port", "8000")

        return Panel(table, title="Cluster", border_style="green")

    def get_agents_panel() -> Panel:
        """Get agents panel."""
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Jobs", style="magenta")

        # Mock data
        table.add_row("a1b2", "researcher", "idle", "42")
        table.add_row("c3d4", "coder", "busy", "17")
        table.add_row("e5f6", "analyst", "idle", "23")

        return Panel(table, title="Agents", border_style="blue")

    def get_jobs_panel() -> Panel:
        """Get jobs panel."""
        table = Table()
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")

        # Mock data
        table.add_row("j001", "chat", "complete")
        table.add_row("j002", "analysis", "running")
        table.add_row("j003", "search", "queued")

        return Panel(table, title="Recent Jobs", border_style="yellow")

    def get_logs_panel() -> Panel:
        """Get logs panel."""
        logs = """[dim]2024-01-20 10:15:23[/dim] Agent started: researcher
[dim]2024-01-20 10:15:24[/dim] Job j002 assigned to coder
[dim]2024-01-20 10:15:25[/dim] Model loaded: llama-3.2-3b
[dim]2024-01-20 10:15:26[/dim] Network peer connected: node-2
[dim]2024-01-20 10:15:27[/dim] Job j001 completed (2.3s)"""

        return Panel(logs, title="Logs", border_style="dim")

    layout["footer"].update(
        Panel(
            "[bold]Q[/bold] Quit  [bold]R[/bold] Refresh  [bold]C[/bold] Clear",
            border_style="dim",
        )
    )

    # Update panels
    layout["cluster"].update(get_cluster_panel())
    layout["agents"].update(get_agents_panel())
    layout["jobs"].update(get_jobs_panel())
    layout["logs"].update(get_logs_panel())

    try:
        with Live(layout, refresh_per_second=1 / refresh_rate, screen=True):
            while True:
                import time

                time.sleep(refresh_rate)

                # Update dynamic panels
                layout["cluster"].update(get_cluster_panel())
                layout["agents"].update(get_agents_panel())
                layout["jobs"].update(get_jobs_panel())
                layout["logs"].update(get_logs_panel())

    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard closed[/yellow]")
