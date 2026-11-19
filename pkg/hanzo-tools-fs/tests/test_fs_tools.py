"""Tests for hanzo-tools-fs."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import fs

        assert fs is not None

    def test_import_tools(self):
        from hanzo_tools.fs import TOOLS

        assert len(TOOLS) > 0

    def test_import_read_tool(self):
        from hanzo_tools.fs import ReadTool

        assert ReadTool.name == "read"

    def test_import_write_tool(self):
        from hanzo_tools.fs import WriteTool

        assert WriteTool.name == "write"

    def test_import_edit_tool(self):
        from hanzo_tools.fs import EditTool

        assert EditTool.name == "edit"


class TestReadTool:
    """Tests for ReadTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.fs import ReadTool

        return ReadTool()

    def test_has_description(self, tool):
        assert tool.description
        assert "read" in tool.description.lower()


class TestWriteTool:
    """Tests for WriteTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.fs import WriteTool

        return WriteTool()

    def test_has_description(self, tool):
        assert tool.description
        assert "write" in tool.description.lower()


class TestFsApplyPatch:
    """fs apply_patch edits in one call (hanzo-inc/cloud#758), as the Rust and TS tools do.

    A model that sends uri, old_text and new_text without a prior read is not refused
    into a read-then-retry loop: the unique match is the guard, and a base_hash, when
    sent, is still checked.
    """

    @pytest.fixture
    def tool(self, tmp_path):
        from hanzo_tools.fs import FsTool
        from hanzo_tools.core import PermissionManager

        return FsTool(permission_manager=PermissionManager(allowed_paths=[tmp_path]))

    async def test_edits_in_one_call_without_a_prior_read(self, tool, tmp_path):
        f = tmp_path / "c.txt"
        f.write_text("one\ntwo\nthree\n")

        ok = await tool.call(None, action="apply_patch", uri=str(f), old_text="two", new_text="2")

        assert ok["ok"] is True, ok
        assert f.read_text() == "one\n2\nthree\n"
        assert ok["data"]["previous_hash"].startswith("sha256:")

    async def test_without_a_hash_the_match_must_be_unique(self, tool, tmp_path):
        f = tmp_path / "c.txt"
        f.write_text("x x\n")

        twice = await tool.call(None, action="apply_patch", uri=str(f), old_text="x", new_text="y")
        none = await tool.call(None, action="apply_patch", uri=str(f), old_text="z", new_text="y")

        assert twice["error"]["code"] == "INVALID_PARAMS"
        assert none["error"]["code"] == "NOT_FOUND"
        assert f.read_text() == "x x\n"

    async def test_a_sent_hash_still_refuses_a_stale_edit(self, tool, tmp_path):
        f = tmp_path / "b.txt"
        f.write_text("alpha beta\n")
        stale = await tool.call(
            None, action="apply_patch", uri=str(f), old_text="alpha", new_text="A", base_hash="sha256:0"
        )
        assert stale["error"]["code"] == "CONFLICT"

        current = (await tool.call(None, action="stat", uri=str(f)))["data"]["hash"]
        ok = await tool.call(
            None, action="apply_patch", uri=str(f), old_text="alpha", new_text="A", base_hash=current
        )
        assert ok["ok"] is True, ok
        assert ok["data"]["previous_hash"] == current
        assert f.read_text() == "A beta\n"

    async def test_a_patch_text_is_pointed_at_the_patch_action(self, tool, tmp_path):
        f = tmp_path / "d.txt"
        f.write_text("one\n")

        r = await tool.call(
            None, action="apply_patch", uri=str(f), input="*** Begin Patch\n*** End Patch"
        )

        assert r["error"]["code"] == "INVALID_PARAMS"
        assert "old_text" in r["error"]["message"] and "new_text" in r["error"]["message"]
        assert 'action "patch"' in r["error"]["message"]
        assert f.read_text() == "one\n"

    def test_the_schema_says_what_apply_patch_takes(self, tool):
        assert "apply_patch: uri, old_text (must match exactly once), new_text" in tool.description
        schema = tool._handlers["apply_patch"].schema
        assert schema["required"] == ["uri", "old_text", "new_text"]
        assert "optional" in schema["properties"]["base_hash"]["description"]
