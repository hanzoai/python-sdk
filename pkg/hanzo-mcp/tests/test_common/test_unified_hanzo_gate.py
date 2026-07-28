"""Tests for the unified `hanzo` surface and the gate that hides per-service tools.

Regression cover for a live outage: the gate force-disabled the ten Hanzo cloud
tools in favour of a `hanzo` tool that no installed package provided, so the
whole cloud surface disappeared with no warning. The invariant below is the
point -- there must always be a way to reach the services.
"""

import pytest
from mcp.server import FastMCP

from hanzo_tools.core import PermissionManager

from hanzo_mcp.tools import HANZO_SERVICE_TOOLS, register_all_tools
from hanzo_mcp.tools.common.entrypoint_loader import tool_identity


def _registered(**kwargs) -> set[str]:
    """Tool names an MCP server ends up exposing for a given configuration."""
    import asyncio

    server = FastMCP("test")
    pm = PermissionManager()
    register_all_tools(server, pm, use_mode=False, **kwargs)
    return {tool.name for tool in asyncio.run(server.list_tools())}


class TestUnifiedSurfaceGate:
    def test_hanzo_tool_is_registered(self):
        assert "hanzo" in _registered()

    def test_hanzo_supersedes_per_service_tools(self):
        assert not (_registered() & set(HANZO_SERVICE_TOOLS))

    def test_per_service_tools_survive_when_hanzo_is_unavailable(self):
        """Never hide the old way while the new way is absent."""
        names = _registered(enabled_tools={"hanzo": False})
        assert "hanzo" not in names
        assert set(HANZO_SERVICE_TOOLS) <= names

    def test_gate_warns_when_falling_back(self, caplog):
        _registered(enabled_tools={"hanzo": False})
        assert "Unified `hanzo` tool unavailable" in caplog.text

    def test_every_advertised_service_resolves(self):
        """`hanzo` must not advertise a service it cannot dispatch to."""
        from hanzo_tools.api.hanzo_tool import SERVICE_TOOL_PATHS, HanzoTool

        tool = HanzoTool()
        for service in SERVICE_TOOL_PATHS:
            assert tool._load_delegate(service) is not None


class TestToolIdentity:
    @pytest.mark.parametrize("attr_index", [0, 1])
    def test_resolves_property_declarations(self, attr_index):
        """@property read off the class yields a descriptor, not the value.

        Returning it raw is what made `tool list` fail on len().
        """

        class PropertyTool:
            @property
            def name(self) -> str:
                return "propertied"

            @property
            def description(self) -> str:
                return "described"

        assert tool_identity(PropertyTool)[attr_index] in ("propertied", "described")
        assert isinstance(tool_identity(PropertyTool)[attr_index], str)

    def test_falls_back_when_class_cannot_be_instantiated(self):
        class NeedsArgs:
            def __init__(self, required):
                pass

            @property
            def name(self) -> str:
                return "never reached"

        assert tool_identity(NeedsArgs) == ("needsargs", "")

    def test_registry_descriptions_are_all_strings(self):
        from hanzo_mcp.config.tool_config import DynamicToolRegistry

        DynamicToolRegistry.reset()
        entries = DynamicToolRegistry.list_all()
        assert entries
        assert all(isinstance(e.description, str) for e in entries.values())
