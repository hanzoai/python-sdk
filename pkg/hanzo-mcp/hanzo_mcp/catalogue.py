"""The fleet's tool catalogue, as the contract publishes it.

`catalogue.json` beside this file is GENERATED — pulled from hanzoai/openapi's
`tools.py`, which projects the published document. Regenerate with
`scripts/tools.sh`; never edit it by hand, and never add a tool here. A tool
exists because hanzoai/cloud serves an operation, and the only way to add one is
to serve it.

A tool's name IS its operationId, verbatim. That is not a convention this file
chose — it is what the fleet's own door answers with, so a name invented here
would name something `POST /v1/mcp` cannot be told to run.

This is the CONTRACT plane: what the API exposes. It is not the local tool set
(`fs`, `exec`, `git`, …), which describes this machine rather than the fleet and
which no document can generate.
"""

import json
from functools import lru_cache
from pathlib import Path

CATALOGUE = Path(__file__).with_name("catalogue.json")


@lru_cache(maxsize=1)
def _doc() -> dict:
    return json.loads(CATALOGUE.read_text())


def catalogue() -> list[dict]:
    """Every tool the contract publishes: `name`, `description`, `inputSchema`."""
    return _doc()["tools"]


def names() -> list[str]:
    """Every tool name, sorted. Each is an operationId the fleet answers to."""
    return [t["name"] for t in catalogue()]


def find(name: str) -> dict | None:
    """One tool by name, or None. The name is an operationId."""
    return next((t for t in catalogue() if t["name"] == name), None)
