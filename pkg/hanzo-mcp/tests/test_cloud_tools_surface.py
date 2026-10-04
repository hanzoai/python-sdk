"""The cloud-backed tools ride the default surface of every mode.

A mode disables every registered tool it does not list, so a tool missing from
ESSENTIAL_TOOLS is installed and invisible. llm (completions, the catalog, the
plan's limits), kai_decide and repo (repositories on Hanzo git) are HTTP calls to
api.hanzo.ai, so every mode carries them.
"""

from hanzo_mcp.tools.common.entrypoint_loader import PACKAGE_TOOL_PREFIXES
from hanzo_mcp.tools.common.mode import ModeRegistry
from hanzo_mcp.tools.common.mode_loader import ModeLoader
from hanzo_mcp.tools.common.personality import ESSENTIAL_TOOLS

CLOUD_TOOLS = ("llm", "kai_decide", "repo")


def test_the_cloud_tools_are_essential():
    assert set(CLOUD_TOOLS) <= set(ESSENTIAL_TOOLS)
    assert PACKAGE_TOOL_PREFIXES["llm"] == ["llm", "kai_decide"]
    assert PACKAGE_TOOL_PREFIXES["vcs"] == ["git", "repo"]


def test_every_mode_enables_them():
    ModeLoader.initialize_modes()
    modes = ModeRegistry.list()
    assert modes
    for mode in modes:
        enabled = ModeLoader.get_enabled_tools_from_mode(force_mode=mode.name)
        assert all(enabled.get(t) for t in CLOUD_TOOLS), (
            mode.name,
            {t: enabled.get(t) for t in CLOUD_TOOLS},
        )
