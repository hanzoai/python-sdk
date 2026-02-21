"""Hanzo Vector - Vector database CLI.

Purpose-built vector database for AI/ML embeddings and similarity search.
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

VECTOR_URL = os.getenv("HANZO_VECTOR_URL", "https://vector.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(VECTOR_URL, method, path, **kwargs)


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
    payload = {"name": name, "tier": tier, "default_metric": metric}
    if region:
        payload["region"] = region

    resp = _request("post", "/v1/databases", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Vector database '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Tier: {tier}")
    console.print(f"  Default metric: {metric}")
    if region:
        console.print(f"  Region: {region}")


@vector_group.command(name="list")
def vector_list():
    """List vector databases."""
    resp = _request("get", "/v1/databases")
    data = check_response(resp)
    dbs = data.get("databases", data.get("items", []))

    table = Table(title="Vector Databases", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Collections", style="green")
    table.add_column("Vectors", style="yellow")
    table.add_column("Dimensions", style="white")
    table.add_column("Status", style="dim")

    for db in dbs:
        status = db.get("status", "unknown")
        style = "green" if status == "running" else "yellow"
        table.add_row(
            db.get("name", ""),
            str(db.get("collection_count", 0)),
            str(db.get("vector_count", 0)),
            str(db.get("dimensions", "-")),
            f"[{style}]● {status}[/{style}]",
        )

    console.print(table)
    if not dbs:
        console.print("[dim]No vector databases found. Create one with 'hanzo vector create'[/dim]")


@vector_group.command(name="describe")
@click.argument("name")
def vector_describe(name: str):
    """Show vector database details."""
    resp = _request("get", f"/v1/databases/{name}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    style = "green" if status == "running" else "yellow"

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Status:[/cyan] [{style}]● {status}[/{style}]\n"
            f"[cyan]Collections:[/cyan] {data.get('collection_count', 0)}\n"
            f"[cyan]Total vectors:[/cyan] {data.get('vector_count', 0):,}\n"
            f"[cyan]Storage:[/cyan] {data.get('storage', '0 B')}\n"
            f"[cyan]Default metric:[/cyan] {data.get('default_metric', 'cosine')}\n"
            f"[cyan]Region:[/cyan] {data.get('region', '-')}\n"
            f"[cyan]Endpoint:[/cyan] {data.get('endpoint', f'{VECTOR_URL}/{name}')}",
            title="Vector Database Details",
            border_style="cyan",
        )
    )


@vector_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def vector_delete(name: str, force: bool):
    """Delete a vector database."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete vector database '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/databases/{name}")
    check_response(resp)
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
    payload = {"name": name, "dimension": dimension, "index_type": index_type}
    if metric:
        payload["metric"] = metric

    resp = _request("post", f"/v1/databases/{db}/collections", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Collection '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Dimension: {dimension}")
    console.print(f"  Index type: {index_type}")
    if metric:
        console.print(f"  Metric: {metric}")


@collections.command(name="list")
@click.option("--db", "-d", default="default")
def collections_list(db: str):
    """List collections."""
    resp = _request("get", f"/v1/databases/{db}/collections")
    data = check_response(resp)
    items = data.get("collections", data.get("items", []))

    table = Table(title=f"Collections in '{db}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Dimension", style="white")
    table.add_column("Vectors", style="green")
    table.add_column("Metric", style="yellow")
    table.add_column("Index", style="dim")

    for c in items:
        table.add_row(
            c.get("name", ""),
            str(c.get("dimension", "-")),
            str(c.get("vector_count", 0)),
            c.get("metric", "cosine"),
            c.get("index_type", "hnsw"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No collections found[/dim]")


@collections.command(name="describe")
@click.argument("name")
@click.option("--db", "-d", default="default")
def collections_describe(name: str, db: str):
    """Show collection details."""
    resp = _request("get", f"/v1/databases/{db}/collections/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Collection:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Dimension:[/cyan] {data.get('dimension', '-')}\n"
            f"[cyan]Vectors:[/cyan] {data.get('vector_count', 0):,}\n"
            f"[cyan]Metric:[/cyan] {data.get('metric', 'cosine')}\n"
            f"[cyan]Index:[/cyan] {data.get('index_type', 'hnsw')}\n"
            f"[cyan]Storage:[/cyan] {data.get('storage', '0 B')}",
            title="Collection Details",
            border_style="cyan",
        )
    )


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

    resp = _request("delete", f"/v1/databases/{db}/collections/{name}")
    check_response(resp)
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
    from pathlib import Path

    source_path = Path(source)
    if not source_path.exists():
        raise click.ClickException(f"Source file not found: {source}")

    console.print(f"[cyan]Upserting into '{collection}' from '{source}'...[/cyan]")

    vectors = []
    with open(source_path) as f:
        for line in f:
            line = line.strip()
            if line:
                vectors.append(json.loads(line))

    total = 0
    errors = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        payload = {
            "vectors": batch,
            "vector_field": vector_field,
        }
        if id_field:
            payload["id_field"] = id_field
        if embed:
            payload["embed_model"] = embed

        resp = _request("post", f"/v1/databases/{db}/collections/{collection}/upsert", json=payload)
        result = check_response(resp)
        total += result.get("upserted", len(batch))
        errors += result.get("errors", 0)
        console.print(f"  Batch {i // batch_size + 1}: {result.get('upserted', len(batch))} upserted")

    console.print(f"[green]✓[/green] Upsert complete")
    console.print(f"  Vectors: {total}")
    console.print(f"  Errors: {errors}")


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
def vector_query(
    collection: str,
    db: str,
    text: str,
    vector: str,
    topk: int,
    filter: str,
    include_vectors: bool,
    include_metadata: bool,
    embed: str,
):
    """Query similar vectors.

    \b
    Examples:
      hanzo vector query -c docs -t "machine learning" -k 20
      hanzo vector query -c images -v "[0.1, 0.2, ...]" --filter "category=animals"
    """
    if not text and not vector:
        raise click.ClickException("Provide --text or --vector for query")

    payload = {
        "top_k": topk,
        "include_vectors": include_vectors,
        "include_metadata": include_metadata,
    }
    if text:
        payload["text"] = text
    if vector:
        payload["vector"] = json.loads(vector)
    if filter:
        payload["filter"] = filter
    if embed:
        payload["embed_model"] = embed

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/query", json=payload)
    data = check_response(resp)
    matches = data.get("matches", data.get("results", []))

    table = Table(title=f"Results from '{collection}'", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Metadata", style="white")

    for i, m in enumerate(matches, 1):
        metadata = m.get("metadata", {})
        meta_str = json.dumps(metadata, default=str)[:80] if metadata else "-"
        table.add_row(
            str(i),
            str(m.get("id", ""))[:24],
            f"{m.get('score', 0):.4f}",
            meta_str,
        )

    console.print(table)
    if not matches:
        console.print("[dim]No results found[/dim]")


@vector_group.command(name="fetch")
@click.argument("ids", nargs=-1, required=True)
@click.option("--collection", "-c", required=True)
@click.option("--db", "-d", default="default")
@click.option("--include-vectors", is_flag=True)
def vector_fetch(ids: tuple, collection: str, db: str, include_vectors: bool):
    """Fetch vectors by ID."""
    payload = {"ids": list(ids), "include_vectors": include_vectors}

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/fetch", json=payload)
    data = check_response(resp)
    vectors = data.get("vectors", [])

    for v in vectors:
        console.print(
            Panel(
                f"[cyan]ID:[/cyan] {v.get('id', '-')}\n"
                f"[cyan]Metadata:[/cyan] {json.dumps(v.get('metadata', {}), indent=2, default=str)}",
                border_style="cyan",
            )
        )
        if include_vectors and v.get("values"):
            dims = v["values"][:5]
            console.print(f"  Vector: [{', '.join(f'{d:.4f}' for d in dims)}, ...] ({len(v['values'])} dims)")

    if not vectors:
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

    payload = {}
    if ids:
        payload["ids"] = [i.strip() for i in ids.split(",")]
    if filter:
        payload["filter"] = filter
    if delete_all:
        payload["delete_all"] = True

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/delete", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Deleted {data.get('deleted', 0)} vector(s) from '{collection}'")


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
    resp = _request("get", f"/v1/databases/{db}/collections/{collection}/indexes")
    data = check_response(resp)
    items = data.get("indexes", [])

    table = Table(title=f"Indexes on '{collection}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Metric", style="yellow")
    table.add_column("Parameters", style="dim")

    for idx in items:
        params = idx.get("parameters", {})
        param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else "-"
        table.add_row(
            idx.get("name", "-"),
            idx.get("type", "-"),
            idx.get("metric", "-"),
            param_str,
        )

    console.print(table)
    if not items:
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
def indexes_create(
    collection: str, db: str, name: str, idx_type: str, metric: str, hnsw_m: int, hnsw_ef: int, ivf_nlist: int
):
    """Create a vector index.

    \b
    Examples:
      hanzo vector indexes create embeddings --type hnsw --hnsw-m 32
      hanzo vector indexes create images --type ivf --ivf-nlist 256
    """
    payload = {"type": idx_type}
    if name:
        payload["name"] = name
    if metric:
        payload["metric"] = metric

    if idx_type == "hnsw":
        payload["parameters"] = {"m": hnsw_m, "ef_construction": hnsw_ef}
    elif idx_type == "ivf":
        payload["parameters"] = {"nlist": ivf_nlist}

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/indexes", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Index created on '{collection}'")
    console.print(f"  Name: {data.get('name', name or 'default')}")
    console.print(f"  Type: {idx_type}")
    if idx_type == "hnsw":
        console.print(f"  M: {hnsw_m}, efConstruction: {hnsw_ef}")
    elif idx_type == "ivf":
        console.print(f"  nlist: {ivf_nlist}")


@indexes.command(name="rebuild")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--name", "-n", help="Specific index name")
def indexes_rebuild(collection: str, db: str, name: str):
    """Rebuild vector index."""
    payload = {}
    if name:
        payload["index_name"] = name

    console.print(f"[cyan]Rebuilding index for '{collection}'...[/cyan]")
    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/indexes/rebuild", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Index rebuilt ({data.get('duration', '-')})")


# ============================================================================
# Admin
# ============================================================================


@vector_group.command(name="stats")
@click.option("--db", "-d", default="default")
def vector_stats(db: str):
    """Show database statistics."""
    resp = _request("get", f"/v1/databases/{db}/stats")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Database:[/cyan] {data.get('name', db)}\n"
            f"[cyan]Collections:[/cyan] {data.get('collection_count', 0)}\n"
            f"[cyan]Total vectors:[/cyan] {data.get('vector_count', 0):,}\n"
            f"[cyan]Storage:[/cyan] {data.get('storage', '0 B')}\n"
            f"[cyan]Queries/day:[/cyan] {data.get('queries_per_day', 0):,}\n"
            f"[cyan]Avg latency:[/cyan] {data.get('avg_latency_ms', 0)}ms",
            title="Vector Statistics",
            border_style="cyan",
        )
    )


@vector_group.command(name="bind")
@click.option("--service", "-s", required=True, help="Service to bind to")
@click.option("--db", "-d", default="default")
@click.option("--env", "-e", help="Environment")
def vector_bind(service: str, db: str, env: str):
    """Bind database to a service."""
    payload = {"service": service, "database": db}
    if env:
        payload["environment"] = env

    resp = _request("post", "/v1/bindings", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Bound '{db}' to service '{service}'")
    if env:
        console.print(f"  Environment: {env}")


@vector_group.command(name="backup")
@click.option("--db", "-d", default="default")
@click.option("--collection", "-c", help="Specific collection")
@click.option("--output", "-o", help="Output location")
def vector_backup(db: str, collection: str, output: str):
    """Backup vector data."""
    payload = {"database": db}
    if collection:
        payload["collection"] = collection
    if output:
        payload["output"] = output

    resp = _request("post", "/v1/backups", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Backup created")
    console.print(f"  Backup ID: {data.get('id', '-')}")
    console.print(f"  Size: {data.get('size', '-')}")
