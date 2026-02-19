"""PaaS context management — remember current org/project/env.

Stores selection at ~/.hanzo/paas/context.json so you don't have to
pass --org / --project / --env on every command.

Set with:  hanzo paas use --org myorg --project myproj --env production
Clear with: hanzo paas use --clear
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTEXT_DIR = Path.home() / ".hanzo" / "paas"
CONTEXT_FILE = CONTEXT_DIR / "context.json"


def load_context() -> dict[str, Any]:
    """Load stored PaaS context."""
    if not CONTEXT_FILE.exists():
        return {}
    try:
        return json.loads(CONTEXT_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_context(ctx: dict[str, Any]) -> None:
    """Persist PaaS context."""
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2))
    CONTEXT_FILE.chmod(0o600)


def clear_context() -> None:
    """Remove stored context."""
    if CONTEXT_FILE.exists():
        CONTEXT_FILE.unlink()


def resolve(
    cli_org: str | None,
    cli_project: str | None,
    cli_env: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Merge CLI flags over stored context.

    Returns (org_id, project_id, env_id) — any may be None.
    """
    ctx = load_context()
    return (
        cli_org or ctx.get("org_id"),
        cli_project or ctx.get("project_id"),
        cli_env or ctx.get("env_id"),
    )
