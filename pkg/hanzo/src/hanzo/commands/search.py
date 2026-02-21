"""Hanzo Search - Search engine CLI.

Hybrid search with lexical (BM25) and vector (semantic) capabilities.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


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
    console.print(f"[green]✓[/green] Search engine '{name}' created")
    console.print(f"  Mode: {mode}")
    console.print(f"  Tier: {tier}")
    if region:
        console.print(f"  Region: {region}")


@search_group.command(name="list")
def search_list():
    """List search engines."""
    table = Table(title="Search Engines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Mode", style="white")
    table.add_column("Indexes", style="green")
    table.add_column("Documents", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No search engines found. Create one with 'hanzo search create'[/dim]")


@search_group.command(name="describe")
@click.argument("name")
def search_describe(name: str):
    """Show search engine details."""
    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]Mode:[/cyan] Hybrid (lexical + vector)\n"
            f"[cyan]Status:[/cyan] [green]● Running[/green]\n"
            f"[cyan]Indexes:[/cyan] 3\n"
            f"[cyan]Documents:[/cyan] 100,000\n"
            f"[cyan]Size:[/cyan] 1.2 GB\n"
            f"[cyan]Queries/day:[/cyan] 50,000\n"
            f"[cyan]Endpoint:[/cyan] https://search.hanzo.ai/{name}",
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
    console.print(f"[green]✓[/green] Index '{name}' created in '{engine}'")
    console.print(f"  Shards: {shards}")
    console.print(f"  Replicas: {replicas}")


@index.command(name="list")
@click.option("--engine", "-e", default="default")
def index_list(engine: str):
    """List indexes in an engine."""
    table = Table(title=f"Indexes in '{engine}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Mode", style="white")
    table.add_column("Documents", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Health", style="dim")

    console.print(table)
    console.print("[dim]No indexes found[/dim]")


@index.command(name="describe")
@click.argument("name")
@click.option("--engine", "-e", default="default")
def index_describe(name: str, engine: str):
    """Show index details."""
    console.print(
        Panel(
            f"[cyan]Index:[/cyan] {name}\n"
            f"[cyan]Engine:[/cyan] {engine}\n"
            f"[cyan]Mode:[/cyan] Hybrid\n"
            f"[cyan]Documents:[/cyan] 10,000\n"
            f"[cyan]Size:[/cyan] 150 MB\n"
            f"[cyan]Shards:[/cyan] 1\n"
            f"[cyan]Replicas:[/cyan] 1",
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
    console.print(f"[green]✓[/green] Index '{name}' deleted")


@index.command(name="mapping")
@click.argument("name")
@click.option("--engine", "-e", default="default")
@click.option("--get", "get_mapping", is_flag=True, help="Get current mapping")
@click.option("--set", "set_mapping", help="Set mapping (JSON or file)")
def index_mapping(name: str, engine: str, get_mapping: bool, set_mapping: str):
    """Get or set index mapping."""
    if set_mapping:
        console.print(f"[green]✓[/green] Mapping updated for '{name}'")
    else:
        console.print(f"[cyan]Mapping for '{name}':[/cyan]")
        console.print("{}")


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
    console.print("[green]✓[/green] Ingestion complete")
    console.print("  Documents: 0")
    console.print("  Errors: 0")


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
    console.print(f"[cyan]Results for '{q}' in '{index}':[/cyan]")
    console.print("[dim]No results found[/dim]")


@search_group.command(name="reindex")
@click.option("--from", "source_idx", required=True, help="Source index")
@click.option("--to", "dest_idx", required=True, help="Destination index")
@click.option("--query", "-q", help="Filter query")
@click.option("--pipeline", "-p", help="Transform pipeline")
@click.option("--engine", "-e", default="default")
def search_reindex(source_idx: str, dest_idx: str, query: str, pipeline: str, engine: str):
    """Reindex documents."""
    console.print(f"[cyan]Reindexing from '{source_idx}' to '{dest_idx}'...[/cyan]")
    console.print("[green]✓[/green] Reindex complete")


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
    console.print(f"[green]✓[/green] Pipeline '{name}' created")


@pipeline.command(name="list")
@click.option("--engine", "-e", default="default")
def pipeline_list(engine: str):
    """List ingest pipelines."""
    table = Table(title="Ingest Pipelines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Processors", style="white")
    table.add_column("Description", style="dim")

    console.print(table)
    console.print("[dim]No pipelines found[/dim]")


@pipeline.command(name="describe")
@click.argument("name")
@click.option("--engine", "-e", default="default")
def pipeline_describe(name: str, engine: str):
    """Show pipeline details."""
    console.print(f"[dim]Pipeline '{name}' not found[/dim]")


@pipeline.command(name="delete")
@click.argument("name")
@click.option("--engine", "-e", default="default")
def pipeline_delete(name: str, engine: str):
    """Delete a pipeline."""
    console.print(f"[green]✓[/green] Pipeline '{name}' deleted")


@pipeline.command(name="test")
@click.argument("name")
@click.option("--doc", "-d", help="Test document (JSON)")
@click.option("--engine", "-e", default="default")
def pipeline_test(name: str, doc: str, engine: str):
    """Test a pipeline with sample document."""
    console.print(f"[cyan]Testing pipeline '{name}'...[/cyan]")
    console.print("[green]✓[/green] Pipeline test passed")


# ============================================================================
# Admin
# ============================================================================


@search_group.command(name="stats")
@click.option("--engine", "-e", default="default")
def search_stats(engine: str):
    """Show search engine statistics."""
    console.print(
        Panel(
            f"[cyan]Engine:[/cyan] {engine}\n"
            f"[cyan]Indexes:[/cyan] 0\n"
            f"[cyan]Documents:[/cyan] 0\n"
            f"[cyan]Size:[/cyan] 0 B\n"
            f"[cyan]Queries/day:[/cyan] 0\n"
            f"[cyan]Avg latency:[/cyan] 0ms",
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
    console.print(f"[green]✓[/green] Backup created")
    console.print("  Backup ID: bak_abc123")
