"""The cloud surface is GENERATED, so what is asserted is the generation.

The valuable assertion is the last one: the catalog this package ships must be
byte-identical to the one the TypeScript and Rust runtimes ship. Three copies of
one value is how they come to disagree, and nothing else here would notice.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hanzo_tools.cloud import operations, reach, services
from hanzo_tools.cloud.cloud_tool import _CATALOG


def test_the_fleet_is_whole() -> None:
    assert len(services()) > 100, f"expected the fleet, got {len(services())}"
    assert reach() > 1000, f"expected the fleet's operations, got {reach()}"


def test_a_subsystem_carries_its_operations() -> None:
    assert "iam" in services()
    assert "get_iam_users" in operations("iam")


def test_what_the_fleet_withholds_is_absent() -> None:
    # The rule is applied once, in cloud, and reaches here through the generated
    # file: reading who holds a role is not the same act as granting one.
    assert "post_iam_users" not in operations("iam")
    assert "delete_iam_users" not in operations("iam")


def test_a_name_the_fleet_dropped_is_not_offered() -> None:
    # paas became platform and storage became s3. A client still naming the old
    # ones describes an API that has moved.
    assert "paas" not in services()
    assert "storage" not in services()
    assert "platform" in services()


def test_an_unserved_subsystem_is_refused_rather_than_called() -> None:
    from hanzo_tools.cloud import call

    with pytest.raises(ValueError, match="does not serve"):
        call("paas", "anything")


def test_every_runtime_ships_the_same_catalog() -> None:
    """The three runtimes must not drift.

    Skipped rather than failed when a sibling is not checked out — absence of a
    checkout is not evidence of disagreement, and a test that fails on a partial
    workspace is a test people learn to ignore.
    """
    mine = hashlib.sha256(_CATALOG.read_bytes()).hexdigest()
    root = Path(__file__).resolve().parents[4]
    siblings = {
        "@hanzo/mcp": root / "mcp" / "src" / "tools" / "catalog.json",
        "cloud": root / "cloud" / "fleet" / "mcp.json",
    }
    checked = 0
    for name, path in siblings.items():
        if not path.exists():
            continue
        checked += 1
        assert hashlib.sha256(path.read_bytes()).hexdigest() == mine, (
            f"{name} ships a different catalog than this package. "
            f"Regenerate them together: `pnpm sync:catalog` in hanzoai/mcp."
        )
    if checked == 0:
        pytest.skip("no sibling runtime checked out beside this one")


def test_the_catalog_is_the_shape_the_runtimes_read() -> None:
    raw = json.loads(_CATALOG.read_text())
    assert all(sorted(entry) == ["ops"] for entry in raw.values())
    assert all(entry["ops"] for entry in raw.values()), "an empty enum is a tool nobody can call"
