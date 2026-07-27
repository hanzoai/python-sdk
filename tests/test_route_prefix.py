"""Guard: no Hanzo service route may carry the banned `/api/` path segment.

The standard (hanzoai/openapi README) is `/v1/<service>/<resource>`. This test
is what keeps the prefix dead after the sweep that removed it.

It inspects STRING LITERALS via `ast`, not lines of text: only a literal can BE
a route. Prose that names the prefix — a comment recording what a rewrite
replaced — is documentation, and the parser tells the two apart exactly.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# The trees swept clean and verified against the deployed IAM route table.
# `pkg/hanzo` is listed per-module, not wholesale: its CLI IAM commands are
# clean, while `infra/functions.py` still addresses the dashboard service under
# the banned prefix. Guarding a tree nobody has cleaned would mean a standing
# allow-list, and an allow-list is how a guard becomes decoration.
PKGS = [
    ROOT / "pkg" / "hanzoai",
    ROOT / "pkg" / "hanzo-iam",
    ROOT / "pkg" / "hanzo" / "src" / "hanzo" / "commands" / "iam.py",
    ROOT / "pkg" / "hanzo" / "src" / "hanzo" / "commands" / "auth.py",
]

# An `/api/` PATH segment. Deliberately does NOT match the `api.hanzo.ai`
# HOSTNAME — the standard bans the path segment, not the api.* subdomain.
API_PREFIX = re.compile(r"(?:^|[^.\w])/api/")

# A third-party service whose OWN API lives under `/api/` declares itself, on
# the offending line, with a reason. One mechanism, no distant allow-list to
# drift: the exemption travels with the literal it exempts.
FOREIGN = re.compile(r"foreign-api:")


def _offenders(root: Path) -> list[str]:
    out: list[str] = []
    for path in [root] if root.is_file() else sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:  # a file we cannot parse is a file we cannot vouch for
            out.append(f"{path}: unparseable ({exc})")
            continue
        lines = src.splitlines()
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if not API_PREFIX.search(node.value):
                continue
            line = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            if FOREIGN.search(line):
                continue
            out.append(f"{path}:{node.lineno}: {node.value!r}")
    return out


def test_no_api_prefix_in_sdk_source() -> None:
    offenders = [o for pkg in PKGS for o in _offenders(pkg)]
    assert not offenders, "the /api/ prefix is banned; use /v1/<service>/:\n" + "\n".join(offenders)


@pytest.mark.parametrize(
    "expected",
    ["/v1/iam/signup", "/v1/iam/login", "/v1/iam/get-users"],
)
def test_iam_resource_targets_v1_iam(expected: str) -> None:
    """Every IAM resource path is a verb-noun under /v1/iam, checked against the
    deployed route table of iam v1.33.24."""
    src = (ROOT / "pkg" / "hanzoai" / "resources" / "iam.py").read_text(encoding="utf-8")
    assert f'"{expected}"' in src, f"expected path {expected} not found in iam.py"


def test_hanzo_iam_client_uses_the_one_prefix_constant() -> None:
    """The canonical hanzo-iam client composes every admin action from the single
    IAM_ROUTE_PREFIX value, so the prefix has exactly one spelling.

    Read statically — a guard that needs the package's runtime dependencies
    installed is a guard that gets skipped in the environment that needs it."""
    models = ROOT / "pkg" / "hanzo-iam" / "hanzo_iam" / "models.py"
    tree = ast.parse(models.read_text(encoding="utf-8"), filename=str(models))
    prefix = next(
        (
            node.value.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(getattr(t, "id", None) == "IAM_ROUTE_PREFIX" for t in node.targets)
            and isinstance(node.value, ast.Constant)
        ),
        None,
    )
    assert prefix == "/v1/iam", f"IAM_ROUTE_PREFIX is {prefix!r}"
    for name in ("client.py", "async_client.py"):
        src = (ROOT / "pkg" / "hanzo-iam" / "hanzo_iam" / name).read_text(encoding="utf-8")
        assert 'f"{IAM_ROUTE_PREFIX}/get-user"' in src, f"{name} does not route through the constant"
