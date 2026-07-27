"""Guard: no Hanzo service route may carry the banned `/api/` path segment.

The standard (hanzoai/openapi README) is `/v1/<service>/<resource>`. This test
is what keeps the prefix dead after the sweep that removed it — it fails the
build if one comes back in the SDK's own source.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parent.parent / "pkg" / "hanzoai"

# An `/api/` PATH segment. Deliberately does NOT match the `api.hanzo.ai`
# HOSTNAME — the standard bans the path segment, not the api.* subdomain.
API_PREFIX = re.compile(r"(?:^|[^.\w])/api/")

# A third-party service whose OWN API lives under `/api/` declares itself, in
# place, with a reason. One mechanism, no distant allow-list to drift: the
# exemption travels with the line it exempts.
FOREIGN = re.compile(r"foreign-api:")


def _offenders(root: Path) -> list[str]:
    out: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if API_PREFIX.search(line) and not FOREIGN.search(line):
                out.append(f"{path}:{n}: {line.strip()}")
    return out


def test_no_api_prefix_in_sdk_source() -> None:
    offenders = _offenders(PKG)
    assert not offenders, "the /api/ prefix is banned; use /v1/<service>/:\n" + "\n".join(offenders)


@pytest.mark.parametrize(
    "method,expected",
    [
        ("signup", "/v1/iam/signup"),
        ("login", "/v1/iam/login"),
        ("get_users", "/v1/iam/get-users"),
    ],
)
def test_iam_resource_targets_v1_iam(method: str, expected: str) -> None:
    """Every IAM resource path is a verb-noun under /v1/iam, verified against the
    live route table of iam v1.33.24."""
    src = (PKG / "resources" / "iam.py").read_text(encoding="utf-8")
    assert f'"{expected}"' in src, f"{method}: expected path {expected} not found in iam.py"
