"""The default surface is what every prompt of an agent carries: tools/list is its schema bill.

The active mode is the whole manifest. A tool it does not list is off, whichever package ships it (before,
only the names `register_all_tools` enumerated obeyed the mode, so the shell and browser helpers stayed on
in every mode); what the user asks for by name stands over the mode.
"""

import asyncio
import json

import pytest
from mcp.server.fastmcp import FastMCP

from hanzo_mcp.tools import register_all_tools
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.common.mode import ModeRegistry
from hanzo_mcp.tools.common.mode_loader import ModeLoader
from hanzo_mcp.tools.common.personality import DEFAULT_TOOLS

# Tools registered outside any mode: the way to a wider surface.
SYSTEM = {"tool", "version", "stats", "mode"}
BUDGET_BYTES = 36_000  # the default surface at 0.15.20 was 61,000


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HANZO_MCP_ENABLED_TOOLS", raising=False)
    monkeypatch.delenv("HANZO_MCP_MODE", raising=False)
    ModeRegistry.clear() if hasattr(ModeRegistry, "clear") else None
    ModeLoader.initialize_modes()


def listed():
    server = FastMCP("surface")
    register_all_tools(server, PermissionManager())
    return asyncio.run(server.list_tools())


def test_the_default_lists_the_default_mode_and_nothing_else():
    names = {t.name for t in listed()}
    assert names <= set(DEFAULT_TOOLS) | SYSTEM, sorted(names - set(DEFAULT_TOOLS) - SYSTEM)
    assert {"fs", "zsh", "git", "browser", "playwright"} <= names


def test_the_default_stays_inside_its_schema_budget():
    size = sum(len(json.dumps(t.model_dump(exclude_none=True))) for t in listed())
    assert size < BUDGET_BYTES, size


def test_a_name_asked_for_stands_over_the_mode(monkeypatch):
    assert "memory" not in {t.name for t in listed()}
    monkeypatch.setenv("HANZO_MCP_ENABLED_TOOLS", "memory,critic")
    assert {"memory", "critic"} <= {t.name for t in listed()}


def test_all_restores_every_tool(monkeypatch):
    base = {t.name for t in listed()}
    monkeypatch.setenv("HANZO_MCP_ENABLED_TOOLS", "all")
    names = {t.name for t in listed()}
    assert base < names and {"memory", "computer", "wget"} <= names
