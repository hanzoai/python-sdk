"""Hanzo Brain — recipe loader (Python port of @hanzo/bot-recipes-brain).

YAML recipes for daily-life automation:
    auth + cron + ingest + classify + draft + enqueue + on_swipe.

Loads recipes from `<this_package>/recipes/*.yaml` plus any
user-defined dir in `HANZO_BRAIN_RECIPES`. Same shape as the TS pack
so a single brain.db file works for either runtime.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_HERE = Path(__file__).parent
_BUILTIN = _HERE / "recipes"


def _recipe_dirs() -> list[Path]:
    dirs: list[Path] = []
    if _BUILTIN.is_dir():
        dirs.append(_BUILTIN)
    env_dir = os.environ.get("HANZO_BRAIN_RECIPES")
    if env_dir:
        p = Path(env_dir).expanduser()
        if p.is_dir():
            dirs.append(p)
    return dirs


def list_recipes() -> list[str]:
    """Return the names (without `.yaml`) of every available recipe."""
    seen: dict[str, None] = {}
    for d in _recipe_dirs():
        for f in d.glob("*.yaml"):
            seen.setdefault(f.stem, None)
    return list(seen.keys())


def load_recipe(name: str) -> dict[str, Any]:
    """Load and parse one recipe by name."""
    for d in _recipe_dirs():
        path = d / f"{name}.yaml"
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ValueError(f"recipe `{name}` did not parse to a mapping")
            return data
    available = ", ".join(list_recipes()) or "(none)"
    raise FileNotFoundError(
        f"recipe `{name}` not found. Available: {available}. "
        f"Drop a yaml into {_BUILTIN} or set HANZO_BRAIN_RECIPES to your own dir."
    )
