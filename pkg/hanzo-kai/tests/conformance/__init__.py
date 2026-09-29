"""Contract conformance: one fixture per rule, sent through the SDK on both paths and checked.

Each `*.json` beside this file holds a `rule` and its `cases`. A case names its `path` (`native` is
`POST /v1/decisions` through `hanzo_kai.Kai`, `compat` is `POST /v1/systemone` through
`hanzo_kai.jev.Client`; a list runs it on each), what it `send`s, and what it must `expect`:
`status`, the `error` class, its `code` and `message`, the number of HTTP `attempts`, and named
`checks`. `"live": false` marks a case that needs a fault only the fake can script; `"key":
"invalid"` sends a key no account holds. The suite runs every case against `fake.Service`;
`live_conformance.py` runs them against the API.

Generators keep large requests short: `{"$questions": [n, question or [questions]]}`,
`{"$labels": n}`, `{"$levels": n}`, `{"$words": n}` and `{"$bytes": n}`. A `model` of `"$version"`
is the served checkpoint's versioned id, which the runner resolves.
"""

import re
import json
import math
from typing import Any
from pathlib import Path
from dataclasses import dataclass
from collections.abc import Callable

import httpx
from hanzo_kai import Kai, Model, APIError, KaiError, RetryPolicy
from hanzo_kai.jev import Client, Response, ListModelsResponse

HERE = Path(__file__).parent
INVALID = "sk-conformance-no-such-key"
WORDS = (
    "the invoice for march shows two charges of the same amount on one card and the customer "
    "asks support to refund the duplicate before the next billing cycle closes while the account "
    "stays open and every order ships on time"
).split()
JEV = {
    "noul": {"type", "noul"},
    "choice": {"type", "choice", "confidence", "probabilities"},
    "score": {"type", "score", "confidence", "legend", "probabilities"},
}

type Outcome = Any
type Check = Callable[["Case", list[Outcome]], list[str]]


@dataclass(frozen=True)
class Case:
    rule: str
    name: str
    path: str
    send: tuple[dict[str, Any], ...]
    expect: dict[str, Any]
    live: bool = True
    key: str | None = None
    fault: tuple[tuple[int, dict[str, str]], ...] = ()


def load() -> list[Case]:
    """Every case of every fixture, one per path."""
    cases = []
    for file in sorted(HERE.glob("*.json")):
        fixture = json.loads(file.read_text())
        for case in fixture["cases"]:
            paths = case["path"] if isinstance(case["path"], list) else [case["path"]]
            for path in paths:
                name = "/".join([file.stem, path, *([case["name"]] if "name" in case else [])])
                cases.append(
                    Case(
                        rule=fixture["rule"],
                        name=name,
                        path=path,
                        send=tuple(expand(body) for body in case["send"]),
                        expect=case["expect"],
                        live=case.get("live", True),
                        key=case.get("key"),
                        fault=tuple((status, headers) for status, headers in case.get("fault", [])),
                    )
                )
    return cases


def expand(value: Any) -> Any:
    """The fixture value with its generators written out."""
    if isinstance(value, list):
        return [expand(item) for item in value]
    if not isinstance(value, dict):
        return value
    if len(value) == 1:
        [(key, arg)] = value.items()
        if key == "$questions":
            count, shapes = arg
            shapes = shapes if isinstance(shapes, list) else [shapes]
            return {f"q{index + 1}": expand(shapes[index % len(shapes)]) for index in range(count)}
        if key == "$labels":
            return {f"option {index + 1}": None for index in range(arg)}
        if key == "$levels":
            return [f"level {index}" for index in range(arg)]
        if key == "$words":
            return " ".join(WORDS[index % len(WORDS)] for index in range(arg))
        if key == "$bytes":
            line = " ".join(WORDS) + " "
            return (line * (arg // len(line) + 1))[:arg]
    return {key: expand(item) for key, item in value.items()}


def client(
    case: Case,
    *,
    key: str | None = None,
    base_url: str | None = None,
    transport: httpx.BaseTransport | None = None,
    retry: RetryPolicy | None = None,
) -> tuple[Kai | Client, Callable[[], int]]:
    """The SDK client a case runs through, and a count of the HTTP attempts it has made."""
    sent: list[httpx.Request] = []
    http = httpx.Client(transport=transport, timeout=120.0, event_hooks={"request": [sent.append]})
    kind = Kai if case.path == "native" else Client
    sdk = kind(INVALID if case.key == "invalid" else key, base_url=base_url, retry=retry, http_client=http)
    return sdk, lambda: len(sent)


def run(case: Case, sdk: Kai | Client, attempts: Callable[[], int], version: Callable[[], str]) -> list[str]:
    """What did not hold when the case went through `sdk`; empty when it passed.

    `version` gives the served checkpoint's versioned id, for a case that sends `"$version"`.
    """
    outcomes = [
        call(case, sdk, {**body, "model": version()} if body.get("model") == "$version" else body) for body in case.send
    ]
    expect = case.expect
    failures = [problem for outcome in outcomes for problem in verdict(expect, outcome)]
    if failures:
        return failures
    for name in expect.get("checks", []):
        failures += CHECKS[name](case, outcomes)
    if "attempts" in expect and attempts() != expect["attempts"]:
        failures.append(f"expected {expect['attempts']} attempts, made {attempts()}")
    return failures


def call(case: Case, sdk: Any, body: dict[str, Any]) -> Outcome:
    try:
        if body.get("call") == "models":
            return sdk.models.list()
        ask = sdk.decide if case.path == "native" else sdk.system_one
        return ask(body["state"], body["questions"], model=body.get("model", "kai"))
    except KaiError as error:
        return error


def status(outcome: Outcome) -> int | None:
    if isinstance(outcome, APIError):
        return outcome.status
    if isinstance(outcome, KaiError):
        return None
    return outcome.raw_http_response.status_code if hasattr(outcome, "raw_http_response") else 200


def said(outcome: Outcome) -> str:
    if isinstance(outcome, KaiError):
        text = f"{type(outcome).__name__}: {outcome}"
        return text if len(text) <= 240 else text[:240] + "…"
    return type(outcome).__name__


def verdict(expect: dict[str, Any], outcome: Outcome) -> list[str]:
    """Whether an outcome has the status, error class, code and message the case expects."""
    want = expect.get("status", 200)
    got = status(outcome)
    if got != want:
        return [f"expected {want}, got {got} ({said(outcome)})"]
    problems = []
    if "error" in expect and type(outcome).__name__ != expect["error"]:
        problems.append(f"expected {expect['error']}, got {said(outcome)}")
    if "code" in expect and getattr(outcome, "code", None) != expect["code"]:
        problems.append(f"expected code {expect['code']!r}, got {getattr(outcome, 'code', None)!r} ({said(outcome)})")
    if "message" in expect and getattr(outcome, "message", None) != expect["message"]:
        problems.append(f"expected message {expect['message']!r}, got {getattr(outcome, 'message', None)!r}")
    return problems


def responses(outcomes: list[Outcome]) -> list[Response]:
    return [outcome for outcome in outcomes if isinstance(outcome, Response)]


def distributions(outcomes: list[Outcome]) -> list[tuple[str, dict[Any, float]]]:
    return [
        (name, answer.probabilities)
        for response in responses(outcomes)
        for name, answer in response.answers.items()
        if answer.type != "noul"
    ]


def sums(case: Case, outcomes: list[Outcome]) -> list[str]:
    """Every distribution sums to 1 within 1e-6, and every noul lies in [0, 1]."""
    problems = [
        f"{name}: probabilities sum to {math.fsum(p.values())!r}"
        for name, p in distributions(outcomes)
        if abs(math.fsum(p.values()) - 1) > 1e-6
    ]
    for response in responses(outcomes):
        problems += [f"{name}: noul {a.noul!r}" for name, a in response.nouls.items() if not 0 <= a.noul <= 1]
    return problems


def argmax(case: Case, outcomes: list[Outcome]) -> list[str]:
    """`choice` is the most probable label and `score` is Σ i·p_i."""
    problems = []
    for response in responses(outcomes):
        for name, a in response.choices.items():
            if a.probabilities[a.choice] < max(a.probabilities.values()):
                problems.append(f"{name}: chose {a.choice!r} at {a.probabilities[a.choice]!r} under the top")
        for name, s in response.scores.items():
            expected = math.fsum(level * p for level, p in s.probabilities.items())
            if abs(s.score - expected) > 1e-9:
                problems.append(f"{name}: score {s.score!r}, Σ i·p_i {expected!r}")
    return problems


def usage_once(case: Case, outcomes: list[Outcome]) -> list[str]:
    """Five equal questions cost four questions more than one, the state billed once."""
    one, five = (response.usage for response in responses(outcomes))
    if one.input_tokens is None or five.input_tokens is None:
        return [f"input_tokens missing: {one.input_tokens!r}, {five.input_tokens!r}"]
    extra = five.input_tokens - one.input_tokens
    question = extra // 4
    state = one.input_tokens - question
    if extra <= 0 or extra % 4 or question >= state:
        return [
            f"1 question billed {one.input_tokens}, 5 billed {five.input_tokens}: {extra} more, "
            f"so each question costs {extra / 4:g} beside a state of {one.input_tokens - extra / 4:g}"
        ]
    if one.output_tokens != 0 or five.output_tokens != 0:
        return [f"output_tokens {one.output_tokens!r}, {five.output_tokens!r}, not 0"]
    return []


def noul_confidence(case: Case, outcomes: list[Outcome]) -> list[str]:
    """A native noul's `confidence` is |2p - 1|."""
    problems = []
    for response in responses(outcomes):
        for name, a in response.nouls.items():
            if a.confidence is None or abs(a.confidence - abs(2 * a.noul - 1)) > 1e-12:
                problems.append(f"{name}: noul {a.noul!r}, confidence {a.confidence!r}")
    return problems


def confidences(case: Case, outcomes: list[Outcome]) -> list[str]:
    """A native choice's or score's `confidence` is (n·p_max - 1)/(n - 1) and `answer_confidence` is p_max."""
    problems = []
    for response in responses(outcomes):
        for name, a in [*response.choices.items(), *response.scores.items()]:
            n, top = len(a.probabilities), max(a.probabilities.values())
            if abs(a.confidence - (n * top - 1) / (n - 1)) > 1e-9 or a.answer_confidence != top:
                problems.append(
                    f"{name}: p_max {top!r} over {n}, confidence {a.confidence!r}, answer_confidence {a.answer_confidence!r}"
                )
    return problems


def legend_verbatim(case: Case, outcomes: list[Outcome]) -> list[str]:
    """A score's `legend` echoes its levels verbatim, keyed "0", "1", …"""
    problems = []
    for body, response in zip(case.send, responses(outcomes), strict=True):
        answers = response.raw_http_response.json()["answers"]
        for name, q in body["questions"].items():
            if q["type"] == "score":
                want = {str(level): text for level, text in enumerate(q["criteria"])}
                if answers[name].get("legend") != want:
                    problems.append(f"{name}: legend {answers[name].get('legend')!r}, levels {want!r}")
    return problems


def jev_shape(case: Case, outcomes: list[Outcome]) -> list[str]:
    """The body is Jev's: `model`, `answers`, `usage`, each answer Jev's fields, 64 KB at most."""
    problems = []
    for response in responses(outcomes):
        raw = response.raw_http_response
        data = raw.json()
        if set(data) != {"model", "answers", "usage"}:
            problems.append(f"top-level keys {sorted(data)}")
        if set(data.get("usage", {})) != {"input_tokens", "output_tokens"}:
            problems.append(f"usage keys {sorted(data.get('usage', {}))}")
        for name, a in data.get("answers", {}).items():
            if set(a) != JEV.get(a.get("type"), set()):
                problems.append(f"{name}: keys {sorted(a)}")
                break
        if len(raw.content) > 65536:
            problems.append(f"{len(raw.content)} bytes over 64 KB")
    return problems


def same_answers(case: Case, outcomes: list[Outcome]) -> list[str]:
    """The same questions under other ids get bit-identical answers."""
    first, second = responses(outcomes)
    problems = []
    for a, b in zip(case.send[0]["questions"], case.send[1]["questions"], strict=True):
        left, right = first.answers[a].model_dump(), second.answers[b].model_dump()
        if left != right:
            problems.append(f"{a} and {b}: {left!r} against {right!r}")
    return problems


def answered(case: Case, outcomes: list[Outcome]) -> list[str]:
    """Every question asked has an answer."""
    return [
        f"asked {len(body['questions'])}, answered {len(response.answers)}"
        for body, response in zip(case.send, responses(outcomes), strict=True)
        if set(response.answers) != set(body["questions"])
    ]


def model_kai(case: Case, outcomes: list[Outcome]) -> list[str]:
    """The answering model is Kai."""
    return [f"model {r.model!r}" for r in responses(outcomes) if "kai" not in r.model]


def catalog(case: Case, outcomes: list[Outcome]) -> list[str]:
    """`hanzo_kai.jev` lists the decision models of `data` in Jev's shape, and the `models` key stays `[]`."""
    problems = []
    for listing in outcomes:
        if not isinstance(listing, ListModelsResponse):
            return [f"not a listing: {said(listing)}"]
        if not listing.models or "kai" not in [m.name for m in listing.models]:
            problems.append(f"models {listing.models!r}")
        for m in listing.models:
            if not isinstance(m.description, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", m.release_date or ""):
                problems.append(f"row {m!r}")
        raw = listing.raw_http_response.json()
        if raw.get("models") != [] or "data" not in raw:
            problems.append(f"models key {raw.get('models')!r}, data key {'present' if 'data' in raw else 'gone'}")
    return problems


def versioned(case: Case, outcomes: list[Outcome]) -> list[str]:
    """The answer names Kai's versioned id: `kai-` and 12 hex digits of its weights' SHA-256."""
    return [f"model {r.model!r}" for r in responses(outcomes) if not re.fullmatch(r"kai-[0-9a-f]{12}", r.model)]


def data(case: Case, outcomes: list[Outcome]) -> list[str]:
    """`GET /v1/models` still lists `kai` under `data`, with decision outputs."""
    return [
        f"decision models {[m.id for m in listing]}"
        for listing in outcomes
        if not (
            isinstance(listing, list)
            and all(isinstance(m, Model) for m in listing)
            and "kai" in [m.id for m in listing]
        )
    ]


def request_id(case: Case, outcomes: list[Outcome]) -> list[str]:
    """Every response carries `x-request-id`."""
    return [f"no x-request-id on {said(outcome)}" for outcome in outcomes if not getattr(outcome, "request_id", None)]


def fastapi(case: Case, outcomes: list[Outcome]) -> list[str]:
    """A `/v1/systemone` error body is FastAPI's: `detail`, a sentence or a list of `{loc, msg, type}`."""
    if case.path != "compat":
        return []
    problems = []
    for outcome in outcomes:
        body = getattr(outcome, "body", None)
        detail = body.get("detail") if isinstance(body, dict) else None
        entries = detail if isinstance(detail, list) else []
        fields = all(
            isinstance(e, dict)
            and isinstance(e.get("loc"), list)
            and isinstance(e.get("msg"), str)
            and isinstance(e.get("type"), str)
            for e in entries
        )
        if not ((isinstance(detail, str) and detail) or (entries and fields)):
            problems.append(f"body {body!r}")
    return problems


CHECKS: dict[str, Check] = {
    check.__name__: check
    for check in (
        sums,
        argmax,
        usage_once,
        noul_confidence,
        confidences,
        legend_verbatim,
        jev_shape,
        same_answers,
        answered,
        model_kai,
        catalog,
        versioned,
        data,
        request_id,
        fastapi,
    )
}
