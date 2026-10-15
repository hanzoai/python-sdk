"""The wire records hold the crate's (and the server's) fields, and read the server's answers tolerantly."""

from __future__ import annotations

import os
import json
import math

from fake import jwt
from hanzo_research import Run, Listing, Measure, Benchmark, Comparison, wire

VECTORS = json.load(open(os.path.join(os.path.dirname(__file__), "vectors", "rust.json"), encoding="utf-8"))


def test_a_run_has_the_crates_fields():
    rust = VECTORS["records"]["run"]["value"]
    assert set(Run().dump()) == set(rust)
    assert set(Measure().dump()) == set(rust["measures"][0])
    assert Run.load(rust).dump() == rust


def test_reads_are_tolerant():
    r = Run.load({"id": "x", "measures": None, "k": None, "unknown": 1, "temperature": 0})
    assert r.measures == [] and r.k is None and r.temperature == 0.0 and isinstance(r.temperature, float)
    c = Comparison.load({"comparable": True, "blocks": None, "config": None, "deltas": None, "a": None})
    assert c.blocks == [] and c.config == [] and c.a is None
    b = Benchmark.load({"splits": [{"name": "dev", "items": 3}], "metrics": None})
    assert b.splits[0].items == 3 and b.splits[0].definition == "" and b.metrics == []
    assert Listing.load({"data": [{"id": "x"}], "total": 1}).completion is None


def test_completion_is_derived_as_the_server_derives_it():
    assert wire.completion(Run(questions=10, answered=10, ended="2026-10-15T00:00:00Z")) == "complete"
    assert wire.completion(Run(questions=10, answered=10)) == "unknown"
    assert wire.completion(Run(questions=10, answered=7, ended="t")) == "partial"
    assert wire.completion(Run(questions=10, answered=11, ended="t")) == "inconsistent"
    assert wire.completion(Run(questions=10)) == "unknown"


def test_put_records_only_finite_numbers():
    r = Run()
    r.put("all", "acc", 0.5, n=2, of=4).put("all", "nan", math.nan).put("all", "inf", math.inf)
    r.put("all", "bool", True).put("all", "text", "0.5").put("all", "int", 3, lo=2.0, hi=4.0)
    assert [m.metric for m in r.measures] == ["acc", "int"]
    assert r.measure("all", "acc") == Measure("all", "acc", 0.5, None, None, 2, 4)
    assert r.measure("all", "int").value == 3.0 and r.measure("x", "y") is None


def test_dump_passes_a_mapping_through():
    d = {"id": "x", "measures": [{"category": "all"}]}
    assert wire.dump(d) == d and wire.dump([Run(id="y"), d])[1] == d


def test_token_claims():
    t = jwt({"owner": "hanzo", "project": "atlas", "exp": 4102444800})
    assert wire.claims(t)["owner"] == "hanzo"
    assert wire.claimed(t) == "atlas"
    assert wire.claimed(jwt({"owner": "hanzo"})) == "default"
    assert wire.claimed("sk-opaque") is None and wire.claims("a.b.c") is None
    assert wire.left(t) > 0 and wire.left(jwt({})) is None
    assert wire.scope(" ") == "default" and wire.scope("x") == "x"
    assert wire.now().endswith("Z") and len(wire.now()) == 20


def test_token_reads_the_environment_first(monkeypatch):
    monkeypatch.undo()
    monkeypatch.setenv("HANZO_API_KEY", " sk-env ")
    assert wire.token() == "sk-env"
