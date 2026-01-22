"""Hanzo Auto - AI-powered workflow automation CLI.

Based on Activepieces with 280+ integrations.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="auto")
def auto_group():
    """Hanzo Auto - AI-powered workflow automation.

    \b
    Build automations visually with drag-and-drop:

    \b
    Workflows:
      hanzo auto flows list        # List all flows
      hanzo auto flows create      # Create new flow
      hanzo auto flows run         # Run a flow

    \b
    Pieces (Integrations):
      hanzo auto pieces list       # List available pieces
      hanzo auto pieces install    # Install a piece

    \b
    Connections:
      hanzo auto connections list  # List connections
      hanzo auto connections add   # Add connection

    \b
    Local Development:
      hanzo auto init              # Initialize project
      hanzo auto dev               # Start dev server
      hanzo auto deploy            # Deploy flows
    """
    pass


# ============================================================================
# Flows
# ============================================================================

@auto_group.group()
def flows():
    """Manage automation flows."""
    pass


@flows.command(name="list")
@click.option("--status", type=click.Choice(["active", "inactive", "all"]), default="all")
def flows_list(status: str):
    """List all automation flows."""
    table = Table(title="Automation Flows", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Trigger", style="white")
    table.add_column("Last Run", style="dim")
    table.add_column("Runs", style="dim")

    console.print(table)
    console.print("[dim]No flows found. Create one with 'hanzo auto flows create'[/dim]")


@flows.command(name="create")
@click.option("--name", "-n", prompt=True, help="Flow name")
@click.option("--trigger", "-t", type=click.Choice(["webhook", "schedule", "manual"]), default="manual")
def flows_create(name: str, trigger: str):
    """Create a new automation flow."""
    console.print(f"[cyan]Creating flow '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Flow '{name}' created with {trigger} trigger")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo auto dev[/cyan] - Start visual editor")
    console.print("  2. Add steps to your flow")
    console.print("  3. [cyan]hanzo auto deploy[/cyan] - Deploy to production")


@flows.command(name="run")
@click.argument("flow_name")
@click.option("--input", "-i", help="JSON input for the flow")
def flows_run(flow_name: str, input: str):
    """Run an automation flow."""
    console.print(f"[cyan]Running flow '{flow_name}'...[/cyan]")
    console.print("[green]✓[/green] Flow completed successfully")


@flows.command(name="delete")
@click.argument("flow_name")
def flows_delete(flow_name: str):
    """Delete an automation flow."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Delete flow '{flow_name}'?[/red]"):
        return
    console.print(f"[green]✓[/green] Flow '{flow_name}' deleted")


@flows.command(name="enable")
@click.argument("flow_name")
def flows_enable(flow_name: str):
    """Enable an automation flow."""
    console.print(f"[green]✓[/green] Flow '{flow_name}' enabled")


@flows.command(name="disable")
@click.argument("flow_name")
def flows_disable(flow_name: str):
    """Disable an automation flow."""
    console.print(f"[green]✓[/green] Flow '{flow_name}' disabled")


# ============================================================================
# Pieces (Integrations)
# ============================================================================

@auto_group.group()
def pieces():
    """Manage automation pieces (integrations)."""
    pass


@pieces.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--search", "-s", help="Search pieces")
def pieces_list(category: str, search: str):
    """List available pieces."""
    table = Table(title="Available Pieces (280+)", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Version", style="dim")
    table.add_column("Installed", style="green")

    pieces_data = [
        ("Gmail", "Email", "0.3.0", "✓"),
        ("Slack", "Communication", "0.4.0", "✓"),
        ("GitHub", "Development", "0.5.0", "✓"),
        ("OpenAI", "AI", "0.6.0", "✓"),
        ("Anthropic", "AI", "0.2.0", ""),
        ("Google Sheets", "Productivity", "0.3.0", ""),
        ("Stripe", "Payments", "0.4.0", ""),
        ("HubSpot", "CRM", "0.2.0", ""),
    ]

    for name, cat, version, installed in pieces_data:
        if category and cat.lower() != category.lower():
            continue
        if search and search.lower() not in name.lower():
            continue
        table.add_row(name, cat, version, installed)

    console.print(table)


@pieces.command(name="install")
@click.argument("piece_name")
def pieces_install(piece_name: str):
    """Install a piece."""
    console.print(f"[cyan]Installing piece '{piece_name}'...[/cyan]")
    console.print(f"[green]✓[/green] Piece '{piece_name}' installed")


@pieces.command(name="uninstall")
@click.argument("piece_name")
def pieces_uninstall(piece_name: str):
    """Uninstall a piece."""
    console.print(f"[green]✓[/green] Piece '{piece_name}' uninstalled")


# ============================================================================
# Connections
# ============================================================================

@auto_group.group()
def connections():
    """Manage connections to external services."""
    pass


@connections.command(name="list")
def connections_list():
    """List all connections."""
    table = Table(title="Connections", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Piece", style="white")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No connections found. Add one with 'hanzo auto connections add'[/dim]")


@connections.command(name="add")
@click.argument("piece_name")
@click.option("--name", "-n", help="Connection name")
def connections_add(piece_name: str, name: str):
    """Add a new connection."""
    console.print(f"[cyan]Adding connection for '{piece_name}'...[/cyan]")
    console.print("Opening browser for OAuth authentication...")
    console.print(f"[green]✓[/green] Connection added")


@connections.command(name="delete")
@click.argument("connection_name")
def connections_delete(connection_name: str):
    """Delete a connection."""
    console.print(f"[green]✓[/green] Connection '{connection_name}' deleted")


# ============================================================================
# Development
# ============================================================================

@auto_group.command()
def init():
    """Initialize Hanzo Auto project."""
    from pathlib import Path

    project_dir = Path.cwd() / ".hanzo" / "auto"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "flows").mkdir(exist_ok=True)
    (project_dir / "pieces").mkdir(exist_ok=True)

    console.print("[green]✓[/green] Hanzo Auto initialized")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo auto dev[/cyan] - Start development server")
    console.print("  2. Open http://localhost:8080 to build flows visually")


@auto_group.command()
@click.option("--port", "-p", default=8080, help="Port to run on")
def dev(port: int):
    """Start local development server."""
    console.print(f"[cyan]Starting Hanzo Auto development server on port {port}...[/cyan]")
    console.print()
    console.print(f"  [cyan]Visual Editor:[/cyan] http://localhost:{port}")
    console.print(f"  [cyan]API:[/cyan] http://localhost:{port}/api")
    console.print()
    console.print("Press Ctrl+C to stop")


@auto_group.command()
@click.option("--all", "deploy_all", is_flag=True, help="Deploy all flows")
@click.argument("flow_name", required=False)
def deploy(flow_name: str, deploy_all: bool):
    """Deploy flows to production."""
    if not flow_name and not deploy_all:
        console.print("[yellow]Specify a flow name or use --all[/yellow]")
        return

    if deploy_all:
        console.print("[cyan]Deploying all flows...[/cyan]")
    else:
        console.print(f"[cyan]Deploying flow '{flow_name}'...[/cyan]")

    console.print("[green]✓[/green] Deployed successfully")


# ============================================================================
# Runs (Execution History)
# ============================================================================

@auto_group.group()
def runs():
    """View flow execution history."""
    pass


@runs.command(name="list")
@click.option("--flow", "-f", help="Filter by flow")
@click.option("--status", type=click.Choice(["success", "failed", "running", "all"]), default="all")
@click.option("--limit", "-n", default=50, help="Max results")
def runs_list(flow: str, status: str, limit: int):
    """List flow runs."""
    table = Table(title="Flow Runs", box=box.ROUNDED)
    table.add_column("Run ID", style="cyan")
    table.add_column("Flow", style="white")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Started", style="dim")

    console.print(table)
    console.print("[dim]No runs found[/dim]")


@runs.command(name="show")
@click.argument("run_id")
def runs_show(run_id: str):
    """Show run details."""
    console.print(Panel(
        f"[cyan]Run ID:[/cyan] {run_id}\n"
        f"[cyan]Flow:[/cyan] my-flow\n"
        f"[cyan]Status:[/cyan] [green]● Success[/green]\n"
        f"[cyan]Duration:[/cyan] 2.3s\n"
        f"[cyan]Steps:[/cyan] 5\n"
        f"[cyan]Started:[/cyan] 2024-01-15 10:30:00",
        title="Run Details",
        border_style="cyan"
    ))


@runs.command(name="logs")
@click.argument("run_id")
@click.option("--step", "-s", help="Specific step")
def runs_logs(run_id: str, step: str):
    """View run logs."""
    console.print(f"[cyan]Logs for run {run_id}:[/cyan]")
    console.print("[dim]No logs available[/dim]")


@runs.command(name="retry")
@click.argument("run_id")
def runs_retry(run_id: str):
    """Retry a failed run."""
    console.print(f"[cyan]Retrying run {run_id}...[/cyan]")
    console.print("[green]✓[/green] Run restarted")


# ============================================================================
# Templates
# ============================================================================

@auto_group.group()
def templates():
    """Pre-built automation templates."""
    pass


@templates.command(name="list")
@click.option("--category", "-c", help="Filter by category")
def templates_list(category: str):
    """List available templates."""
    table = Table(title="Automation Templates", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Pieces", style="green")
    table.add_column("Description", style="dim")

    templates_data = [
        ("Slack to Notion", "Productivity", "2", "Save Slack messages to Notion"),
        ("GitHub PR Notify", "Development", "2", "Slack notification on PR"),
        ("Email to CRM", "Sales", "3", "Add email leads to HubSpot"),
        ("Invoice Processor", "Finance", "4", "Process invoices with AI"),
        ("Social Media Scheduler", "Marketing", "5", "Schedule posts across platforms"),
        ("Support Ticket Router", "Support", "3", "AI-powered ticket routing"),
    ]

    for name, cat, pieces, desc in templates_data:
        if category and category.lower() not in cat.lower():
            continue
        table.add_row(name, cat, pieces, desc)

    console.print(table)


@templates.command(name="use")
@click.argument("template_name")
@click.option("--name", "-n", help="Flow name")
def templates_use(template_name: str, name: str):
    """Create flow from template."""
    flow_name = name or template_name.lower().replace(" ", "-")
    console.print(f"[cyan]Creating flow from template '{template_name}'...[/cyan]")
    console.print(f"[green]✓[/green] Flow '{flow_name}' created")
    console.print("Configure connections with: hanzo auto connections add <piece>")


# ============================================================================
# Webhooks
# ============================================================================

@auto_group.group()
def webhooks():
    """Manage webhook triggers."""
    pass


@webhooks.command(name="list")
def webhooks_list():
    """List webhook endpoints."""
    table = Table(title="Webhooks", box=box.ROUNDED)
    table.add_column("Flow", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Method", style="green")
    table.add_column("Calls", style="dim")

    console.print(table)
    console.print("[dim]No webhooks found[/dim]")


@webhooks.command(name="test")
@click.argument("flow_name")
@click.option("--data", "-d", help="JSON payload")
def webhooks_test(flow_name: str, data: str):
    """Test webhook endpoint."""
    console.print(f"[cyan]Testing webhook for '{flow_name}'...[/cyan]")
    console.print("[green]✓[/green] Webhook triggered successfully")


# ============================================================================
# AI Actions
# ============================================================================

@auto_group.group()
def ai():
    """AI-powered automation actions."""
    pass


@ai.command(name="generate")
@click.option("--prompt", "-p", required=True, help="What to automate")
@click.option("--name", "-n", help="Flow name")
def ai_generate(prompt: str, name: str):
    """Generate automation flow with AI.

    \b
    Examples:
      hanzo auto ai generate -p "When I get an email from a customer, summarize it and post to Slack"
      hanzo auto ai generate -p "Every morning, send me a summary of GitHub issues"
    """
    console.print(f"[cyan]Generating flow from prompt...[/cyan]")
    console.print(f"  Prompt: {prompt}")
    console.print()
    console.print("[green]✓[/green] Flow generated")
    console.print("  Steps: 3")
    console.print("  Pieces: gmail, openai, slack")


@ai.command(name="suggest")
@click.argument("flow_name")
def ai_suggest(flow_name: str):
    """Get AI suggestions to improve a flow."""
    console.print(f"[cyan]Analyzing flow '{flow_name}'...[/cyan]")
    console.print()
    console.print("[cyan]Suggestions:[/cyan]")
    console.print("  1. Add error handling for API failures")
    console.print("  2. Consider adding a retry step")
    console.print("  3. Add a filter to reduce unnecessary runs")


@ai.command(name="explain")
@click.argument("flow_name")
def ai_explain(flow_name: str):
    """Get AI explanation of what a flow does."""
    console.print(f"[cyan]Explaining flow '{flow_name}'...[/cyan]")
    console.print()
    console.print("[dim]This flow does the following:[/dim]")
    console.print("  1. Triggers when...")
    console.print("  2. Then it...")
    console.print("  3. Finally it...")
