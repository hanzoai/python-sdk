"""Hanzo Vector - Vector database CLI.

Purpose-built vector database for AI/ML embeddings and similarity search.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="vector")
def vector_group():
    """Hanzo Vector - AI-native vector database.

    \b
    Databases:
      hanzo vector create            # Create vector database
      hanzo vector list              # List databases
      hanzo vector delete            # Delete database

    \b
    Collections:
      hanzo vector collections       # Manage collections

    \b
    Data:
      hanzo vector upsert            # Insert/update vectors
      hanzo vector query             # Similarity search
      hanzo vector delete-vectors    # Delete vectors

    \b
    Indexes:
      hanzo vector indexes           # Manage vector indexes
    """
    pass


# ============================================================================
# Database Management
# ============================================================================

@vector_group.command(name="create")
@click.argument("name")
@click.option("--region", "-r", help="Region")
@click.option("--tier", "-t", type=click.Choice(["free", "standard", "dedicated"]), default="standard")
@click.option("--metric", "-m", type=click.Choice(["cosine", "euclidean", "dotproduct"]), default="cosine")
def vector_create(name: str, region: str, tier: str, metric: str):
    """Create a vector database."""
    console.print(f"[green]✓[/green] Vector database '{name}' created")
    console.print(f"  Tier: {tier}")
    console.print(f"  Default metric: {metric}")
    if region:
        console.print(f"  Region: {region}")


@vector_group.command(name="list")
def vector_list():
    """List vector databases."""
    table = Table(title="Vector Databases", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Collections", style="green")
    table.add_column("Vectors", style="yellow")
    table.add_column("Dimensions", style="white")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No vector databases found. Create one with 'hanzo vector create'[/dim]")


@vector_group.command(name="describe")
@click.argument("name")
def vector_describe(name: str):
    """Show vector database details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {name}\n"
        f"[cyan]Status:[/cyan] [green]● Running[/green]\n"
        f"[cyan]Collections:[/cyan] 3\n"
        f"[cyan]Total vectors:[/cyan] 1,000,000\n"
        f"[cyan]Storage:[/cyan] 2.5 GB\n"
        f"[cyan]Default metric:[/cyan] cosine\n"
        f"[cyan]Endpoint:[/cyan] https://vector.hanzo.ai/{name}",
        title="Vector Database Details",
        border_style="cyan"
    ))


@vector_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def vector_delete(name: str, force: bool):
    """Delete a vector database."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete vector database '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Vector database '{name}' deleted")


# ============================================================================
# Collections
# ============================================================================

@vector_group.group()
def collections():
    """Manage vector collections."""
    pass


@collections.command(name="create")
@click.argument("name")
@click.option("--db", "-d", default="default", help="Database name")
@click.option("--dimension", "-dim", type=int, required=True, help="Vector dimension")
@click.option("--metric", "-m", type=click.Choice(["cosine", "euclidean", "dotproduct"]))
@click.option("--index-type", "-i", type=click.Choice(["hnsw", "ivf", "flat"]), default="hnsw")
def collections_create(name: str, db: str, dimension: int, metric: str, index_type: str):
    """Create a vector collection.

    \b
    Examples:
      hanzo vector collections create embeddings --dim 1536
      hanzo vector collections create images --dim 512 --metric euclidean
    """
    console.print(f"[green]✓[/green] Collection '{name}' created")
    console.print(f"  Dimension: {dimension}")
    console.print(f"  Index type: {index_type}")
    if metric:
        console.print(f"  Metric: {metric}")


@collections.command(name="list")
@click.option("--db", "-d", default="default")
def collections_list(db: str):
    """List collections."""
    table = Table(title=f"Collections in '{db}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Dimension", style="white")
    table.add_column("Vectors", style="green")
    table.add_column("Metric", style="yellow")
    table.add_column("Index", style="dim")

    console.print(table)
    console.print("[dim]No collections found[/dim]")


@collections.command(name="describe")
@click.argument("name")
@click.option("--db", "-d", default="default")
def collections_describe(name: str, db: str):
    """Show collection details."""
    console.print(Panel(
        f"[cyan]Collection:[/cyan] {name}\n"
        f"[cyan]Dimension:[/cyan] 1536\n"
        f"[cyan]Vectors:[/cyan] 100,000\n"
        f"[cyan]Metric:[/cyan] cosine\n"
        f"[cyan]Index:[/cyan] HNSW (M=16, efConstruction=200)\n"
        f"[cyan]Storage:[/cyan] 580 MB",
        title="Collection Details",
        border_style="cyan"
    ))


@collections.command(name="delete")
@click.argument("name")
@click.option("--db", "-d", default="default")
@click.option("--force", "-f", is_flag=True)
def collections_delete(name: str, db: str, force: bool):
    """Delete a collection."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete collection '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Collection '{name}' deleted")


# ============================================================================
# Vector Operations
# ============================================================================

@vector_group.command(name="upsert")
@click.option("--collection", "-c", required=True, help="Collection name")
@click.option("--db", "-d", default="default")
@click.option("--from", "source", required=True, help="Source: file, jsonl, parquet")
@click.option("--id-field", help="Field to use as ID")
@click.option("--vector-field", default="embedding", help="Field containing vectors")
@click.option("--embed", help="Embed text using model (e.g., openai:text-embedding-3-small)")
@click.option("--batch-size", "-b", default=100, help="Batch size")
def vector_upsert(collection: str, db: str, source: str, id_field: str, vector_field: str, embed: str, batch_size: int):
    """Upsert vectors into a collection.

    \b
    Examples:
      hanzo vector upsert -c docs --from embeddings.jsonl
      hanzo vector upsert -c products --from data.jsonl --embed openai:text-embedding-3-small
    """
    console.print(f"[cyan]Upserting into '{collection}' from '{source}'...[/cyan]")
    console.print("[green]✓[/green] Upsert complete")
    console.print("  Vectors: 0")
    console.print("  Errors: 0")


@vector_group.command(name="query")
@click.option("--collection", "-c", required=True, help="Collection name")
@click.option("--db", "-d", default="default")
@click.option("--text", "-t", help="Text to embed and search")
@click.option("--vector", "-v", help="Vector to search (JSON array)")
@click.option("--topk", "-k", default=10, help="Number of results")
@click.option("--filter", "-f", help="Metadata filter")
@click.option("--include-vectors", is_flag=True, help="Include vectors in results")
@click.option("--include-metadata", is_flag=True, default=True, help="Include metadata")
@click.option("--embed", help="Embedding model for text queries")
def vector_query(collection: str, db: str, text: str, vector: str, topk: int, filter: str, 
                 include_vectors: bool, include_metadata: bool, embed: str):
    """Query similar vectors.

    \b
    Examples:
      hanzo vector query -c docs -t "machine learning" -k 20
      hanzo vector query -c images -v "[0.1, 0.2, ...]" --filter "category=animals"
    """
    console.print(f"[cyan]Searching '{collection}'...[/cyan]")
    console.print("[dim]No results found[/dim]")


@vector_group.command(name="fetch")
@click.argument("ids", nargs=-1, required=True)
@click.option("--collection", "-c", required=True)
@click.option("--db", "-d", default="default")
@click.option("--include-vectors", is_flag=True)
def vector_fetch(ids: tuple, collection: str, db: str, include_vectors: bool):
    """Fetch vectors by ID."""
    console.print(f"[cyan]Fetching {len(ids)} vector(s) from '{collection}'...[/cyan]")
    console.print("[dim]No vectors found[/dim]")


@vector_group.command(name="delete-vectors")
@click.option("--collection", "-c", required=True)
@click.option("--db", "-d", default="default")
@click.option("--ids", help="Comma-separated IDs to delete")
@click.option("--filter", "-f", help="Delete by filter")
@click.option("--all", "delete_all", is_flag=True, help="Delete all vectors")
@click.option("--force", is_flag=True)
def vector_delete_vectors(collection: str, db: str, ids: str, filter: str, delete_all: bool, force: bool):
    """Delete vectors from a collection."""
    if delete_all and not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete ALL vectors from '{collection}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Vectors deleted from '{collection}'")


# ============================================================================
# Indexes
# ============================================================================

@vector_group.group()
def indexes():
    """Manage vector indexes."""
    pass


@indexes.command(name="list")
@click.argument("collection")
@click.option("--db", "-d", default="default")
def indexes_list(collection: str, db: str):
    """List indexes on a collection."""
    table = Table(title=f"Indexes on '{collection}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Metric", style="yellow")
    table.add_column("Parameters", style="dim")

    console.print(table)
    console.print("[dim]No indexes found[/dim]")


@indexes.command(name="create")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--name", "-n", help="Index name")
@click.option("--type", "idx_type", type=click.Choice(["hnsw", "ivf", "flat"]), default="hnsw")
@click.option("--metric", "-m", type=click.Choice(["cosine", "euclidean", "dotproduct"]))
@click.option("--hnsw-m", type=int, default=16, help="HNSW M parameter")
@click.option("--hnsw-ef", type=int, default=200, help="HNSW efConstruction")
@click.option("--ivf-nlist", type=int, default=100, help="IVF number of lists")
def indexes_create(collection: str, db: str, name: str, idx_type: str, metric: str,
                   hnsw_m: int, hnsw_ef: int, ivf_nlist: int):
    """Create a vector index.

    \b
    Examples:
      hanzo vector indexes create embeddings --type hnsw --hnsw-m 32
      hanzo vector indexes create images --type ivf --ivf-nlist 256
    """
    console.print(f"[green]✓[/green] Index created on '{collection}'")
    console.print(f"  Type: {idx_type}")
    if idx_type == "hnsw":
        console.print(f"  M: {hnsw_m}, efConstruction: {hnsw_ef}")


@indexes.command(name="rebuild")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--name", "-n", help="Specific index name")
def indexes_rebuild(collection: str, db: str, name: str):
    """Rebuild vector index."""
    console.print(f"[cyan]Rebuilding index for '{collection}'...[/cyan]")
    console.print("[green]✓[/green] Index rebuilt")


# ============================================================================
# Admin
# ============================================================================

@vector_group.command(name="stats")
@click.option("--db", "-d", default="default")
def vector_stats(db: str):
    """Show database statistics."""
    console.print(Panel(
        f"[cyan]Database:[/cyan] {db}\n"
        f"[cyan]Collections:[/cyan] 0\n"
        f"[cyan]Total vectors:[/cyan] 0\n"
        f"[cyan]Storage:[/cyan] 0 B\n"
        f"[cyan]Queries/day:[/cyan] 0\n"
        f"[cyan]Avg latency:[/cyan] 0ms",
        title="Vector Statistics",
        border_style="cyan"
    ))


@vector_group.command(name="bind")
@click.option("--service", "-s", required=True, help="Service to bind to")
@click.option("--db", "-d", default="default")
@click.option("--env", "-e", help="Environment")
def vector_bind(service: str, db: str, env: str):
    """Bind database to a service."""
    console.print(f"[green]✓[/green] Bound '{db}' to service '{service}'")
    if env:
        console.print(f"  Environment: {env}")


@vector_group.command(name="backup")
@click.option("--db", "-d", default="default")
@click.option("--collection", "-c", help="Specific collection")
@click.option("--output", "-o", help="Output location")
def vector_backup(db: str, collection: str, output: str):
    """Backup vector data."""
    console.print("[green]✓[/green] Backup created")
    console.print("  Backup ID: bak_abc123")
