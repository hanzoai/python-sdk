"""`hanzo-research` against the fake."""

from __future__ import annotations

import json

import pytest
from conftest import HANZO
from hanzo_research.cli import main


@pytest.fixture
def cli(server, monkeypatch, capsys):
    monkeypatch.setenv("HANZO_API_KEY", HANZO)
    monkeypatch.setenv("RESEARCH_BASE", server.url)

    def go(*argv):
        code = main(argv)
        out, err = capsys.readouterr()
        return code, (json.loads(out) if out.strip() else None), err

    return go


def run(i):
    return {
        "id": f"demo-dev-c-s{i}",
        "benchmark": "demo",
        "system": f"s{i}",
        "questions": 2,
        "answered": 2,
        "ended": "2026-10-15T00:00:00Z",
        "measures": [{"category": "all", "metric": "accuracy", "value": 0.5}],
    }


def test_post_a_jsonl_file_and_grant(cli, server, tmp_path):
    f = tmp_path / "runs.jsonl"
    f.write_text("\n".join(json.dumps(run(i)) for i in range(3)) + "\n")
    code, out, _ = cli("post", str(f), "--grant", "public", "--publishable")
    assert code == 0 and out["runs"]["recorded"] == 3
    assert out["granted"] == {f"demo-dev-c-s{i}": 1 for i in range(3)}
    code, out, _ = cli("list", "runs", "--public", "hanzo")
    assert out["total"] == 3 and out["completion"]["complete"] == 3


def test_a_plan_files_benchmarks_before_runs(cli, server, tmp_path):
    f = tmp_path / "plan.json"
    f.write_text(json.dumps({"runs": [run(1)], "benchmarks": [{"id": "demo", "metric": "accuracy"}]}))
    code, out, _ = cli("post", str(f), "--dry")
    assert code == 0 and list(out) == ["benchmarks", "runs"] and len(server.fake.requests) == 0
    code, out, _ = cli("post", str(f))
    assert [q["path"] for q in server.fake.requests] == ["/v1/research/benchmarks", "/v1/research/runs"]
    code, out, _ = cli("list", "benchmarks")
    assert out[0]["id"] == "demo"


def test_get_grant_retract_compare(cli, server, tmp_path):
    f = tmp_path / "two.json"
    f.write_text(json.dumps([run(1), run(2)]))
    cli("post", str(f))
    code, out, _ = cli("get", "demo-dev-c-s1")
    assert out["completion"] == "complete"
    code, out, _ = cli("grant", "demo-dev-c-s1", "--visibility", "org", "--no-publishable")
    assert out == {"demo-dev-c-s1": 1} and server.fake.requests[-1]["body"]["publishable"] is False
    code, out, _ = cli("compare", "demo-dev-c-s1", "demo-dev-c-s2")
    assert out["comparable"] and out["deltas"][0]["change"] == 0
    code, out, _ = cli("retract", "demo-dev-c-s1", "--why", "wrong split")
    assert out["recorded"] == 1
    code, out, err = cli("get", "demo-dev-c-s1")
    assert code == 1 and "no canonical run" in err


def test_refusals_exit_nonzero_with_the_servers_sentence(cli, tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"id": "x"}))
    code, out, err = cli("post", str(f))
    assert code == 1 and "run needs an id and a benchmark" in err
    code, out, err = cli("--org", "zoo", "list", "runs")
    assert code == 1 and "cannot act in org zoo" in err
    code, out, err = cli("grant")
    assert code == 2


def test_provenance_and_arena(cli, server):
    code, out, _ = cli(
        "provenance", "--model", "m", "--weights", "sha256:" + "c" * 64, "--no-gpu", "--package", "pytest"
    )
    assert code == 0 and out["model"] == "m" and out["weights"] == "sha256:" + "c" * 64 and "pytest" in out["packages"]
    code, out, _ = cli("arena", "catalog")
    assert out[0]["id"] == "gpqa_diamond"
    code, out, _ = cli("arena", "compare", "a", "b", "--benchmark", "livecodebench")
    assert out["benchmark"] == "livecodebench"
    code, out, _ = cli("arena", "leaderboard")
    assert out["rows"] == []
