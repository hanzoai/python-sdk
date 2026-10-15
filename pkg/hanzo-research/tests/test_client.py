"""`Research` against the fake: the bodies, headers and answers of every /v1/research route."""

from __future__ import annotations

import json
import base64

import pytest
from fake import jwt
from conftest import ATLAS, HANZO, SUPER
from hanzo_research import (
    Run,
    Error,
    Paper,
    Split,
    Study,
    Denied,
    Invalid,
    Missing,
    Research,
    Benchmark,
    Unavailable,
    wire,
    canonical,
    transport,
)


def client(server, token=HANZO, **kw):
    return Research(base=server.url, api_key=token, repo=".", **kw)


def run(id="demo.bench-dev-a-sys", **kw):
    base = dict(
        benchmark="demo.bench",
        split="dev",
        system="sys",
        version="v1",
        commit="c0ffee",
        questions=4,
        answered=4,
        ended="2026-10-15T00:00:00Z",
    )
    r = Run(id=id, **{**base, **kw})
    return r.put("all", "accuracy", 0.75, n=3, of=4, lo=0.3, hi=0.95)


def test_records_file_in_their_batch_and_read_back(server):
    r = client(server)
    b = r.record(
        benchmarks=[Benchmark(id="demo.bench", title="Demo", splits=[Split("dev", 4, "all four")], metric="accuracy")]
    )["benchmarks"]
    assert (b.project, b.recorded, b.canonical) == ("default", 1, 1)
    batch = r.record(runs=[run(), run("demo.bench-dev-b-sys", system="other")])["runs"]
    assert batch.recorded == 2
    sent = server.fake.requests[-1]
    assert sent["method"] == "POST" and sent["path"] == "/v1/research/runs" and set(sent["body"]) == {"runs"}
    assert sent["body"]["runs"][0] == run().dump()
    h = sent["headers"]
    assert h["Authorization"] == f"Bearer {HANZO}" and h["X-Project-Id"] == "default" and "X-Org-Id" not in h
    assert h["Content-Type"] == "application/json" and h["User-Agent"].startswith("hanzo-research/")
    listing = r.runs(benchmark="demo.bench")
    assert listing.total == len(listing) == 2 and listing.completion.complete == 2
    assert [x.system for x in listing] == ["sys", "other"] and listing[0].id == "demo.bench-dev-a-sys"
    got = r.get_run("demo.bench-dev-a-sys")
    assert isinstance(got, Run) and got.completion == "complete" and got.canonical and got.visibility == "private"
    assert got.measure("all", "accuracy").lo == 0.3
    assert r.get_benchmark("demo.bench").splits[0].definition == "all four"
    assert {g.field for g in listing.gaps} >= {"prompt", "k"}


def test_a_mapping_is_sent_as_given(server):
    r = client(server)
    row = {"id": "x-dev-c-s", "benchmark": "x", "measures": [{"category": "all", "metric": "m", "value": 1}]}
    r.record(runs=[row])["runs"]
    assert server.fake.requests[-1]["body"] == {"runs": [row]}


def test_the_same_record_twice_records_nothing(server):
    r = client(server)
    assert r.record(runs=[run()])["runs"].recorded == 1
    assert r.record(runs=[run()])["runs"].recorded == 0
    both = r.record(runs=[run()], benchmarks=[Benchmark(id="demo.bench")])
    assert (both["benchmarks"].recorded, both["runs"].recorded) == (1, 0)
    assert [q["path"] for q in server.fake.requests[-2:]] == ["/v1/research/benchmarks", "/v1/research/runs"]
    n = len(server.fake.requests)
    assert r.record() == {} and r.record(runs=[], papers=()) == {}
    assert len(server.fake.requests) == n


def test_studies_and_papers(server):
    r = client(server)
    out = r.record(papers=[Paper(id="p", cites=["a", "b"], study="s")], studies=[Study(id="s", question="does it?")])
    assert list(out) == ["studies", "papers"]
    assert r.studies(id="s")[0].question == "does it?"
    assert r.papers(cites="b")[0].id == "p" and r.papers(cites="z") == []


def test_grant_then_the_public_read_needs_no_credential(server):
    r = client(server)
    r.record(runs=[run()])
    with pytest.raises(Missing):
        r.runs(org="hanzo")
    assert r.grant("demo.bench-dev-a-sys", visibility="public", publishable=True) == 1
    sent = server.fake.requests[-1]["body"]
    assert sent == {"project": "default", "id": "demo.bench-dev-a-sys", "visibility": "public", "publishable": True}
    public = Research(base=server.url, api_key="", repo=".").runs(org="hanzo")
    assert public.total == 1 and public.data[0].publishable and public.data[0].visibility == "public"
    q = server.fake.requests[-1]
    assert q["query"] == {"org": "hanzo"} and "Authorization" not in q["headers"] and "X-Project-Id" not in q["headers"]
    # a credentialled client reading ?org= still sends none: the server answers ?org= only to a caller with no org
    assert r.get_run("demo.bench-dev-a-sys", org="hanzo").id == "demo.bench-dev-a-sys"
    assert "Authorization" not in server.fake.requests[-1]["headers"]
    with pytest.raises(Missing, match="no records for that target"):
        r.grant("nope", visibility="public")
    with pytest.raises(Invalid, match="visibility must be"):
        r.grant("demo.bench-dev-a-sys", visibility="world")


def test_retract_withdraws_and_revise_appends(server):
    r = client(server)
    r.record(runs=[run()])
    fixed = r.get_run("demo.bench-dev-a-sys")
    fixed.measures[0].value = 0.5
    assert r.revise(fixed, notes="rescored").recorded == 1
    again = r.get_run("demo.bench-dev-a-sys")
    assert again.revision == "corrected" and again.measures[0].value == 0.5 and again.notes == "rescored"
    with pytest.raises(Invalid):
        r.retract("demo.bench-dev-a-sys", " ")
    assert r.retract("demo.bench-dev-a-sys", "read on the wrong split").recorded == 1
    assert server.fake.requests[-1]["body"]["runs"][0]["revision"] == "retracted"
    with pytest.raises(Missing):
        r.get_run("demo.bench-dev-a-sys")
    assert r.runs().total == 0


def test_compare_names_what_blocks_it(server):
    r = client(server)
    r.record(runs=[run(), run("demo.bench-dev-b-sys", system="other", answered=3)])["runs"]
    c = r.compare("demo.bench-dev-a-sys", "demo.bench-dev-b-sys")
    assert not c.comparable and any("not established as complete" in b for b in c.blocks)
    assert c.a.id == "demo.bench-dev-a-sys" and c.config[0].field == "system"
    assert c.deltas[0].change == 0 and c.deltas[0].overlap is True
    with pytest.raises(Missing, match='no canonical run "zz"'):
        r.compare("demo.bench-dev-a-sys", "zz")


def test_refusals_carry_the_servers_sentence(server):
    r = client(server)
    with pytest.raises(Invalid, match="run needs an id and a benchmark") as e:
        r.record(runs=[{"id": "x"}])["runs"]
    assert e.value.status == 422 and e.value.path == "/v1/research/runs"
    with pytest.raises(Invalid, match="completion must be"):
        r.runs(completion="done")


def test_what_json_cannot_hold_never_leaves(server):
    n = len(server.fake.requests)
    with pytest.raises(ValueError):
        client(server).record(runs=[{"id": "x", "benchmark": "b", "measures": [{"value": float("nan")}]}])
    assert len(server.fake.requests) == n


def test_503_is_asked_again(server):
    r = client(server)
    server.fake.unavailable = 2
    assert r.record(runs=[run()])["runs"].recorded == 1
    server.fake.unavailable = 9
    with pytest.raises(Unavailable, match="failover"):
        r.runs()


def test_no_credential_says_how_to_get_one(server):
    with pytest.raises(Denied, match="HANZO_API_KEY"):
        Research(base=server.url, api_key="", repo=".").runs()


def test_an_expired_cli_token_is_fetched_again(server, monkeypatch):
    server.fake.expired.add("old")
    fresh = iter(["old", HANZO])
    monkeypatch.setattr(wire, "token", lambda: next(fresh))
    r = Research(base=server.url, repo=".")
    assert r.runs().total == 0
    auths = [q["headers"].get("Authorization") for q in server.fake.requests]
    assert auths == ["Bearer old", f"Bearer {HANZO}"]
    server.fake.expired.add(HANZO)
    with pytest.raises(Denied, match="token expired"):
        Research(base=server.url, api_key=HANZO, repo=".").runs()


def test_the_acting_org_is_one_the_token_names(server):
    r = client(server, org="lux")
    r.record(runs=[run()])
    assert server.fake.requests[-1]["headers"]["X-Org-Id"] == "lux"
    assert r.org == "lux" and client(server).org == "hanzo"
    assert client(server).runs().total == 0 and r.runs().total == 1
    n = len(server.fake.requests)
    with pytest.raises(Denied, match="cannot act in org zoo"):
        client(server, org="zoo").runs()
    with pytest.raises(Denied, match="cannot act in org admin"):
        client(server, org="admin").runs()
    assert len(server.fake.requests) == n
    assert client(server, token=SUPER, org="zoo").runs().total == 0


def test_the_project_is_the_tokens(server):
    with pytest.raises(Error, match="the token's project is default, not atlas"):
        client(server, project="atlas").runs()
    r = client(server, token=ATLAS)
    assert r.project == "atlas"
    assert r.record(runs=[run()])["runs"].project == "atlas"
    assert server.fake.requests[-1]["headers"]["X-Project-Id"] == "atlas"


def test_redirects_and_oversized_answers_are_refused(server, monkeypatch):
    t = client(server).http
    with pytest.raises(Error, match="redirect"):
        t.call("GET", "/redirect", None, None, True)
    monkeypatch.setattr(transport, "MAX_RESPONSE_BYTES", 10)
    with pytest.raises(Error, match="past 10 bytes"):
        client(server).runs()


def test_no_answer_is_unavailable():
    with pytest.raises(Unavailable, match="no answer"):
        Research(base="http://127.0.0.1:9", api_key=HANZO, repo=".", timeout=2).runs()


def test_the_experiment_plane(server, tmp_path):
    r = client(server)
    with r.experiment("benchmark", "grok-4.5", "gpqa_diamond", n_total=2, hypothesis="H", predict="P") as e:
        e.record("q1", "grok-4.5", {"answer": "A", "correct": True})
        e.record("q2", "grok-4.5", {"answer": "B", "correct": False, "gold": "C"})
        e.record("q3", "grok-4.5", {"answer": "", "correct": False, "status": "faulted"})
        e.log("one seed")
    posts = [
        q["body"] for q in server.fake.requests if q["path"] == "/v1/research/experiments" and q["method"] == "POST"
    ]
    running, done = posts[0]["experiments"][0], posts[-1]["experiments"][0]
    assert running["status"] == "running" and running["meta"]["log"] == [] and running["meta"]["hypothesis"] == "H"
    assert done["status"] == "complete" and done["value"] == 50.0 and done["meta"]["verdict"] == "inconclusive"
    assert done["meta"]["log"] == ["one seed"] and done["id"] == "benchmark:grok-4.5:gpqa_diamond"
    assert posts[1]["attempts"][0]["source"] == "hanzo-measured"
    k = r.experiment("kernel-perf", "matvec", "vulkan/6144", metric="ratio_vs_hand")
    ack = k.conclude("refuted", because="0.79x", value=0.79)
    assert ack.experiments_ingested == 1
    with pytest.raises(ValueError):
        k.conclude("maybe")
    with pytest.raises(RuntimeError):
        with r.experiment("training", "a7", "stage-a") as t:
            raise RuntimeError("boom")
    assert server.fake.requests[-1]["body"]["experiments"][0]["status"] == "faulted"
    assert {x.id for x in r.query()} >= {"benchmark:grok-4.5:gpqa_diamond", "kernel-perf:matvec:vulkan/6144"}
    assert r.totals().experiments == 3 and r.projects()[0].project == "default"


def test_artifacts_are_addressed_by_their_bytes(server):
    r = client(server)
    s = r.upload_artifact("report", "demo.bench-dev-a-sys", b"# notes\n", "text/markdown")
    assert s.created and s.ref == "sha256:" + s.sha256
    body = server.fake.requests[-1]["body"]
    assert base64.b64decode(body["content"]) == b"# notes\n" and body["content_sha256"] == s.sha256
    assert body["artifact_id"] == "demo.bench-dev-a-sys:report" and body["uncompressed_size"] == 8
    assert not r.upload_artifact("report", "demo.bench-dev-a-sys", b"# notes\n").created
    value = {"b": 1, "a": [1.5, "é"]}
    j = r.upload_json_artifact("report", "demo.bench-dev-a-sys", value)
    assert j.sha256 == canonical.digest(value)
    assert r.get_artifact(j.sha256) == canonical.canonicalize(value)
    assert {a.sha256 for a in r.artifacts(run="demo.bench-dev-a-sys")} == {s.sha256, j.sha256}
    assert r.grant(sha256=j.sha256, visibility="public") == 1
    with pytest.raises(Invalid, match="kind must be"):
        r.upload_artifact("blob", "x", b"x")
    with pytest.raises(Missing):
        r.get_artifact("0" * 64)


def test_url_is_the_public_read_of_one_run(server):
    r = client(server)
    assert (
        r.url("enso.gpqa_diamond-test-frontier-x")
        == f"{server.url}/v1/research/runs?org=hanzo&id=enso.gpqa_diamond-test-frontier-x"
    )
    assert r.url("a b", org="zoo").endswith("?org=zoo&id=a%20b")
    with pytest.raises(ValueError, match="no org"):
        Research(base=server.url, api_key="sk-opaque", repo=".").url("x")
    assert json.loads(json.dumps(r.arena.catalog()[0].dump()))["id"] == "gpqa_diamond"


def test_the_default_client(server, monkeypatch):
    import hanzo_research as research

    monkeypatch.setattr(research, "_default", None)
    research.configure(base=server.url, api_key=HANZO, repo=".")
    out = research.record(
        benchmarks=[{"id": "b"}], runs=[{"id": "r1", "benchmark": "b"}, {"id": "r2", "benchmark": "b"}]
    )
    assert list(out) == ["benchmarks", "runs"] and out["runs"].recorded == 2
    assert server.fake.requests[-1]["body"] == {
        "runs": [{"id": "r1", "benchmark": "b"}, {"id": "r2", "benchmark": "b"}]
    }
    assert [x.id for x in research.runs(benchmark="b")] == ["r1", "r2"]
    assert server.fake.requests[-1]["query"] == {"benchmark": "b"}
    assert research.benchmarks(id="b")[0].id == "b" and research.studies() == [] and research.papers() == []
    c = research.compare("r1", "r2")
    assert c.a.id == "r1" and c.b.id == "r2" and server.fake.requests[-1]["query"] == {"a": "r1", "b": "r2"}


def test_a_batch_filed_under_another_project_is_refused(server):
    server.fake.project = "elsewhere"
    with pytest.raises(Error, match="runs were committed under project elsewhere, not default"):
        client(server).record(runs=[run()])


def test_a_lookup_stays_in_the_clients_project(server):
    atlas, home = client(server, token=ATLAS), client(server)
    atlas.record(runs=[run("r1")])
    atlas.grant("r1", visibility="public")
    with pytest.raises(Missing):
        home.retract("r1", "wrong split")
    assert server.fake.requests[-1]["query"] == {"id": "r1", "project": "default"}
    theirs = atlas.get_run("r1")
    with pytest.raises(Invalid, match="r1 is in project atlas; this client files under default"):
        home.revise(theirs)
    assert home.runs(org="hanzo").data[0].id == "r1"


def test_revise_keeps_the_runs_grants_and_refuses_no_change(server):
    r = client(server)
    r.record(runs=[run()])
    r.grant("demo.bench-dev-a-sys", visibility="public", publishable=True)
    got = r.get_run("demo.bench-dev-a-sys")
    got.measures[0].value = 0.5
    r.revise(got, notes="rescored")
    public = r.get_run("demo.bench-dev-a-sys", org="hanzo")
    assert public.revision == "corrected" and public.visibility == "public" and public.publishable
    with pytest.raises(Invalid, match="already holds this version"):
        r.revise(r.get_run("demo.bench-dev-a-sys"))


def test_identity_is_read_as_the_server_reads_it(server):
    acme = jwt({"sub": "u", "owner": "hanzo", "orgs": [{"org": "acme"}, {"org": "lux"}], "exp": 4102444800})
    r = client(server, token=acme)
    assert r.org == "acme" and r.url("x").endswith("?org=acme&id=x")  # owner is the app's org, not the home
    machine = jwt({"owner": "admin", "type": "application", "exp": 4102444800})
    with pytest.raises(Denied, match="a machine token acts in its own org, admin, never hanzo"):
        client(server, token=machine, org="hanzo").runs()
    assert client(server, token=machine).org == "admin"
    with pytest.raises(Denied, match="an API key acts in the org it was minted in"):
        client(server, token="sk-opaque", org="hanzo").runs()
    with pytest.raises(Error, match="the token's project is default, not kai"):
        client(server, token="sk-opaque", project="kai").runs()
    assert client(server, token="sk-opaque").project == "default"


def test_a_credential_a_header_cannot_carry_is_never_echoed(server):
    with pytest.raises(Denied) as e:
        client(server, token="sk-SECRET-ONE\nSECRET-TWO").runs()
    assert "SECRET" not in str(e.value) and server.fake.requests == []


def test_a_401_after_the_last_wait_refreshes_once(server, monkeypatch):
    server.fake.expired.add("old")
    server.fake.unavailable = 3
    fresh = iter(["old", HANZO])
    monkeypatch.setattr(wire, "token", lambda: next(fresh))
    assert Research(base=server.url, repo=".").runs().total == 0
    assert len(server.fake.requests) == 5


def test_a_bearer_token_never_crosses_a_network_in_the_clear():
    with pytest.raises(ValueError, match="neither https nor http on this machine"):
        Research(base="http://api.example.com", api_key=HANZO)
    assert Research(base="http://localhost:8080", api_key=HANZO).base == "http://localhost:8080"
