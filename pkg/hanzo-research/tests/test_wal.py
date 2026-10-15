"""The WAL chains as the crate's: a log the crate wrote verifies here, and one written here resumes."""

from __future__ import annotations

import os
import json
import shutil

import pytest
from hanzo_research import wal
from hanzo_research.wal import GENESIS, ResearchWal

HERE = os.path.join(os.path.dirname(__file__), "vectors")
VECTORS = json.load(open(os.path.join(HERE, "rust.json"), encoding="utf-8"))


def test_a_log_the_crate_wrote_verifies(tmp_path):
    assert wal.verify(os.path.join(HERE, "wal.jsonl")) == VECTORS["wal"]["last"]
    shutil.copy(os.path.join(HERE, "wal.jsonl"), tmp_path / "wal.jsonl")
    w = ResearchWal.open(str(tmp_path), "run-1")
    assert w.sequence == 3 and w.last_event_hash == VECTORS["wal"]["last"]
    e = w.append("step", {"step": 4, "loss": 0.9})
    assert e.sequence == 4 and e.previous_event_hash == VECTORS["wal"]["last"]
    assert wal.verify(w.path) == w.last_event_hash


def test_append_chains_and_resumes(tmp_path):
    w = ResearchWal.open(str(tmp_path), "run-test")
    e1 = w.append("step", {"step": 1, "loss": 1.25})
    assert e1.sequence == 1 and e1.previous_event_hash == GENESIS and e1.event_id == "run-test-worker-0-1-step"
    e2 = w.append("step", {"step": 2, "loss": 1.10})
    assert e2.previous_event_hash == e1.digest()
    again = ResearchWal.open(str(tmp_path), "run-test")
    assert again.sequence == 2 and again.last_event_hash == e2.digest()
    w7 = ResearchWal.open(str(tmp_path), "run-test", "worker-7")
    assert w7.path.endswith("wal-worker-7.jsonl") and w7.sequence == 0


def test_a_changed_line_breaks_the_chain(tmp_path):
    w = ResearchWal.open(str(tmp_path), "run")
    for i in range(3):
        w.append("step", {"step": i})
    lines = open(w.path).read().splitlines()
    lines[1] = lines[1].replace('"step":1', '"step":9')
    open(w.path, "w").write("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="line 2's payload"):
        wal.verify(w.path)
    del lines[1]
    open(w.path, "w").write("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="sequence"):
        wal.verify(w.path)


def test_workers_merge_in_one_order(tmp_path):
    a = ResearchWal.open(str(tmp_path), "run", "worker-a")
    b = ResearchWal.open(str(tmp_path), "run", "worker-b")
    evs = [b.append("x", {"i": 1}), a.append("x", {"i": 1}), a.append("x", {"i": 2})]
    got = wal.ordered(evs)
    assert [(e.sequence, e.worker_id) for e in got] == [(1, "worker-a"), (1, "worker-b"), (2, "worker-a")]


def test_a_payload_with_no_json_form_is_refused(tmp_path):
    with pytest.raises(ValueError):
        ResearchWal.open(str(tmp_path), "run").append("step", {"loss": float("nan")})


def test_a_torn_last_line_is_cut_and_a_whole_one_kept(tmp_path):
    w = ResearchWal.open(str(tmp_path), "run")
    w.append("step", {"i": 1})
    w.append("step", {"i": 2})
    with open(w.path, "a") as f:
        f.write('{"run_id":"run","seq')
    again = ResearchWal.open(str(tmp_path), "run")
    assert again.sequence == 2
    again.append("step", {"i": 3})
    assert wal.verify(again.path) == again.last_event_hash
    text = open(again.path).read().rstrip("\n")
    open(again.path, "w").write(text)
    last = ResearchWal.open(str(tmp_path), "run")
    assert last.sequence == 3 and last.append("step", {"i": 4}).sequence == 4
    assert wal.verify(last.path) == last.last_event_hash
