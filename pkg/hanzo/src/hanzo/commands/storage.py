"""Hanzo Storage — S3-compatible object storage CLI.

Connects to s3.hanzo.ai (S3-compatible API) using stored credentials.

Environment variables:
    HANZO_S3_ENDPOINT    — S3 endpoint (default: https://s3.hanzo.ai)
    HANZO_S3_REGION      — Region (default: us-east-1)
    AWS_ACCESS_KEY_ID    — S3 access key (or from hanzo auth)
    AWS_SECRET_ACCESS_KEY — S3 secret key (or from hanzo auth)
"""

from __future__ import annotations

import os
import sys
import json
from typing import Any
from pathlib import Path

import click
from rich import box
from rich.table import Table
from rich.progress import Progress, TextColumn, SpinnerColumn

from ..utils.output import console

S3_ENDPOINT = os.getenv("HANZO_S3_ENDPOINT", "https://s3.hanzo.ai")
S3_REGION = os.getenv("HANZO_S3_REGION", "us-east-1")


def _get_s3_client():
    """Create an S3 client connected to s3.hanzo.ai."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        console.print("[red]boto3 not installed.[/red] Run: pip install 'hanzo[storage]'")
        raise SystemExit(1)

    # Try to get credentials from env or hanzo auth
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not access_key or not secret_key:
        # Try loading from hanzo auth token
        token_file = Path.home() / ".hanzo" / "auth" / "s3_credentials.json"
        if token_file.exists():
            try:
                creds = json.loads(token_file.read_text())
                access_key = creds.get("access_key_id")
                secret_key = creds.get("secret_access_key")
            except (json.JSONDecodeError, OSError):
                pass

    if not access_key or not secret_key:
        console.print("[red]S3 credentials not configured.[/red]")
        console.print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or run:")
        console.print("  hanzo storage auth")
        raise SystemExit(1)

    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
    )


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _parse_s3_path(path: str) -> tuple[str, str]:
    """Parse 's3://bucket/key' or 'bucket/key' into (bucket, key)."""
    path = path.removeprefix("s3://")
    parts = path.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


@click.group(name="s3")
def storage_group():
    """Hanzo S3 — S3-compatible object storage (hanzo.space / s3.hanzo.ai).

    \b
    Buckets:
      hanzo s3 buckets list     List buckets
      hanzo s3 buckets create   Create bucket
      hanzo s3 buckets delete   Delete bucket

    \b
    Objects:
      hanzo s3 ls               List objects
      hanzo s3 cp               Copy files (upload/download)
      hanzo s3 mv               Move/rename objects
      hanzo s3 rm               Delete objects
      hanzo s3 sync             Sync directories

    \b
    Sharing:
      hanzo s3 presign          Generate presigned URL
      hanzo s3 public           Make object public

    \b
    Endpoint: s3.hanzo.ai (S3-compatible)
    """
    pass


# ============================================================================
# Auth
# ============================================================================


@storage_group.command(name="auth")
@click.option("--access-key", prompt="Access Key ID", help="S3 access key ID")
@click.option(
    "--secret-key",
    prompt="Secret Access Key",
    hide_input=True,
    help="S3 secret access key",
)
@click.option("--endpoint", default=S3_ENDPOINT, help="S3 endpoint URL")
def storage_auth(access_key: str, secret_key: str, endpoint: str):
    """Configure S3 credentials for hanzo storage.

    Credentials are stored at ~/.hanzo/auth/s3_credentials.json
    """
    creds_dir = Path.home() / ".hanzo" / "auth"
    creds_dir.mkdir(parents=True, exist_ok=True)
    creds_file = creds_dir / "s3_credentials.json"
    creds_file.write_text(
        json.dumps(
            {
                "access_key_id": access_key,
                "secret_access_key": secret_key,
                "endpoint": endpoint,
            },
            indent=2,
        )
    )
    creds_file.chmod(0o600)
    console.print(f"[green]S3 credentials saved to {creds_file}[/green]")


# ============================================================================
# Bucket Management
# ============================================================================


@storage_group.group()
def buckets():
    """Manage storage buckets."""
    pass


@buckets.command(name="list")
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
def buckets_list(json_out: bool):
    """List all buckets."""
    s3 = _get_s3_client()
    response = s3.list_buckets()
    bucket_list = response.get("Buckets", [])

    if json_out:
        click.echo(json.dumps(
            [{"name": b["Name"], "created": b["CreationDate"].isoformat()} for b in bucket_list],
            indent=2,
        ))
        return

    if not bucket_list:
        console.print("[dim]No buckets found. Create one with 'hanzo storage buckets create'[/dim]")
        return

    table = Table(title=f"Buckets ({len(bucket_list)})", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Created", style="dim")

    for b in bucket_list:
        table.add_row(b["Name"], b["CreationDate"].strftime("%Y-%m-%d %H:%M:%S"))

    console.print(table)


@buckets.command(name="create")
@click.argument("name")
@click.option("--region", "-r", default=S3_REGION, help="Bucket region")
def buckets_create(name: str, region: str):
    """Create a bucket."""
    s3 = _get_s3_client()
    create_config = {}
    if region and region != "us-east-1":
        create_config["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(Bucket=name, **create_config)
    console.print(f"[green]Bucket '{name}' created.[/green]")


@buckets.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Delete even if not empty")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def buckets_delete(name: str, force: bool, yes: bool):
    """Delete a bucket."""
    if not yes:
        click.confirm(f"Delete bucket '{name}'?", abort=True)

    s3 = _get_s3_client()

    if force:
        # Delete all objects first
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=name):
            objects = page.get("Contents", [])
            if objects:
                s3.delete_objects(
                    Bucket=name,
                    Delete={"Objects": [{"Key": o["Key"]} for o in objects]},
                )

    s3.delete_bucket(Bucket=name)
    console.print(f"[green]Bucket '{name}' deleted.[/green]")


# ============================================================================
# Object Operations
# ============================================================================


@storage_group.command(name="ls")
@click.argument("path", default="")
@click.option("--recursive", "-r", is_flag=True, help="List recursively")
@click.option("--human", "-h", is_flag=True, help="Human-readable sizes")
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
def storage_ls(path: str, recursive: bool, human: bool, json_out: bool):
    """List objects in a bucket.

    \b
    PATH format: bucket/prefix or s3://bucket/prefix

    \b
    Examples:
      hanzo storage ls mybucket              List top-level objects
      hanzo storage ls mybucket/images/ -r   List recursively
      hanzo storage ls s3://mybucket -h      Human-readable sizes
    """
    if not path:
        console.print("[dim]Usage: hanzo storage ls <bucket>[/prefix][/dim]")
        return

    bucket, prefix = _parse_s3_path(path)
    s3 = _get_s3_client()

    all_objects = []
    all_prefixes = []

    paginator = s3.get_paginator("list_objects_v2")
    params: dict[str, Any] = {"Bucket": bucket}
    if prefix:
        params["Prefix"] = prefix
    if not recursive:
        params["Delimiter"] = "/"

    for page in paginator.paginate(**params):
        all_objects.extend(page.get("Contents", []))
        all_prefixes.extend(page.get("CommonPrefixes", []))

    if json_out:
        items = []
        for p in all_prefixes:
            items.append({"key": p["Prefix"], "type": "directory"})
        for o in all_objects:
            items.append({
                "key": o["Key"],
                "size": o["Size"],
                "modified": o["LastModified"].isoformat(),
                "type": "file",
            })
        click.echo(json.dumps(items, indent=2))
        return

    if not all_objects and not all_prefixes:
        console.print("[dim]No objects found[/dim]")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Modified", style="dim")

    for p in all_prefixes:
        table.add_row(f"[bold]{p['Prefix']}[/bold]", "DIR", "")

    for o in all_objects:
        size_str = _format_size(o["Size"]) if human else str(o["Size"])
        modified = o["LastModified"].strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(o["Key"], size_str, modified)

    console.print(table)
    total = sum(o["Size"] for o in all_objects)
    console.print(
        f"[dim]{len(all_objects)} object(s), {len(all_prefixes)} prefix(es), "
        f"total {_format_size(total)}[/dim]"
    )


@storage_group.command(name="cp")
@click.argument("source")
@click.argument("dest")
@click.option("--recursive", "-r", is_flag=True, help="Copy recursively")
def storage_cp(source: str, dest: str, recursive: bool):
    """Copy files to/from storage.

    \b
    Examples:
      hanzo storage cp file.txt mybucket/           Upload
      hanzo storage cp mybucket/file.txt ./          Download
      hanzo storage cp -r ./dir mybucket/prefix/     Upload directory
      hanzo storage cp mybucket/a.txt mybucket/b.txt Server-side copy
    """
    s3 = _get_s3_client()
    is_s3_src = source.startswith("s3://") or "/" in source and not os.path.exists(source)
    is_s3_dst = dest.startswith("s3://") or "/" in dest and not os.path.exists(os.path.dirname(dest) or ".")

    # Heuristic: if source exists locally, it's an upload
    if os.path.exists(source) and not source.startswith("s3://"):
        is_s3_src = False

    if not is_s3_src and is_s3_dst:
        # Upload
        bucket, key = _parse_s3_path(dest)
        local_path = Path(source)

        if recursive and local_path.is_dir():
            files = list(local_path.rglob("*"))
            files = [f for f in files if f.is_file()]
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Uploading {len(files)} files...", total=len(files))
                for f in files:
                    rel = f.relative_to(local_path)
                    obj_key = f"{key}{rel}" if key else str(rel)
                    s3.upload_file(str(f), bucket, obj_key)
                    progress.advance(task)
            console.print(f"[green]Uploaded {len(files)} files to {bucket}/{key}[/green]")
        else:
            if not key or key.endswith("/"):
                key = key + local_path.name
            s3.upload_file(str(local_path), bucket, key)
            console.print(f"[green]Uploaded {source} -> s3://{bucket}/{key}[/green]")

    elif is_s3_src and not is_s3_dst:
        # Download
        bucket, key = _parse_s3_path(source)
        local_path = Path(dest)

        if recursive:
            paginator = s3.get_paginator("list_objects_v2")
            objects = []
            for page in paginator.paginate(Bucket=bucket, Prefix=key):
                objects.extend(page.get("Contents", []))

            if not objects:
                console.print("[yellow]No objects found to download.[/yellow]")
                return

            local_path.mkdir(parents=True, exist_ok=True)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Downloading {len(objects)} files...", total=len(objects))
                for obj in objects:
                    rel_key = obj["Key"].removeprefix(key).lstrip("/")
                    if not rel_key:
                        continue
                    dest_file = local_path / rel_key
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    s3.download_file(bucket, obj["Key"], str(dest_file))
                    progress.advance(task)
            console.print(f"[green]Downloaded {len(objects)} files to {dest}[/green]")
        else:
            if local_path.is_dir():
                filename = key.rsplit("/", 1)[-1] if "/" in key else key
                local_path = local_path / filename
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, key, str(local_path))
            console.print(f"[green]Downloaded s3://{bucket}/{key} -> {local_path}[/green]")

    elif is_s3_src and is_s3_dst:
        # Server-side copy
        src_bucket, src_key = _parse_s3_path(source)
        dst_bucket, dst_key = _parse_s3_path(dest)
        s3.copy_object(
            CopySource={"Bucket": src_bucket, "Key": src_key},
            Bucket=dst_bucket,
            Key=dst_key,
        )
        console.print(f"[green]Copied s3://{src_bucket}/{src_key} -> s3://{dst_bucket}/{dst_key}[/green]")
    else:
        console.print("[red]At least one path must be an S3 path (bucket/key or s3://bucket/key).[/red]")
        raise SystemExit(1)


@storage_group.command(name="mv")
@click.argument("source")
@click.argument("dest")
def storage_mv(source: str, dest: str):
    """Move or rename objects in storage.

    \b
    Examples:
      hanzo storage mv mybucket/old.txt mybucket/new.txt    Rename
      hanzo storage mv mybucket/a.txt other-bucket/a.txt    Move between buckets
    """
    s3 = _get_s3_client()
    src_bucket, src_key = _parse_s3_path(source)
    dst_bucket, dst_key = _parse_s3_path(dest)

    # Copy then delete
    s3.copy_object(
        CopySource={"Bucket": src_bucket, "Key": src_key},
        Bucket=dst_bucket,
        Key=dst_key,
    )
    s3.delete_object(Bucket=src_bucket, Key=src_key)
    console.print(f"[green]Moved s3://{src_bucket}/{src_key} -> s3://{dst_bucket}/{dst_key}[/green]")


@storage_group.command(name="rm")
@click.argument("path")
@click.option("--recursive", "-r", is_flag=True, help="Delete recursively")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def storage_rm(path: str, recursive: bool, yes: bool):
    """Delete objects from storage.

    \b
    Examples:
      hanzo storage rm mybucket/file.txt          Delete single object
      hanzo storage rm -r mybucket/prefix/        Delete all under prefix
    """
    bucket, key = _parse_s3_path(path)
    s3 = _get_s3_client()

    if recursive:
        # Count objects first
        paginator = s3.get_paginator("list_objects_v2")
        objects = []
        for page in paginator.paginate(Bucket=bucket, Prefix=key):
            objects.extend(page.get("Contents", []))

        if not objects:
            console.print("[yellow]No objects found to delete.[/yellow]")
            return

        if not yes:
            click.confirm(f"Delete {len(objects)} object(s) under '{path}'?", abort=True)

        # Delete in batches of 1000 (S3 limit)
        for i in range(0, len(objects), 1000):
            batch = objects[i : i + 1000]
            s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": o["Key"]} for o in batch]},
            )
        console.print(f"[green]Deleted {len(objects)} object(s).[/green]")
    else:
        if not yes:
            click.confirm(f"Delete '{path}'?", abort=True)
        s3.delete_object(Bucket=bucket, Key=key)
        console.print(f"[green]Deleted s3://{bucket}/{key}[/green]")


@storage_group.command(name="sync")
@click.argument("source")
@click.argument("dest")
@click.option("--delete", "delete_extra", is_flag=True, help="Delete files not in source")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
def storage_sync(source: str, dest: str, delete_extra: bool, dry_run: bool):
    """Sync directories with storage.

    \b
    Examples:
      hanzo storage sync ./build mybucket/assets/    Upload (sync local -> S3)
      hanzo storage sync mybucket/assets/ ./local/   Download (sync S3 -> local)
    """
    s3 = _get_s3_client()
    src_local = os.path.exists(source) and not source.startswith("s3://")

    if src_local:
        # Upload sync: local -> S3
        bucket, prefix = _parse_s3_path(dest)
        local_path = Path(source)

        # Get local files
        local_files = {}
        for f in local_path.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(local_path))
                local_files[rel] = f

        # Get remote files
        remote_files: dict[str, dict] = {}
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                rel_key = obj["Key"].removeprefix(prefix).lstrip("/")
                if rel_key:
                    remote_files[rel_key] = obj

        # Determine what to upload
        to_upload = []
        for rel, f in local_files.items():
            if rel not in remote_files:
                to_upload.append(rel)
            else:
                # Compare by size (quick check)
                if f.stat().st_size != remote_files[rel]["Size"]:
                    to_upload.append(rel)

        to_delete = []
        if delete_extra:
            to_delete = [k for k in remote_files if k not in local_files]

        if dry_run:
            for rel in to_upload:
                console.print(f"  [green]upload[/green]  {rel}")
            for rel in to_delete:
                console.print(f"  [red]delete[/red]  {rel}")
            console.print(f"[dim]Would upload {len(to_upload)}, delete {len(to_delete)}[/dim]")
            return

        for rel in to_upload:
            obj_key = f"{prefix}{rel}" if prefix else rel
            s3.upload_file(str(local_files[rel]), bucket, obj_key)

        if to_delete:
            for i in range(0, len(to_delete), 1000):
                batch = to_delete[i : i + 1000]
                s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": [{"Key": f"{prefix}{k}"} for k in batch]},
                )

        console.print(
            f"[green]Synced: {len(to_upload)} uploaded, "
            f"{len(to_delete)} deleted[/green]"
        )
    else:
        # Download sync: S3 -> local
        bucket, prefix = _parse_s3_path(source)
        local_path = Path(dest)
        local_path.mkdir(parents=True, exist_ok=True)

        # Get remote files
        remote_files: dict[str, dict] = {}
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                rel_key = obj["Key"].removeprefix(prefix).lstrip("/")
                if rel_key:
                    remote_files[rel_key] = obj

        # Get local files
        local_files_set = set()
        for f in local_path.rglob("*"):
            if f.is_file():
                local_files_set.add(str(f.relative_to(local_path)))

        to_download = []
        for rel, obj in remote_files.items():
            dest_file = local_path / rel
            if not dest_file.exists():
                to_download.append(rel)
            elif dest_file.stat().st_size != obj["Size"]:
                to_download.append(rel)

        to_delete = []
        if delete_extra:
            to_delete = [k for k in local_files_set if k not in remote_files]

        if dry_run:
            for rel in to_download:
                console.print(f"  [green]download[/green]  {rel}")
            for rel in to_delete:
                console.print(f"  [red]delete[/red]  {rel}")
            console.print(f"[dim]Would download {len(to_download)}, delete {len(to_delete)}[/dim]")
            return

        for rel in to_download:
            dest_file = local_path / rel
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, remote_files[rel]["Key"], str(dest_file))

        for rel in to_delete:
            (local_path / rel).unlink()

        console.print(
            f"[green]Synced: {len(to_download)} downloaded, "
            f"{len(to_delete)} deleted[/green]"
        )


@storage_group.command(name="presign")
@click.argument("path")
@click.option("--expires", "-e", default=3600, type=int, help="Expiration in seconds (default: 3600)")
@click.option("--method", "-m", default="GET", type=click.Choice(["GET", "PUT"]))
def storage_presign(path: str, expires: int, method: str):
    """Generate a presigned URL for an object.

    \b
    Examples:
      hanzo storage presign mybucket/file.txt            1-hour GET URL
      hanzo storage presign mybucket/file.txt -e 86400   24-hour URL
      hanzo storage presign mybucket/upload.txt -m PUT    Upload URL
    """
    bucket, key = _parse_s3_path(path)
    s3 = _get_s3_client()

    client_method = "get_object" if method == "GET" else "put_object"
    url = s3.generate_presigned_url(
        ClientMethod=client_method,
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )
    console.print(f"[cyan]Presigned URL ({method}, expires in {expires}s):[/cyan]")
    click.echo(url)


@storage_group.command(name="public")
@click.argument("path")
@click.option("--recursive", "-r", is_flag=True, help="Apply to all objects in prefix")
def storage_public(path: str, recursive: bool):
    """Make object(s) publicly accessible via CDN.

    Sets the ACL to public-read and prints the CDN URL.

    \b
    Examples:
      hanzo storage public mybucket/image.png         Single object
      hanzo storage public -r mybucket/assets/        All under prefix
    """
    bucket, key = _parse_s3_path(path)
    s3 = _get_s3_client()

    if recursive:
        paginator = s3.get_paginator("list_objects_v2")
        count = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=key):
            for obj in page.get("Contents", []):
                s3.put_object_acl(Bucket=bucket, Key=obj["Key"], ACL="public-read")
                count += 1
        console.print(f"[green]Made {count} object(s) public.[/green]")
        console.print(f"  CDN: https://cdn.hanzo.ai/{bucket}/{key}")
    else:
        s3.put_object_acl(Bucket=bucket, Key=key, ACL="public-read")
        console.print(f"[green]Made '{key}' public.[/green]")
        console.print(f"  URL: https://cdn.hanzo.ai/{bucket}/{key}")
