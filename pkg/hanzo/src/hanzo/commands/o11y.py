"""Hanzo Observability - Metrics, logs, traces CLI.

Full visibility into your systems.
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

SERVICE_URL = os.getenv("HANZO_O11Y_URL", "https://o11y.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(SERVICE_URL, method, path, **kwargs)


@click.group(name="o11y")
def o11y_group():
    """Hanzo Observability - Metrics, logs, traces, and LLM monitoring.

    \b
    Infrastructure Observability:
      hanzo o11y metrics list      # List metric series
      hanzo o11y logs search       # Search logs
      hanzo o11y traces list       # List distributed traces
      hanzo o11y dashboards list   # List dashboards
      hanzo o11y alerts list       # List alert rules

    \b
    LLM Observability (Langfuse-style):
      hanzo o11y prompts list      # Manage prompt templates
      hanzo o11y generations list  # Track LLM generations
      hanzo o11y sessions list     # Track conversation sessions
      hanzo o11y llm costs         # LLM cost analysis

    \b
    Evaluations & Scoring:
      hanzo o11y evals create      # Create evaluation runs
      hanzo o11y scores list       # View scores & feedback
      hanzo o11y datasets list     # Manage eval datasets

    \b
    Alias: hanzo observe
    """
    pass


# ============================================================================
# Metrics
# ============================================================================


@o11y_group.group()
def metrics():
    """Manage metrics and time-series data."""
    pass


@metrics.command(name="list")
@click.option("--filter", "-f", help="Filter metric names")
@click.option("--limit", "-n", default=100, help="Max results")
def metrics_list(filter: str, limit: int):
    """List available metric series."""
    params = {"limit": limit}
    if filter:
        params["filter"] = filter
    resp = _request("get", "/v1/metrics", params=params)
    data = check_response(resp)

    table = Table(title="Metrics", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Labels", style="dim")
    table.add_column("Points", style="dim")

    for m in data.get("metrics", []):
        table.add_row(
            m.get("name", ""),
            m.get("type", ""),
            ", ".join(m.get("labels", [])),
            str(m.get("points", 0)),
        )

    console.print(table)


@metrics.command(name="query")
@click.argument("promql")
@click.option("--start", "-s", help="Start time")
@click.option("--end", "-e", help="End time")
@click.option("--step", default="1m", help="Query step")
def metrics_query(promql: str, start: str, end: str, step: str):
    """Query metrics using PromQL."""
    payload = {"query": promql, "step": step}
    if start:
        payload["start"] = start
    if end:
        payload["end"] = end
    resp = _request("post", "/v1/metrics/query", json=payload)
    data = check_response(resp)

    console.print(f"[cyan]Query:[/cyan] {promql}")
    console.print(f"[cyan]Step:[/cyan] {step}")
    console.print()

    results = data.get("result", [])
    if not results:
        console.print("[dim]No data points returned[/dim]")
        return

    table = Table(title="Query Results", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_column("Timestamp", style="dim")

    for r in results:
        labels = r.get("metric", {})
        label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
        for ts, val in r.get("values", []):
            table.add_row(label_str, str(val), str(ts))

    console.print(table)


@metrics.command(name="export")
@click.argument("promql")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", help="Output file")
@click.option("--start", "-s", help="Start time")
@click.option("--end", "-e", help="End time")
def metrics_export(promql: str, fmt: str, output: str, start: str, end: str):
    """Export metrics to file."""
    payload = {"query": promql, "format": fmt}
    if start:
        payload["start"] = start
    if end:
        payload["end"] = end
    resp = _request("post", "/v1/metrics/export", json=payload)
    data = check_response(resp)

    content = data.get("data", "")
    if output:
        with open(output, "w") as f:
            f.write(content if isinstance(content, str) else json.dumps(content, indent=2))
        console.print(f"[green]✓[/green] Exported to {output}")
    else:
        console.print(content if isinstance(content, str) else json.dumps(content, indent=2))


# ============================================================================
# Logs
# ============================================================================


@o11y_group.group()
def logs():
    """Search and analyze logs."""
    pass


@logs.command(name="search")
@click.argument("query")
@click.option("--source", "-s", help="Log source")
@click.option("--level", "-l", type=click.Choice(["debug", "info", "warn", "error"]))
@click.option("--limit", "-n", default=100, help="Max results")
@click.option("--start", help="Start time")
@click.option("--end", help="End time")
def logs_search(query: str, source: str, level: str, limit: int, start: str, end: str):
    """Search logs."""
    payload: dict = {"query": query, "limit": limit}
    if source:
        payload["source"] = source
    if level:
        payload["level"] = level
    if start:
        payload["start"] = start
    if end:
        payload["end"] = end
    resp = _request("post", "/v1/logs/search", json=payload)
    data = check_response(resp)

    entries = data.get("logs", [])
    if not entries:
        console.print("[dim]No matching logs found[/dim]")
        return

    table = Table(title="Log Results", box=box.ROUNDED)
    table.add_column("Time", style="dim")
    table.add_column("Level", style="yellow")
    table.add_column("Source", style="cyan")
    table.add_column("Message", style="white")

    for entry in entries:
        lvl = entry.get("level", "info")
        lvl_style = {"error": "red", "warn": "yellow", "info": "green", "debug": "dim"}.get(lvl, "white")
        table.add_row(
            entry.get("timestamp", ""),
            f"[{lvl_style}]{lvl}[/{lvl_style}]",
            entry.get("source", ""),
            entry.get("message", ""),
        )

    console.print(table)


@logs.command(name="tail")
@click.option("--source", "-s", help="Log source")
@click.option("--filter", "-f", help="Filter expression")
@click.option("--level", "-l", type=click.Choice(["debug", "info", "warn", "error"]))
def logs_tail(source: str, filter: str, level: str):
    """Tail live logs."""
    params: dict = {}
    if source:
        params["source"] = source
    if filter:
        params["filter"] = filter
    if level:
        params["level"] = level

    console.print("[cyan]Tailing logs... (Ctrl+C to stop)[/cyan]")

    try:
        url = f"{SERVICE_URL}/v1/logs/tail"
        from .base import get_api_key
        api_key = get_api_key()
        if not api_key:
            raise click.ClickException("Not authenticated. Run 'hanzo login' first.")

        with httpx.Client(timeout=None) as client:
            with client.stream("GET", url, params=params, headers={"Authorization": f"Bearer {api_key}"}) as stream:
                for line in stream.iter_lines():
                    if line:
                        try:
                            entry = json.loads(line)
                            lvl = entry.get("level", "info")
                            lvl_style = {"error": "red", "warn": "yellow", "info": "green", "debug": "dim"}.get(lvl, "white")
                            console.print(f"[dim]{entry.get('timestamp', '')}[/dim] [{lvl_style}]{lvl}[/{lvl_style}] [cyan]{entry.get('source', '')}[/cyan] {entry.get('message', '')}")
                        except json.JSONDecodeError:
                            console.print(line)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped tailing logs[/dim]")
    except httpx.ConnectError:
        raise click.ClickException(f"Could not connect to {SERVICE_URL}")


@logs.command(name="sources")
def logs_sources():
    """List log sources."""
    resp = _request("get", "/v1/logs/sources")
    data = check_response(resp)

    table = Table(title="Log Sources", box=box.ROUNDED)
    table.add_column("Source", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Status", style="green")
    table.add_column("Volume", style="dim")

    for src in data.get("sources", []):
        status = src.get("status", "active")
        style = "green" if status == "active" else "yellow"
        table.add_row(
            src.get("name", ""),
            src.get("type", ""),
            f"[{style}]{status}[/{style}]",
            src.get("volume", ""),
        )

    console.print(table)


# ============================================================================
# Traces
# ============================================================================


@o11y_group.group()
def traces():
    """Analyze distributed traces."""
    pass


@traces.command(name="list")
@click.option("--service", "-s", help="Filter by service")
@click.option("--operation", "-o", help="Filter by operation")
@click.option("--min-duration", help="Minimum duration (e.g., 100ms)")
@click.option("--limit", "-n", default=20, help="Max traces")
def traces_list(service: str, operation: str, min_duration: str, limit: int):
    """List recent traces."""
    params: dict = {"limit": limit}
    if service:
        params["service"] = service
    if operation:
        params["operation"] = operation
    if min_duration:
        params["min_duration"] = min_duration
    resp = _request("get", "/v1/traces", params=params)
    data = check_response(resp)

    table = Table(title="Traces", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Service", style="white")
    table.add_column("Operation", style="white")
    table.add_column("Duration", style="yellow")
    table.add_column("Spans", style="dim")
    table.add_column("Status", style="green")

    for t in data.get("traces", []):
        status = t.get("status", "ok")
        style = "green" if status == "ok" else "red"
        table.add_row(
            t.get("trace_id", "")[:16],
            t.get("service", ""),
            t.get("operation", ""),
            t.get("duration", ""),
            str(t.get("spans", 0)),
            f"[{style}]{status}[/{style}]",
        )

    console.print(table)


@traces.command(name="show")
@click.argument("trace_id")
def traces_show(trace_id: str):
    """Show trace details."""
    resp = _request("get", f"/v1/traces/{trace_id}")
    data = check_response(resp)

    info = (
        f"[cyan]Trace ID:[/cyan] {data.get('trace_id', trace_id)}\n"
        f"[cyan]Duration:[/cyan] {data.get('duration', 'N/A')}\n"
        f"[cyan]Spans:[/cyan] {data.get('span_count', 0)}\n"
        f"[cyan]Services:[/cyan] {', '.join(data.get('services', []))}\n"
        f"[cyan]Status:[/cyan] {data.get('status', 'ok')}"
    )
    console.print(Panel(info, title="Trace Details", border_style="cyan"))

    spans = data.get("spans", [])
    if spans:
        table = Table(title="Spans", box=box.ROUNDED)
        table.add_column("Span ID", style="cyan")
        table.add_column("Service", style="white")
        table.add_column("Operation", style="white")
        table.add_column("Duration", style="yellow")
        table.add_column("Status", style="green")

        for s in spans:
            st = s.get("status", "ok")
            st_style = "green" if st == "ok" else "red"
            table.add_row(
                s.get("span_id", "")[:12],
                s.get("service", ""),
                s.get("operation", ""),
                s.get("duration", ""),
                f"[{st_style}]{st}[/{st_style}]",
            )

        console.print(table)


@traces.command(name="services")
def traces_services():
    """List traced services."""
    resp = _request("get", "/v1/traces/services")
    data = check_response(resp)

    table = Table(title="Services", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Operations", style="white")
    table.add_column("Avg Duration", style="yellow")
    table.add_column("Error Rate", style="red")

    for svc in data.get("services", []):
        table.add_row(
            svc.get("name", ""),
            str(svc.get("operations", 0)),
            svc.get("avg_duration", ""),
            svc.get("error_rate", ""),
        )

    console.print(table)


# ============================================================================
# Dashboards
# ============================================================================


@o11y_group.group()
def dashboards():
    """Manage observability dashboards."""
    pass


@dashboards.command(name="list")
def dashboards_list():
    """List all dashboards."""
    resp = _request("get", "/v1/dashboards")
    data = check_response(resp)

    table = Table(title="Dashboards", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Panels", style="white")
    table.add_column("Updated", style="dim")

    for d in data.get("dashboards", []):
        table.add_row(
            d.get("name", ""),
            str(d.get("panel_count", 0)),
            d.get("updated_at", ""),
        )

    console.print(table)


@dashboards.command(name="create")
@click.option("--name", "-n", prompt=True, help="Dashboard name")
@click.option("--file", "-f", help="Import from JSON file")
def dashboards_create(name: str, file: str):
    """Create a new dashboard."""
    payload: dict = {"name": name}
    if file:
        with open(file) as f:
            payload["config"] = json.load(f)
    resp = _request("post", "/v1/dashboards", json=payload)
    data = check_response(resp)

    dashboard_id = data.get("id", "")
    console.print(f"[green]✓[/green] Dashboard '{name}' created")
    console.print(f"[dim]View at: {SERVICE_URL}/dashboards/{dashboard_id}[/dim]")


@dashboards.command(name="delete")
@click.argument("name")
def dashboards_delete(name: str):
    """Delete a dashboard."""
    resp = _request("delete", f"/v1/dashboards/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Dashboard '{name}' deleted")


@dashboards.command(name="open")
@click.argument("name")
def dashboards_open(name: str):
    """Open dashboard in browser."""
    import webbrowser

    url = f"{SERVICE_URL}/dashboards/{name}"
    console.print(f"[cyan]Opening: {url}[/cyan]")
    webbrowser.open(url)


# ============================================================================
# Alerts
# ============================================================================


@o11y_group.group()
def alerts():
    """Manage alert rules."""
    pass


@alerts.command(name="list")
@click.option("--status", type=click.Choice(["firing", "pending", "inactive", "all"]), default="all")
def alerts_list(status: str):
    """List alert rules."""
    params: dict = {}
    if status != "all":
        params["status"] = status
    resp = _request("get", "/v1/alerts", params=params)
    data = check_response(resp)

    table = Table(title="Alert Rules", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Condition", style="white")
    table.add_column("Status", style="green")
    table.add_column("Severity", style="yellow")
    table.add_column("Last Fired", style="dim")

    for a in data.get("alerts", []):
        st = a.get("status", "inactive")
        st_style = {"firing": "red", "pending": "yellow"}.get(st, "green")
        sev = a.get("severity", "warning")
        sev_style = {"critical": "red", "warning": "yellow"}.get(sev, "dim")
        table.add_row(
            a.get("name", ""),
            a.get("condition", ""),
            f"[{st_style}]{st}[/{st_style}]",
            f"[{sev_style}]{sev}[/{sev_style}]",
            a.get("last_fired", "never"),
        )

    console.print(table)


@alerts.command(name="create")
@click.option("--name", "-n", prompt=True, help="Alert name")
@click.option("--condition", "-c", required=True, help="PromQL condition")
@click.option("--severity", "-s", type=click.Choice(["critical", "warning", "info"]), default="warning")
@click.option("--channel", help="Notification channel")
@click.option("--for-duration", "for_duration", default="5m", help="Duration before firing")
def alerts_create(name: str, condition: str, severity: str, channel: str, for_duration: str):
    """Create an alert rule."""
    payload: dict = {
        "name": name,
        "condition": condition,
        "severity": severity,
        "for": for_duration,
    }
    if channel:
        payload["channel"] = channel
    resp = _request("post", "/v1/alerts", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Alert rule '{name}' created")


@alerts.command(name="silence")
@click.argument("alert_name")
@click.option("--duration", "-d", default="1h", help="Silence duration")
@click.option("--comment", "-c", help="Reason for silencing")
def alerts_silence(alert_name: str, duration: str, comment: str):
    """Silence an alert."""
    payload: dict = {"duration": duration}
    if comment:
        payload["comment"] = comment
    resp = _request("post", f"/v1/alerts/{alert_name}/silence", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Alert '{alert_name}' silenced for {duration}")


@alerts.command(name="delete")
@click.argument("alert_name")
def alerts_delete(alert_name: str):
    """Delete an alert rule."""
    resp = _request("delete", f"/v1/alerts/{alert_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Alert rule '{alert_name}' deleted")


# ============================================================================
# LLM Observability (Langfuse-style)
# ============================================================================


@o11y_group.group()
def prompts():
    """Manage LLM prompt templates (Langfuse-style)."""
    pass


@prompts.command(name="list")
@click.option("--label", "-l", help="Filter by label")
@click.option("--limit", "-n", default=50, help="Max results")
def prompts_list(label: str, limit: int):
    """List prompt templates."""
    params: dict = {"limit": limit}
    if label:
        params["label"] = label
    resp = _request("get", "/v1/prompts", params=params)
    data = check_response(resp)

    table = Table(title="Prompt Templates", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Label", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Updated", style="dim")

    for p in data.get("prompts", []):
        table.add_row(
            p.get("name", ""),
            f"v{p.get('version', '1')}",
            p.get("label", ""),
            p.get("model", ""),
            p.get("updated_at", ""),
        )

    console.print(table)


@prompts.command(name="create")
@click.argument("name")
@click.option("--template", "-t", required=True, help="Prompt template")
@click.option("--model", "-m", help="Default model")
@click.option("--config", "-c", help="Model config JSON")
@click.option("--label", "-l", default="latest", help="Version label")
def prompts_create(name: str, template: str, model: str, config: str, label: str):
    """Create a prompt template."""
    payload: dict = {"name": name, "template": template, "label": label}
    if model:
        payload["model"] = model
    if config:
        payload["config"] = json.loads(config)
    resp = _request("post", "/v1/prompts", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Prompt '{name}' created (v{data.get('version', '1')})")
    if model:
        console.print(f"  Model: {model}")


@prompts.command(name="get")
@click.argument("name")
@click.option("--version", "-v", type=int, help="Specific version")
@click.option("--label", "-l", help="Get by label (production, staging)")
def prompts_get(name: str, version: int, label: str):
    """Get a prompt template."""
    params: dict = {}
    if version:
        params["version"] = version
    if label:
        params["label"] = label
    resp = _request("get", f"/v1/prompts/{name}", params=params)
    data = check_response(resp)

    info = (
        f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
        f"[cyan]Version:[/cyan] v{data.get('version', '1')}\n"
        f"[cyan]Label:[/cyan] {data.get('label', '')}\n"
        f"[cyan]Model:[/cyan] {data.get('model', 'N/A')}\n"
        f"[cyan]Template:[/cyan]\n  {data.get('template', '')}"
    )
    console.print(Panel(info, title="Prompt Template", border_style="cyan"))

    if data.get("config"):
        console.print(f"\n[cyan]Config:[/cyan]")
        console.print(json.dumps(data["config"], indent=2))


@prompts.command(name="promote")
@click.argument("name")
@click.option("--version", "-v", required=True, type=int, help="Version to promote")
@click.option("--to", "to_label", required=True, help="Target label")
def prompts_promote(name: str, version: int, to_label: str):
    """Promote a prompt version to a label."""
    resp = _request("post", f"/v1/prompts/{name}/promote", json={"version": version, "label": to_label})
    check_response(resp)
    console.print(f"[green]✓[/green] Promoted '{name}' v{version} to {to_label}")


@prompts.command(name="history")
@click.argument("name")
def prompts_history(name: str):
    """Show prompt version history."""
    resp = _request("get", f"/v1/prompts/{name}/versions")
    data = check_response(resp)

    table = Table(title=f"History for '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Author", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Note", style="dim")

    for v in data.get("versions", []):
        table.add_row(
            f"v{v.get('version', '')}",
            v.get("label", ""),
            v.get("author", ""),
            v.get("created_at", ""),
            v.get("note", ""),
        )

    console.print(table)


# ============================================================================
# Generations (LLM Call Tracking)
# ============================================================================


@o11y_group.group()
def generations():
    """Track LLM generations and calls (Langfuse-style)."""
    pass


@generations.command(name="list")
@click.option("--model", "-m", help="Filter by model")
@click.option("--prompt", "-p", help="Filter by prompt name")
@click.option("--user", "-u", help="Filter by user ID")
@click.option("--limit", "-n", default=50, help="Max results")
def generations_list(model: str, prompt: str, user: str, limit: int):
    """List LLM generations."""
    params: dict = {"limit": limit}
    if model:
        params["model"] = model
    if prompt:
        params["prompt"] = prompt
    if user:
        params["user"] = user
    resp = _request("get", "/v1/generations", params=params)
    data = check_response(resp)

    table = Table(title="Generations", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Prompt", style="white")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Latency", style="dim")
    table.add_column("Time", style="dim")

    for g in data.get("generations", []):
        total_tokens = g.get("input_tokens", 0) + g.get("output_tokens", 0)
        table.add_row(
            g.get("id", "")[:12],
            g.get("model", ""),
            g.get("prompt_name", ""),
            str(total_tokens),
            f"${g.get('cost', 0):.4f}",
            g.get("latency", ""),
            g.get("created_at", ""),
        )

    console.print(table)


@generations.command(name="show")
@click.argument("generation_id")
def generations_show(generation_id: str):
    """Show generation details."""
    resp = _request("get", f"/v1/generations/{generation_id}")
    data = check_response(resp)

    info = (
        f"[cyan]Generation ID:[/cyan] {data.get('id', generation_id)}\n"
        f"[cyan]Trace ID:[/cyan] {data.get('trace_id', 'N/A')}\n"
        f"[cyan]Model:[/cyan] {data.get('model', 'N/A')}\n"
        f"[cyan]Prompt:[/cyan] {data.get('prompt_name', 'N/A')} v{data.get('prompt_version', '?')}\n"
        f"[cyan]Input Tokens:[/cyan] {data.get('input_tokens', 0)}\n"
        f"[cyan]Output Tokens:[/cyan] {data.get('output_tokens', 0)}\n"
        f"[cyan]Total Cost:[/cyan] ${data.get('cost', 0):.4f}\n"
        f"[cyan]Latency:[/cyan] {data.get('latency', 'N/A')}\n"
        f"[cyan]Finish Reason:[/cyan] {data.get('finish_reason', 'N/A')}"
    )
    console.print(Panel(info, title="Generation Details", border_style="cyan"))

    if data.get("input"):
        console.print("\n[cyan]Input:[/cyan]")
        console.print(data["input"])
    if data.get("output"):
        console.print("\n[cyan]Output:[/cyan]")
        console.print(data["output"])


@generations.command(name="stats")
@click.option("--range", "-r", "time_range", default="7d", help="Time range")
@click.option("--by", type=click.Choice(["model", "prompt", "user"]), default="model")
def generations_stats(time_range: str, by: str):
    """Show generation statistics."""
    resp = _request("get", "/v1/generations/stats", params={"range": time_range, "group_by": by})
    data = check_response(resp)

    console.print(f"[cyan]Generation Statistics (last {time_range}):[/cyan]")
    console.print()

    table = Table(title=f"By {by.title()}", box=box.ROUNDED)
    table.add_column(by.title(), style="cyan")
    table.add_column("Calls", style="white")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Avg Latency", style="dim")

    for s in data.get("stats", []):
        table.add_row(
            s.get("key", ""),
            str(s.get("calls", 0)),
            str(s.get("total_tokens", 0)),
            f"${s.get('total_cost', 0):.2f}",
            s.get("avg_latency", ""),
        )

    console.print(table)

    total = data.get("total", {})
    if total:
        console.print(f"\n[bold]Total Cost:[/bold] ${total.get('cost', 0):.2f}")


# ============================================================================
# Evaluations (Langfuse-style)
# ============================================================================


@o11y_group.group()
def evals():
    """Manage LLM evaluations (Langfuse-style)."""
    pass


@evals.command(name="list")
@click.option("--status", type=click.Choice(["pending", "running", "completed", "all"]), default="all")
def evals_list(status: str):
    """List evaluations."""
    params: dict = {}
    if status != "all":
        params["status"] = status
    resp = _request("get", "/v1/evals", params=params)
    data = check_response(resp)

    table = Table(title="Evaluations", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Dataset", style="white")
    table.add_column("Prompt", style="white")
    table.add_column("Status", style="green")
    table.add_column("Score", style="yellow")
    table.add_column("Created", style="dim")

    for e in data.get("evals", []):
        st = e.get("status", "pending")
        st_style = {"completed": "green", "running": "cyan", "pending": "yellow", "failed": "red"}.get(st, "white")
        score = f"{e.get('score', 0):.2f}" if e.get("score") is not None else "-"
        table.add_row(
            e.get("name", ""),
            e.get("dataset", ""),
            e.get("prompt", ""),
            f"[{st_style}]{st}[/{st_style}]",
            score,
            e.get("created_at", ""),
        )

    console.print(table)


@evals.command(name="create")
@click.option("--name", "-n", required=True, help="Evaluation name")
@click.option("--dataset", "-d", required=True, help="Dataset to use")
@click.option("--prompt", "-p", required=True, help="Prompt to evaluate")
@click.option("--scorer", "-s", multiple=True, help="Scorer(s) to use")
def evals_create(name: str, dataset: str, prompt: str, scorer: tuple):
    """Create an evaluation run."""
    payload: dict = {"name": name, "dataset": dataset, "prompt": prompt}
    if scorer:
        payload["scorers"] = list(scorer)
    resp = _request("post", "/v1/evals", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Evaluation '{name}' created")
    console.print(f"  ID: {data.get('id', '')}")
    console.print(f"  Run with: hanzo o11y evals run {name}")


@evals.command(name="run")
@click.argument("name")
@click.option("--parallel", "-p", default=5, help="Parallel executions")
def evals_run(name: str, parallel: int):
    """Run an evaluation."""
    resp = _request("post", f"/v1/evals/{name}/run", json={"parallel": parallel})
    data = check_response(resp)

    console.print(f"[green]✓[/green] Evaluation '{name}' started")
    console.print(f"  Run ID: {data.get('run_id', '')}")
    console.print(f"  Parallelism: {parallel}")


@evals.command(name="results")
@click.argument("name")
@click.option("--format", "-f", "fmt", type=click.Choice(["table", "json"]), default="table")
def evals_results(name: str, fmt: str):
    """Show evaluation results."""
    resp = _request("get", f"/v1/evals/{name}/results")
    data = check_response(resp)

    if fmt == "json":
        console.print(json.dumps(data, indent=2))
        return

    info = (
        f"[cyan]Evaluation:[/cyan] {data.get('name', name)}\n"
        f"[cyan]Status:[/cyan] {data.get('status', 'unknown')}\n"
        f"[cyan]Samples:[/cyan] {data.get('sample_count', 0)}\n"
        f"[cyan]Avg Score:[/cyan] {data.get('avg_score', 0):.2f}\n"
        f"[cyan]Duration:[/cyan] {data.get('duration', 'N/A')}"
    )
    console.print(Panel(info, title="Evaluation Results", border_style="cyan"))

    scores = data.get("scorer_results", [])
    if scores:
        table = Table(title="Scorer Breakdown", box=box.ROUNDED)
        table.add_column("Scorer", style="cyan")
        table.add_column("Mean", style="yellow")
        table.add_column("Median", style="yellow")
        table.add_column("Min", style="dim")
        table.add_column("Max", style="dim")

        for s in scores:
            table.add_row(
                s.get("name", ""),
                f"{s.get('mean', 0):.2f}",
                f"{s.get('median', 0):.2f}",
                f"{s.get('min', 0):.2f}",
                f"{s.get('max', 0):.2f}",
            )

        console.print(table)


# ============================================================================
# Scores (Metrics & Feedback)
# ============================================================================


@o11y_group.group()
def scores():
    """Manage scores and feedback (Langfuse-style)."""
    pass


@scores.command(name="list")
@click.option("--trace", "-t", help="Filter by trace ID")
@click.option("--name", "-n", help="Filter by score name")
@click.option("--source", type=click.Choice(["api", "human", "model", "all"]), default="all")
@click.option("--limit", default=50, help="Max results")
def scores_list(trace: str, name: str, source: str, limit: int):
    """List scores."""
    params: dict = {"limit": limit}
    if trace:
        params["trace_id"] = trace
    if name:
        params["name"] = name
    if source != "all":
        params["source"] = source
    resp = _request("get", "/v1/scores", params=params)
    data = check_response(resp)

    table = Table(title="Scores", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Value", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Comment", style="dim")
    table.add_column("Created", style="dim")

    for s in data.get("scores", []):
        table.add_row(
            s.get("trace_id", "")[:16],
            s.get("name", ""),
            f"{s.get('value', 0):.2f}",
            s.get("source", ""),
            s.get("comment", ""),
            s.get("created_at", ""),
        )

    console.print(table)


@scores.command(name="add")
@click.option("--trace", "-t", required=True, help="Trace ID")
@click.option("--name", "-n", required=True, help="Score name")
@click.option("--value", "-v", type=float, required=True, help="Score value (0-1)")
@click.option("--comment", "-c", help="Optional comment")
@click.option("--source", "-s", type=click.Choice(["api", "human", "model"]), default="api")
def scores_add(trace: str, name: str, value: float, comment: str, source: str):
    """Add a score to a trace."""
    payload: dict = {"trace_id": trace, "name": name, "value": value, "source": source}
    if comment:
        payload["comment"] = comment
    resp = _request("post", "/v1/scores", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Score added")
    console.print(f"  Trace: {trace}")
    console.print(f"  {name}: {value}")


@scores.command(name="stats")
@click.option("--name", "-n", help="Score name")
@click.option("--range", "-r", "time_range", default="7d", help="Time range")
def scores_stats(name: str, time_range: str):
    """Show score statistics."""
    params: dict = {"range": time_range}
    if name:
        params["name"] = name
    resp = _request("get", "/v1/scores/stats", params=params)
    data = check_response(resp)

    console.print(f"[cyan]Score Statistics (last {time_range}):[/cyan]")
    console.print()

    table = Table(title="Score Summary", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Count", style="white")
    table.add_column("Mean", style="yellow")
    table.add_column("Median", style="yellow")
    table.add_column("Min", style="dim")
    table.add_column("Max", style="dim")

    for s in data.get("stats", []):
        table.add_row(
            s.get("name", ""),
            str(s.get("count", 0)),
            f"{s.get('mean', 0):.2f}",
            f"{s.get('median', 0):.2f}",
            f"{s.get('min', 0):.2f}",
            f"{s.get('max', 0):.2f}",
        )

    console.print(table)


# ============================================================================
# Datasets (Test Data for Evals)
# ============================================================================


@o11y_group.group()
def datasets():
    """Manage evaluation datasets (Langfuse-style)."""
    pass


@datasets.command(name="list")
def datasets_list():
    """List datasets."""
    resp = _request("get", "/v1/datasets")
    data = check_response(resp)

    table = Table(title="Datasets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Items", style="white")
    table.add_column("Runs", style="green")
    table.add_column("Last Run", style="dim")
    table.add_column("Updated", style="dim")

    for d in data.get("datasets", []):
        table.add_row(
            d.get("name", ""),
            str(d.get("item_count", 0)),
            str(d.get("run_count", 0)),
            d.get("last_run_at", ""),
            d.get("updated_at", ""),
        )

    console.print(table)


@datasets.command(name="create")
@click.argument("name")
@click.option("--description", "-d", help="Dataset description")
def datasets_create(name: str, description: str):
    """Create a dataset."""
    payload: dict = {"name": name}
    if description:
        payload["description"] = description
    resp = _request("post", "/v1/datasets", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Dataset '{name}' created")


@datasets.command(name="delete")
@click.argument("name")
def datasets_delete(name: str):
    """Delete a dataset."""
    resp = _request("delete", f"/v1/datasets/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Dataset '{name}' deleted")


@datasets.command(name="add-item")
@click.argument("dataset_name")
@click.option("--input", "-i", "input_data", required=True, help="Input JSON")
@click.option("--expected", "-e", help="Expected output")
@click.option("--metadata", "-m", help="Metadata JSON")
def datasets_add_item(dataset_name: str, input_data: str, expected: str, metadata: str):
    """Add an item to a dataset."""
    payload: dict = {"input": json.loads(input_data)}
    if expected:
        payload["expected_output"] = expected
    if metadata:
        payload["metadata"] = json.loads(metadata)
    resp = _request("post", f"/v1/datasets/{dataset_name}/items", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Item added to '{dataset_name}'")


@datasets.command(name="import")
@click.argument("dataset_name")
@click.option("--file", "-f", "file_path", required=True, help="File to import (JSON/CSV)")
def datasets_import(dataset_name: str, file_path: str):
    """Import items from file."""
    with open(file_path) as f:
        content = f.read()

    if file_path.endswith(".csv"):
        resp = _request("post", f"/v1/datasets/{dataset_name}/import", content=content, headers={"Content-Type": "text/csv"})
    else:
        resp = _request("post", f"/v1/datasets/{dataset_name}/import", json=json.loads(content))
    data = check_response(resp)
    console.print(f"[green]✓[/green] Imported {data.get('count', '?')} items to '{dataset_name}'")


@datasets.command(name="export")
@click.argument("dataset_name")
@click.option("--output", "-o", help="Output file")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json")
def datasets_export(dataset_name: str, output: str, fmt: str):
    """Export dataset to file."""
    resp = _request("get", f"/v1/datasets/{dataset_name}/export", params={"format": fmt})
    data = check_response(resp)

    out_file = output or f"{dataset_name}.{fmt}"
    content = data.get("data", "")
    with open(out_file, "w") as f:
        f.write(content if isinstance(content, str) else json.dumps(content, indent=2))
    console.print(f"[green]✓[/green] Exported to '{out_file}'")


# ============================================================================
# Sessions (Conversation Tracking)
# ============================================================================


@o11y_group.group()
def sessions():
    """Track conversation sessions (Langfuse-style)."""
    pass


@sessions.command(name="list")
@click.option("--user", "-u", help="Filter by user ID")
@click.option("--limit", "-n", default=50, help="Max results")
def sessions_list(user: str, limit: int):
    """List sessions."""
    params: dict = {"limit": limit}
    if user:
        params["user"] = user
    resp = _request("get", "/v1/sessions", params=params)
    data = check_response(resp)

    table = Table(title="Sessions", box=box.ROUNDED)
    table.add_column("Session ID", style="cyan")
    table.add_column("User", style="white")
    table.add_column("Traces", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Started", style="dim")

    for s in data.get("sessions", []):
        table.add_row(
            s.get("id", "")[:16],
            s.get("user_id", ""),
            str(s.get("trace_count", 0)),
            s.get("duration", ""),
            s.get("created_at", ""),
        )

    console.print(table)


@sessions.command(name="show")
@click.argument("session_id")
def sessions_show(session_id: str):
    """Show session details."""
    resp = _request("get", f"/v1/sessions/{session_id}")
    data = check_response(resp)

    info = (
        f"[cyan]Session ID:[/cyan] {data.get('id', session_id)}\n"
        f"[cyan]User:[/cyan] {data.get('user_id', 'N/A')}\n"
        f"[cyan]Traces:[/cyan] {data.get('trace_count', 0)}\n"
        f"[cyan]Generations:[/cyan] {data.get('generation_count', 0)}\n"
        f"[cyan]Total Tokens:[/cyan] {data.get('total_tokens', 0):,}\n"
        f"[cyan]Total Cost:[/cyan] ${data.get('total_cost', 0):.2f}\n"
        f"[cyan]Duration:[/cyan] {data.get('duration', 'N/A')}\n"
        f"[cyan]Avg Score:[/cyan] {data.get('avg_score', 0):.2f}"
    )
    console.print(Panel(info, title="Session Details", border_style="cyan"))


@sessions.command(name="traces")
@click.argument("session_id")
def sessions_traces(session_id: str):
    """List traces in a session."""
    resp = _request("get", f"/v1/sessions/{session_id}/traces")
    data = check_response(resp)

    table = Table(title=f"Traces in Session '{session_id[:16]}'", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Generations", style="green")
    table.add_column("Tokens", style="yellow")
    table.add_column("Score", style="yellow")
    table.add_column("Time", style="dim")

    for t in data.get("traces", []):
        score = f"{t.get('score', 0):.2f}" if t.get("score") is not None else "-"
        table.add_row(
            t.get("id", "")[:16],
            t.get("name", ""),
            str(t.get("generation_count", 0)),
            str(t.get("total_tokens", 0)),
            score,
            t.get("created_at", ""),
        )

    console.print(table)


# ============================================================================
# LLM Traces (Enhanced for Langfuse)
# ============================================================================


@o11y_group.group()
def llm():
    """LLM-specific observability (Langfuse-style)."""
    pass


@llm.command(name="traces")
@click.option("--user", "-u", help="Filter by user ID")
@click.option("--name", "-n", help="Filter by trace name")
@click.option("--session", "-s", help="Filter by session ID")
@click.option("--limit", default=50, help="Max results")
def llm_traces(user: str, name: str, session: str, limit: int):
    """List LLM traces."""
    params: dict = {"limit": limit}
    if user:
        params["user"] = user
    if name:
        params["name"] = name
    if session:
        params["session_id"] = session
    resp = _request("get", "/v1/llm/traces", params=params)
    data = check_response(resp)

    table = Table(title="LLM Traces", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("User", style="white")
    table.add_column("Generations", style="green")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Duration", style="dim")

    for t in data.get("traces", []):
        table.add_row(
            t.get("id", "")[:16],
            t.get("name", ""),
            t.get("user_id", ""),
            str(t.get("generation_count", 0)),
            str(t.get("total_tokens", 0)),
            f"${t.get('total_cost', 0):.4f}",
            t.get("duration", ""),
        )

    console.print(table)


@llm.command(name="costs")
@click.option("--range", "-r", "time_range", default="30d", help="Time range")
@click.option("--by", type=click.Choice(["model", "user", "prompt", "day"]), default="model")
def llm_costs(time_range: str, by: str):
    """Show LLM cost analysis."""
    resp = _request("get", "/v1/llm/costs", params={"range": time_range, "group_by": by})
    data = check_response(resp)

    console.print(f"[cyan]LLM Cost Analysis (last {time_range}):[/cyan]")
    console.print()

    table = Table(title=f"Costs by {by.title()}", box=box.ROUNDED)
    table.add_column(by.title(), style="cyan")
    table.add_column("Calls", style="white")
    table.add_column("Input Tokens", style="yellow")
    table.add_column("Output Tokens", style="yellow")
    table.add_column("Cost", style="green")

    for item in data.get("costs", []):
        table.add_row(
            item.get("key", ""),
            str(item.get("calls", 0)),
            str(item.get("input_tokens", 0)),
            str(item.get("output_tokens", 0)),
            f"${item.get('cost', 0):.2f}",
        )

    console.print(table)
    total = data.get("total_cost", 0)
    console.print(f"\n[bold]Total Cost:[/bold] ${total:.2f}")


@llm.command(name="latency")
@click.option("--range", "-r", "time_range", default="24h", help="Time range")
@click.option("--by", type=click.Choice(["model", "prompt", "endpoint"]), default="model")
def llm_latency(time_range: str, by: str):
    """Show LLM latency analysis."""
    resp = _request("get", "/v1/llm/latency", params={"range": time_range, "group_by": by})
    data = check_response(resp)

    console.print(f"[cyan]LLM Latency Analysis (last {time_range}):[/cyan]")
    console.print()

    table = Table(title=f"Latency by {by.title()}", box=box.ROUNDED)
    table.add_column(by.title(), style="cyan")
    table.add_column("Calls", style="white")
    table.add_column("P50", style="yellow")
    table.add_column("P90", style="yellow")
    table.add_column("P99", style="red")

    for item in data.get("latency", []):
        table.add_row(
            item.get("key", ""),
            str(item.get("calls", 0)),
            item.get("p50", ""),
            item.get("p90", ""),
            item.get("p99", ""),
        )

    console.print(table)


@llm.command(name="errors")
@click.option("--range", "-r", "time_range", default="24h", help="Time range")
@click.option("--model", "-m", help="Filter by model")
def llm_errors(time_range: str, model: str):
    """Show LLM error analysis."""
    params: dict = {"range": time_range}
    if model:
        params["model"] = model
    resp = _request("get", "/v1/llm/errors", params=params)
    data = check_response(resp)

    console.print(f"[cyan]LLM Errors (last {time_range}):[/cyan]")
    console.print()

    table = Table(title="Error Summary", box=box.ROUNDED)
    table.add_column("Error Type", style="cyan")
    table.add_column("Count", style="red")
    table.add_column("Model", style="white")
    table.add_column("Last Seen", style="dim")

    for e in data.get("errors", []):
        table.add_row(
            e.get("type", ""),
            str(e.get("count", 0)),
            e.get("model", ""),
            e.get("last_seen", ""),
        )

    console.print(table)

    total = sum(e.get("count", 0) for e in data.get("errors", []))
    if total:
        console.print(f"\n[bold]Total Errors:[/bold] {total}")
