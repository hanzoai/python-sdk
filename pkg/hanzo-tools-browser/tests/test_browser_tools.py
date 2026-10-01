"""Tests for hanzo-tools-browser."""

import struct

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
    async def test_no_router_is_reported(self, tool, monkeypatch):
        # A router that never answers is the router's own error, named.
        class NoRouter:
            def resolve_browser(self, browser, client_id):
                raise TimeoutError("zapd: no router on this machine")

        monkeypatch.setattr("hanzo_tools.browser.cdp_tool.get_consumer", lambda: NoRouter())
        result = await tool.execute(action="tabs")
        assert result.get("transport") == "native-zap"
        assert "zapd" in result["error"]

    @pytest.mark.asyncio
    async def test_no_browser_says_how_to_pair(self, tool, monkeypatch):
        class Alone:
            def resolve_browser(self, browser, client_id):
                return None

        monkeypatch.setattr("hanzo_tools.browser.cdp_tool.get_consumer", lambda: Alone())
        result = await tool.execute(action="tabs")
        assert "hanzo-mcp pair" in result["error"]

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
                return "browser/host/chrome-1a2b"

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


class TestZapdWire:
    """The router is the embedded zapd; the one codec here is the browser
    command body the extension's decodeCmd reads."""

    def test_the_router_is_embedded_not_spawned(self):
        from hanzo_tools.browser import zapd_consumer as zc

        assert zc.zapd.__name__ == "zapd"
        for gone in ("ensure_zapd_running", "_find_zapd", "_socket_live", "socket_path", "ZapClient"):
            assert not hasattr(zc, gone), f"{gone} is the retired daemon path"

    def test_a_browser_is_found_by_engine_or_name(self):
        from hanzo_tools.browser.zapd_consumer import ZapdConsumer

        c = ZapdConsumer.__new__(ZapdConsumer)
        nodes = [
            {"id": "mcp/spark/hanzo-42", "attrs": {}},
            {"id": "browser/spark/firefox-9c1d", "attrs": {"engine": "firefox"}},
            {"id": "browser/spark/chrome-1a2b", "attrs": {"engine": "chrome"}},
        ]
        c.list_providers = lambda: nodes
        assert c.resolve_browser(None, None) == "browser/spark/firefox-9c1d"
        assert c.resolve_browser("chrome", None) == "browser/spark/chrome-1a2b"
        assert c.resolve_browser("safari", None) is None
        assert c.resolve_browser(None, "browser/spark/chrome-1a2b") == "browser/spark/chrome-1a2b"
        assert c.resolve_browser(None, "mcp/spark/hanzo-42") is None

    def test_cmd_codec_is_extension_compatible_untagged(self):
        """``_encode_cmd`` matches the extension's ``decodeCmd`` byte layout:
        method + u16 count + per-param(key + u32 len + value), no type tag."""
        from hanzo_tools.browser.zapd_consumer import _encode_cmd

        method, params = "Page.navigate", {"url": "https://example.com", "tabId": "7"}
        buf = _encode_cmd(method, params)

        # Mirror extension/.../shared/native-zap.ts decodeCmd (little-endian).
        o = 0
        ml = struct.unpack_from("<H", buf, o)[0]; o += 2
        assert buf[o:o + ml].decode() == method; o += ml
        n = struct.unpack_from("<H", buf, o)[0]; o += 2
        assert n == len(params)
        out: dict[str, str] = {}
        for _ in range(n):
            kl = struct.unpack_from("<H", buf, o)[0]; o += 2
            k = buf[o:o + kl].decode(); o += kl
            vl = struct.unpack_from("<I", buf, o)[0]; o += 4  # u32 value len, no tag
            out[k] = buf[o:o + vl].decode(); o += vl
        assert o == len(buf)
        assert out == params



class TestConnectedBrowserIsTheAnswer:
    """A connected browser's own failure comes back; Playwright never stands in for it."""

    @pytest.fixture
    def tool(self, monkeypatch):
        import importlib

        from hanzo_tools.browser import BrowserTool

        browser_tool = importlib.import_module("hanzo_tools.browser.browser_tool")

        async def failed(*a, **k):
            return {"error": "timed out waiting for browser/dgx/chrome"}

        monkeypatch.setattr(browser_tool, "_extension_command", failed)
        monkeypatch.setattr(browser_tool, "PLAYWRIGHT_AVAILABLE", False)
        t = BrowserTool()
        t.backend = "auto"
        return t, browser_tool

    @pytest.mark.asyncio
    async def test_connected(self, tool, monkeypatch):
        t, bt = tool

        async def yes(**k):
            return True

        monkeypatch.setattr(bt, "_check_extension", yes)
        r = await t.execute(action="navigate", url="https://example.com")
        assert r["error"] == "timed out waiting for browser/dgx/chrome"

    @pytest.mark.asyncio
    async def test_none_connected_falls_through(self, tool, monkeypatch):
        t, bt = tool

        async def no(**k):
            return False

        monkeypatch.setattr(bt, "_check_extension", no)
        r = await t.execute(action="navigate", url="https://example.com")
        assert "timed out" not in str(r)
