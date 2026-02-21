"""Hanzo Growth - Analytics, experiments, and engagement CLI.

Product analytics, feature flags, A/B testing, lifecycle messaging.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

SERVICE_URL = os.getenv("HANZO_GROWTH_URL", "https://growth.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(SERVICE_URL, method, path, **kwargs)


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
@click.option("--user", "-u", help="Filter by user ID")
def events_list(limit: int, event: str, user: str):
    """List recent events."""
    params: dict = {"limit": limit}
    if event:
        params["event"] = event
    if user:
        params["user"] = user
    resp = _request("get", "/v1/events", params=params)
    data = check_response(resp)

    table = Table(title="Recent Events", box=box.ROUNDED)
    table.add_column("Event", style="cyan")
    table.add_column("User", style="white")
    table.add_column("Properties", style="dim")
    table.add_column("Time", style="dim")

    for e in data.get("events", []):
        props = e.get("properties", {})
        props_str = (
            ", ".join(f"{k}={v}" for k, v in props.items())
            if isinstance(props, dict)
            else str(props)
        )
        table.add_row(
            e.get("event", ""),
            e.get("user_id", ""),
            props_str[:60],
            e.get("timestamp", ""),
        )

    console.print(table)


@events.command(name="track")
@click.argument("event_name")
@click.option("--user", "-u", help="User ID")
@click.option("--props", "-p", help="JSON properties")
def events_track(event_name: str, user: str, props: str):
    """Track an event."""
    payload: dict = {"event": event_name}
    if user:
        payload["user_id"] = user
    if props:
        payload["properties"] = json.loads(props)
    resp = _request("post", "/v1/events", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Event '{event_name}' tracked")


@events.command(name="schema")
def events_schema():
    """Show event schema."""
    resp = _request("get", "/v1/events/schema")
    data = check_response(resp)

    table = Table(title="Event Schema", box=box.ROUNDED)
    table.add_column("Event", style="cyan")
    table.add_column("Properties", style="white")
    table.add_column("Count", style="dim")

    for s in data.get("schemas", []):
        props = ", ".join(s.get("properties", []))
        table.add_row(
            s.get("event", ""),
            props[:60],
            str(s.get("count", 0)),
        )

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
    resp = _request("get", "/v1/funnels")
    data = check_response(resp)

    table = Table(title="Funnels", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Steps", style="white")
    table.add_column("Conversion", style="green")
    table.add_column("Users", style="dim")

    for f in data.get("funnels", []):
        conv = f.get("conversion_rate")
        conv_str = f"{conv:.1f}%" if conv is not None else "-"
        table.add_row(
            f.get("name", ""),
            str(f.get("step_count", 0)),
            conv_str,
            str(f.get("user_count", 0)),
        )

    console.print(table)


@funnels.command(name="show")
@click.argument("funnel_name")
@click.option("--period", "-p", default="30d", help="Time period")
def funnels_show(funnel_name: str, period: str):
    """Show funnel details."""
    resp = _request("get", f"/v1/funnels/{funnel_name}", params={"period": period})
    data = check_response(resp)

    info = (
        f"[cyan]Funnel:[/cyan] {data.get('name', funnel_name)}\n"
        f"[cyan]Steps:[/cyan] {data.get('step_count', 0)}\n"
        f"[cyan]Conversion:[/cyan] {data.get('conversion_rate', 0):.1f}%\n"
        f"[cyan]Period:[/cyan] {period}"
    )
    console.print(Panel(info, title="Funnel Details", border_style="cyan"))

    steps = data.get("steps", [])
    if steps:
        table = Table(title="Funnel Steps", box=box.ROUNDED)
        table.add_column("Step", style="cyan")
        table.add_column("Event", style="white")
        table.add_column("Users", style="dim")
        table.add_column("Conversion", style="green")
        table.add_column("Drop-off", style="red")

        for i, step in enumerate(steps, 1):
            table.add_row(
                str(i),
                step.get("event", ""),
                str(step.get("users", 0)),
                f"{step.get('conversion', 0):.1f}%",
                f"{step.get('dropoff', 0):.1f}%",
            )

        console.print(table)


@funnels.command(name="create")
@click.option("--name", "-n", prompt=True, help="Funnel name")
@click.option("--steps", "-s", required=True, help="Comma-separated event names")
def funnels_create(name: str, steps: str):
    """Create a funnel."""
    step_list = [s.strip() for s in steps.split(",")]
    resp = _request("post", "/v1/funnels", json={"name": name, "steps": step_list})
    check_response(resp)
    console.print(
        f"[green]✓[/green] Funnel '{name}' created with {len(step_list)} steps"
    )


@funnels.command(name="delete")
@click.argument("funnel_name")
def funnels_delete(funnel_name: str):
    """Delete a funnel."""
    resp = _request("delete", f"/v1/funnels/{funnel_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Funnel '{funnel_name}' deleted")


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
    resp = _request("get", "/v1/web/sites")
    data = check_response(resp)

    table = Table(title="Tracked Websites", box=box.ROUNDED)
    table.add_column("Domain", style="cyan")
    table.add_column("Visitors", style="white")
    table.add_column("Pageviews", style="white")
    table.add_column("Status", style="green")

    for site in data.get("sites", []):
        st = site.get("status", "active")
        st_style = "green" if st == "active" else "yellow"
        table.add_row(
            site.get("domain", ""),
            str(site.get("visitors", 0)),
            str(site.get("pageviews", 0)),
            f"[{st_style}]{st}[/{st_style}]",
        )

    console.print(table)


@web.command(name="add")
@click.argument("domain")
def web_add(domain: str):
    """Add a website to track."""
    resp = _request("post", "/v1/web/sites", json={"domain": domain})
    data = check_response(resp)

    console.print(f"[green]✓[/green] Website '{domain}' added")
    console.print()

    script_id = data.get("site_id", domain)
    console.print("[dim]Add this script to your website:[/dim]")
    console.print(
        Panel(
            f'<script defer src="https://analytics.hanzo.ai/script.js" data-website-id="{script_id}"></script>',
            border_style="dim",
        )
    )


@web.command(name="stats")
@click.argument("domain")
@click.option("--period", "-p", default="7d", help="Time period (e.g., 7d, 30d)")
def web_stats(domain: str, period: str):
    """View website statistics."""
    resp = _request("get", f"/v1/web/sites/{domain}/stats", params={"period": period})
    data = check_response(resp)

    info = (
        f"[cyan]Domain:[/cyan] {data.get('domain', domain)}\n"
        f"[cyan]Period:[/cyan] {period}\n"
        f"[cyan]Visitors:[/cyan] {data.get('visitors', 0):,}\n"
        f"[cyan]Pageviews:[/cyan] {data.get('pageviews', 0):,}\n"
        f"[cyan]Bounce Rate:[/cyan] {data.get('bounce_rate', 0):.0f}%\n"
        f"[cyan]Avg Duration:[/cyan] {data.get('avg_duration', 'N/A')}"
    )
    console.print(Panel(info, title="Website Stats", border_style="cyan"))

    pages = data.get("top_pages", [])
    if pages:
        table = Table(title="Top Pages", box=box.ROUNDED)
        table.add_column("Page", style="cyan")
        table.add_column("Views", style="white")
        table.add_column("Visitors", style="dim")

        for p in pages[:10]:
            table.add_row(
                p.get("path", ""), str(p.get("views", 0)), str(p.get("visitors", 0))
            )

        console.print(table)


@web.command(name="remove")
@click.argument("domain")
def web_remove(domain: str):
    """Remove a tracked website."""
    resp = _request("delete", f"/v1/web/sites/{domain}")
    check_response(resp)
    console.print(f"[green]✓[/green] Website '{domain}' removed")


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
    resp = _request("get", "/v1/flags")
    data = check_response(resp)

    table = Table(title="Feature Flags", box=box.ROUNDED)
    table.add_column("Key", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Rollout", style="white")
    table.add_column("Updated", style="dim")

    for f in data.get("flags", []):
        enabled = f.get("enabled", False)
        status_str = "[green]enabled[/green]" if enabled else "[dim]disabled[/dim]"
        table.add_row(
            f.get("key", ""),
            status_str,
            f"{f.get('rollout', 0)}%",
            f.get("updated_at", ""),
        )

    console.print(table)


@flags.command(name="create")
@click.option("--key", "-k", prompt=True, help="Flag key")
@click.option("--description", "-d", help="Description")
@click.option("--rollout", "-r", default=0, help="Rollout percentage")
def flags_create(key: str, description: str, rollout: int):
    """Create a feature flag."""
    payload: dict = {"key": key, "rollout": rollout}
    if description:
        payload["description"] = description
    resp = _request("post", "/v1/flags", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Feature flag '{key}' created")


@flags.command(name="enable")
@click.argument("flag_key")
@click.option("--rollout", "-r", default=100, help="Rollout percentage")
def flags_enable(flag_key: str, rollout: int):
    """Enable a feature flag."""
    resp = _request(
        "patch", f"/v1/flags/{flag_key}", json={"enabled": True, "rollout": rollout}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Flag '{flag_key}' enabled at {rollout}%")


@flags.command(name="disable")
@click.argument("flag_key")
def flags_disable(flag_key: str):
    """Disable a feature flag."""
    resp = _request("patch", f"/v1/flags/{flag_key}", json={"enabled": False})
    check_response(resp)
    console.print(f"[green]✓[/green] Flag '{flag_key}' disabled")


@flags.command(name="delete")
@click.argument("flag_key")
def flags_delete(flag_key: str):
    """Delete a feature flag."""
    resp = _request("delete", f"/v1/flags/{flag_key}")
    check_response(resp)
    console.print(f"[green]✓[/green] Flag '{flag_key}' deleted")


# ============================================================================
# A/B Tests
# ============================================================================


@growth_group.group()
def tests():
    """Manage A/B tests."""
    pass


@tests.command(name="list")
@click.option(
    "--status",
    type=click.Choice(["running", "completed", "draft", "all"]),
    default="all",
)
def tests_list(status: str):
    """List A/B tests."""
    params: dict = {}
    if status != "all":
        params["status"] = status
    resp = _request("get", "/v1/tests", params=params)
    data = check_response(resp)

    table = Table(title="A/B Tests", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Variants", style="white")
    table.add_column("Traffic", style="dim")
    table.add_column("Winner", style="yellow")

    for t in data.get("tests", []):
        st = t.get("status", "draft")
        st_style = {"running": "green", "completed": "cyan", "draft": "dim"}.get(
            st, "white"
        )
        winner = t.get("winner", "-")
        table.add_row(
            t.get("name", ""),
            f"[{st_style}]{st}[/{st_style}]",
            str(t.get("variant_count", 0)),
            f"{t.get('traffic_percent', 0)}%",
            winner,
        )

    console.print(table)


@tests.command(name="create")
@click.option("--name", "-n", prompt=True, help="Test name")
@click.option(
    "--variants", "-v", default="control,treatment", help="Comma-separated variants"
)
@click.option("--metric", "-m", required=True, help="Primary metric")
@click.option("--traffic", "-t", default=100, help="Traffic percentage")
def tests_create(name: str, variants: str, metric: str, traffic: int):
    """Create an A/B test."""
    variant_list = [v.strip() for v in variants.split(",")]
    resp = _request(
        "post",
        "/v1/tests",
        json={
            "name": name,
            "variants": variant_list,
            "primary_metric": metric,
            "traffic_percent": traffic,
        },
    )
    check_response(resp)
    console.print(
        f"[green]✓[/green] A/B test '{name}' created with {len(variant_list)} variants"
    )


@tests.command(name="start")
@click.argument("test_name")
def tests_start(test_name: str):
    """Start an A/B test."""
    resp = _request("post", f"/v1/tests/{test_name}/start")
    check_response(resp)
    console.print(f"[green]✓[/green] A/B test '{test_name}' started")


@tests.command(name="stop")
@click.argument("test_name")
def tests_stop(test_name: str):
    """Stop an A/B test."""
    resp = _request("post", f"/v1/tests/{test_name}/stop")
    check_response(resp)
    console.print(f"[green]✓[/green] A/B test '{test_name}' stopped")


@tests.command(name="results")
@click.argument("test_name")
@click.option(
    "--format", "-f", "fmt", type=click.Choice(["table", "json"]), default="table"
)
def tests_results(test_name: str, fmt: str):
    """View A/B test results."""
    resp = _request("get", f"/v1/tests/{test_name}/results")
    data = check_response(resp)

    if fmt == "json":
        console.print(json.dumps(data, indent=2))
        return

    info = (
        f"[cyan]Test:[/cyan] {data.get('name', test_name)}\n"
        f"[cyan]Status:[/cyan] {data.get('status', 'unknown')}\n"
        f"[cyan]Participants:[/cyan] {data.get('participant_count', 0):,}\n"
        f"[cyan]Confidence:[/cyan] {data.get('confidence', 0):.0f}%"
    )
    console.print(Panel(info, title="Test Results", border_style="cyan"))

    variants = data.get("variants", [])
    if variants:
        table = Table(title="Variant Results", box=box.ROUNDED)
        table.add_column("Variant", style="cyan")
        table.add_column("Users", style="white")
        table.add_column("Conversions", style="green")
        table.add_column("Rate", style="yellow")
        table.add_column("Lift", style="dim")

        for v in variants:
            is_winner = v.get("is_winner", False)
            name_str = (
                f"[bold]{v.get('name', '')}[/bold] *"
                if is_winner
                else v.get("name", "")
            )
            table.add_row(
                name_str,
                str(v.get("users", 0)),
                str(v.get("conversions", 0)),
                f"{v.get('conversion_rate', 0):.1f}%",
                f"{v.get('lift', 0):+.1f}%" if v.get("lift") else "-",
            )

        console.print(table)


@tests.command(name="delete")
@click.argument("test_name")
def tests_delete(test_name: str):
    """Delete an A/B test."""
    resp = _request("delete", f"/v1/tests/{test_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] A/B test '{test_name}' deleted")


# ============================================================================
# Campaigns (Engagement)
# ============================================================================


@growth_group.group()
def campaigns():
    """Manage engagement campaigns."""
    pass


@campaigns.command(name="list")
@click.option(
    "--status",
    type=click.Choice(["active", "draft", "completed", "all"]),
    default="all",
)
def campaigns_list(status: str):
    """List campaigns."""
    params: dict = {}
    if status != "all":
        params["status"] = status
    resp = _request("get", "/v1/campaigns", params=params)
    data = check_response(resp)

    table = Table(title="Campaigns", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Status", style="green")
    table.add_column("Sent", style="dim")
    table.add_column("Opens", style="dim")

    for c in data.get("campaigns", []):
        st = c.get("status", "draft")
        st_style = {"active": "green", "completed": "cyan", "draft": "dim"}.get(
            st, "white"
        )
        table.add_row(
            c.get("name", ""),
            c.get("type", ""),
            f"[{st_style}]{st}[/{st_style}]",
            str(c.get("sent_count", 0)),
            str(c.get("open_count", 0)),
        )

    console.print(table)


@campaigns.command(name="create")
@click.option("--name", "-n", prompt=True, help="Campaign name")
@click.option(
    "--type",
    "-t",
    "campaign_type",
    type=click.Choice(["email", "push", "sms", "in-app"]),
    default="email",
)
@click.option("--segment", "-s", help="Target segment")
@click.option("--subject", help="Email subject")
@click.option("--body", "-b", help="Message body")
def campaigns_create(
    name: str, campaign_type: str, segment: str, subject: str, body: str
):
    """Create a campaign."""
    payload: dict = {"name": name, "type": campaign_type}
    if segment:
        payload["segment"] = segment
    if subject:
        payload["subject"] = subject
    if body:
        payload["body"] = body
    resp = _request("post", "/v1/campaigns", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Campaign '{name}' created")


@campaigns.command(name="send")
@click.argument("campaign_name")
@click.option("--schedule", help="Schedule time (ISO format)")
def campaigns_send(campaign_name: str, schedule: str):
    """Send or schedule a campaign."""
    payload: dict = {}
    if schedule:
        payload["scheduled_at"] = schedule
    resp = _request("post", f"/v1/campaigns/{campaign_name}/send", json=payload)
    check_response(resp)
    if schedule:
        console.print(
            f"[green]✓[/green] Campaign '{campaign_name}' scheduled for {schedule}"
        )
    else:
        console.print(f"[green]✓[/green] Campaign '{campaign_name}' sent")


@campaigns.command(name="stats")
@click.argument("campaign_name")
def campaigns_stats(campaign_name: str):
    """View campaign statistics."""
    resp = _request("get", f"/v1/campaigns/{campaign_name}/stats")
    data = check_response(resp)

    sent = data.get("sent", 0)
    delivered = data.get("delivered", 0)
    opens = data.get("opens", 0)
    clicks = data.get("clicks", 0)
    conversions = data.get("conversions", 0)

    delivery_rate = (delivered / sent * 100) if sent > 0 else 0
    open_rate = (opens / delivered * 100) if delivered > 0 else 0
    click_rate = (clicks / delivered * 100) if delivered > 0 else 0
    conv_rate = (conversions / delivered * 100) if delivered > 0 else 0

    info = (
        f"[cyan]Campaign:[/cyan] {data.get('name', campaign_name)}\n"
        f"[cyan]Sent:[/cyan] {sent:,}\n"
        f"[cyan]Delivered:[/cyan] {delivered:,} ({delivery_rate:.1f}%)\n"
        f"[cyan]Opens:[/cyan] {opens:,} ({open_rate:.1f}%)\n"
        f"[cyan]Clicks:[/cyan] {clicks:,} ({click_rate:.1f}%)\n"
        f"[cyan]Conversions:[/cyan] {conversions:,} ({conv_rate:.1f}%)"
    )
    console.print(Panel(info, title="Campaign Stats", border_style="cyan"))


@campaigns.command(name="delete")
@click.argument("campaign_name")
def campaigns_delete(campaign_name: str):
    """Delete a campaign."""
    resp = _request("delete", f"/v1/campaigns/{campaign_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Campaign '{campaign_name}' deleted")
