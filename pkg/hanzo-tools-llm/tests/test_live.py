"""The two tools against api.hanzo.ai, with the credential HanzoCloud resolves.

Skipped when no credential resolves (HANZO_API_KEY, ~/.hanzo/config.json, or a
signed-in `hanzo` CLI). The premium query spends a few tokens of credit.
"""

import json
import asyncio

import pytest
from hanzo_tools.llm import KaiDecideTool, UnifiedLLMTool
from hanzo_tools.core import HanzoCloud

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not HanzoCloud().configured(), reason="no Hanzo credential"),
]


def run(tool, **kw):
    async def call():
        try:
            return await tool.call(None, **kw)
        finally:
            if tool._cloud is not None:
                await tool._cloud.aclose()

    return asyncio.run(call())


def test_live_limits_states_shares_and_never_a_figure():
    env = run(UnifiedLLMTool(), action="limits")
    assert env["ok"], env
    d = env["data"]
    assert d["state"] in ("ok", "near", "limited") and d["plan"]
    assert all(set(a) == {"kind", "label", "url", "plan", "model"} for a in d["actions"])
    assert "$" not in json.dumps(d)


def test_live_models_by_class_carry_their_price():
    env = run(UnifiedLLMTool(), action="models", **{"class": "ours"}, family="kai")
    assert env["ok"], env
    kai = {m["id"]: m for m in env["data"]["models"]}["kai"]
    assert (kai["class"], kai["input_per_million"]) == ("ours", 0.021)


def test_live_a_premium_query_says_credits_paid_or_names_the_empty_wallet():
    env = run(UnifiedLLMTool(), prompt="Say ok", model="anthropic/claude-sonnet-4.5", max_tokens=5)
    if env["ok"]:
        d = env["data"]
        assert (d["served"], d["usage_class"], d["paid_by"]) == ("anthropic/claude-sonnet-4.5", "premium", "credits")
    else:
        assert (env["error"]["code"], env["error"]["status"]) == ("insufficient_balance", 402), env


def test_live_kai_decides_or_names_its_refusal():
    env = run(
        KaiDecideTool(),
        state="I was charged twice for one order",
        questions={"team": {"type": "choice", "criteria": ["payments", "account"]}},
    )
    if env["ok"]:
        assert env["data"]["answers"]["team"]["choice"] in ("payments", "account")
    else:
        e = env["error"]
        assert e["code"] == "free_plan_cap" and e["class"] == "ours" and e["resets_at"]
