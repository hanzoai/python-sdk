"""New shard download utilities."""

from pathlib import Path


async def ensure_downloads_dir():
    """Ensure downloads directory exists."""
    downloads_dir = Path.home() / ".hanzo" / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir
