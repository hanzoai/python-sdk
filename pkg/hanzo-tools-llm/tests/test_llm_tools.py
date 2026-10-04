"""Tests for hanzo-tools-llm: llm (Enso, the catalog, feedback) and kai_decide.

The tools run against a real HanzoCloud whose httpx transport is a recorder
answering as api.hanzo.ai does, so each test reads the exact request that went
out (method, path, bearer, Enso's headers, body) and what the tool made of the
answer. No socket is opened.
"""

import json
import asyncio

import httpx
import pytest
from hanzo_tools.llm import TOOLS, KaiDecideTool, UnifiedLLMTool
from hanzo_tools.core import HanzoCloud

COMPLETION = {
    "id": "chatcmpl-ae7c311d-5c64-47da-886b-86ceb2fd185f",
    "object": "chat.completion",
    "model": "enso-free",
    "choices": [
        {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "Hi there, friend."}}
    ],
    "usage": {"prompt_tokens": 110, "completion_tokens": 6, "total_tokens": 116},
}
CATALOG = {
    "object": "list",
    "data": [
        {
            "id": "kai",
            "family": "kai",
            "class": "ours",
            "outputs": ["decision"],
            "pricing": {"input_per_million": 0.021, "output_per_million": 0},
        },
        {
            "id": "enso-auto",
            "family": "enso",
            "class": "free",
            "outputs": ["text"],
            "context_window": 1000000,
            "pricing": {"input_per_million": 0, "output_per_million": 0},
        },
        {
            "id": "zen5",
            "family": "zen",
            "class": "ours",
            "pricing": {"input_per_million": 0.3, "output_per_million": 1.2},
        },
        {
            "id": "anthropic/claude-sonnet-4.5",
            "name": "Anthropic: Claude Sonnet 4.5",
            "owned_by": "anthropic",
            "family": None,
            "class": "premium",
            "inputs": ["text", "image"],
            "outputs": ["text"],
            "supports_tools": True,
            "supports_vision": True,
            "supports_reasoning": True,
            "pricing": {"input_per_million": 3, "output_per_million": 15},
        },
        {
            "id": "openrouter/auto",
            "name": "Auto Router",
            "class": "premium",
            "outputs": ["text"],
            "pricing": {"input_per_million": 0, "output_per_million": 0, "variable": True},
        },
    ],
}
#: A limits answer, plus three figures it must never hand on (spent_usd, used, cap).
LIMITS = {
    "plan": "dev",
    "state": "near",
    "period_start": "2026-10-01T00:00:00Z",
    "period_end": "2026-11-01T00:00:00Z",
    "spent_usd": 731.25,
    "classes": {
        "premium": {
            "percent": 85,
            "state": "near",
            "paying": "plan",
            "resets_at": "2026-11-01T00:00:00Z",
            "used": 987654,
            "window": {"percent": 40, "state": "ok", "resets_at": "2026-10-05T03:00:00Z", "cap": 424242},
        }
    },
    "session": {"percent": 10, "state": "ok", "resets_at": "2026-10-05T01:00:00Z"},
    "day": {"percent": 35, "state": "ok", "resets_at": "2026-10-05T00:00:00Z"},
    "paused": [{"model": "anthropic/claude-opus-4.1", "fallback": "enso", "resets_at": "2026-10-05T05:00:00Z"}],
    "actions": [
        {"kind": "upgrade", "label": "Upgrade to Max", "url": "https://hanzo.ai/pay/cart?plan=max-5x", "plan": "max-5x"}
    ],
    "upgrade": "max-5x",
    "credits_after_allowance": False,
}
#: Measured: POST /v1/decisions, model kai, org on the free plan.
FREE_PLAN_CAP = {
    "error": {
        "message": "Free plan: today's Kai requests are used. Upgrade for more: https://hanzo.ai/pay",
        "type": "rate_limit_error",
        "code": "free_plan_cap",
        "class": "ours",
        "resets_at": "2026-10-05T00:00:00Z",
        "upgrade_url": "https://hanzo.ai/pay/cart?plan=dev",
        "actions": [
            {
                "kind": "upgrade",
                "label": "Upgrade your plan",
                "url": "https://hanzo.ai/pay/cart?plan=dev",
                "plan": "dev",
            },
            {"kind": "topup", "label": "Add prepaid credit", "url": "https://hanzo.ai/pay"},
        ],
    }
}
MODEL_CAP = {
    "error": {
        "message": "This model has used its share of your plan for now. https://hanzo.ai/pay",
        "type": "billing_error",
        "code": "model_cap",
        "class": "premium",
        "model": "anthropic/claude-opus-4.1",
        "fallback": "enso",
        "resets_at": "2026-10-05T05:00:00Z",
        "upgrade_url": "https://hanzo.ai/pay/cart?plan=max-5x",
        "actions": [
            {"kind": "switch", "label": "Try Enso", "model": "enso"},
            {"kind": "topup", "label": "Add prepaid credit", "url": "https://hanzo.ai/pay"},
        ],
    }
}
DECISION = {
    "id": "dec_ff9388f6b8b85328960ba301635ac108",
    "model": "kai",
    "provider": "Hanzo",
    "answers": {
        "team": {
            "type": "choice",
            "choice": "payments",
            "confidence": 0.9983,
            "probabilities": {"account": 0.0006, "payments": 0.9989},
            "answer_confidence": 0.9989,
        }
    },
    "usage": {"input_tokens": 30, "output_tokens": 0},
}


class Gateway:
    """Records each request and answers it the way api.hanzo.ai does."""

    def __init__(self):
        self.seen: list[httpx.Request] = []
        self.answer = None  # (status, body) or (status, body, headers) to force one reply

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        if self.answer:
            status, body, *headers = self.answer
            return httpx.Response(status, json=body, headers=headers[0] if headers else None)
        path = request.url.path
        if path == "/v1/models":
            return httpx.Response(200, json=CATALOG)
        if path == "/v1/ai/limits":
            return httpx.Response(200, json=LIMITS)
        if path == "/v1/decisions":
            return httpx.Response(200, json=DECISION)
        if path == "/v1/ai/feedback":
            sent = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "msg": "",
                    "data": {"request_id": sent["request_id"].removeprefix("chatcmpl-"), "reward": 1, "recorded": True},
                },
            )
        return httpx.Response(200, json=COMPLETION, headers={"X-Routed-Model": "enso-free"})

    @property
    def last(self) -> httpx.Request:
        return self.seen[-1]


def wired(tool_class):
    gw = Gateway()
    cloud = HanzoCloud(base_url="https://api.hanzo.ai", key="sk-test")
    cloud._client = httpx.AsyncClient(base_url="https://api.hanzo.ai", transport=httpx.MockTransport(gw))
    tool = tool_class()
    tool._cloud = cloud
    return tool, gw


def run(tool, **kw):
    return asyncio.run(tool.call(None, **kw))


def body(req: httpx.Request):
    return json.loads(req.content) if req.content else None


def test_the_package_carries_llm_and_kai_decide():
    assert [t.name for t in TOOLS] == ["llm", "kai_decide"]
    assert UnifiedLLMTool.DEFAULT_ACTION == "query"
    assert KaiDecideTool.DEFAULT_ACTION == "decide"


def test_query_defaults_to_enso_auto_and_sends_no_unasked_bound():
    tool, gw = wired(UnifiedLLMTool)
    env = run(tool, prompt="Say hi.")
    assert env["ok"], env
    assert (gw.last.method, gw.last.url.path) == ("POST", "/v1/chat/completions")
    assert gw.last.headers["authorization"] == "Bearer sk-test"
    assert "x-max-cost" not in gw.last.headers and "x-max-latency-ms" not in gw.last.headers
    assert body(gw.last) == {"model": "enso-auto", "messages": [{"role": "user", "content": "Say hi."}]}


def test_query_carries_auto_and_the_bounds_and_returns_the_model_that_served():
    tool, gw = wired(UnifiedLLMTool)
    env = run(
        tool,
        action="query",
        model="auto",
        system="Be brief.",
        prompt="Say hi.",
        max_tokens=20,
        max_cost=0.01,
        max_latency_ms=800.4,
    )
    assert gw.last.headers["x-max-cost"] == "0.01"
    assert gw.last.headers["x-max-latency-ms"] == "800"
    assert body(gw.last) == {
        "model": "auto",
        "messages": [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Say hi."}],
        "max_tokens": 20,
    }
    assert env["data"] == {
        "id": COMPLETION["id"],
        "model": "enso-free",
        "content": "Hi there, friend.",
        "finish_reason": "stop",
        "usage": COMPLETION["usage"],
        "served": None,
        "paid_by": None,
        "usage_state": None,
        "usage_class": None,
        "fallback": None,
        "fallback_reason": None,
    }


def test_query_reads_who_answered_and_who_paid_from_the_headers():
    tool, gw = wired(UnifiedLLMTool)
    gw.answer = (
        200,
        {**COMPLETION, "model": "anthropic/claude-sonnet-4.5"},
        {
            "x-hanzo-usage": "ok",
            "x-hanzo-usage-class": "premium",
            "x-hanzo-paid-by": "credits",
            "x-hanzo-served": "anthropic/claude-sonnet-4.5",
        },
    )
    data = run(tool, prompt="Say ok", model="anthropic/claude-sonnet-4.5")["data"]
    assert (data["model"], data["served"], data["paid_by"], data["usage_state"], data["usage_class"]) == (
        "anthropic/claude-sonnet-4.5",
        "anthropic/claude-sonnet-4.5",
        "credits",
        "ok",
        "premium",
    )
    assert (data["fallback"], data["fallback_reason"]) == (None, None)


def test_query_fallback_opts_in_and_the_answer_names_who_answered_instead():
    tool, gw = wired(UnifiedLLMTool)
    gw.answer = (
        200,
        {**COMPLETION, "model": "enso"},
        {
            "x-hanzo-usage": "limited",
            "x-hanzo-fallback": "enso",
            "x-hanzo-usage-reason": "model_cap",
            "x-hanzo-served": "enso",
        },
    )
    data = run(tool, prompt="hi", model="anthropic/claude-opus-4.1", fallback=True)["data"]
    assert gw.last.headers["x-hanzo-fallback"] == "allow"
    assert (data["fallback"], data["fallback_reason"], data["usage_state"]) == ("enso", "model_cap", "limited")
    run(tool, prompt="hi")
    assert "x-hanzo-fallback" not in gw.last.headers


def test_query_takes_a_conversation_and_refuses_a_bad_bound_before_sending():
    tool, gw = wired(UnifiedLLMTool)
    msgs = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}, {"role": "user", "content": "c"}]
    run(tool, messages=msgs, model="enso-pro")
    assert body(gw.last) == {"model": "enso-pro", "messages": msgs}
    env = run(tool, prompt="hi", max_cost=-1)
    assert not env["ok"] and "max_cost must be a positive number" in env["error"]["message"]
    assert len(gw.seen) == 1


def test_a_refusal_carries_the_status_and_the_servers_sentence():
    tool, gw = wired(UnifiedLLMTool)
    gw.answer = (402, {"error": {"message": "Pick a plan", "type": "billing_error"}})
    env = run(tool, prompt="hi")
    assert not env["ok"]
    assert env["error"]["code"] == "UPSTREAM"
    assert "402" in env["error"]["message"] and "Pick a plan" in env["error"]["message"]


def test_models_lists_the_catalogs_own_prices_by_family():
    tool, gw = wired(UnifiedLLMTool)
    env = run(tool, action="models", family="kai")
    assert (gw.last.method, gw.last.url.path) == ("GET", "/v1/models")
    assert env["data"] == {
        "count": 1,
        "models": [
            {
                "id": "kai",
                "family": "kai",
                "class": "ours",
                "outputs": ["decision"],
                "context_window": None,
                "supports": [],
                "input_per_million": 0.021,
                "output_per_million": 0,
                "variable": False,
            }
        ],
    }
    assert run(tool, action="models")["data"]["count"] == 5


def test_models_searches_by_class_capability_and_words_and_shows_the_price():
    tool, gw = wired(UnifiedLLMTool)
    ids = lambda env: [m["id"] for m in env["data"]["models"]]  # noqa: E731
    assert ids(run(tool, action="models", **{"class": "ours"})) == ["kai", "zen5"]
    assert ids(run(tool, action="models", **{"class": "premium"}, capability="vision")) == [
        "anthropic/claude-sonnet-4.5"
    ]
    assert ids(run(tool, action="models", capability="decision")) == ["kai"]
    sonnet = run(tool, action="models", search="claude sonnet")["data"]["models"]
    assert [(m["id"], m["input_per_million"], m["output_per_million"], m["supports"]) for m in sonnet] == [
        ("anthropic/claude-sonnet-4.5", 3, 15, ["tools", "vision", "reasoning"])
    ]
    auto = run(tool, action="models", search="router")["data"]["models"]
    assert [(m["id"], m["variable"]) for m in auto] == [("openrouter/auto", True)]
    n = len(gw.seen)
    env = run(tool, action="models", **{"class": "gold"})
    assert not env["ok"] and "class must be one of premium, ours, free" in env["error"]["message"]
    assert len(gw.seen) == n


def test_limits_reads_shares_states_resets_and_actions_and_never_a_figure():
    tool, gw = wired(UnifiedLLMTool)
    env = run(tool, action="limits")
    assert (gw.last.method, gw.last.url.path) == ("GET", "/v1/ai/limits")
    d = env["data"]
    assert (d["plan"], d["state"], d["upgrade"], d["credits_after_allowance"]) == ("dev", "near", "max-5x", False)
    assert d["classes"] == {
        "premium": {
            "percent": 85,
            "state": "near",
            "resets_at": "2026-11-01T00:00:00Z",
            "paying": "plan",
            "window": {"percent": 40, "state": "ok", "resets_at": "2026-10-05T03:00:00Z"},
        }
    }
    assert d["day"] == {"percent": 35, "state": "ok", "resets_at": "2026-10-05T00:00:00Z"}
    assert d["paused"] == [
        {"model": "anthropic/claude-opus-4.1", "fallback": "enso", "resets_at": "2026-10-05T05:00:00Z"}
    ]
    assert d["actions"][0]["url"] == "https://hanzo.ai/pay/cart?plan=max-5x"
    wire = json.dumps(env)
    for figure in ("731.25", "987654", "424242", "spent_usd", '"used"', '"cap"'):
        assert figure not in wire


def test_limits_on_a_free_plan_with_nothing_used():
    tool, gw = wired(UnifiedLLMTool)
    gw.answer = (
        200,
        {
            "plan": "free",
            "state": "ok",
            "classes": {},
            "actions": [{"kind": "topup", "label": "Add prepaid credit", "url": "https://hanzo.ai/pay"}],
            "upgrade": "dev",
            "credits_after_allowance": False,
        },
    )
    d = run(tool, action="limits")["data"]
    assert (d["plan"], d["state"], d["classes"], d["session"], d["limited"], d["paused"]) == (
        "free",
        "ok",
        {},
        None,
        None,
        None,
    )


def test_a_plan_refusal_is_an_error_named_by_its_code_with_the_ways_on():
    tool, gw = wired(UnifiedLLMTool)
    gw.answer = (402, MODEL_CAP, {"x-hanzo-usage": "limited", "x-hanzo-usage-class": "premium"})
    env = run(tool, prompt="hi", model="anthropic/claude-opus-4.1")
    assert not env["ok"]
    e = env["error"]
    assert (e["code"], e["status"], e["class"], e["model"], e["fallback"], e["resets_at"]) == (
        "model_cap",
        402,
        "premium",
        "anthropic/claude-opus-4.1",
        "enso",
        "2026-10-05T05:00:00Z",
    )
    assert e["message"] == MODEL_CAP["error"]["message"]
    # The upgrade the body named only as upgrade_url leads the actions.
    assert e["actions"] == [
        {"kind": "upgrade", "url": "https://hanzo.ai/pay/cart?plan=max-5x"},
        {"kind": "switch", "label": "Try Enso", "model": "enso"},
        {"kind": "topup", "label": "Add prepaid credit", "url": "https://hanzo.ai/pay"},
    ]
    assert "window" not in e


def test_feedback_posts_the_signal_and_returns_what_was_recorded():
    tool, gw = wired(UnifiedLLMTool)
    env = run(tool, action="feedback", request_id=COMPLETION["id"], signal="rating", rating=3)
    assert (gw.last.method, gw.last.url.path) == ("POST", "/v1/ai/feedback")
    assert body(gw.last) == {"request_id": COMPLETION["id"], "signal": "rating", "rating": 3}
    assert env["data"] == {"request_id": "ae7c311d-5c64-47da-886b-86ceb2fd185f", "reward": 1, "recorded": True}


def test_feedback_refuses_what_the_server_would_and_reads_an_error_envelope():
    tool, gw = wired(UnifiedLLMTool)
    assert (
        "signal must be one of"
        in run(tool, action="feedback", request_id="chatcmpl-1", signal="bogus")["error"]["message"]
    )
    assert (
        "rating must be 1, 2 or 3"
        in run(tool, action="feedback", request_id="chatcmpl-1", signal="rating", rating=4)["error"]["message"]
    )
    assert gw.seen == []
    gw.answer = (200, {"status": "error", "msg": "request not found", "data": None})
    env = run(tool, action="feedback", request_id="chatcmpl-1", signal="down")
    assert not env["ok"] and env["error"]["message"] == "request not found"


def test_kai_decide_posts_the_decision_and_returns_it():
    tool, gw = wired(KaiDecideTool)
    questions = {
        "team": {
            "type": "choice",
            "instructions": "Which team?",
            "criteria": {"account": "logins", "payments": "charges and refunds"},
        }
    }
    env = run(tool, state={"message": "charged twice"}, questions=questions)
    assert env["ok"], env
    assert env["data"] == DECISION
    assert (gw.last.method, gw.last.url.path) == ("POST", "/v1/decisions")
    assert body(gw.last) == {"model": "kai", "state": {"message": "charged twice"}, "questions": questions}


@pytest.mark.parametrize(
    "question,said",
    [
        ({"type": "vote"}, "type must be one of"),
        ({"type": "choice", "criteria": ["a", "a"]}, "at least 2 labels, not 1"),
        ({"type": "score", "criteria": []}, "at least 1 level"),
        ({"type": "score", "criteria": ["a", None]}, "score level 1 is null"),
        ({"type": "noul", "criteria": {"maybe": "x"}}, "not maybe"),
    ],
)
def test_kai_decide_names_each_shape_the_contract_refuses(question, said):
    tool, gw = wired(KaiDecideTool)
    env = run(tool, state="s", questions={"q": question})
    assert not env["ok"] and said in env["error"]["message"]
    assert gw.seen == []


def test_kai_decide_carries_the_plan_cap_refusal():
    tool, gw = wired(KaiDecideTool)
    gw.answer = (429, FREE_PLAN_CAP, {"retry-after": "3032", "x-hanzo-usage": "limited", "x-hanzo-usage-class": "ours"})
    env = run(tool, state="s", questions={"q": {"type": "noul"}}, model="kai")
    assert not env["ok"]
    e = env["error"]
    assert (e["code"], e["status"], e["class"], e["resets_at"]) == (
        "free_plan_cap",
        429,
        "ours",
        "2026-10-05T00:00:00Z",
    )
    assert e["message"].startswith("Free plan: today's Kai requests are used.")
    assert [a["kind"] for a in e["actions"]] == ["upgrade", "topup"]


def test_kai_decide_asks_the_model_named():
    tool, gw = wired(KaiDecideTool)
    run(tool, state="s", questions={"q": {"type": "noul"}}, model="typesafe/jev-1.13")
    assert body(gw.last)["model"] == "typesafe/jev-1.13"
