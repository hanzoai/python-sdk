"""Tests for hanzo-tools-llm: llm (Enso, the catalog, feedback) and kai_decide.

The tools run against a real HanzoCloud whose httpx transport is a recorder
answering as api.hanzo.ai does, so each test reads the exact request that went
out (method, path, bearer, Enso's headers, body) and what the tool made of the
answer. No socket is opened.
"""

import asyncio
import json

import httpx
import pytest

from hanzo_tools.core import HanzoCloud
from hanzo_tools.llm import TOOLS, KaiDecideTool, UnifiedLLMTool

COMPLETION = {
    "id": "chatcmpl-ae7c311d-5c64-47da-886b-86ceb2fd185f",
    "object": "chat.completion",
    "model": "enso-free",
    "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "Hi there, friend."}}],
    "usage": {"prompt_tokens": 110, "completion_tokens": 6, "total_tokens": 116},
}
CATALOG = {
    "object": "list",
    "data": [
        {"id": "kai", "family": "kai", "class": "ours", "outputs": ["decision"], "pricing": {"input_per_million": 0.021, "output_per_million": 0}},
        {"id": "enso-auto", "family": "enso", "class": "free", "outputs": ["text"], "context_window": 1000000, "pricing": {"input_per_million": 0, "output_per_million": 0}},
        {"id": "zen5", "family": "zen", "class": "ours", "pricing": {"input_per_million": 0.3, "output_per_million": 1.2}},
    ],
}
DECISION = {
    "id": "dec_ff9388f6b8b85328960ba301635ac108",
    "model": "kai",
    "provider": "Hanzo",
    "answers": {"team": {"type": "choice", "choice": "payments", "confidence": 0.9983, "probabilities": {"account": 0.0006, "payments": 0.9989}, "answer_confidence": 0.9989}},
    "usage": {"input_tokens": 30, "output_tokens": 0},
}


class Gateway:
    """Records each request and answers it the way api.hanzo.ai does."""

    def __init__(self):
        self.seen: list[httpx.Request] = []
        self.answer = None  # (status, body) to force one reply

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        if self.answer:
            status, body = self.answer
            return httpx.Response(status, json=body)
        path = request.url.path
        if path == "/v1/models":
            return httpx.Response(200, json=CATALOG)
        if path == "/v1/decisions":
            return httpx.Response(200, json=DECISION)
        if path == "/v1/ai/feedback":
            sent = json.loads(request.content)
            return httpx.Response(200, json={"status": "ok", "msg": "", "data": {"request_id": sent["request_id"].removeprefix("chatcmpl-"), "reward": 1, "recorded": True}})
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
    env = run(tool, action="query", model="auto", system="Be brief.", prompt="Say hi.", max_tokens=20, max_cost=0.01, max_latency_ms=800.4)
    assert gw.last.headers["x-max-cost"] == "0.01"
    assert gw.last.headers["x-max-latency-ms"] == "800"
    assert body(gw.last) == {
        "model": "auto",
        "messages": [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Say hi."}],
        "max_tokens": 20,
    }
    assert env["data"] == {"id": COMPLETION["id"], "model": "enso-free", "content": "Hi there, friend.", "finish_reason": "stop", "usage": COMPLETION["usage"]}


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
    assert env["data"] == {"count": 1, "models": [{"id": "kai", "family": "kai", "class": "ours", "outputs": ["decision"], "context_window": None, "input_per_million": 0.021, "output_per_million": 0}]}
    assert run(tool, action="models")["data"]["count"] == 3


def test_feedback_posts_the_signal_and_returns_what_was_recorded():
    tool, gw = wired(UnifiedLLMTool)
    env = run(tool, action="feedback", request_id=COMPLETION["id"], signal="rating", rating=3)
    assert (gw.last.method, gw.last.url.path) == ("POST", "/v1/ai/feedback")
    assert body(gw.last) == {"request_id": COMPLETION["id"], "signal": "rating", "rating": 3}
    assert env["data"] == {"request_id": "ae7c311d-5c64-47da-886b-86ceb2fd185f", "reward": 1, "recorded": True}


def test_feedback_refuses_what_the_server_would_and_reads_an_error_envelope():
    tool, gw = wired(UnifiedLLMTool)
    assert "signal must be one of" in run(tool, action="feedback", request_id="chatcmpl-1", signal="bogus")["error"]["message"]
    assert "rating must be 1, 2 or 3" in run(tool, action="feedback", request_id="chatcmpl-1", signal="rating", rating=4)["error"]["message"]
    assert gw.seen == []
    gw.answer = (200, {"status": "error", "msg": "request not found", "data": None})
    env = run(tool, action="feedback", request_id="chatcmpl-1", signal="down")
    assert not env["ok"] and env["error"]["message"] == "request not found"


def test_kai_decide_posts_the_decision_and_returns_it():
    tool, gw = wired(KaiDecideTool)
    questions = {"team": {"type": "choice", "instructions": "Which team?", "criteria": {"account": "logins", "payments": "charges and refunds"}}}
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
    gw.answer = (429, {"error": {"message": "Free plan: today's Kai requests are used.", "code": "free_plan_cap"}})
    env = run(tool, state="s", questions={"q": {"type": "noul"}})
    assert not env["ok"] and "429" in env["error"]["message"] and "free_plan_cap" in env["error"]["message"]
