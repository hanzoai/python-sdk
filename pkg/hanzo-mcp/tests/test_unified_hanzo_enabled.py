"""Regression: the default mode must leave the unified `hanzo` tool enabled.

The bug this guards against: ``register_all_tools`` gates the unified tool on
``is_tool_enabled("hanzo", True)``, which returns ``tool_config["hanzo"]``
whenever that key exists. ``ModeLoader.get_enabled_tools_from_mode`` builds
``tool_config`` by disabling every key in ``TOOL_REGISTRY`` and then re-enabling
only the active mode's ``tools`` list. ``TOOL_REGISTRY`` has ``"hanzo"``, so a
mode that omits it does not fall back to the ``True`` default — it explicitly
disables it.

That is what shipped in 0.15.13: the tool built, imported, and registered its
entry point, yet ``tools/list`` came back with 40 tools and no ``hanzo``, while
the server logged "unified `hanzo` tool unavailable". Two things broke at once,
because ``register_all_tools`` only retires the per-service cloud tools once
``hanzo`` is enabled — so the 166-service surface was off AND the ten tools it
replaces were still on. An import-level check cannot catch this: the import
succeeds. The gate has to be tested where it is actually decided.
"""

import pytest

from hanzo_mcp.config.tool_config import TOOL_REGISTRY
from hanzo_mcp.tools import SUPERSEDED_BY_HANZO, _unified_hanzo_available
from hanzo_mcp.tools.common.mode import ModeRegistry, activate_mode_from_env
from hanzo_mcp.tools.common.mode_loader import ModeLoader

UNIFIED = "hanzo"


@pytest.fixture(autouse=True)
def _modes_loaded():
    """Modes are registered lazily; the gate reads whatever is active."""
    ModeLoader.initialize_modes()
    activate_mode_from_env()


def test_unified_tool_is_in_the_registry():
    """If it left TOOL_REGISTRY the clean-slate loop could no longer reach it."""
    assert UNIFIED in TOOL_REGISTRY


def test_default_mode_lists_the_unified_tool():
    """The active mode must name `hanzo`, or the clean slate leaves it off."""
    mode = ModeRegistry.get_active()
    assert mode is not None, "no active mode; the gate would read an empty config"
    assert UNIFIED in mode.tools, (
        f"mode {mode.name!r} omits {UNIFIED!r}, so ModeLoader disables it. "
        f"mode.tools={sorted(mode.tools)}"
    )


def test_resolved_config_enables_the_unified_tool():
    """The fingerprint of the 0.15.13 regression: tool_config['hanzo'] is False."""
    config = ModeLoader.get_enabled_tools_from_mode(
        base_enabled_tools=None, force_mode=None
    )
    assert config.get(UNIFIED) is True, (
        f"tool_config[{UNIFIED!r}]={config.get(UNIFIED)!r} — register_all_tools "
        "will skip the unified tool and keep the per-service tools it replaces."
    )


def test_superseded_tools_are_retired_when_the_unified_tool_is_available():
    """Enabling `hanzo` is what retires the ten per-service cloud tools.

    Mirrors the branch in register_all_tools so the two cannot drift: if the
    unified tool imports and the mode enables it, none of the tools it replaces
    should survive into the resolved config.
    """
    if not _unified_hanzo_available():
        pytest.skip("hanzo-tools-api not installed; nothing to supersede")

    config = ModeLoader.get_enabled_tools_from_mode(
        base_enabled_tools=None, force_mode=None
    )
    assert config.get(UNIFIED) is True

    still_on = [t for t in SUPERSEDED_BY_HANZO if config.get(t)]
    assert not still_on, (
        f"{still_on} stayed enabled alongside the unified tool that replaces them"
    )
