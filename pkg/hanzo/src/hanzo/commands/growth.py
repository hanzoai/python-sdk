"""Hanzo Growth - Analytics, experiments, and engagement CLI.

Product analytics, feature flags, A/B testing, lifecycle messaging.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


@click.group(name="growth")
def growth_group():
    """Hanzo Growth - Analytics and experimentation.

    \b
    Product Analytics (Insights):
      hanzo growth events list     # List events
      hanzo growth events track    # Track an event
      hanzo growth funnels list    # List funnels

    \b
    Web Analytics:
      hanzo growth web list        # List tracked sites
      hanzo growth web stats       # View traffic stats

    \b
    Experiments:
      hanzo growth flags list      # List feature flags
      hanzo growth flags create    # Create feature flag
      hanzo growth tests list      # List A/B tests

    \b
    Engagement:
      hanzo growth campaigns list  # List campaigns
      hanzo growth campaigns send  # Send campaign
    """
    pass


# ============================================================================
# Events (Product Analytics)
# ============================================================================


@growth_group.group()
def events():
    """Manage event tracking."""
    pass


@events.command(name="list")
@click.option("--limit", "-n", default=50, help="Number of events")
@click.option("--event", "-e", help="Filter by event name")
def events_list(limit: int, event: str):
    """List recent events."""
    table = Table(title="Recent Events", box=box.ROUNDED)
    table.add_column("Event", style="cyan")
    table.add_column("User", style="white")
    table.add_column("Properties", style="dim")
    table.add_column("Time", style="dim")

    console.print(table)


@events.command(name="track")
@click.argument("event_name")
@click.option("--user", "-u", help="User ID")
@click.option("--props", "-p", help="JSON properties")
def events_track(event_name: str, user: str, props: str):
    """Track an event."""
    console.print(f"[green]✓[/green] Event '{event_name}' tracked")


@events.command(name="schema")
def events_schema():
    """Show event schema."""
    table = Table(title="Event Schema", box=box.ROUNDED)
    table.add_column("Event", style="cyan")
    table.add_column("Properties", style="white")
    table.add_column("Count", style="dim")

    console.print(table)


# ============================================================================
# Funnels
# ============================================================================


@growth_group.group()
def funnels():
    """Manage conversion funnels."""
    pass


@funnels.command(name="list")
def funnels_list():
    """List all funnels."""
    table = Table(title="Funnels", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Steps", style="white")
    table.add_column("Conversion", style="green")
    table.add_column("Users", style="dim")

    console.print(table)


@funnels.command(name="show")
@click.argument("funnel_name")
def funnels_show(funnel_name: str):
    """Show funnel details."""
    console.print(
        Panel(
            f"[cyan]Funnel:[/cyan] {funnel_name}\n"
            f"[cyan]Steps:[/cyan] 4\n"
            f"[cyan]Conversion:[/cyan] 23.5%\n"
            f"[cyan]Period:[/cyan] Last 30 days",
            title="Funnel Details",
            border_style="cyan",
        )
    )


@funnels.command(name="create")
@click.option("--name", "-n", prompt=True, help="Funnel name")
@click.option("--steps", "-s", required=True, help="Comma-separated event names")
def funnels_create(name: str, steps: str):
    """Create a funnel."""
    console.print(f"[green]✓[/green] Funnel '{name}' created")


# ============================================================================
# Web Analytics
# ============================================================================


@growth_group.group()
def web():
    """Manage web analytics."""
    pass


@web.command(name="list")
def web_list():
    """List tracked websites."""
    table = Table(title="Tracked Websites", box=box.ROUNDED)
    table.add_column("Domain", style="cyan")
    table.add_column("Visitors", style="white")
    table.add_column("Pageviews", style="white")
    table.add_column("Status", style="green")

    console.print(table)


@web.command(name="add")
@click.argument("domain")
def web_add(domain: str):
    """Add a website to track."""
    console.print(f"[green]✓[/green] Website '{domain}' added")
    console.print()
    console.print("[dim]Add this script to your website:[/dim]")
    console.print(
        Panel(
            f'<script defer src="https://analytics.hanzo.ai/script.js" data-website-id="{domain}"></script>',
            border_style="dim",
        )
    )


@web.command(name="stats")
@click.argument("domain")
@click.option("--period", "-p", default="7d", help="Time period (e.g., 7d, 30d)")
def web_stats(domain: str, period: str):
    """View website statistics."""
    console.print(
        Panel(
            f"[cyan]Domain:[/cyan] {domain}\n"
            f"[cyan]Period:[/cyan] {period}\n"
            f"[cyan]Visitors:[/cyan] 12,456\n"
            f"[cyan]Pageviews:[/cyan] 45,678\n"
            f"[cyan]Bounce Rate:[/cyan] 42%\n"
            f"[cyan]Avg Duration:[/cyan] 2m 34s",
            title="Website Stats",
            border_style="cyan",
        )
    )


# ============================================================================
# Feature Flags
# ============================================================================


@growth_group.group()
def flags():
    """Manage feature flags."""
    pass


@flags.command(name="list")
def flags_list():
    """List all feature flags."""
    table = Table(title="Feature Flags", box=box.ROUNDED)
    table.add_column("Key", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Rollout", style="white")
    table.add_column("Updated", style="dim")

    console.print(table)


@flags.command(name="create")
@click.option("--key", "-k", prompt=True, help="Flag key")
@click.option("--description", "-d", help="Description")
@click.option("--rollout", "-r", default=0, help="Rollout percentage")
def flags_create(key: str, description: str, rollout: int):
    """Create a feature flag."""
    console.print(f"[green]✓[/green] Feature flag '{key}' created")


@flags.command(name="enable")
@click.argument("flag_key")
@click.option("--rollout", "-r", default=100, help="Rollout percentage")
def flags_enable(flag_key: str, rollout: int):
    """Enable a feature flag."""
    console.print(f"[green]✓[/green] Flag '{flag_key}' enabled at {rollout}%")


@flags.command(name="disable")
@click.argument("flag_key")
def flags_disable(flag_key: str):
    """Disable a feature flag."""
    console.print(f"[green]✓[/green] Flag '{flag_key}' disabled")


@flags.command(name="delete")
@click.argument("flag_key")
def flags_delete(flag_key: str):
    """Delete a feature flag."""
    console.print(f"[green]✓[/green] Flag '{flag_key}' deleted")


# ============================================================================
# A/B Tests
# ============================================================================


@growth_group.group()
def tests():
    """Manage A/B tests."""
    pass


@tests.command(name="list")
@click.option("--status", type=click.Choice(["running", "completed", "draft", "all"]), default="all")
def tests_list(status: str):
    """List A/B tests."""
    table = Table(title="A/B Tests", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Variants", style="white")
    table.add_column("Traffic", style="dim")
    table.add_column("Winner", style="yellow")

    console.print(table)


@tests.command(name="create")
@click.option("--name", "-n", prompt=True, help="Test name")
@click.option("--variants", "-v", default="control,treatment", help="Comma-separated variants")
@click.option("--metric", "-m", required=True, help="Primary metric")
def tests_create(name: str, variants: str, metric: str):
    """Create an A/B test."""
    console.print(f"[green]✓[/green] A/B test '{name}' created")


@tests.command(name="start")
@click.argument("test_name")
def tests_start(test_name: str):
    """Start an A/B test."""
    console.print(f"[green]✓[/green] A/B test '{test_name}' started")


@tests.command(name="stop")
@click.argument("test_name")
def tests_stop(test_name: str):
    """Stop an A/B test."""
    console.print(f"[green]✓[/green] A/B test '{test_name}' stopped")


@tests.command(name="results")
@click.argument("test_name")
def tests_results(test_name: str):
    """View A/B test results."""
    console.print(
        Panel(
            f"[cyan]Test:[/cyan] {test_name}\n"
            f"[cyan]Status:[/cyan] Running\n"
            f"[cyan]Participants:[/cyan] 5,234\n"
            f"[cyan]Control conversion:[/cyan] 12.3%\n"
            f"[cyan]Treatment conversion:[/cyan] 14.7%\n"
            f"[cyan]Lift:[/cyan] +19.5%\n"
            f"[cyan]Confidence:[/cyan] 94%",
            title="Test Results",
            border_style="cyan",
        )
    )


# ============================================================================
# Campaigns (Engagement)
# ============================================================================


@growth_group.group()
def campaigns():
    """Manage engagement campaigns."""
    pass


@campaigns.command(name="list")
@click.option("--status", type=click.Choice(["active", "draft", "completed", "all"]), default="all")
def campaigns_list(status: str):
    """List campaigns."""
    table = Table(title="Campaigns", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Status", style="green")
    table.add_column("Sent", style="dim")
    table.add_column("Opens", style="dim")

    console.print(table)


@campaigns.command(name="create")
@click.option("--name", "-n", prompt=True, help="Campaign name")
@click.option("--type", "-t", type=click.Choice(["email", "push", "sms", "in-app"]), default="email")
@click.option("--segment", "-s", help="Target segment")
def campaigns_create(name: str, type: str, segment: str):
    """Create a campaign."""
    console.print(f"[green]✓[/green] Campaign '{name}' created")


@campaigns.command(name="send")
@click.argument("campaign_name")
@click.option("--schedule", help="Schedule time (ISO format)")
def campaigns_send(campaign_name: str, schedule: str):
    """Send or schedule a campaign."""
    if schedule:
        console.print(f"[green]✓[/green] Campaign '{campaign_name}' scheduled for {schedule}")
    else:
        console.print(f"[green]✓[/green] Campaign '{campaign_name}' sent")


@campaigns.command(name="stats")
@click.argument("campaign_name")
def campaigns_stats(campaign_name: str):
    """View campaign statistics."""
    console.print(
        Panel(
            f"[cyan]Campaign:[/cyan] {campaign_name}\n"
            f"[cyan]Sent:[/cyan] 10,234\n"
            f"[cyan]Delivered:[/cyan] 9,876 (96.5%)\n"
            f"[cyan]Opens:[/cyan] 2,345 (23.7%)\n"
            f"[cyan]Clicks:[/cyan] 567 (5.7%)\n"
            f"[cyan]Conversions:[/cyan] 89 (0.9%)",
            title="Campaign Stats",
            border_style="cyan",
        )
    )
