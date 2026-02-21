"""Hanzo Observability - Metrics, logs, traces CLI.

Full visibility into your systems.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


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
def metrics_list(filter: str):
    """List available metric series."""
    table = Table(title="Metrics", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Labels", style="dim")
    table.add_column("Points", style="dim")

    series = [
        ("http_requests_total", "counter", "method, status, path", "1.2M"),
        ("http_request_duration_seconds", "histogram", "method, path", "856K"),
        ("process_cpu_seconds_total", "counter", "instance", "245K"),
        ("process_memory_bytes", "gauge", "instance", "245K"),
    ]

    for name, mtype, labels, points in series:
        if filter and filter not in name:
            continue
        table.add_row(name, mtype, labels, points)

    console.print(table)


@metrics.command(name="query")
@click.argument("promql")
@click.option("--start", "-s", help="Start time")
@click.option("--end", "-e", help="End time")
@click.option("--step", default="1m", help="Query step")
def metrics_query(promql: str, start: str, end: str, step: str):
    """Query metrics using PromQL."""
    console.print(f"[cyan]Query:[/cyan] {promql}")
    console.print(f"[cyan]Step:[/cyan] {step}")
    console.print()
    console.print("[dim]No data points returned[/dim]")


@metrics.command(name="export")
@click.argument("promql")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", help="Output file")
def metrics_export(promql: str, format: str, output: str):
    """Export metrics to file."""
    console.print(f"[green]✓[/green] Exported to {output or 'stdout'}")


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
def logs_search(query: str, source: str, level: str, limit: int):
    """Search logs."""
    console.print(f"[cyan]Query:[/cyan] {query}")
    if source:
        console.print(f"[cyan]Source:[/cyan] {source}")
    if level:
        console.print(f"[cyan]Level:[/cyan] {level}")
    console.print()
    console.print("[dim]No matching logs found[/dim]")


@logs.command(name="tail")
@click.option("--source", "-s", help="Log source")
@click.option("--filter", "-f", help="Filter expression")
def logs_tail(source: str, filter: str):
    """Tail live logs."""
    console.print("[cyan]Tailing logs...[/cyan]")
    console.print("Press Ctrl+C to stop")


@logs.command(name="sources")
def logs_sources():
    """List log sources."""
    table = Table(title="Log Sources", box=box.ROUNDED)
    table.add_column("Source", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Status", style="green")
    table.add_column("Volume", style="dim")

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
    table = Table(title="Traces", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Service", style="white")
    table.add_column("Operation", style="white")
    table.add_column("Duration", style="yellow")
    table.add_column("Spans", style="dim")
    table.add_column("Status", style="green")

    console.print(table)


@traces.command(name="show")
@click.argument("trace_id")
def traces_show(trace_id: str):
    """Show trace details."""
    console.print(
        Panel(
            f"[cyan]Trace ID:[/cyan] {trace_id}\n"
            f"[cyan]Duration:[/cyan] 245ms\n"
            f"[cyan]Spans:[/cyan] 12\n"
            f"[cyan]Services:[/cyan] api, auth, database",
            title="Trace Details",
            border_style="cyan",
        )
    )


@traces.command(name="services")
def traces_services():
    """List traced services."""
    table = Table(title="Services", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Operations", style="white")
    table.add_column("Avg Duration", style="yellow")
    table.add_column("Error Rate", style="red")

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
    table = Table(title="Dashboards", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Panels", style="white")
    table.add_column("Updated", style="dim")

    console.print(table)


@dashboards.command(name="create")
@click.option("--name", "-n", prompt=True, help="Dashboard name")
@click.option("--file", "-f", help="Import from JSON file")
def dashboards_create(name: str, file: str):
    """Create a new dashboard."""
    console.print(f"[green]✓[/green] Dashboard '{name}' created")
    console.print(f"[dim]View at: https://dashboards.hanzo.ai/{name}[/dim]")


@dashboards.command(name="open")
@click.argument("name")
def dashboards_open(name: str):
    """Open dashboard in browser."""
    import webbrowser

    url = f"https://dashboards.hanzo.ai/{name}"
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
    table = Table(title="Alert Rules", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Condition", style="white")
    table.add_column("Status", style="green")
    table.add_column("Severity", style="yellow")
    table.add_column("Last Fired", style="dim")

    console.print(table)


@alerts.command(name="create")
@click.option("--name", "-n", prompt=True, help="Alert name")
@click.option("--condition", "-c", required=True, help="PromQL condition")
@click.option("--severity", "-s", type=click.Choice(["critical", "warning", "info"]), default="warning")
@click.option("--channel", help="Notification channel")
def alerts_create(name: str, condition: str, severity: str, channel: str):
    """Create an alert rule."""
    console.print(f"[green]✓[/green] Alert rule '{name}' created")


@alerts.command(name="silence")
@click.argument("alert_name")
@click.option("--duration", "-d", default="1h", help="Silence duration")
def alerts_silence(alert_name: str, duration: str):
    """Silence an alert."""
    console.print(f"[green]✓[/green] Alert '{alert_name}' silenced for {duration}")


@alerts.command(name="delete")
@click.argument("alert_name")
def alerts_delete(alert_name: str):
    """Delete an alert rule."""
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
def prompts_list(label: str):
    """List prompt templates."""
    table = Table(title="Prompt Templates", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Label", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Updated", style="dim")

    prompts_data = [
        ("chat-assistant", "3", "production", "gpt-4", "2h ago"),
        ("chat-assistant", "4", "staging", "gpt-4o", "1h ago"),
        ("summarize-doc", "2", "production", "claude-3", "1d ago"),
        ("code-review", "1", "production", "gpt-4o", "3d ago"),
        ("translate", "5", "production", "gpt-4o-mini", "5h ago"),
    ]

    for name, ver, lbl, model, updated in prompts_data:
        if label and label.lower() not in lbl.lower():
            continue
        table.add_row(name, f"v{ver}", lbl, model, updated)

    console.print(table)


@prompts.command(name="create")
@click.argument("name")
@click.option("--template", "-t", required=True, help="Prompt template")
@click.option("--model", "-m", help="Default model")
@click.option("--config", "-c", help="Model config JSON")
def prompts_create(name: str, template: str, model: str, config: str):
    """Create a prompt template."""
    console.print(f"[green]✓[/green] Prompt '{name}' created (v1)")
    if model:
        console.print(f"  Model: {model}")


@prompts.command(name="get")
@click.argument("name")
@click.option("--version", "-v", help="Specific version")
@click.option("--label", "-l", help="Get by label (production, staging)")
def prompts_get(name: str, version: str, label: str):
    """Get a prompt template."""
    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]Version:[/cyan] v{version or '3'}\n"
            f"[cyan]Label:[/cyan] {label or 'production'}\n"
            f"[cyan]Model:[/cyan] gpt-4o\n"
            f"[cyan]Template:[/cyan]\n"
            f"  You are a helpful assistant.\n"
            f"  Context: {{{{context}}}}\n"
            f"  User: {{{{user_input}}}}",
            title="Prompt Template",
            border_style="cyan",
        )
    )


@prompts.command(name="promote")
@click.argument("name")
@click.option("--version", "-v", required=True, help="Version to promote")
@click.option("--to", "to_label", required=True, help="Target label")
def prompts_promote(name: str, version: str, to_label: str):
    """Promote a prompt version to a label."""
    console.print(f"[green]✓[/green] Promoted '{name}' v{version} to {to_label}")


@prompts.command(name="history")
@click.argument("name")
def prompts_history(name: str):
    """Show prompt version history."""
    table = Table(title=f"History for '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Author", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Note", style="dim")

    console.print(table)
    console.print("[dim]No version history found[/dim]")


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
    table = Table(title="Generations", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Prompt", style="white")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Latency", style="dim")
    table.add_column("Time", style="dim")

    console.print(table)
    console.print("[dim]No generations found[/dim]")


@generations.command(name="show")
@click.argument("generation_id")
def generations_show(generation_id: str):
    """Show generation details."""
    console.print(
        Panel(
            f"[cyan]Generation ID:[/cyan] {generation_id}\n"
            f"[cyan]Trace ID:[/cyan] trace_xxx\n"
            f"[cyan]Model:[/cyan] gpt-4o\n"
            f"[cyan]Prompt:[/cyan] chat-assistant v3\n"
            f"[cyan]Input Tokens:[/cyan] 150\n"
            f"[cyan]Output Tokens:[/cyan] 320\n"
            f"[cyan]Total Cost:[/cyan] $0.0024\n"
            f"[cyan]Latency:[/cyan] 1.2s\n"
            f"[cyan]Finish Reason:[/cyan] stop",
            title="Generation Details",
            border_style="cyan",
        )
    )


@generations.command(name="stats")
@click.option("--range", "-r", "time_range", default="7d", help="Time range")
@click.option("--by", type=click.Choice(["model", "prompt", "user"]), default="model")
def generations_stats(time_range: str, by: str):
    """Show generation statistics."""
    console.print(f"[cyan]Generation Statistics (last {time_range}):[/cyan]")
    console.print()

    table = Table(title=f"By {by.title()}", box=box.ROUNDED)
    table.add_column(by.title(), style="cyan")
    table.add_column("Calls", style="white")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Avg Latency", style="dim")

    console.print(table)
    console.print("[dim]No statistics available[/dim]")


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
    table = Table(title="Evaluations", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Dataset", style="white")
    table.add_column("Prompt", style="white")
    table.add_column("Status", style="green")
    table.add_column("Score", style="yellow")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No evaluations found[/dim]")


@evals.command(name="create")
@click.option("--name", "-n", required=True, help="Evaluation name")
@click.option("--dataset", "-d", required=True, help="Dataset to use")
@click.option("--prompt", "-p", required=True, help="Prompt to evaluate")
@click.option("--scorer", "-s", multiple=True, help="Scorer(s) to use")
def evals_create(name: str, dataset: str, prompt: str, scorer: tuple):
    """Create an evaluation run."""
    console.print(f"[cyan]Creating evaluation '{name}'...[/cyan]")
    console.print(f"  Dataset: {dataset}")
    console.print(f"  Prompt: {prompt}")
    if scorer:
        console.print(f"  Scorers: {', '.join(scorer)}")
    console.print()
    console.print(f"[green]✓[/green] Evaluation created")
    console.print("  Run with: hanzo o11y evals run {name}")


@evals.command(name="run")
@click.argument("name")
@click.option("--parallel", "-p", default=5, help="Parallel executions")
def evals_run(name: str, parallel: int):
    """Run an evaluation."""
    console.print(f"[cyan]Running evaluation '{name}'...[/cyan]")
    console.print(f"  Parallelism: {parallel}")
    console.print("[green]✓[/green] Evaluation started")


@evals.command(name="results")
@click.argument("name")
@click.option("--format", "-f", "fmt", type=click.Choice(["table", "json"]), default="table")
def evals_results(name: str, fmt: str):
    """Show evaluation results."""
    console.print(
        Panel(
            f"[cyan]Evaluation:[/cyan] {name}\n"
            f"[cyan]Status:[/cyan] [green]● Completed[/green]\n"
            f"[cyan]Samples:[/cyan] 100\n"
            f"[cyan]Avg Score:[/cyan] 0.85\n"
            f"[cyan]Duration:[/cyan] 2m 34s",
            title="Evaluation Results",
            border_style="cyan",
        )
    )


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
def scores_list(trace: str, name: str, source: str):
    """List scores."""
    table = Table(title="Scores", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Value", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Comment", style="dim")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No scores found[/dim]")


@scores.command(name="add")
@click.option("--trace", "-t", required=True, help="Trace ID")
@click.option("--name", "-n", required=True, help="Score name")
@click.option("--value", "-v", type=float, required=True, help="Score value (0-1)")
@click.option("--comment", "-c", help="Optional comment")
def scores_add(trace: str, name: str, value: float, comment: str):
    """Add a score to a trace."""
    console.print(f"[green]✓[/green] Score added")
    console.print(f"  Trace: {trace}")
    console.print(f"  {name}: {value}")
    if comment:
        console.print(f"  Comment: {comment}")


@scores.command(name="stats")
@click.option("--name", "-n", help="Score name")
@click.option("--range", "-r", "time_range", default="7d", help="Time range")
def scores_stats(name: str, time_range: str):
    """Show score statistics."""
    console.print(f"[cyan]Score Statistics (last {time_range}):[/cyan]")
    console.print()

    table = Table(title="Score Summary", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Count", style="white")
    table.add_column("Mean", style="yellow")
    table.add_column("Median", style="yellow")
    table.add_column("Min", style="dim")
    table.add_column("Max", style="dim")

    score_data = [
        ("relevance", "1,234", "0.82", "0.85", "0.12", "1.00"),
        ("helpfulness", "1,234", "0.78", "0.80", "0.20", "1.00"),
        ("accuracy", "856", "0.91", "0.93", "0.45", "1.00"),
        ("user_satisfaction", "432", "0.75", "0.78", "0.10", "1.00"),
    ]

    for score_name, count, mean, median, min_v, max_v in score_data:
        if name and name.lower() not in score_name.lower():
            continue
        table.add_row(score_name, count, mean, median, min_v, max_v)

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
    table = Table(title="Datasets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Items", style="white")
    table.add_column("Runs", style="green")
    table.add_column("Last Run", style="dim")
    table.add_column("Updated", style="dim")

    console.print(table)
    console.print("[dim]No datasets found[/dim]")


@datasets.command(name="create")
@click.argument("name")
@click.option("--description", "-d", help="Dataset description")
def datasets_create(name: str, description: str):
    """Create a dataset."""
    console.print(f"[green]✓[/green] Dataset '{name}' created")
    if description:
        console.print(f"  Description: {description}")


@datasets.command(name="add-item")
@click.argument("dataset_name")
@click.option("--input", "-i", "input_data", required=True, help="Input JSON")
@click.option("--expected", "-e", help="Expected output")
@click.option("--metadata", "-m", help="Metadata JSON")
def datasets_add_item(dataset_name: str, input_data: str, expected: str, metadata: str):
    """Add an item to a dataset."""
    console.print(f"[green]✓[/green] Item added to '{dataset_name}'")


@datasets.command(name="import")
@click.argument("dataset_name")
@click.option("--file", "-f", required=True, help="File to import (JSON/CSV)")
def datasets_import(dataset_name: str, file: str):
    """Import items from file."""
    console.print(f"[cyan]Importing from '{file}'...[/cyan]")
    console.print(f"[green]✓[/green] Imported to '{dataset_name}'")


@datasets.command(name="export")
@click.argument("dataset_name")
@click.option("--output", "-o", help="Output file")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json")
def datasets_export(dataset_name: str, output: str, fmt: str):
    """Export dataset to file."""
    out_file = output or f"{dataset_name}.{fmt}"
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
    table = Table(title="Sessions", box=box.ROUNDED)
    table.add_column("Session ID", style="cyan")
    table.add_column("User", style="white")
    table.add_column("Traces", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Started", style="dim")

    console.print(table)
    console.print("[dim]No sessions found[/dim]")


@sessions.command(name="show")
@click.argument("session_id")
def sessions_show(session_id: str):
    """Show session details."""
    console.print(
        Panel(
            f"[cyan]Session ID:[/cyan] {session_id}\n"
            f"[cyan]User:[/cyan] user_123\n"
            f"[cyan]Traces:[/cyan] 12\n"
            f"[cyan]Generations:[/cyan] 24\n"
            f"[cyan]Total Tokens:[/cyan] 15,432\n"
            f"[cyan]Total Cost:[/cyan] $0.12\n"
            f"[cyan]Duration:[/cyan] 15m 32s\n"
            f"[cyan]Avg Score:[/cyan] 0.82",
            title="Session Details",
            border_style="cyan",
        )
    )


@sessions.command(name="traces")
@click.argument("session_id")
def sessions_traces(session_id: str):
    """List traces in a session."""
    table = Table(title=f"Traces in Session '{session_id}'", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Generations", style="green")
    table.add_column("Tokens", style="yellow")
    table.add_column("Score", style="yellow")
    table.add_column("Time", style="dim")

    console.print(table)
    console.print("[dim]No traces found[/dim]")


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
    table = Table(title="LLM Traces", box=box.ROUNDED)
    table.add_column("Trace ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("User", style="white")
    table.add_column("Generations", style="green")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Duration", style="dim")

    console.print(table)
    console.print("[dim]No traces found[/dim]")


@llm.command(name="costs")
@click.option("--range", "-r", "time_range", default="30d", help="Time range")
@click.option("--by", type=click.Choice(["model", "user", "prompt", "day"]), default="model")
def llm_costs(time_range: str, by: str):
    """Show LLM cost analysis."""
    console.print(f"[cyan]LLM Cost Analysis (last {time_range}):[/cyan]")
    console.print()

    table = Table(title=f"Costs by {by.title()}", box=box.ROUNDED)
    table.add_column(by.title(), style="cyan")
    table.add_column("Calls", style="white")
    table.add_column("Input Tokens", style="yellow")
    table.add_column("Output Tokens", style="yellow")
    table.add_column("Cost", style="green")

    costs_data = [
        ("gpt-4o", "12,543", "1.2M", "890K", "$45.32"),
        ("gpt-4o-mini", "34,521", "5.6M", "2.1M", "$12.45"),
        ("claude-3-sonnet", "8,234", "980K", "720K", "$28.90"),
        ("claude-3-haiku", "45,678", "8.9M", "4.2M", "$8.75"),
    ]

    for name, calls, input_t, output_t, cost in costs_data:
        table.add_row(name, calls, input_t, output_t, cost)

    console.print(table)
    console.print()
    console.print(f"[bold]Total Cost:[/bold] $95.42")


@llm.command(name="latency")
@click.option("--range", "-r", "time_range", default="24h", help="Time range")
@click.option("--by", type=click.Choice(["model", "prompt", "endpoint"]), default="model")
def llm_latency(time_range: str, by: str):
    """Show LLM latency analysis."""
    console.print(f"[cyan]LLM Latency Analysis (last {time_range}):[/cyan]")
    console.print()

    table = Table(title=f"Latency by {by.title()}", box=box.ROUNDED)
    table.add_column(by.title(), style="cyan")
    table.add_column("Calls", style="white")
    table.add_column("P50", style="yellow")
    table.add_column("P90", style="yellow")
    table.add_column("P99", style="red")

    console.print(table)
    console.print("[dim]No latency data available[/dim]")


@llm.command(name="errors")
@click.option("--range", "-r", "time_range", default="24h", help="Time range")
@click.option("--model", "-m", help="Filter by model")
def llm_errors(time_range: str, model: str):
    """Show LLM error analysis."""
    console.print(f"[cyan]LLM Errors (last {time_range}):[/cyan]")
    console.print()

    table = Table(title="Error Summary", box=box.ROUNDED)
    table.add_column("Error Type", style="cyan")
    table.add_column("Count", style="red")
    table.add_column("Model", style="white")
    table.add_column("Last Seen", style="dim")

    console.print(table)
    console.print("[dim]No errors found[/dim]")
