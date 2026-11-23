"""Tests for canonical ExperimentRecordV2, adaptive testing, WAL sync, and opportunity queue."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from hanzo_research import (
    CorrectnessChecks,
    ExperimentRecordV2,
    HardwareSpec,
    LocalResearchLedger,
    Opportunity,
    Research,
    ResearchWal,
    StatisticalComparison,
    WorkloadManifest,
    impacted_benchmarks,
    paired_accuracy_look,
    paired_comparison,
    paired_metric_anytime_look,
    wal,
)
from hanzo_research.cli import main as cli_main


def _sample_experiment(
    *,
    exp_id: str = "ml:bitcos:bonsai2-2b",
    repo: str = "hanzoai/ml",
    study: str = "bitcos-ternary-packing",
    historical: bool = False,
) -> ExperimentRecordV2:
    return ExperimentRecordV2(
        project="default",
        study=study,
        objective="Minimize ternary decode bandwidth via zero-density-aware packing",
        hypothesis="BitcosMatrix G128 beats dense PQ2_0 at z >= 0.50 sparsity",
        experiment_id=exp_id,
        parent_experiment="ml:pq2:baseline",
        prior_best=2.0,
        repo=repo,
        commit="f149e2ea8dcdef69464df0f03cfedd46d500cb11",
        branch="research/bitcos-ternary-packing",
        pr="#76",
        artifact_hashes={"weights": "a" * 64},
        hardware=HardwareSpec(
            host="dgx",
            architecture="aarch64",
            gpu="NVIDIA GB10",
            driver="570.0",
            compiler="rustc 1.88 / nvcc 13.0",
            backend="CUDA",
            precision="BF16",
            memory_gb=128.0,
        ),
        config={"group_size": 128},
        workload_manifest=WorkloadManifest(
            manifest_id="bonsai2-ffn-4096x12288",
            dataset="Ternary-Bonsai-2-2B-PQ2_0.gguf",
            split="bench",
            shapes=["4096x12288"],
            input_lengths=[128],
            batch_size=1,
            seed=17,
            manifest_sha256="b" * 64,
        ),
        baseline={"name": "PQ2_0", "mean_us": 420.0, "n": 5},
        candidate={"name": "BitcosMatrix-G128", "mean_us": 260.0, "n": 5},
        statistical_comparison=StatisticalComparison(
            metric="ratio_vs_pq2",
            unit="x",
            higher_is_better=True,
            n=5,
            baseline_mean=1.0,
            candidate_mean=1.615,
            baseline_ci95=0.02,
            candidate_ci95=0.03,
            delta=0.615,
            ratio=1.615,
            ratio_lo=1.57,
            ratio_hi=1.66,
            p_value=0.001,
            anytime_valid=True,
            verdict="win",
        ),
        correctness=CorrectnessChecks(
            parity_passed=True,
            max_abs_diff=0.0,
            ulp_diff=0.0,
            safety_passed=True,
            memory_integrity_passed=True,
            details="0.0 ULP exact match vs PQ2_0",
        ),
        raw_samples={
            "baseline": [0.99, 1.00, 1.01, 0.995, 1.005],
            "candidate": [1.60, 1.61, 1.62, 1.63, 1.615],
        },
        gpu_time_sec=4.2,
        compute_cost_usd=0.05,
        conclusion="BitcosMatrix G128 delivers 1.615x speedup at 0.0 ULP error",
        next_hypothesis="Apply BitcosMatrix layout policy to G64 sparse attention projections",
        historical=historical,
    )


def test_rejects_bare_pass_or_missing_samples(tmp_path: Path) -> None:
    ledger = LocalResearchLedger(tmp_path)
    bad = _sample_experiment()
    bad.raw_samples = {}
    with pytest.raises(ValueError, match="raw_samples"):
        ledger.record_experiment(bad)

    bad2 = _sample_experiment(historical=True)
    bad2.artifact_hashes = {}
    with pytest.raises(ValueError, match="artifact_hashes"):
        ledger.record_experiment(bad2)


def test_wal_ledger_records_queries_and_syncs_offline_safely(tmp_path: Path) -> None:
    ledger = LocalResearchLedger(tmp_path, run_id="shared-test")
    ml_exp = _sample_experiment(exp_id="ml:bitcos:v1", repo="hanzoai/ml", historical=False)
    eng_exp = _sample_experiment(exp_id="engine:qmm:v1", repo="hanzoai/engine", study="qmm-cuda", historical=False)
    res1 = ledger.record_experiment(ml_exp, artifacts={"bench_json": b'{"mean":1.615}'})
    res2 = ledger.record_experiment(eng_exp, artifacts={"bench_json": b'{"mean":2.1}'})
    assert res1["wal_seq"] == 1
    assert res2["wal_seq"] == 2
    assert len(wal.read(str(ledger.wal_dir / "wal.jsonl"))) == 2
    wal.verify(str(ledger.wal_dir / "wal.jsonl"))

    assert len(ledger.query()) == 2
    assert [r.experiment_id for r in ledger.query(repo="hanzoai/engine")] == ["engine:qmm:v1"]

    # Sync with mock client verifying read-back
    class _FakeHttp:
        def __init__(self) -> None:
            self.arts: dict[str, dict[str, Any]] = {}

        def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
            if path == "/v1/research/artifacts":
                self.arts[body["sha256"]] = body
                return {"sha256": body["sha256"], "created": True}
            return {"recorded": 1, "canonical": 1, "project": "default"}

        def get(self, path: str) -> Any:
            sha = path.rsplit("/", 1)[-1]
            return self.arts[sha]

    class _FakeClient:
        def __init__(self) -> None:
            self.http = _FakeHttp()
            self.stored_runs: list[Any] = []

        def record(self, benchmarks=(), studies=(), runs=(), papers=()):
            self.stored_runs.extend(runs)
            return {}

        def runs(self, id=None):
            return [r for r in self.stored_runs if r.id == id]

    receipts = ledger.sync_to_cloud(_FakeClient())
    assert len(receipts) == 2
    assert all(r.status == "synced_verified" and r.readback_verified for r in receipts)


def test_opportunity_queue_propagation_and_statistical_helpers(tmp_path: Path) -> None:
    ledger = LocalResearchLedger(tmp_path)
    exp = _sample_experiment()
    ops = ledger.opportunities.propagate_discovery(
        exp,
        [
            ("ffn_down_sparse", "kernel", "enable BitcosMatrix G128 on down_proj", 0.35, 0.5),
            ("kv_dense", "attention", "test sparse gating on dense KV", 0.10, 2.0),
        ],
    )
    assert len(ops) == 2
    best = ledger.opportunities.next_best()
    assert best is not None
    assert best.objective == "ffn_down_sparse"

    comp = paired_comparison([10.0, 10.2, 9.8], [15.0, 15.1, 14.9], higher_is_better=True)
    assert comp["verdict"] == "win"
    assert comp["ratio"] > 1.4

    scr = paired_accuracy_look([True] * 64, [False] * 64, look_index=1, family_budget=240)
    assert scr["decision"] == "promising"

    anytime = paired_metric_anytime_look(
        [0.9] * 32,
        [0.1] * 32,
        lambda v: sum(v) / len(v),
        metric_name="spearman",
        dev_sha="1" * 64,
        candidate_sha="2" * 64,
        order_sha="3" * 64,
        population_n=128,
        look_index=1,
        permutations=50000,
    )
    assert anytime["decision"] == "promising"

    imp = impacted_benchmarks(["imdb", "boolq"], ["train/campaign/recipes/imdb/train.py"])
    assert imp["tasks"] == ["imdb"]


def test_exhaustive_small_sample_paired_mcnemar_and_alpha_spending() -> None:
    import math
    from hanzo_research import paired_accuracy_look, verify_progressive_screen

    # Exhaustive check across n in 1..12 for every possible discordant pair (a, b) with a + b <= n.
    for n in range(1, 13):
        for a in range(n + 1):
            for b in range(n - a + 1):
                ca = [True] * a + [False] * b + [True] * (n - a - b)
                je = [False] * a + [True] * b + [True] * (n - a - b)
                res = paired_accuracy_look(ca, je, look_index=1, min_samples=1, family_budget=240)
                d = a + b
                exp_better = 1.0 if a == 0 else sum(math.comb(d, i) for i in range(a, d + 1)) * (0.5 ** d)
                exp_worse = 1.0 if b == 0 else sum(math.comb(d, i) for i in range(b, d + 1)) * (0.5 ** d)
                assert abs(res["one_sided_p_better"] - exp_better) < 1e-12
                assert abs(res["one_sided_p_worse"] - exp_worse) < 1e-12
                # Impossible for paired McNemar to produce p < 2^-d or < 2^-n
                assert res["one_sided_p_better"] >= (0.5 ** n) - 1e-15
                assert res["one_sided_p_worse"] >= (0.5 ** n) - 1e-15

    # Check n=32 exact boundary: with 16 candidate errors and 0 baseline errors (b=16, a=0),
    # minimum possible paired McNemar p-value is 2^-16 = 1.5258789e-5 (NEVER 1.615e-9).
    res32 = paired_accuracy_look([False] * 16 + [True] * 16, [True] * 32, look_index=1, family_budget=240)
    assert abs(res32["one_sided_p_worse"] - (2.0 ** -16)) < 1e-12
    assert res32["decision"] == "futility"

    # At b=14, a=0, p_worse = 2^-14 = 6.10e-5 > spent_alpha (5.208e-5) -> must NOT stop early
    res14 = paired_accuracy_look([False] * 14 + [True] * 18, [True] * 32, look_index=1, family_budget=240)
    assert res14["decision"] == "continue"

    # Alpha spending sums across k=1..1000 strictly <= alpha / family_budget < alpha
    total_spent = sum(0.05 / (240 * k * (k + 1)) for k in range(1, 1001))
    assert total_spent < 0.05 / 240.0

    # Non-paired one-sample binomial screen must be rejected by verify_progressive_screen
    req = {"metric": "accuracy", "jev_reference": 0.91315, "screen_plan": {"family_budget": 240}}
    bad_dev = {
        "dev_score": 0.5,
        "dev_n": 32,
        "dev_sha": "a" * 64,
        "candidate_sha": "b" * 64,
        "screening": {
            "metric": "accuracy",
            "method": "binomial_reference_anytime",
            "dev_sha": "a" * 64,
            "candidate_sha": "b" * 64,
            "population_n": 367,
            "n": 32,
            "look_index": 1,
            "order_sha": "c" * 64,
        },
    }
    assert verify_progressive_screen(req, bad_dev, family_budget=240)["decision"] == "unverified"


