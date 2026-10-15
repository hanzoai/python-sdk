"""`Arena` against the fake: catalog, board, claims, presets, and the paid run behind confirm."""

from __future__ import annotations

import pytest
from conftest import HANZO, SUPER
from hanzo_research import Arena, Denied, Invalid, Research
from hanzo_research.benchmark import Claim, Preset


def arena(server, token=HANZO, org=None):
    return Arena(base=server.url, api_key=token, org=org)


def claim(source="https://api.hanzo.ai/v1/research/runs?org=hanzo&id=r", protocol="hanzo-measured", **kw):
    return Claim(
        benchmark=kw.pop("benchmark", "gpqa_diamond"),
        provider="hanzo",
        model=kw.pop("model", "enso-ultra"),
        score=kw.pop("score", 91.4),
        protocol=protocol,
        source=source,
    )


def test_reads(server):
    a = arena(server)
    assert [e.id for e in a.catalog()] == ["gpqa_diamond", "livecodebench"] and a.catalog()[0].items == 198
    assert a.compare("x", "y").mcnemar_p == 1.0
    assert a.history("gpqa_diamond", model="x") == []
    assert a.presets()[0].panel == 3
    assert server.fake.requests[-3]["query"] == {"benchmark": "gpqa_diamond", "a": "x", "b": "y"}


def test_claims_reach_the_board_only_from_org_admin(server):
    a = arena(server)
    f = a.post_claims([claim()], visibility="public")
    assert (f.recorded, f.org, f.visibility, f.rejected) == (1, "hanzo", "public", [])
    want = {k: claim().dump()[k] for k in ("benchmark", "provider", "model", "score", "protocol", "source")}
    assert server.fake.requests[-1]["body"] == {"data": [want], "visibility": "public"}
    assert a.leaderboard().rows == []
    assert [c.org for c in a.claims(benchmark="gpqa_diamond")] == ["hanzo"]
    assert arena(server, token=SUPER).post_claims([claim(model="zen5")], visibility="public").org == "admin"
    rows = a.leaderboard("gpqa_diamond").rows
    assert [r.model for r in rows] == ["zen5"] and rows[0].published == 91.4 and rows[0].measured is None
    private = a.post_claims([claim(model="secret")])
    assert private.visibility == "private"
    assert "secret" in {c.model for c in a.claims()}
    assert "secret" not in {c.model for c in Arena(base=server.url, api_key="").claims()}


def test_a_claim_names_its_protocol_and_source(server):
    a = arena(server)
    n = len(server.fake.requests)
    with pytest.raises(Invalid, match="row 0 needs a protocol and a source"):
        a.post_claims([claim(protocol="")])
    with pytest.raises(Invalid, match="row 1"):
        a.post_claims([claim(), {"benchmark": "gpqa_diamond", "model": "m", "score": 1, "protocol": "x"}])
    assert len(server.fake.requests) == n
    f = a.post_claims([claim(benchmark="nope"), claim(score=101)])
    assert f.recorded == 0 and f.rejected == [
        "row 0: unknown benchmark",
        "row 1: a score is a percentage from 0 to 100",
    ]


def test_org_admin_needs_a_superadmin_token(server):
    with pytest.raises(Denied, match="cannot act in org admin"):
        arena(server, org="admin").post_claims([claim()])


def test_a_paid_run_needs_confirm(server):
    a = arena(server)
    n = len(server.fake.requests)
    with pytest.raises(Invalid, match="paid execution"):
        a.post_run(["gpqa_diamond"], model="zen5-pro")
    assert len(server.fake.requests) == n
    adm = a.post_run(["gpqa_diamond"], model="zen5-pro", confirm=True)
    assert adm.status == "queued" and adm.org == "hanzo"
    assert server.fake.requests[-1]["body"] == {"benchmarks": ["gpqa_diamond"], "model": "zen5-pro"}


def test_presets_echo(server):
    acc = arena(server).post_preset(Preset(name="mine", arms=["a", "b"]))
    assert acc.served_as == "enso-mine" and acc.preset.rank == ["a", "b"] and acc.preset.owner == "hanzo"


def test_research_hands_its_credential_to_the_arena(server):
    r = Research(base=server.url, api_key=HANZO, org="lux", repo=".")
    assert r.arena.post_claims([claim()]).org == "lux"
