"""Tests for hanzo-tools-gimp."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import gimp

        assert gimp is not None

    def test_import_tools(self):
        from hanzo_tools.gimp import TOOLS

        assert len(TOOLS) == 1

    def test_import_gimp_tool(self):
        from hanzo_tools.gimp import GimpTool

        assert GimpTool.name == "gimp"

    def test_register_tools_callable(self):
        from hanzo_tools.gimp import register_tools

        assert callable(register_tools)


class TestGimpTool:
    """Tests for GimpTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.gimp import GimpTool

        return GimpTool()

    def test_name(self, tool):
        assert tool.name == "gimp"

    def test_version(self, tool):
        assert tool.VERSION

    def test_has_description(self, tool):
        assert tool.description
        assert "gimp" in tool.description.lower()

    def test_default_endpoint(self, tool):
        assert tool.host == "127.0.0.1"
        assert tool.port == 9876

    def test_custom_endpoint(self):
        from hanzo_tools.gimp import GimpTool

        t = GimpTool(host="10.0.0.5", port=12345)
        assert t.host == "10.0.0.5"
        assert t.port == 12345

    def test_action_surface(self, tool):
        # The tool must register exactly the documented actions
        # (plus the BaseTool built-ins: help, schema, status).
        expected = {
            "version",
            "open",
            "export",
            "pdb_call",
            "new_image",
            "image_info",
            "list_procedures",
            "flatten",
        }
        registered = set(tool._handlers.keys())
        assert expected <= registered, expected - registered

    def test_builtin_actions_present(self, tool):
        registered = set(tool._handlers.keys())
        assert {"help", "schema", "status"} <= registered


class TestSchema:
    """Schema generation from the registered actions."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.gimp import GimpTool

        return GimpTool()

    @pytest.mark.asyncio
    async def test_schema_action_returns_schemas(self, tool):
        env = await tool.call(None, "schema")
        assert env["ok"] is True
        schemas = env["data"]["schemas"]
        assert "pdb_call" in schemas
        # pdb_call requires a "procedure" string parameter.
        pdb = schemas["pdb_call"]
        assert pdb["properties"]["procedure"]["type"] == "string"
        assert "procedure" in pdb["required"]


class TestBridgeErrors:
    """Behavioral tests that do not require a running GIMP."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.gimp import GimpTool

        # Point at a closed port so connection fails fast.
        return GimpTool(host="127.0.0.1", port=9)

    @pytest.mark.asyncio
    async def test_connection_failure_is_reported(self, tool):
        # call() catches ToolError and returns an error envelope.
        env = await tool.call(None, "version")
        assert env["ok"] is False
        assert env["error"] is not None

    @pytest.mark.asyncio
    async def test_missing_required_param(self, tool):
        # pdb_call without a procedure -> InvalidParamsError -> error envelope.
        env = await tool.call(None, "pdb_call")
        assert env["ok"] is False
