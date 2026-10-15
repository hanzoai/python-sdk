"""Lineage narrows and never widens; records digest as the crate's do."""

from __future__ import annotations

import os
import json

import pytest
from hanzo_research.lineage import (
    ArtifactRef,
    DataPurpose,
    EnvironmentV1,
    LineagePolicy,
    ResearchEvent,
    ContaminationError,
    derive_lineage_policy,
    verify_promotion_eligibility,
)

VECTORS = json.load(open(os.path.join(os.path.dirname(__file__), "vectors", "rust.json"), encoding="utf-8"))


def test_policy_propagation():
    train = LineagePolicy.root(DataPurpose.TRAIN, True)
    train.assert_trainable("source")
    ev = LineagePolicy.root(DataPurpose.EVAL_ONLY, True)
    assert not ev.derivation_allowed
    with pytest.raises(ContaminationError):
        ev.assert_trainable("eval_src")
    derived = LineagePolicy.derive(DataPurpose.TEACHER_MINING, True, [train, ev])
    assert derived.purpose is DataPurpose.EVAL_ONLY and not derived.derivation_allowed
    clean = derive_lineage_policy(DataPurpose.TEACHER_MINING, True, [train])
    assert clean.purpose is DataPurpose.TEACHER_MINING and clean.derivation_allowed
    clean.assert_trainable("clean_child")


def test_promotion_eligibility():
    root = LineagePolicy.root(DataPurpose.TRAIN, True)
    mining = LineagePolicy.derive(DataPurpose.TEACHER_MINING, True, [root])
    ckpt = LineagePolicy.derive(DataPurpose.TRAIN, True, [root, mining])
    verify_promotion_eligibility("ckpt-a10", ckpt, [root, mining])
    with pytest.raises(ContaminationError, match=r"ckpt-a10->transitive_ancestor\[0\] has derivation_allowed = false"):
        verify_promotion_eligibility("ckpt-a10", ckpt, [LineagePolicy(DataPurpose.TRAIN, False)])
    with pytest.raises(ContaminationError, match="purpose EvalOnly"):
        verify_promotion_eligibility("ckpt-a10", LineagePolicy(DataPurpose.EVAL_ONLY, True), [])


def test_purposes_order_and_wire_names():
    assert [p.value for p in DataPurpose] == ["train", "teacher_mining", "dev", "eval_only", "sealed_eval"]
    assert DataPurpose.most_restrictive(DataPurpose.DEV, DataPurpose.TRAIN) is DataPurpose.DEV
    assert DataPurpose.DEV.is_eval() and not DataPurpose.DEV.is_training_allowed()


def test_records_digest_as_the_crates():
    r = VECTORS["records"]
    assert LineagePolicy.load(r["policy"]["value"]).digest() == r["policy"]["digest"]
    assert EnvironmentV1.load(r["environment"]["value"]).digest() == r["environment"]["digest"]
    ev = ResearchEvent.load(r["event"]["value"])
    assert ev.digest() == r["event"]["digest"]
    assert (
        ResearchEvent.new(
            ev.run_id, ev.worker_id, ev.event_id, 1, ev.previous_event_hash, {"loss": 1.25, "step": 1}, ev.created_at
        ).payload_hash
        == ev.payload_hash
    )


def test_artifact_ref():
    a = ArtifactRef.new("ab" * 32, LineagePolicy.root(DataPurpose.TRAIN, True))
    assert a.ref_uri == "sha256:" + "ab" * 32 and a.artifact_id == "artifact:" + "ab" * 32
    assert a.dump()["lineage"] == {"purpose": "train", "derivation_allowed": True}
    assert ArtifactRef.load(a.dump()) == a
