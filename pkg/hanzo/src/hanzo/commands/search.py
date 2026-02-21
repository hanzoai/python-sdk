"""Hanzo Search - Search engine CLI.

Hybrid search with lexical (BM25) and vector (semantic) capabilities.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console
from .base import service_request, check_response

SEARCH_URL = os.getenv("HANZO_SEARCH_URL", "https://search.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(SEARCH_URL, method, path, **kwargs)


@click.group(name="search")
def search_group():
    """Hanzo Search - Hybrid search engine.

    \b
    Engines:
      hanzo search create            # Create search engine
      hanzo search list              # List engines
      hanzo search delete            # Delete engine

    \b
    Indexes:
      hanzo search index create      # Create index
      hanzo search index list        # List indexes
      hanzo search index delete      # Delete index
      hanzo search index mapping     # Manage mappings

    \b
    Data:
      hanzo search ingest            # Ingest documents
      hanzo search query             # Search documents
      hanzo search reindex           # Reindex data

    \b
    Pipelines:
      hanzo search pipeline create   # Create ingest pipeline
      hanzo search pipeline list     # List pipelines
    """
    pass


# ============================================================================
# Engine Management
# ============================================================================


@search_group.command(name="create")
@click.argument("name")
@click.option("--mode", "-m", type=click.Choice(["lexical", "vector", "hybrid"]), default="hybrid")
@click.option("--region", "-r", help="Region")
@click.option("--tier", "-t", type=click.Choice(["free", "standard", "dedicated"]), default="standard")
def search_create(name: str, mode: str, region: str, tier: str):
    """Create a search engine."""
    payload = {"name": name, "mode": mode, "tier": tier}
    if region:
        payload["region"] = region

    resp = _request("post", "/v1/engines", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Search engine '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Mode: {mode}")
    console.print(f"  Tier: {tier}")
    if region:
        console.print(f"  Region: {region}")


@search_group.command(name="list")
def search_list():
    """List search engines."""
    resp = _request("get", "/v1/engines")
    data = check_response(resp)
    engines = data.get("engines", data.get("items", []))

    table = Table(title="Search Engines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Mode", style="white")
    table.add_column("Indexes", style="green")
    table.add_column("Documents", style="yellow")
    table.add_column("Status", style="dim")

    for e in engines:
        status = e.get("status", "unknown")
        style = "green" if status == "running" else "yellow"
        table.add_row(
            e.get("name", ""),
            e.get("mode", "-"),
            str(e.get("index_count", 0)),
            str(e.get("document_count", 0)),
            f"[{style}]● {status}[/{style}]",
        )

    console.print(table)
    if not engines:
        console.print("[dim]No search engines found. Create one with 'hanzo search create'[/dim]")


@search_group.command(name="describe")
@click.argument("name")
def search_describe(name: str):
    """Show search engine details."""
    resp = _request("get", f"/v1/engines/{name}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    style = "green" if status == "running" else "yellow"

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Mode:[/cyan] {data.get('mode', '-')}\n"
            f"[cyan]Status:[/cyan] [{style}]● {status}[/{style}]\n"
            f"[cyan]Indexes:[/cyan] {data.get('index_count', 0)}\n"
            f"[cyan]Documents:[/cyan] {data.get('document_count', 0):,}\n"
            f"[cyan]Size:[/cyan] {data.get('size', '0 B')}\n"
            f"[cyan]Queries/day:[/cyan] {data.get('queries_per_day', 0):,}\n"
            f"[cyan]Endpoint:[/cyan] {data.get('endpoint', f'{SEARCH_URL}/{name}')}",
            title="Search Engine Details",
            border_style="cyan",
        )
    )


@search_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def search_delete(name: str, force: bool):
    """Delete a search engine."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete search engine '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/engines/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Search engine '{name}' deleted")


# ============================================================================
# Index Management
# ============================================================================


@search_group.group()
def index():
    """Manage search indexes."""
    pass


@index.command(name="create")
@click.argument("name")
@click.option("--engine", "-e", default="default", help="Search engine")
@click.option("--mode", "-m", type=click.Choice(["lexical", "vector", "hybrid"]), help="Override engine mode")
@click.option("--mapping", help="Mapping JSON or file")
@click.option("--shards", "-s", default=1, help="Number of shards")
@click.option("--replicas", "-r", default=1, help="Number of replicas")
def index_create(name: str, engine: str, mode: str, mapping: str, shards: int, replicas: int):
    """Create a search index."""
    payload = {"name": name, "shards": shards, "replicas": replicas}
    if mode:
        payload["mode"] = mode
    if mapping:
        from pathlib import Path

        if Path(mapping).exists():
            payload["mapping"] = json.loads(Path(mapping).read_text())
        else:
            payload["mapping"] = json.loads(mapping)

    resp = _request("post", f"/v1/engines/{engine}/indexes", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Index '{name}' created in '{engine}'")
    console.print(f"  Shards: {shards}")
    console.print(f"  Replicas: {replicas}")


@index.command(name="list")
@click.option("--engine", "-e", default="default")
def index_list(engine: str):
    """List indexes in an engine."""
    resp = _request("get", f"/v1/engines/{engine}/indexes")
    data = check_response(resp)
    items = data.get("indexes", data.get("items", []))

    table = Table(title=f"Indexes in '{engine}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Mode", style="white")
    table.add_column("Documents", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Health", style="dim")

    for idx in items:
        health = idx.get("health", "unknown")
        style = "green" if health == "green" else "yellow" if health == "yellow" else "red"
        table.add_row(
            idx.get("name", ""),
            idx.get("mode", "-"),
            str(idx.get("document_count", 0)),
            idx.get("size", "0 B"),
            f"[{style}]● {health}[/{style}]",
        )

    console.print(table)
    if not items:
        console.print("[dim]No indexes found[/dim]")


@index.command(name="describe")
@click.argument("name")
@click.option("--engine", "-e", default="default")
def index_describe(name: str, engine: str):
    """Show index details."""
    resp = _request("get", f"/v1/engines/{engine}/indexes/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Index:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Engine:[/cyan] {engine}\n"
            f"[cyan]Mode:[/cyan] {data.get('mode', '-')}\n"
            f"[cyan]Documents:[/cyan] {data.get('document_count', 0):,}\n"
            f"[cyan]Size:[/cyan] {data.get('size', '0 B')}\n"
            f"[cyan]Shards:[/cyan] {data.get('shards', 1)}\n"
            f"[cyan]Replicas:[/cyan] {data.get('replicas', 1)}",
            title="Index Details",
            border_style="cyan",
        )
    )


@index.command(name="delete")
@click.argument("name")
@click.option("--engine", "-e", default="default")
@click.option("--force", "-f", is_flag=True)
def index_delete(name: str, engine: str, force: bool):
    """Delete an index."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete index '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/engines/{engine}/indexes/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Index '{name}' deleted")


@index.command(name="mapping")
@click.argument("name")
@click.option("--engine", "-e", default="default")
@click.option("--get", "get_mapping", is_flag=True, help="Get current mapping")
@click.option("--set", "set_mapping", help="Set mapping (JSON or file)")
def index_mapping(name: str, engine: str, get_mapping: bool, set_mapping: str):
    """Get or set index mapping."""
    if set_mapping:
        from pathlib import Path

        if Path(set_mapping).exists():
            mapping_data = json.loads(Path(set_mapping).read_text())
        else:
            mapping_data = json.loads(set_mapping)

        resp = _request("put", f"/v1/engines/{engine}/indexes/{name}/mapping", json=mapping_data)
        check_response(resp)
        console.print(f"[green]✓[/green] Mapping updated for '{name}'")
    else:
        resp = _request("get", f"/v1/engines/{engine}/indexes/{name}/mapping")
        data = check_response(resp)
        console.print(f"[cyan]Mapping for '{name}':[/cyan]")
        console.print(json.dumps(data.get("mapping", data), indent=2))


# ============================================================================
# Data Operations
# ============================================================================


@search_group.command(name="ingest")
@click.option("--index", "-i", required=True, help="Target index")
@click.option("--from", "source", required=True, help="Source: file, s3://, storage://")
@click.option("--format", "fmt", type=click.Choice(["jsonl", "json", "csv", "parquet"]), default="jsonl")
@click.option("--pipeline", "-p", help="Ingest pipeline to apply")
@click.option("--batch-size", "-b", default=1000, help="Batch size")
@click.option("--engine", "-e", default="default")
def search_ingest(index: str, source: str, fmt: str, pipeline: str, batch_size: int, engine: str):
    """Ingest documents into an index.

    \b
    Examples:
      hanzo search ingest -i products --from products.jsonl
      hanzo search ingest -i logs --from s3://bucket/logs/*.jsonl
      hanzo search ingest -i docs --from storage://mybucket/docs.parquet
    """
    console.print(f"[cyan]Ingesting into '{index}' from '{source}'...[/cyan]")

    payload = {
        "source": source,
        "format": fmt,
        "batch_size": batch_size,
    }
    if pipeline:
        payload["pipeline"] = pipeline

    resp = _request("post", f"/v1/engines/{engine}/indexes/{index}/ingest", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Ingestion complete")
    console.print(f"  Documents: {data.get('ingested', 0):,}")
    console.print(f"  Errors: {data.get('errors', 0)}")
    if data.get("duration"):
        console.print(f"  Duration: {data['duration']}")


@search_group.command(name="query")
@click.option("--index", "-i", required=True, help="Index to search")
@click.option("--q", required=True, help="Query string")
@click.option("--filter", "-f", help="Filter expression")
@click.option("--topk", "-k", default=10, help="Max results")
@click.option("--mode", "-m", type=click.Choice(["lexical", "vector", "hybrid"]))
@click.option("--vector-field", help="Field for vector search")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--engine", "-e", default="default")
def search_query(index: str, q: str, filter: str, topk: int, mode: str, vector_field: str, as_json: bool, engine: str):
    """Search documents.

    \b
    Examples:
      hanzo search query -i products -q "wireless headphones" -k 20
      hanzo search query -i docs -q "machine learning" --mode vector
      hanzo search query -i users -q "john" -f "status=active"
    """
    payload = {"query": q, "top_k": topk}
    if filter:
        payload["filter"] = filter
    if mode:
        payload["mode"] = mode
    if vector_field:
        payload["vector_field"] = vector_field

    resp = _request("post", f"/v1/engines/{engine}/indexes/{index}/query", json=payload)
    data = check_response(resp)
    hits = data.get("hits", data.get("results", []))

    if as_json:
        click.echo(json.dumps(data, indent=2, default=str))
        return

    table = Table(title=f"Results for '{q}' in '{index}'", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Source", style="white")

    for i, hit in enumerate(hits, 1):
        source = hit.get("_source", hit.get("document", {}))
        source_str = json.dumps(source, default=str)[:80] if source else "-"
        table.add_row(
            str(i),
            str(hit.get("_id", hit.get("id", "")))[:24],
            f"{hit.get('_score', hit.get('score', 0)):.4f}",
            source_str,
        )

    console.print(table)
    total = data.get("total", len(hits))
    console.print(f"[dim]{total} total hit(s), showing top {min(topk, len(hits))}[/dim]")


@search_group.command(name="reindex")
@click.option("--from", "source_idx", required=True, help="Source index")
@click.option("--to", "dest_idx", required=True, help="Destination index")
@click.option("--query", "-q", help="Filter query")
@click.option("--pipeline", "-p", help="Transform pipeline")
@click.option("--engine", "-e", default="default")
def search_reindex(source_idx: str, dest_idx: str, query: str, pipeline: str, engine: str):
    """Reindex documents."""
    console.print(f"[cyan]Reindexing from '{source_idx}' to '{dest_idx}'...[/cyan]")

    payload = {"source": source_idx, "destination": dest_idx}
    if query:
        payload["query"] = query
    if pipeline:
        payload["pipeline"] = pipeline

    resp = _request("post", f"/v1/engines/{engine}/reindex", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Reindex complete")
    console.print(f"  Documents: {data.get('reindexed', 0):,}")
    if data.get("duration"):
        console.print(f"  Duration: {data['duration']}")


# ============================================================================
# Pipelines
# ============================================================================


@search_group.group()
def pipeline():
    """Manage ingest pipelines."""
    pass


@pipeline.command(name="create")
@click.argument("name")
@click.option("--engine", "-e", default="default")
@click.option("--config", "-c", help="Pipeline config (JSON or file)")
def pipeline_create(name: str, engine: str, config: str):
    """Create an ingest pipeline."""
    payload = {"name": name}
    if config:
        from pathlib import Path

        if Path(config).exists():
            payload["config"] = json.loads(Path(config).read_text())
        else:
            payload["config"] = json.loads(config)

    resp = _request("post", f"/v1/engines/{engine}/pipelines", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Pipeline '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")


@pipeline.command(name="list")
@click.option("--engine", "-e", default="default")
def pipeline_list(engine: str):
    """List ingest pipelines."""
    resp = _request("get", f"/v1/engines/{engine}/pipelines")
    data = check_response(resp)
    items = data.get("pipelines", data.get("items", []))

    table = Table(title="Ingest Pipelines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Processors", style="white")
    table.add_column("Description", style="dim")

    for p in items:
        processors = p.get("processors", [])
        table.add_row(
            p.get("name", ""),
            str(len(processors)),
            p.get("description", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No pipelines found[/dim]")


@pipeline.command(name="describe")
@click.argument("name")
@click.option("--engine", "-e", default="default")
def pipeline_describe(name: str, engine: str):
    """Show pipeline details."""
    resp = _request("get", f"/v1/engines/{engine}/pipelines/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Description:[/cyan] {data.get('description', '-')}\n"
            f"[cyan]Processors:[/cyan] {len(data.get('processors', []))}\n"
            f"[cyan]Config:[/cyan]\n{json.dumps(data.get('config', {}), indent=2)}",
            title="Pipeline Details",
            border_style="cyan",
        )
    )


@pipeline.command(name="delete")
@click.argument("name")
@click.option("--engine", "-e", default="default")
def pipeline_delete(name: str, engine: str):
    """Delete a pipeline."""
    resp = _request("delete", f"/v1/engines/{engine}/pipelines/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Pipeline '{name}' deleted")


@pipeline.command(name="test")
@click.argument("name")
@click.option("--doc", "-d", help="Test document (JSON)")
@click.option("--engine", "-e", default="default")
def pipeline_test(name: str, doc: str, engine: str):
    """Test a pipeline with sample document."""
    payload = {}
    if doc:
        payload["document"] = json.loads(doc)

    resp = _request("post", f"/v1/engines/{engine}/pipelines/{name}/test", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Pipeline test passed")
    if data.get("output"):
        console.print(f"  Output: {json.dumps(data['output'], indent=2, default=str)}")


# ============================================================================
# Admin
# ============================================================================


@search_group.command(name="stats")
@click.option("--engine", "-e", default="default")
def search_stats(engine: str):
    """Show search engine statistics."""
    resp = _request("get", f"/v1/engines/{engine}/stats")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Engine:[/cyan] {data.get('name', engine)}\n"
            f"[cyan]Indexes:[/cyan] {data.get('index_count', 0)}\n"
            f"[cyan]Documents:[/cyan] {data.get('document_count', 0):,}\n"
            f"[cyan]Size:[/cyan] {data.get('size', '0 B')}\n"
            f"[cyan]Queries/day:[/cyan] {data.get('queries_per_day', 0):,}\n"
            f"[cyan]Avg latency:[/cyan] {data.get('avg_latency_ms', 0)}ms",
            title="Search Statistics",
            border_style="cyan",
        )
    )


@search_group.command(name="backup")
@click.option("--engine", "-e", default="default")
@click.option("--index", "-i", help="Specific index")
@click.option("--output", "-o", help="Output location")
def search_backup(engine: str, index: str, output: str):
    """Backup search data."""
    payload = {"engine": engine}
    if index:
        payload["index"] = index
    if output:
        payload["output"] = output

    resp = _request("post", f"/v1/engines/{engine}/backups", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Backup created")
    console.print(f"  Backup ID: {data.get('id', '-')}")
    console.print(f"  Size: {data.get('size', '-')}")
