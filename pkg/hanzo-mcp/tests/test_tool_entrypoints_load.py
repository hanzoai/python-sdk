"""Regression: every `hanzo.tools` entry point must import cleanly.

The bug this guards against: PyPI ``hanzo-tools`` 0.3.0 shipped a
``hanzo_tools/core/__init__.py`` that did NOT re-export the HIP-0300 error
classes (``ToolError``, ``ConflictError``, ``InvalidParamsError``,
``NotFoundError``). Six tool packages import those names at entry-point load:

    fs    -> ConflictError
    shell -> ToolError        (exec)
    agent -> ToolError
    code  -> InvalidParamsError
    vcs   -> InvalidParamsError (git)
    net   -> InvalidParamsError (fetch)

When the re-export was missing, each ``ep.load()`` raised ``ImportError`` and
was swallowed by the loader's broad ``except``, so hanzo-mcp silently exposed
only 13 tools instead of the full axis set (fs/exec/code/git/fetch/agent were
the ones dropped — the load-bearing ones). This test fails loudly if any
entry point stops importing, instead of degrading to a partial tool surface.
"""

from importlib.metadata import entry_points

import pytest

TOOLS_ENTRY_POINT_GROUP = "hanzo.tools"

# The exact tools that vanished when core stopped re-exporting the error
# classes. Their absence is the fingerprint of this regression.
LOAD_BEARING_TOOLS = {"fs", "exec", "code", "git", "fetch", "agent"}


def _load_all_entry_points():
    """Load every hanzo.tools entry point, returning {name: (tools|exception)}."""
    results: dict[str, object] = {}
    for ep in entry_points(group=TOOLS_ENTRY_POINT_GROUP):
        try:
            results[ep.name] = ep.load()
        except Exception as e:  # noqa: BLE001 — we WANT to capture the failure
            results[ep.name] = e
    return results


def test_core_reexports_the_error_contract():
    """The exact names the tool packages import must live on hanzo_tools.core."""
    from hanzo_tools import core

    for name in (
        "ToolError",
        "ConflictError",
        "NotFoundError",
        "InvalidParamsError",
        "ActionHandler",
        "Paging",
        "Range",
        "ErrorCode",
        "content_hash",
        "file_uri",
    ):
        assert hasattr(core, name), f"hanzo_tools.core is missing re-export: {name}"


def test_every_tools_entry_point_imports_cleanly():
    """No `hanzo.tools` entry point may fail to load — a failure silently drops the tool."""
    results = _load_all_entry_points()
    failures = {
        name: f"{type(obj).__name__}: {obj}"
        for name, obj in results.items()
        if isinstance(obj, Exception)
    }
    assert not failures, "entry points failed to import: " + "; ".join(
        f"{n} -> {msg}" for n, msg in sorted(failures.items())
    )


def test_load_bearing_tools_are_present():
    """fs/exec/code/git/fetch/agent must be discoverable — the regression's signature."""
    results = _load_all_entry_points()
    discovered: set[str] = set()
    for obj in results.values():
        if isinstance(obj, Exception) or not isinstance(obj, list):
            continue
        for tool_cls in obj:
            name = getattr(tool_cls, "name", None)
            if isinstance(name, str):
                discovered.add(name)
    missing = LOAD_BEARING_TOOLS - discovered
    assert not missing, f"core tools missing from entry points: {sorted(missing)}"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
