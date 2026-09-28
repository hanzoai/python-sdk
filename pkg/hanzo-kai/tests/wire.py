"""A scripted stand-in for the API, and a client that runs either flavour synchronously."""

import copy
import json
import asyncio
from typing import Any
from collections.abc import Callable

import httpx
from hanzo_kai import Kai, AsyncKai

KEY = "sk-test-4b1d9c0e7f"

# A live answer from POST https://api.hanzo.ai/v1/decisions (Kai a7), copied as it came.
BODY: dict[str, Any] = {
    "id": "dec_0cfe54daad6b708eeebb91df8039aa96",
    "model": "kai",
    "provider": "Hanzo",
    "answers": {
        "team": {
            "type": "choice",
            "choice": "billing",
            "confidence": 1.0,
            "probabilities": {"billing": 1.0, "tech": 0.0},
            "answer_confidence": 1.0,
        },
        "billing": {"type": "noul", "noul": 0.746, "answer_confidence": 0.746},
        "urgency": {
            "type": "score",
            "score": 1.4356,
            "confidence": 0.2556,
            "legend": {"0": "can wait", "1": "this week", "2": "today"},
            "probabilities": {"0": 0.0304, "1": 0.5037, "2": 0.4659},
            "answer_confidence": 0.5037,
        },
    },
    "usage": {"input_tokens": 150, "output_tokens": 0},
    "routing": {
        "backend": "kai",
        "checkpoint": "a7",
        "sha256": "0834a74f2d140642a453373da09e5a128e3d2c8d9e8bb1dcaf86d7210a4ecdfc",
        "calibration": "cal_e23c27a1f768bff7",
        "device": "cpu",
        "reason": "explicit model='kai'",
    },
    "state_hash": "sha256:df57ac6b3f6d3c309e3dd1f9922f95324c3eca0c205d3888f8dd4ad3339ca019",
    "latency_ms": 102.466954,
}

type Reply = Callable[[httpx.Request], httpx.Response]


def body() -> dict[str, Any]:
    """A fresh copy of BODY to change."""
    return copy.deepcopy(BODY)


def reply(
    status: int = 200, json_body: Any = None, *, text: str | None = None, headers: dict[str, str] | None = None
) -> Reply:
    """A reply that builds a new response each time it answers."""

    def answer(request: httpx.Request) -> httpx.Response:
        if text is not None:
            return httpx.Response(status, text=text, headers=headers)
        return httpx.Response(status, json=BODY if json_body is None else json_body, headers=headers)

    return answer


def refuse(kind: type[httpx.RequestError], message: str = "refused") -> Reply:
    """A reply that raises an httpx transport error."""

    def answer(request: httpx.Request) -> httpx.Response:
        raise kind(message, request=request)

    return answer


class Wire:
    """Answers each request with the next reply, repeating the last, and keeps every request."""

    def __init__(self, *replies: Reply) -> None:
        self.replies = list(replies) or [reply()]
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        answer = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return answer(request)

    def json(self, index: int = -1) -> Any:
        return json.loads(self.requests[index].content)


class Client:
    """A `Kai` or an `AsyncKai` over a wire, its calls run to completion either way."""

    def __init__(self, flavour: str, wire: Wire, **options: Any) -> None:
        self.flavour = flavour
        kind = AsyncKai if flavour == "async" else Kai
        options.setdefault("api_key", KEY)
        self.kai = kind(transport=httpx.MockTransport(wire), **options)

    def decide(self, *args: Any, **kwargs: Any) -> Any:
        if self.flavour == "async":
            return asyncio.run(self.kai.decide(*args, **kwargs))
        return self.kai.decide(*args, **kwargs)

    def models(self, **kwargs: Any) -> Any:
        if self.flavour == "async":
            return asyncio.run(self.kai.models.list(**kwargs))
        return self.kai.models.list(**kwargs)
