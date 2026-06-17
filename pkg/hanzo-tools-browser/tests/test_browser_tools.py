"""Tests for hanzo-tools-browser."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import browser

        assert browser is not None

    def test_import_tools(self):
        from hanzo_tools.browser import TOOLS

        assert len(TOOLS) > 0

    def test_import_browser_tool(self):
        from hanzo_tools.browser import BrowserTool

        assert BrowserTool.name == "browser"


class TestBrowserTool:
    """Tests for BrowserTool."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.browser import BrowserTool

        return BrowserTool()

    def test_has_description(self, tool):
        assert tool.description
        assert (
            "browser" in tool.description.lower()
            or "playwright" in tool.description.lower()
        )


class TestCdpTool:
    """Tests for the zapd-native `cdp` tool (method-oriented peer of browser)."""

    @pytest.fixture
    def tool(self):
        from hanzo_tools.browser.cdp_tool import CdpTool

        return CdpTool()

    def test_registered_in_tools(self):
        from hanzo_tools.browser import TOOLS
        from hanzo_tools.browser.cdp_tool import CdpTool

        assert CdpTool in TOOLS

    def test_name(self, tool):
        assert tool.name == "cdp"

    @pytest.mark.asyncio
    async def test_send_requires_method(self, tool):
        result = await tool.execute(action="send")
        assert "error" in result and "method" in result["error"]

    @pytest.mark.asyncio
    async def test_zapd_unreachable_is_reported(self, tool, monkeypatch):
        # No zapd → a clear native-zap error, never a stale "server not running".
        monkeypatch.setattr(
            "hanzo_tools.browser.cdp_tool.get_consumer", lambda: None
        )
        result = await tool.execute(action="tabs")
        assert result.get("transport") == "native-zap"
        assert "zapd" in result["error"]

    @pytest.mark.asyncio
    async def test_routes_bare_method_not_cdp_envelope(self, tool, monkeypatch):
        """Regression: `cdp` must put the real CDP method on the wire.

        The old HTTP-bridge path sent {"action": "cdp", "method": ...} which the
        extension dispatch rejected with "Unknown method: cdp". The zapd path
        routes the method name verbatim.
        """
        sent = {}

        class FakeConsumer:
            def resolve_browser(self, browser, client_id):
                return "browser:chrome/host/default"

            def route(self, provider, method, params, timeout=30.0):
                sent["provider"] = provider
                sent["method"] = method
                sent["params"] = params
                return b'{"targetInfos": []}'

        monkeypatch.setattr(
            "hanzo_tools.browser.cdp_tool.get_consumer", lambda: FakeConsumer()
        )

        result = await tool.execute(action="tabs")
        # The method on the wire is the real CDP method, never "cdp".
        assert sent["method"] == "Target.getTargets"
        assert sent["method"] != "cdp"
        assert result["success"] is True
        assert result["transport"] == "native-zap"

        result = await tool.execute(action="status")
        assert sent["method"] == "Browser.getVersion"

        await tool.execute(
            action="send", method="Page.navigate", params={"url": "https://example.com"}
        )
        assert sent["method"] == "Page.navigate"
        assert sent["params"]["url"] == "https://example.com"
