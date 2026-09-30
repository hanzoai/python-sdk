"""The browser tool's progressive surface and its snapshot → ref routing.

The schema carries the core actions; `help` serves the rest. Refs, snapshot and
read go to the extension's page engine, whose replies come back as text or as
errors an agent can act on.
"""

import re
import json
import inspect

import pytest
from mcp.server import FastMCP

from hanzo_tools.browser.zapd_consumer import UNPAIRED
from hanzo_tools.browser.browser_tool import ACTIONS, CORE, TOPICS, BrowserTool, _help

CORE_ACTIONS = ("navigate", "snapshot", "click", "fill", "type", "press", "read", "screenshot", "evaluate", "wait", "tabs", "help")


class FakeConsumer:
    """A zapd consumer with one Chrome provider that answers from `replies`."""

    def __init__(self, replies=None):
        self.sent = []
        self.replies = replies or {}

    def resolve_browser(self, browser, client_id):
        return "browser/host/chrome-1a2b"

    def route(self, provider, method, params, timeout=30.0):
        self.sent.append((method, params))
        reply = self.replies.get(method, {"ok": True})
        return reply.encode() if isinstance(reply, str) else json.dumps(reply).encode()


@pytest.fixture
def consumer(monkeypatch):
    c = FakeConsumer()
    monkeypatch.setattr("hanzo_tools.browser.zapd_consumer.get_consumer", lambda: c)
    return c


@pytest.fixture
def tool():
    return BrowserTool(backend="chrome")


async def schema() -> dict:
    mcp = FastMCP("t")
    BrowserTool(backend="chrome").register(mcp)
    [t] = await mcp.list_tools()
    return {"description": t.description, "schema": t.inputSchema}


class TestSurface:
    def test_core_is_the_default_set(self):
        assert CORE == CORE_ACTIONS

    @pytest.mark.asyncio
    async def test_schema_is_small_and_open_ended(self):
        s = await schema()
        props = s["schema"]["properties"]
        assert set(props) == {
            "action", "selector", "url", "text", "key", "code", "interactive", "compact", "depth",
            "outline", "filter", "annotate", "timeout", "tab_id", "target_browser", "topic", "args",
        }
        # A string, not an enum of every action: the rest is discovered through help.
        assert props["action"]["type"] == "string"
        assert "enum" not in json.dumps(props["action"])
        assert all(a in props["action"]["description"] for a in CORE_ACTIONS)
        assert len(json.dumps(s["schema"])) < 4000

    @pytest.mark.asyncio
    async def test_description_teaches_the_loop_in_a_few_lines(self):
        d = (await schema())["description"]
        assert len(d.splitlines()) <= 15
        for must in ("snapshot", '[ref=e2]', '@e2', "read", "annotate", 'action="help"', "args"):
            assert must in d

    def test_every_action_is_served_somewhere(self):
        """Each action reaches the extension (a wire method) or a Playwright branch, and no branch serves a name the table lacks."""
        src = inspect.getsource(BrowserTool.execute)
        body = src[src.index("# === FALL BACK TO PLAYWRIGHT ===") :]
        branches = set(re.findall(r'action == "(\w+)"', body))
        branches |= {f"expect_{t}" for t in re.findall(r'assertion_type == "(\w+)"', body)}
        branches |= {"expect_url", "expect_title"} & set(re.findall(r'action == "(expect_\w+)"', body))
        assert branches <= set(ACTIONS)
        unserved = [n for n, op in ACTIONS.items() if n not in branches and n not in ("help", "browsers")]
        assert unserved == []

    @pytest.mark.parametrize("gone", [
        "select_option", "get_inner_text", "get_value", "clear", "content", "new_page", "press_key",
        "list_browsers", "list_mcp_instances", "use_browser", "set_default_browser", "claim_browser",
        "locator", "get_by_role", "get_by_text", "first", "nth", "filter", "all", "is_hidden",
        "mouse_wheel", "frame", "main_frame", "on", "off",
    ])
    @pytest.mark.asyncio
    async def test_aliases_and_no_ops_are_gone(self, tool, gone):
        out = await tool.execute(action=gone)
        assert out["error"].startswith(f"Unknown action {gone!r}")
        assert 'action="help"' in out["error"]


class TestHelp:
    def test_default_help_is_the_loop_and_every_other_action(self):
        h = _help()
        assert h.startswith("The loop: snapshot, act on refs")
        assert "covered by a consent banner" in h
        assert 'args={"value": "Weekly"}' in h
        for name, op in ACTIONS.items():
            if op.topic != "core":
                assert re.search(rf"^  {name}\b", h, re.M), name
        assert not re.search(r"^core$", h, re.M)

    def test_topic_narrows(self):
        h = _help("interact")
        assert h.startswith("interact\n")
        assert "  select            selector, args.value" in h
        assert "navigate" not in h
        assert "  navigate" in _help("core")

    def test_playwright_only_actions_are_marked(self):
        assert re.search(r"^  route .*\(Playwright\)$", _help("network"), re.M)
        assert not re.search(r"^  hover .*\(Playwright\)$", _help("interact"), re.M)

    def test_unknown_topic_names_the_topics(self):
        assert _help("nope") == f"No topic 'nope'. Topics: {', '.join(TOPICS)}."

    @pytest.mark.asyncio
    async def test_help_through_the_tool(self, tool):
        assert await tool.execute(action="help", topic="tabs") == _help("tabs")


class TestRouting:
    @pytest.mark.asyncio
    async def test_snapshot_answers_the_tree_as_text(self, tool, consumer):
        consumer.replies["hanzo.snapshot"] = {"tree": '- button "Go" [ref=e2]', "refs": 1, "url": "https://a.test/", "title": "A"}
        out = await tool.execute(action="snapshot", interactive=True, depth=3)
        assert out == 'A — https://a.test/ (1 refs)\n- button "Go" [ref=e2]'
        method, params = consumer.sent[-1]
        assert method == "hanzo.snapshot"
        assert params["interactive"] == "true"
        assert params["depth"] == "3"
        assert "compact" not in params

    @pytest.mark.asyncio
    async def test_act_by_ref(self, tool, consumer):
        consumer.replies["hanzo.act"] = {"clicked": '@e2 (button "Go")'}
        out = await tool.execute(action="click", selector="@e2")
        assert out == {"success": True, "clicked": '@e2 (button "Go")'}
        assert consumer.sent[-1] == ("hanzo.act", {"selector": "@e2", "op": "click"})

    @pytest.mark.parametrize("action,op,extra,wire", [
        ("fill", "fill", {"text": "a@b.co"}, {"text": "a@b.co"}),
        ("type", "type", {"text": "hi"}, {"text": "hi"}),
        ("press", "press", {"key": "Enter"}, {"key": "Enter"}),
        ("select", "select", {"value": "Weekly"}, {"value": "Weekly"}),
        ("check", "check", {}, {}),
        ("get_text", "text", {}, {}),
        ("get_attribute", "attribute", {"attribute": "href"}, {"attribute": "href"}),
        ("scroll_into_view", "scrollIntoView", {}, {}),
        ("scroll", "scroll", {}, {"dy": "300"}),
        ("scroll", "scroll", {"delta_x": 5, "delta_y": -40}, {"dx": "5", "dy": "-40"}),
    ])
    @pytest.mark.asyncio
    async def test_each_act_carries_its_op(self, tool, consumer, action, op, extra, wire):
        await tool.execute(action=action, selector="@e7", **extra)
        method, params = consumer.sent[-1]
        assert method == "hanzo.act"
        assert params == {"selector": "@e7", "op": op, **wire}

    @pytest.mark.asyncio
    async def test_read_answers_markdown(self, tool, consumer):
        consumer.replies["hanzo.read"] = {"markdown": "# Pricing\n\nPro $20", "url": "https://a.test/", "title": "A", "truncated": False}
        out = await tool.execute(action="read", outline=True, filter="pro")
        assert out == "A — https://a.test/\n\n# Pricing\n\nPro $20"
        assert consumer.sent[-1] == ("hanzo.read", {"outline": "true", "filter": "pro"})

    @pytest.mark.asyncio
    async def test_a_page_refusal_is_the_error_itself(self, tool, consumer):
        consumer.replies["hanzo.act"] = "ERR:Stale ref @e4: its element is no longer in the page. Run snapshot again for fresh refs."
        out = await tool.execute(action="click", selector="@e4")
        assert out == {"error": "Stale ref @e4: its element is no longer in the page. Run snapshot again for fresh refs.", "action": "click"}

    @pytest.mark.asyncio
    async def test_annotate_asks_for_labels_and_returns_the_legend(self, tool, consumer):
        import base64
        from io import BytesIO

        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (40, 20), "white").save(buf, "PNG")
        consumer.replies["hanzo.annotate"] = {"data": base64.b64encode(buf.getvalue()).decode(), "format": "png", "legend": ['[2] @e2 button "Go"']}
        out = await tool.execute(action="screenshot", annotate=True)
        assert consumer.sent[-1][0] == "hanzo.annotate"
        assert out["legend"] == ['[2] @e2 button "Go"']
        assert out["success"] is True and "image" in out

    @pytest.mark.asyncio
    async def test_navigate_waits_through_the_engine(self, tool, consumer):
        consumer.replies["hanzo.navigate"] = {"url": "https://a.test/", "title": "A", "loaded": True}
        out = await tool.execute(action="navigate", url="https://a.test/")
        assert out == {"success": True, "url": "https://a.test/", "title": "A", "loaded": True}

    @pytest.mark.asyncio
    async def test_a_bare_wait_is_a_pause(self, tool, consumer):
        assert await tool.execute(action="wait", timeout=1) == {"success": True, "waited_ms": 1}
        assert consumer.sent == []
        await tool.execute(action="wait", text="Welcome", timeout=500)
        assert consumer.sent[-1] == ("hanzo.wait", {"text": "Welcome", "timeout": "500"})


class TestRefsNeedTheExtension:
    @pytest.mark.asyncio
    async def test_no_playwright_stand_in_for_a_ref(self, monkeypatch):
        class Alone:
            def resolve_browser(self, browser, client_id):
                return None

        monkeypatch.setattr("hanzo_tools.browser.zapd_consumer.get_consumer", lambda: Alone())
        out = await BrowserTool(backend="auto").execute(action="click", selector="@e2")
        assert out == {"error": UNPAIRED, "action": "click", "backend": "auto"}

    @pytest.mark.asyncio
    async def test_playwright_backend_refuses_a_ref_by_name(self):
        out = await BrowserTool(backend="playwright").execute(action="click", selector="e12")
        assert out["error"].startswith("e12 is a snapshot ref")


class TestArgs:
    @pytest.mark.asyncio
    async def test_non_core_parameters_travel_in_args(self, consumer):
        mcp = FastMCP("t")
        BrowserTool(backend="chrome").register(mcp)
        await mcp.call_tool("browser", {"action": "select", "selector": "@e4", "args": {"value": "Weekly"}})
        assert consumer.sent[-1] == ("hanzo.act", {"selector": "@e4", "value": "Weekly", "op": "select"})

    @pytest.mark.asyncio
    async def test_unknown_args_are_named(self, consumer):
        mcp = FastMCP("t")
        BrowserTool(backend="chrome").register(mcp)
        out = await mcp.call_tool("browser", {"action": "click", "args": {"selectr": "x", "selector": "y"}})
        text = json.dumps([c.model_dump() for c in (out[0] if isinstance(out, tuple) else out)])
        assert "Unknown args ['selector', 'selectr']" in text
        assert consumer.sent == []

    @pytest.mark.asyncio
    async def test_text_answers_are_text(self, consumer):
        mcp = FastMCP("t")
        BrowserTool(backend="chrome").register(mcp)
        out = await mcp.call_tool("browser", {"action": "help", "topic": "core"})
        blocks = out[0] if isinstance(out, tuple) else out
        assert blocks[0].text == _help("core")
