import asyncio
import inspect
from typing import Any
from collections.abc import Callable

import httpx
import pytest
import hanzo_kai
from wire import KEY, Wire, reply
from hanzo_kai import jev

# The shape /v1/systemone answers in: Jev's fields and nothing of Kai's.
JEV: dict[str, Any] = {
    "model": "kai-a7",
    "answers": {
        "team": {
            "type": "choice",
            "choice": "billing",
            "confidence": 0.9,
            "probabilities": {"billing": 0.95, "tech": 0.05},
        },
        "billing": {"type": "noul", "noul": 0.746},
        "urgency": {
            "type": "score",
            "score": 1.4356,
            "confidence": 0.61,
            "legend": {"0": "can wait", "1": {"when": "this week"}, "2": ["today", "now"]},
            "probabilities": {"0": 0.0304, "1": 0.5037, "2": 0.4659},
        },
    },
    "usage": {"input_tokens": 41, "output_tokens": 0},
}
QUESTIONS = {
    "team": jev.Choice(instructions="Which team?", criteria={"billing": None, "tech": None}),
    "billing": jev.Noul(instructions="Is this about billing?"),
    "urgency": jev.Score(instructions="How urgent?", criteria=["can wait", {"when": "this week"}, ["today", "now"]]),
}
LISTING = {
    "object": "list",
    "data": [{"id": "kai", "object": "model", "outputs": ["decision"], "pricing": {"input": 0.021, "output": 0}}],
    "models": [{"name": "kai", "description": "Kai, Hanzo's decision model", "release_date": "2026-09-28"}],
}


class Compat:
    """A `jev.Client` or a `jev.AsyncClient` over a wire, its calls run to completion either way."""

    def __init__(self, flavour: str, wire: Wire, **options: Any) -> None:
        self.flavour = flavour
        kind = jev.AsyncClient if flavour == "async" else jev.Client
        options.setdefault("api_key", KEY)
        self.client = kind(transport=httpx.MockTransport(wire), **options)

    def system_one(self, *args: Any, **kwargs: Any) -> Any:
        if self.flavour == "async":
            return asyncio.run(self.client.system_one(*args, **kwargs))
        return self.client.system_one(*args, **kwargs)

    def models(self, **kwargs: Any) -> Any:
        if self.flavour == "async":
            return asyncio.run(self.client.models.list(**kwargs))
        return self.client.models.list(**kwargs)


Build = Callable[..., Compat]


@pytest.fixture(params=["sync", "async"])
def compat(request: pytest.FixtureRequest) -> Build:
    def build(wire: Wire, **options: Any) -> Compat:
        return Compat(request.param, wire, **options)

    return build


def test_request(compat: Build) -> None:
    wire = Wire(reply(json_body=JEV))
    compat(wire).system_one({"ticket": "charged twice"}, QUESTIONS, extra_body={"user": "u1"})
    request = wire.requests[0]
    assert request.method == "POST" and str(request.url) == "https://api.hanzo.ai/v1/systemone"
    assert request.headers["authorization"] == f"Bearer {KEY}"
    assert request.headers["user-agent"] == f"hanzo-kai/{hanzo_kai.__version__}"
    assert wire.json() == {
        "model": "kai",
        "state": {"ticket": "charged twice"},
        "questions": {
            "team": {"type": "choice", "instructions": "Which team?", "criteria": {"billing": None, "tech": None}},
            "billing": {"type": "noul", "instructions": "Is this about billing?"},
            "urgency": {
                "type": "score",
                "instructions": "How urgent?",
                "criteria": ["can wait", {"when": "this week"}, ["today", "now"]],
            },
        },
        "user": "u1",
    }


def test_response_in_jevs_shape(compat: Build) -> None:
    response = compat(Wire(reply(json_body=JEV, headers={"x-request-id": "req-j"}))).system_one("x", QUESTIONS)
    assert type(response) is jev.Response and not isinstance(response, hanzo_kai.Decision)
    assert response.model == "kai-a7"
    assert response.usage.input_tokens == 41 and response.usage.output_tokens == 0
    assert response.nouls["billing"].noul == 0.746 and response.nouls["billing"].confidence is None
    team = response.choices["team"]
    assert (team.choice, team.confidence, team.probabilities) == ("billing", 0.9, {"billing": 0.95, "tech": 0.05})
    urgency = response.scores["urgency"]
    assert urgency.legend == {0: "can wait", 1: {"when": "this week"}, 2: ["today", "now"]}
    assert urgency.probabilities == {0: 0.0304, 1: 0.5037, 2: 0.4659}
    assert (urgency.score, urgency.confidence) == (1.4356, 0.61)
    assert response.request_id == "req-j" and response.raw_http_response.json() == JEV


def test_typed_response(compat: Build) -> None:
    class Typed(jev.Response):
        team: jev.ChoiceAnswer
        billing: jev.NoulAnswer
        missing: jev.NoulAnswer | None = None

    response = compat(Wire(reply(json_body=JEV))).system_one("x", QUESTIONS, response_model=Typed)
    assert type(response) is Typed
    assert response.team.choice == "billing" and response.billing.noul == 0.746 and response.missing is None


@pytest.mark.parametrize(
    ("status", "sent", "kind", "message", "code"),
    [
        (400, {"detail": "Unknown model: jev-latest"}, jev.BadRequestError, "Unknown model: jev-latest", None),
        (401, {"detail": "invalid API key"}, jev.AuthenticationError, "invalid API key", None),
        (402, {"detail": "insufficient balance"}, jev.PaymentRequiredError, "insufficient balance", None),
        (
            422,
            {
                "detail": [
                    {"loc": ["body", "questions", "q", "criteria"], "msg": "at most 10 levels", "type": "too_long"}
                ]
            },
            jev.UnprocessableEntityError,
            "questions.q.criteria: at most 10 levels",
            "too_long",
        ),
        (
            422,
            {"detail": [{"loc": ["body", "state"], "msg": "state does not fit", "type": "state_too_long"}]},
            jev.UnprocessableEntityError,
            "state: state does not fit",
            "state_too_long",
        ),
    ],
)
def test_fastapi_errors(
    compat: Build, status: int, sent: dict[str, Any], kind: type[jev.APIError], message: str, code: str | None
) -> None:
    with pytest.raises(kind) as caught:
        compat(
            Wire(reply(status, sent, headers={"x-request-id": "req-e"})), retry=jev.RetryPolicy(max_retries=0)
        ).system_one("x", QUESTIONS, model="jev-latest")
    assert type(caught.value) is kind
    assert (caught.value.status, caught.value.message, caught.value.code) == (status, message, code)
    assert caught.value.request_id == "req-e"
    assert caught.value.endpoint == "POST https://api.hanzo.ai/v1/systemone"


def test_retries_honour_the_headers(compat: Build, slept: list[float]) -> None:
    wire = Wire(
        reply(429, {"detail": "rate limited"}, headers={"Retry-After": "1"}),
        reply(529, {"detail": "overloaded"}, headers={"retry-after-ms": "250"}),
        reply(json_body=JEV),
    )
    assert compat(wire).system_one("x", QUESTIONS).model == "kai-a7"
    assert slept == [1.0, 0.25]
    assert [r.headers.get("x-kai-retry-count") for r in wire.requests] == [None, "1", "2"]


def test_models_reads_the_models_key(compat: Build) -> None:
    wire = Wire(reply(json_body=LISTING, headers={"x-request-id": "req-m"}))
    listing = compat(wire).models()
    assert isinstance(listing, jev.ListModelsResponse)
    assert str(wire.requests[0].url) == "https://api.hanzo.ai/v1/models"
    assert listing.models == (
        jev.ModelMetadata(name="kai", description="Kai, Hanzo's decision model", release_date="2026-09-28"),
    )
    assert listing.request_id == "req-m"
    with pytest.raises(jev.APIResponseValidationError) as caught:
        compat(Wire(reply(json_body={"data": []}))).models()
    assert caught.value.field_path == "models"


def test_one_line_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HANZO_API_KEY", KEY)
    from hanzo_kai.jev import Noul, Score, Choice, Client as TypeSafeClient

    wire = Wire(reply(json_body=JEV))
    with TypeSafeClient(transport=httpx.MockTransport(wire)) as client:
        result = client.system_one(
            state="I was charged twice. Please help.",
            questions={
                "billing": Noul(instructions="Is this about billing?"),
                "team": Choice(instructions="Which team?", criteria={"billing": None, "tech": None}),
                "urgency": Score(instructions="How urgent?", criteria=["can wait", "this week", "today"]),
            },
        )
    assert 0 <= result.nouls["billing"].noul <= 1 and result.choices["team"].choice in {"billing", "tech"}
    assert wire.json()["model"] == "kai"


def parameters(function: Any) -> list[tuple[str, str]]:
    return [(p.name, p.kind.name) for p in inspect.signature(function).parameters.values()]


def test_surface() -> None:
    for name in jev.__all__:
        assert getattr(jev, name) is not None
        assert "TypeSafe" not in name and "SystemOne" not in name and "Jev" not in name
    for name in dir(jev):
        assert "TypeSafe" not in name and "SystemOne" not in name
    assert jev.Choice is hanzo_kai.Choice and jev.BadRequestError is hanzo_kai.BadRequestError
    assert jev.RetryPolicy is hanzo_kai.RetryPolicy
    for kind in (jev.Client, jev.AsyncClient):
        assert parameters(kind.__init__) == parameters(hanzo_kai.Kai.__init__)
        assert parameters(kind.system_one) == [
            ("self", "POSITIONAL_OR_KEYWORD"),
            ("state", "POSITIONAL_OR_KEYWORD"),
            ("questions", "POSITIONAL_OR_KEYWORD"),
            ("model", "KEYWORD_ONLY"),
            ("retry", "KEYWORD_ONLY"),
            ("timeout", "KEYWORD_ONLY"),
            ("extra_headers", "KEYWORD_ONLY"),
            ("extra_body", "KEYWORD_ONLY"),
            ("response_model", "KEYWORD_ONLY"),
        ]
    assert inspect.iscoroutinefunction(jev.AsyncClient.system_one) and inspect.iscoroutinefunction(jev.AsyncModels.list)
