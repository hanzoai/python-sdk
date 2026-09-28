import json
import math
import logging
from types import MappingProxyType
from collections.abc import Callable

import httpx
import pytest
from wire import KEY, BODY, Wire, Client, body, reply
from pydantic import BaseModel, ValidationError
from hanzo_kai import (
    Noul,
    Score,
    Choice,
    Decision,
    KaiError,
    NoulAnswer,
    ScoreAnswer,
    ChoiceAnswer,
    BadRequestError,
    APIResponseValidationError,
    __version__,
)

Build = Callable[..., Client]

STATE = {"ticket": "I was charged twice for my March invoice. Please refund the duplicate."}
QUESTIONS = {
    "team": Choice(instructions="Which team should handle this?", criteria={"billing": "charges", "tech": None}),
    "billing": Noul(instructions="Is this about billing?"),
    "urgency": Score(instructions="How urgent is this?", criteria=["can wait", "this week", "today"]),
}


def test_request_is_the_wire_shape(client: Build) -> None:
    wire = Wire()
    client(wire).decide(
        STATE,
        {
            **QUESTIONS,
            "kind": Choice(instructions={"task": "Pick one"}, criteria=["refund", "question"]),
            "sure": Noul(instructions="Is it sure?", criteria={"true": "certain", "false": None}),
            "raw": {"type": "noul", "instructions": "Raw?", "criteria": {"true": "yes"}},
        },
    )
    request = wire.requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.hanzo.ai/v1/decisions"
    sent = wire.json()
    assert list(sent) == ["model", "state", "questions"]
    assert sent == {
        "model": "kai",
        "state": STATE,
        "questions": {
            "team": {
                "type": "choice",
                "instructions": "Which team should handle this?",
                "criteria": {"billing": "charges", "tech": None},
            },
            "billing": {"type": "noul", "instructions": "Is this about billing?"},
            "urgency": {
                "type": "score",
                "instructions": "How urgent is this?",
                "criteria": ["can wait", "this week", "today"],
            },
            "kind": {"type": "choice", "instructions": {"task": "Pick one"}, "criteria": ["refund", "question"]},
            "sure": {"type": "noul", "instructions": "Is it sure?", "criteria": {"true": "certain", "false": None}},
            "raw": {"type": "noul", "instructions": "Raw?", "criteria": {"true": "yes"}},
        },
    }


def test_headers(client: Build) -> None:
    wire = Wire()
    kai = client(wire, headers={"X-Team": "ops", "X-Trace": "client"})
    kai.decide(
        STATE,
        QUESTIONS,
        extra_headers={
            "X-Trace": "call",
            "Authorization": "Bearer stolen",
            "User-Agent": "other",
            "X-Kai-Runtime": "other",
            "Accept": "text/html",
            "X-Kai-Retry-Count": "7",
        },
    )
    headers = wire.requests[0].headers
    assert headers["authorization"] == f"Bearer {KEY}"
    assert headers["accept"] == "application/json"
    assert headers["content-type"] == "application/json"
    assert headers["user-agent"] == f"hanzo-kai/{__version__}"
    assert headers["x-kai-runtime"].startswith("cpython/") and " httpx/" in headers["x-kai-runtime"]
    assert headers["x-team"] == "ops"
    assert headers["x-trace"] == "call"
    assert "x-kai-retry-count" not in headers


def test_every_answer_type(client: Build) -> None:
    d = client(Wire(reply(headers={"x-request-id": "req-1"}))).decide(STATE, QUESTIONS)
    assert isinstance(d, Decision)
    assert (d.id, d.model, d.provider) == ("dec_0cfe54daad6b708eeebb91df8039aa96", "kai", "Hanzo")
    assert d.usage.input_tokens == 150 and d.usage.output_tokens == 0
    assert d.routing is not None and d.routing["checkpoint"] == "a7"
    assert d.state_hash == BODY["state_hash"]
    assert d.latency_ms == 102.466954
    assert list(d.answers) == ["team", "billing", "urgency"]

    team = d.choices["team"]
    assert isinstance(team, ChoiceAnswer)
    assert (team.type, team.choice, team.confidence, team.answer_confidence) == ("choice", "billing", 1.0, 1.0)
    assert team.probabilities == {"billing": 1.0, "tech": 0.0}

    billing = d.nouls["billing"]
    assert isinstance(billing, NoulAnswer)
    assert (billing.type, billing.noul, billing.answer_confidence) == ("noul", 0.746, 0.746)

    urgency = d.scores["urgency"]
    assert isinstance(urgency, ScoreAnswer)
    assert (urgency.score, urgency.confidence, urgency.answer_confidence) == (1.4356, 0.2556, 0.5037)
    assert urgency.legend == {0: "can wait", 1: "this week", 2: "today"}
    assert urgency.probabilities == {0: 0.0304, 1: 0.5037, 2: 0.4659}

    assert set(d.choices) == {"team"} and set(d.nouls) == {"billing"} and set(d.scores) == {"urgency"}
    assert isinstance(d.raw_http_response, httpx.Response)
    assert d.raw_http_response.json() == BODY
    assert d.request_id == "req-1"


def test_unknown_answer_type_is_skipped(client: Build, caplog: pytest.LogCaptureFixture) -> None:
    sent = body()
    sent["answers"]["rank"] = {"type": "rank", "order": ["a", "b"]}
    with caplog.at_level(logging.WARNING, logger="hanzo_kai"):
        d = client(Wire(reply(json_body=sent))).decide(STATE, QUESTIONS)
    assert list(d.answers) == ["team", "billing", "urgency"]
    assert "rank" in caplog.text and "skipping answer" in caplog.text
    assert d.raw_http_response.json()["answers"]["rank"]["type"] == "rank"


def test_extra_fields_are_kept(client: Build) -> None:
    sent = body()
    sent["answers"]["billing"]["action"] = "route"
    sent["usage"]["cost"] = 0.0000031
    sent["warnings"] = ["calibration is stale"]
    d = client(Wire(reply(json_body=sent))).decide(STATE, QUESTIONS)
    assert d.nouls["billing"].model_extra == {"action": "route"}
    assert d.usage.model_extra == {"cost": 0.0000031}
    assert d.model_extra == {"warnings": ["calibration is stale"]}


def test_sorted_keys_parse_by_name(client: Build) -> None:
    levels = [f"level {n}" for n in range(11)]
    sent = body()
    sent["model"] = "hanzo/kai"
    sent["answers"]["depth"] = {
        "type": "score",
        "score": 9.2,
        "confidence": 0.8,
        "legend": {str(n): text for n, text in enumerate(levels)},
        "probabilities": {str(n): (0.9 if n == 10 else 0.01) for n in range(11)},
        "answer_confidence": 0.9,
    }
    wire = Wire(reply(text=json.dumps(sent, sort_keys=True), headers={"content-type": "application/json"}))
    d = client(wire).decide(
        STATE, {**QUESTIONS, "depth": Score(instructions="How deep?", criteria=levels)}, model="hanzo/kai"
    )
    assert wire.json()["model"] == "hanzo/kai"
    assert d.model == "hanzo/kai"
    assert list(d.answers) == ["billing", "depth", "team", "urgency"]
    assert d.choices["team"].choice == "billing"
    assert list(d.scores["depth"].legend) == list(range(11))
    assert list(d.scores["depth"].probabilities) == list(range(11))
    assert d.scores["depth"].legend[10] == "level 10"


def test_model_and_extra_body(client: Build) -> None:
    wire = Wire()
    kai = client(wire, model="hanzo/kai")
    kai.decide(STATE, QUESTIONS)
    assert wire.json()["model"] == "hanzo/kai"
    kai.decide(STATE, QUESTIONS, model="kai", extra_body={"session_id": "s1", "user": "u1", "trace": True})
    sent = wire.json()
    assert sent["model"] == "kai"
    assert (sent["session_id"], sent["user"], sent["trace"]) == ("s1", "u1", True)
    kai.decide(STATE, QUESTIONS, extra_body={"model": "override"})
    assert wire.json()["model"] == "override"


@pytest.mark.parametrize(
    "questions",
    [
        {},
        [("q", Noul(instructions="x"))],
        {"q": {"type": "score", "instructions": "x", "criteria": "low, high"}},
        {"q": {"type": "score", "instructions": "x"}},
        {"q": {"type": "choice", "instructions": "x", "criteria": "a or b"}},
        {"q": {"type": "choice", "instructions": "x"}},
        {"q": "Is this billing?"},
    ],
)
def test_client_checks(client: Build, questions: object) -> None:
    wire = Wire()
    with pytest.raises(KaiError):
        client(wire).decide(STATE, questions)
    assert wire.requests == []


def test_other_rules_are_the_servers(client: Build) -> None:
    message = "question 'q': no 'instructions'; add the text the model should answer"
    wire = Wire(reply(400, {"error": {"code": 400, "message": message}}))
    kai = client(wire)
    with pytest.raises(BadRequestError) as caught:
        kai.decide("x", {"q": Noul(), "s": Score(criteria=[]), "r": {"type": "rank", "criteria": ["a"]}})
    assert caught.value.message == message
    assert wire.json()["questions"] == {
        "q": {"type": "noul"},
        "s": {"type": "score", "criteria": []},
        "r": {"type": "rank", "criteria": ["a"]},
    }


def test_question_models_validate() -> None:
    with pytest.raises(ValidationError):
        Score(instructions="x", criteria="low, high")
    with pytest.raises(ValidationError):
        Choice(instructions="x", criteria="a or b")
    with pytest.raises(ValidationError):
        Noul(instructions="x", criteria={"yes": "y"})
    with pytest.raises(ValidationError):
        Noul(instruction="typo")
    with pytest.raises(ValidationError):
        Score(instructions="x", criteria=["low", None])
    question = Choice(instructions="x", criteria=["a", "b"])
    with pytest.raises(ValidationError):
        question.instructions = "y"


def test_state_forms(client: Build) -> None:
    class Form(BaseModel):
        subject: str
        lines: tuple[str, ...]

    wire = Wire()
    kai = client(wire)
    for state in ("plain text", ["a", {"b": None}], MappingProxyType({"k": (1, 2)}), Form(subject="s", lines=("x",))):
        kai.decide(state, QUESTIONS)
    assert [json.loads(r.content)["state"] for r in wire.requests] == [
        "plain text",
        ["a", {"b": None}],
        {"k": [1, 2]},
        {"subject": "s", "lines": ["x"]},
    ]
    for bad in ({"x": {1, 2}}, {"x": math.nan}, {"x": b"bytes"}):
        with pytest.raises(KaiError, match="not JSON"):
            kai.decide(bad, QUESTIONS)
    assert len(wire.requests) == 4


class Ticket(Decision):
    team: ChoiceAnswer
    billing: NoulAnswer
    missing: NoulAnswer | None = None


def test_response_model_decision(client: Build) -> None:
    d = client(Wire(reply(headers={"x-request-id": "req-2"}))).decide(STATE, QUESTIONS, response_model=Ticket)
    assert type(d) is Ticket
    assert d.team.choice == "billing" and d.billing.noul == 0.746 and d.missing is None
    assert d.scores["urgency"].score == 1.4356
    assert d.request_id == "req-2"
    assert "_response" not in d.model_dump()


def test_response_model_plain(client: Build) -> None:
    class Spam(BaseModel):
        noul: float

    class Answers(BaseModel):
        billing: Spam

    class Plain(BaseModel):
        model: str
        answers: Answers

    d = client(Wire()).decide(STATE, QUESTIONS, response_model=Plain)
    assert type(d) is Plain
    assert d.answers.billing.noul == 0.746


@pytest.mark.parametrize(
    ("change", "path"),
    [
        (lambda b: b["answers"]["team"].pop("choice"), "answers.team.choice"),
        (lambda b: b["answers"]["urgency"].update(probabilities={"high": 0.5}), "answers.urgency.probabilities.high"),
        (lambda b: b["answers"].update(bad={"noul": 0.5}), "answers.bad.type"),
        (lambda b: b.pop("id"), "id"),
    ],
)
def test_response_that_does_not_fit(client: Build, change: Callable[[dict[str, object]], object], path: str) -> None:
    sent = body()
    change(sent)
    with pytest.raises(APIResponseValidationError) as caught:
        client(Wire(reply(json_body=sent, headers={"x-request-id": "req-3"}))).decide(STATE, QUESTIONS)
    assert caught.value.field_path == path
    assert caught.value.status == 200
    assert caught.value.body == sent
    assert caught.value.request_id == "req-3"


def test_response_that_is_not_json(client: Build) -> None:
    with pytest.raises(APIResponseValidationError) as caught:
        client(Wire(reply(text="<html>gateway</html>"))).decide(STATE, QUESTIONS)
    assert caught.value.field_path == ""
    assert caught.value.body == "<html>gateway</html>"


def test_response_model_that_does_not_fit(client: Build) -> None:
    class Strict(BaseModel):
        missing: str

    with pytest.raises(APIResponseValidationError) as caught:
        client(Wire()).decide(STATE, QUESTIONS, response_model=Strict)
    assert caught.value.field_path == "missing"


def test_decision_built_by_hand() -> None:
    d = Decision(id="dec_1", model="kai")
    assert d.answers == {} and d.usage.input_tokens is None and d.request_id is None
    with pytest.raises(KaiError):
        _ = d.raw_http_response


def test_noul_labels_reach_the_wire(client: Build) -> None:
    wire = Wire()
    labelled = Noul(instructions="Refund?", labels={"true": "refund", "false": "no refund"})
    client(wire).decide(STATE, {"refund": labelled})
    assert wire.json()["questions"]["refund"] == {
        "type": "noul",
        "instructions": "Refund?",
        "labels": {"true": "refund", "false": "no refund"},
    }
    with pytest.raises(ValidationError):
        Noul(labels={"yes": "refund", "no": "no refund"})
    with pytest.raises(ValidationError):
        Noul(labels={"true": "refund"})


def test_contract_answers(client: Build) -> None:
    sent = body()
    sent["answers"]["billing"] = {"type": "noul", "noul": 0.7461, "confidence": 0.4922, "answer_confidence": 0.7461}
    sent["answers"]["team"]["probabilities"] = {"billing": 0.30000000000000004, "tech": 0.7}
    d = client(Wire(reply(json_body=sent))).decide(STATE, QUESTIONS)
    assert d.nouls["billing"].confidence == 0.4922
    assert d.choices["team"].probabilities["billing"] == 0.30000000000000004
    assert client(Wire()).decide(STATE, QUESTIONS).nouls["billing"].confidence is None
