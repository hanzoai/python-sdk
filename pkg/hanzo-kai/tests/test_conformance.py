"""Every conformance fixture, sent through the SDK to a service that answers as the contract says."""

import httpx
import pytest
from conformance import CHECKS, Case, run, load, client
from conformance.fake import KEY, Service

CASES = load()


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_contract(case: Case, slept: list[float]) -> None:
    sdk, attempts = client(case, key=KEY, transport=httpx.MockTransport(Service(case.fault)))
    with sdk:
        assert run(case, sdk, attempts) == []


def test_fixtures() -> None:
    names = {case.name for case in CASES}
    assert len(names) == len(CASES)
    for rule in (
        "jev_ids",
        "kai",
        "instructions",
        "questions",
        "labels",
        "levels",
        "null_level",
        "sums",
        "usage",
        "reach",
        "noul_confidence",
        "legend",
        "models",
        "request_id",
    ):
        assert any(name.startswith(f"{rule}/") for name in names), rule
    used = {check for case in CASES for check in case.expect.get("checks", [])}
    assert used == set(CHECKS)


def test_a_broken_service_fails_the_checks() -> None:
    """The checks read what the service sent: one that rounds, bills per question or drops a field fails them."""

    def broken(request: httpx.Request) -> httpx.Response:
        answer = Service()(request)
        body = answer.json()
        for a in body["answers"].values():
            if a["type"] == "noul":
                a.pop("confidence", None)
            else:
                a["probabilities"] = {key: round(p * 0.9, 2) for key, p in a["probabilities"].items()}
        body["usage"]["input_tokens"] *= len(body["answers"])
        return httpx.Response(200, json=body, headers=answer.headers)

    for rule, check in (
        ("sums", "sums"),
        ("usage", "usage_once"),
        ("noul_confidence", "noul_confidence"),
        ("argmax", "argmax"),
    ):
        case = next(c for c in CASES if c.name == f"{rule}/native")
        sdk, attempts = client(case, key=KEY, transport=httpx.MockTransport(broken))
        with sdk:
            failures = run(case, sdk, attempts)
        assert failures, check
