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


class TestZapdWire:
    """The consumer delegates the router envelope to canonical ``zap.frame`` and
    keeps only the untagged browser-command codec the extension peer decodes."""

    def test_uses_canonical_frame(self):
        # No hand-rolled envelope: socket_path and the client come from zap.
        from hanzo_tools.browser import zapd_consumer as zc
        from zap import frame
        from zap.client import ZapClient

        assert zc.socket_path() == frame.socket_path()
        assert zc.ZapClient is ZapClient
        # The duplicated framing primitives are gone from this module.
        for gone in ("_encode_frame", "_hello_payload", "_parse_providers", "_read_frame"):
            assert not hasattr(zc, gone), f"{gone} should be deleted (use zap.frame)"

    def test_cmd_codec_is_extension_compatible_untagged(self):
        """``_encode_cmd`` must match the extension's ``decodeCmd`` byte layout:
        method + u16 count + per-param(key + u32 len + value), NO type tag.

        This is intentionally NOT ``zap.frame.encode_cmd`` (which inserts a
        per-value tag byte). Decode it here exactly as native-zap.ts does and
        confirm the round trip; then confirm the tagged helper differs.
        """
        from hanzo_tools.browser.zapd_consumer import _encode_cmd
        from zap import frame

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

        # The canonical (tagged) helper is a different, longer wire — proving we
        # were right not to use it for this peer.
        assert frame.encode_cmd(method, params) != buf
        assert len(frame.encode_cmd(method, params)) == len(buf) + len(params)
