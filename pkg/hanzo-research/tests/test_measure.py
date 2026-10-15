"""`key` and `measure` against the fake: the key is the server's byte for byte, a held complete run
is returned without spending, a miss measures and records, and `force` measures anyway."""

from __future__ import annotations

import pytest
from conftest import HANZO
from hanzo_research import IDENTITY, Run, Invalid, Research, key

# hanzo-inc/cloud apps/research key_test.go TestKeyVector: the same identities, the same keys.
VECTORS = [
    (
        Run(
            benchmark="locomo",
            split="all",
            system="enso-flash",
            version="1.2.0",
            k=20,
            temperature=0.0,
            max_tokens=512,
            embedder="text-embedding-3-small",
            reader="zen6",
            prompt_digest="9f2c",
            dataset_digest="79fa87e90f040813",
        ),
        "098c0e3fe9a62a04ee9b814f62f4812b058cdadc6c72521b5a0112a5440258da",
    ),
    (
        {"benchmark": "coding.repair", "split": "held", "system": "hanzo-dev", "temperature": 0.7},
        "8304fbac139f449f61526f5d58e8c429df235230da789367159c7ab98609a552",
    ),
]

IDENT = {**VECTORS[0][0].dump(), "id": "locomo-all-k20-enso-flash"}
DONE = {
    "questions": 282,
    "answered": 282,
    "ended": "2026-10-15T00:00:00Z",
    "measures": [{"category": "all", "metric": "f1", "value": 0.45}],
}


def client(server):
    return Research(base=server.url, api_key=HANZO, repo=".")


class Spend:
    """A measurement that counts how often it was paid for."""

    def __init__(self, out=DONE):
        self.out, self.calls = out, 0

    def __call__(self):
        self.calls += 1
        return dict(self.out)


def posts(server):
    return [q for q in server.fake.requests if q["method"] == "POST" and q["path"] == "/v1/research/runs"]


def test_the_key_is_the_servers():
    for identity, want in VECTORS:
        assert key(identity) == want
    assert IDENTITY[0] == "benchmark" and IDENTITY[-1] == "facts_digest" and len(IDENTITY) == 13


def test_the_key_reads_numbers_as_go_writes_them():
    for given, same in ((0, 0.0), (1.0, 1), (100.0, 1e2), (0.7, 0.70), (1e-07, 0.0000001)):
        assert key({"temperature": given}) == key({"temperature": same})
    assert key({"temperature": 0.0}) != key({}) and key({"k": 0}) != key({})
    assert key({"split": "allenso", "system": ""}) != key({"split": "all", "system": "enso"})
    with pytest.raises(TypeError):
        key({"k": 20.0})


def test_a_miss_measures_and_records(server):
    fn = Spend()
    run = client(server).measure(IDENT, fn)
    assert fn.calls == 1 and len(posts(server)) == 1
    assert key(run) == VECTORS[0][1] and run.completion == "complete" and run.measure("all", "f1").value == 0.45


def test_a_held_run_is_returned_without_spending(server):
    r = client(server)
    first = r.measure(IDENT, Spend())
    fn = Spend()
    again = r.measure({**IDENT, "id": "a-rerun-under-another-name", "commit": "later"}, fn)
    assert fn.calls == 0 and len(posts(server)) == 1
    assert again.id == first.id and key(again) == key(first)
    assert server.fake.requests[-1]["query"] == {"key": VECTORS[0][1], "completion": "complete"}


def test_force_measures_anyway(server):
    r = client(server)
    r.measure(IDENT, Spend())
    fn = Spend({**DONE, "ended": "2026-10-16T00:00:00Z"})
    r.measure(IDENT, fn, force=True)
    assert fn.calls == 1 and len(posts(server)) == 2


def test_a_partial_run_or_another_configuration_is_not_a_hit(server):
    r = client(server)
    r.measure(IDENT, Spend({**DONE, "answered": 57}))
    fn = Spend()
    r.measure(IDENT, fn)
    r.measure({**IDENT, "id": "k10", "k": 10}, fn)
    assert fn.calls == 2


def test_fn_may_not_move_the_identity(server):
    with pytest.raises(Invalid, match="changed its measurement identity"):
        client(server).measure(IDENT, Spend({**DONE, "reader": "zen6-flash"}))
    assert posts(server) == []


def test_a_server_that_ignores_the_key_is_not_a_hit(server):
    r = client(server)
    r.measure({**IDENT, "id": "another", "k": 10}, Spend())
    real = server.fake.runs
    server.fake.runs = lambda who, q: real(who, {k: v for k, v in q.items() if k != "key"})
    fn = Spend()
    r.measure(IDENT, fn)
    assert fn.calls == 1
