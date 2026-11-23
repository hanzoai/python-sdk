"""The default surface is what every prompt of an agent carries: tools/list is its schema bill.

Under the finalized HIP-0300 canonical surface ("one and one way to do everything"),
`tools/list` advertises the exact 19 canonical tools across Rust, TypeScript, and Python:
fs, exec, code, git, fetch, workspace, browser, computer, ui, kai, think, plan, memory,
tasks, tracker, coding, research, skills, hanzo.
"""

import asyncio
import json

import pytest
from mcp.server.fastmcp import FastMCP

from hanzo_mcp.tools import register_all_tools
from hanzo_mcp.tools.canonical import CANONICAL_TOOLS
from hanzo_mcp.tools.common.mode import ModeRegistry
from hanzo_mcp.tools.common.mode_loader import ModeLoader
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.common.personality import DEFAULT_TOOLS

BUDGET_BYTES = 36_000  # the default surface at 0.15.20 was 61,000


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HANZO_MCP_ENABLED_TOOLS", raising=False)
    monkeypatch.delenv("HANZO_MCP_MODE", raising=False)
    monkeypatch.delenv("HANZO_MCP_LEGACY_SURFACE", raising=False)
    ModeRegistry.clear() if hasattr(ModeRegistry, "clear") else None
    ModeLoader.initialize_modes()


def listed():
    server = FastMCP("surface")
    register_all_tools(server, PermissionManager())
    return asyncio.run(server.list_tools())


def test_the_default_lists_the_19_canonical_tools_and_nothing_else():
    names = {t.name for t in listed()}
    assert len(CANONICAL_TOOLS) == 19
    assert set(DEFAULT_TOOLS) == set(CANONICAL_TOOLS)
    assert names == set(CANONICAL_TOOLS), (
        f"missing={sorted(set(CANONICAL_TOOLS) - names)}, extra={sorted(names - set(CANONICAL_TOOLS))}"
    )


def test_the_default_stays_inside_its_schema_budget():
    size = sum(len(json.dumps(t.model_dump(exclude_none=True))) for t in listed())
    assert size < BUDGET_BYTES, size


def test_a_name_asked_for_stands_over_the_mode(monkeypatch):
    assert "critic" not in {t.name for t in listed()}
    monkeypatch.setenv("HANZO_MCP_ENABLED_TOOLS", "critic,lsp")
    assert {"critic", "lsp"} <= {t.name for t in listed()}


def test_all_restores_every_tool(monkeypatch):
    base = {t.name for t in listed()}
    monkeypatch.setenv("HANZO_MCP_ENABLED_TOOLS", "all")
    names = {t.name for t in listed()}
    assert base < names and {"critic", "computer", "wget"} <= names


def test_canonical_skills_and_kai_execute_cleanly(monkeypatch, tmp_path):
    monkeypatch.setenv("HANZO_SKILLS_DIR", str(tmp_path / "skills"))
    server = FastMCP("exec_check")
    tools = {t.name: t for t in register_all_tools(server, PermissionManager())}

    guard_out = json.loads(asyncio.run(tools["kai"].call(None, action="command_guard", command="rm -rf /")))
    assert guard_out["verdict"] == "deny"

    bad_slug = json.loads(asyncio.run(tools["skills"].call(None, action="install", slug="../evil", content="# x")))
    assert bad_slug["ok"] is False

    good_install = json.loads(
        asyncio.run(tools["skills"].call(None, action="install", slug="rust-expert", content="# Rust\n"))
    )
    assert good_install["ok"] is True
    assert (tmp_path / "skills" / "rust-expert" / "SKILL.md").read_text() == "# Rust\n"


def test_native_binary_delegation_verifies_elf_magic(monkeypatch, tmp_path):
    from hanzo_mcp.cli import _is_native_binary, _maybe_delegate_native, find_native_hanzo_mcp

    fake_py = tmp_path / "hanzo-mcp-py"
    fake_py.write_bytes(b"#!/usr/bin/env python3\nprint('hi')\n")
    fake_py.chmod(0o755)
    assert _is_native_binary(str(fake_py)) is False

    fake_elf = tmp_path / "hanzo-mcp-rs"
    fake_elf.write_bytes(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 56)
    fake_elf.chmod(0o755)
    assert _is_native_binary(str(fake_elf)) is True

    monkeypatch.setenv("HANZO_MCP_NATIVE", str(fake_elf))
    assert find_native_hanzo_mcp() == str(fake_elf)

    called = {}
    monkeypatch.setenv("HANZO_MCP_DELEGATE_NATIVE", "1")
    monkeypatch.delenv("HANZO_MCP_PURE_PYTHON", raising=False)
    monkeypatch.setattr("os.execv", lambda path, argv: called.update(path=path, argv=argv))

    assert _maybe_delegate_native(["hanzo-mcp", "serve", "--project-dir", "/tmp/proj"]) is True
    assert called["path"] == str(fake_elf)
    assert called["argv"] == [str(fake_elf), "-t", "stdio", "--project-dir", "/tmp/proj"]

