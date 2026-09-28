"""A service that answers as the frozen contract says, for `httpx.MockTransport`.

It serves `/v1/decisions`, `/v1/systemone` and `GET /v1/models`, refuses what the contract refuses
with each path's error shape, and answers the first requests with scripted faults when told to.
Its probabilities come from a hash of the state and the question, never the question's id.
"""

import re
import json
import math
import uuid
import random
import hashlib
from typing import Any

import httpx

KEY = "sk-test-4b1d9c0e7f"
REACH = 8192
"""Tokens of state and one question the served checkpoint reads."""
VERSION = "kai-a10"
"""The versioned id `kai` resolves to."""
NATIVE = frozenset({"kai", "hanzo/kai", VERSION})
COMPAT = frozenset({"kai", VERSION})
FAULTS = {402: "insufficient balance", 429: "rate limited", 529: "overloaded"}
LISTING = {
    "object": "list",
    "data": [
        {
            "id": "hanzo/kai",
            "object": "model",
            "owned_by": "hanzo",
            "outputs": ["decision"],
            "pricing": {"input": 0.021, "output": 0},
        },
        {
            "id": "kai",
            "object": "model",
            "owned_by": "hanzo",
            "outputs": ["decision"],
            "pricing": {"input": 0.021, "output": 0},
        },
        {
            "id": "zen5",
            "object": "model",
            "owned_by": "hanzo",
            "outputs": ["text"],
            "pricing": {"input": 1, "output": 2},
        },
    ],
    "models": [{"name": "kai", "description": "Kai, Hanzo's decision model", "release_date": "2026-09-28"}],
}


class Refusal(Exception):
    """A request the contract refuses, and how."""

    def __init__(self, status: int, message: str, code: str | None = None, loc: tuple[Any, ...] = ("body",)) -> None:
        super().__init__(message)
        self.status, self.message, self.code, self.loc = status, message, code, loc

    def body(self, compat: bool) -> dict[str, Any]:
        if compat:
            if self.status == 422:
                return {"detail": [{"loc": list(self.loc), "msg": self.message, "type": self.code or "value_error"}]}
            return {"detail": self.message}
        if self.status == 401:
            return {"status": "error", "msg": self.message}
        return {"error": {"code": self.code or self.status, "message": self.message}}


class Service:
    """The handler: `httpx.MockTransport(Service())`."""

    def __init__(self, faults: tuple[tuple[int, dict[str, str]], ...] = ()) -> None:
        self.faults = list(faults)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        compat = path == "/v1/systemone"
        headers = {"x-request-id": uuid.uuid4().hex}
        if request.method == "GET" and path == "/v1/models":
            return httpx.Response(200, json=LISTING, headers=headers)
        if request.method != "POST" or path not in ("/v1/decisions", "/v1/systemone"):
            return httpx.Response(404, text="not found", headers=headers)
        try:
            if request.headers.get("authorization") != f"Bearer {KEY}":
                raise Refusal(401, "API key validation failed")
            if self.faults:
                status, extra = self.faults.pop(0)
                headers.update(extra)
                raise Refusal(status, FAULTS[status])
            try:
                body = json.loads(request.content)
            except ValueError as error:
                raise Refusal(400, f"body is not JSON: {error}") from error
            return httpx.Response(200, json=answer(body, compat), headers=headers)
        except Refusal as refusal:
            return httpx.Response(refusal.status, json=refusal.body(compat), headers=headers)


def answer(body: dict[str, Any], compat: bool) -> dict[str, Any]:
    model = body.get("model")
    if model not in (COMPAT if compat else NATIVE):
        raise Refusal(400, f"Unknown model: {model}" if compat else f"unknown model {model!r}")
    state = body.get("state")
    if not isinstance(state, str | dict | list):
        raise Refusal(422, "state must be a string, an object or an array", loc=("body", "state"))
    questions = body.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= 100:
        raise Refusal(422, "questions holds 1 to 100 questions", loc=("body", "questions"))
    asked = {name: question(name, q, compat) for name, q in questions.items()}
    need = tokens(state) + max(cost(q) for q in asked.values())
    if need > REACH:
        raise Refusal(
            422, f"state and question need {need} tokens; Kai reads {REACH}", "state_too_long", ("body", "state")
        )
    answers = {name: decide(state, q, compat) for name, q in asked.items()}
    usage = {"input_tokens": tokens(state) + sum(cost(q) for q in asked.values()), "output_tokens": 0}
    if compat:
        return {"model": VERSION, "answers": answers, "usage": usage}
    digest = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    return {
        "id": "dec_" + uuid.uuid4().hex,
        "model": model,
        "provider": "Hanzo",
        "answers": answers,
        "usage": usage,
        "routing": {"backend": "kai", "checkpoint": "fake"},
        "state_hash": f"sha256:{digest}",
        "latency_ms": 1.0,
    }


def question(name: str, q: Any, compat: bool) -> dict[str, Any]:
    """The question as the service reads it: its type, instructions and options, its id dropped."""
    loc = ("body", "questions", name)
    if not isinstance(q, dict) or q.get("type") not in ("noul", "choice", "score"):
        raise Refusal(422, "a question's type is noul, choice or score", loc=(*loc, "type"))
    kind, criteria = q["type"], q.get("criteria")
    if kind == "noul":
        sides = criteria or {}
        if not isinstance(sides, dict) or set(sides) - {"true", "false"}:
            raise Refusal(422, "a noul's criteria describes 'true' and 'false'", loc=(*loc, "criteria"))
        labels = q.get("labels")
        if labels is not None and (compat or not isinstance(labels, dict) or set(labels) != {"true", "false"}):
            raise Refusal(422, "labels names 'true' and 'false'", loc=(*loc, "labels"))
        options = [("false", sides.get("false")), ("true", sides.get("true"))]
    elif kind == "choice":
        if isinstance(criteria, list) and not compat:
            criteria = dict.fromkeys(criteria)
        if not isinstance(criteria, dict) or len(criteria) < 2:
            raise Refusal(422, "a choice needs at least 2 labels", loc=(*loc, "criteria"))
        if compat and len(criteria) > 255:
            raise Refusal(422, "a choice takes at most 255 labels", "too_long", (*loc, "criteria"))
        options = list(criteria.items())
    else:
        if not isinstance(criteria, list) or not criteria:
            raise Refusal(422, "a score needs at least 1 level", loc=(*loc, "criteria"))
        if compat and len(criteria) > 10:
            raise Refusal(422, "a score takes at most 10 levels", "too_long", (*loc, "criteria"))
        if any(level is None for level in criteria):
            raise Refusal(422, "a score level is null", loc=(*loc, "criteria"))
        options = [(str(level), text) for level, text in enumerate(criteria)]
    return {"type": kind, "instructions": q.get("instructions"), "options": options, "labels": q.get("labels")}


def decide(state: Any, q: dict[str, Any], compat: bool) -> dict[str, Any]:
    p = distribution(state, q)
    top = max(p)
    n = len(p)
    if q["type"] == "noul":
        yes = p[1]
        if compat:
            return {"type": "noul", "noul": yes}
        return {"type": "noul", "noul": yes, "confidence": abs(2 * yes - 1), "answer_confidence": max(yes, 1 - yes)}
    keys = [key for key, _ in q["options"]]
    probabilities = dict(zip(keys, p, strict=True))
    confidence = (n * top - 1) / (n - 1) if n > 1 else 1.0
    if q["type"] == "choice":
        chosen = {
            "type": "choice",
            "choice": keys[p.index(top)],
            "confidence": confidence,
            "probabilities": probabilities,
        }
        return chosen if compat else {**chosen, "answer_confidence": top}
    legend = {key: text for key, text in q["options"]}
    expected = math.fsum(level * weight for level, weight in enumerate(p))
    if compat:
        mode = p.index(top)
        spread = sum(abs(level - (n - 1) / 2) for level in range(n)) / n
        off = math.fsum(weight * abs(level - mode) for level, weight in enumerate(p))
        jev = max(0.0, 1 - off / spread) if spread else 1.0
        return {"type": "score", "score": expected, "confidence": jev, "legend": legend, "probabilities": probabilities}
    return {
        "type": "score",
        "score": expected,
        "confidence": confidence,
        "answer_confidence": top,
        "legend": legend,
        "probabilities": probabilities,
    }


def distribution(state: Any, q: dict[str, Any]) -> list[float]:
    """A softmax over the options, seeded by the state and the question, normalized in f64."""
    seed = hashlib.sha256(json.dumps([state, q], sort_keys=True, default=str).encode()).digest()
    draw = random.Random(seed)
    logits = [draw.gauss(0, 1.5) for _ in q["options"]]
    top = max(logits)
    weights = [math.exp(logit - top) for logit in logits]
    total = math.fsum(weights)
    return [weight / total for weight in weights]


def tokens(value: Any) -> int:
    """Words and punctuation marks, a stand-in for Kai's tokenizer."""
    if value is None:
        return 0
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False)
    return len(re.findall(r"\w+|[^\w\s]", text))


def cost(q: dict[str, Any]) -> int:
    """A question's billed text: its instructions and its options, once."""
    return tokens(q["instructions"]) + sum(tokens(key) + tokens(text) for key, text in q["options"])
