"""Comprehensive conformance tests for WAL crash-safety, Spooler, CloudLeaseManager, HIP-1403,
4-axis TransferEngine, ProgressiveAbRunner checkpointing, Kai#22 power analysis, Cloud#938,
AutonomousController, and CLI subcommands.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import HANZO
from hanzo_research import (
    AutonomousController,
    CampaignRegistry,
    CloudLeaseManager,
    CorrectnessChecks,
    CounterEvidence,
    ExperimentRecordV2,
    HardwareSpec,
    HypothesisRecord,
    LeaseLostError,
    LocalResearchLedger,
    ObjectiveSpec,
    ProgressiveAbPlan,
    ProgressiveAbRunner,
    ProgressiveStage,
    ProgressiveStageOutput,
    Research,
    ResearchArtifact,
    ResearchBudget,
    ResearchWal,
    SearchArm,
    Spooler,
    StatisticalComparison,
    TransferCatalog,
    WorkloadManifest,
    beta_binomial_e_value,
    canonical,
    cli,
    epistemic_verdict,
    generate_transfer_hypotheses,
    impacted_benchmarks,
    paired_comparison,
    power_analysis,
    research_yield,
    successor_research_lift,
    wal,
)
from hanzo_research.backfill import backfill_verified_history

PKG_ROOT = Path(__file__).resolve().parent.parent


def _client(server) -> Research:
    return Research(base=server.url, api_key=HANZO, repo=str(PKG_ROOT))


def test_wal_2_procs_x_1000_torn_tail_tamper_and_idempotent(tmp_path):
    wal_dir = tmp_path / "mp_wal"
    wal_dir.mkdir()
    worker_code = """
import sys
from hanzo_research.wal import ResearchWal
w = ResearchWal.open(sys.argv[1], "mp-run")
for i in range(1000):
    w.append("tick", {"proc": sys.argv[2], "i": i})
"""
    env = dict(os.environ, PYTHONPATH=f"{PKG_ROOT}:{PKG_ROOT.parent / 'hanzo-login'}")
    p1 = subprocess.Popen([sys.executable, "-c", worker_code, str(wal_dir), "p1"], env=env)
    p2 = subprocess.Popen([sys.executable, "-c", worker_code, str(wal_dir), "p2"], env=env)
    assert p1.wait() == 0
    assert p2.wait() == 0

    wal_file = str(wal_dir / "wal.jsonl")
    head = wal.verify(wal_file)
    assert len(head) == 64
    events = wal.read(wal_file)
    assert len(events) == 2000
    assert [e.sequence for e in events] == list(range(1, 2001))

    # Torn final line mends cleanly; append_idempotent deduplicates retries and rejects collisions.
    crash_dir = tmp_path / "crash_wal"
    w = ResearchWal.open(str(crash_dir), "run-crash")
    w.append("step", {"k": 1})
    w.append("step", {"k": 2})
    with open(w.path, "a", encoding="utf-8") as fp:
        fp.write('{"event_id":"torn","sequence":3')

    reopened = ResearchWal.open(str(crash_dir), "run-crash")
    assert reopened.sequence == 2
    ev3 = reopened.append_idempotent("resume", {"z": 1e21, "a": 1e-7, "m": -0.0, "b": 0.1})
    ev3_dup = reopened.append_idempotent("resume", {"b": 0.1, "m": -0.0, "a": 1e-7, "z": 1e21})
    assert ev3.sequence == 3
    assert ev3.event_id == ev3_dup.event_id
    assert len(wal.read(reopened.path)) == 3

    with pytest.raises(ValueError, match="collision"):
        reopened.append_idempotent("resume", {"different": True}, event_id=ev3.event_id)

    # Interior tamper fails closed on open.
    lines = Path(reopened.path).read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"k":1', '"k":99')
    Path(reopened.path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ResearchWal.open(str(crash_dir), "run-crash")


def test_spooler_offline_backoff_dedup_and_cursor_survival(server, tmp_path):
    r = _client(server)
    wal_dir = tmp_path / "wal"
    cursor_path = tmp_path / "cursor.json"
    w = ResearchWal.open(str(wal_dir), "spool-run")
    w.append("ev1", {"idx": 1})
    w.append("ev2", {"idx": 2})
    w.append("ev3", {"idx": 3})

    # Simulate transient 503 unavailability: max_retries=0 reports offline cleanly.
    server.fake.unavailable = 5
    rep_off = Spooler.drain(r, w.path, cursor_path, max_retries=0, base_backoff_sec=0.005)
    assert rep_off.offline and rep_off.drained == 0 and rep_off.pending == 3

    # Retry past remaining 503 and drain all 3 events.
    rep_ok = Spooler.drain(r, w.path, cursor_path, max_retries=3, base_backoff_sec=0.005)
    assert not rep_ok.offline and rep_ok.drained == 3 and rep_ok.committed_seq == 3

    # Restart with intact cursor sends 0 events.
    rep_noop = Spooler.drain(r, w.path, cursor_path, max_retries=1, base_backoff_sec=0.005)
    assert rep_noop.drained == 0 and rep_noop.committed_seq == 3

    # Simulate crash before cursor fsync: Idempotency-Key prevents duplicate server versions.
    cursor_path.unlink()
    rep_replay = Spooler.drain(r, w.path, cursor_path, max_retries=1, base_backoff_sec=0.005)
    assert rep_replay.drained == 3
    for i in (1, 2, 3):
        vers = r.evidence_versions(f"wal://spool-run/{i}")
        assert len(vers) == 1


def test_cloud_lease_fencing_reclaim_and_release(server, tmp_path):
    now_box = [1_700_000_000]
    mgr_a = CloudLeaseManager(
        _client(server),
        worker_id="worker-a",
        commit="51701f9a672c",
        local_dir=tmp_path / "a",
        clock_fn=lambda: now_box[0],
    )
    mgr_b = CloudLeaseManager(
        _client(server),
        worker_id="worker-b",
        commit="51701f9a672c",
        local_dir=tmp_path / "b",
        clock_fn=lambda: now_box[0],
    )

    out_a = mgr_a.acquire_lease("ml-camp", "opp-bitcos", ttl_sec=60)
    assert out_a.status == "acquired" and out_a.lease is not None
    lease_a = out_a.lease
    assert lease_a.fencing_token == 1

    out_b = mgr_b.acquire_lease("ml-camp", "opp-bitcos", ttl_sec=60)
    assert out_b.status == "busy" and out_b.holder_worker_id == "worker-a"

    now_box[0] = 1_700_000_030
    lease_a2 = mgr_a.renew_lease(lease_a, ttl_sec=60)
    assert lease_a2.fencing_token == 2
    mgr_a.verify_fencing(lease_a2)

    # Advance past expiry + skew grace -> worker B reclaims stale lease.
    now_box[0] = 1_700_000_100
    reclaimed = mgr_b.reclaim_stale("ml-camp", "opp-bitcos", ttl_sec=60)
    assert reclaimed.status == "acquired" and reclaimed.lease is not None
    lease_b = reclaimed.lease
    assert lease_b.fencing_token == 3 and lease_b.reclaimed_from == "worker-a"

    with pytest.raises(LeaseLostError):
        mgr_a.verify_fencing(lease_a2)
    with pytest.raises(LeaseLostError):
        mgr_a.renew_lease(lease_a2, ttl_sec=60)

    rel = mgr_b.release_lease(lease_b, final_state="completed")
    assert rel is not None and rel.version == 4
    now_box[0] = 1_700_000_101
    again = mgr_a.acquire_lease("ml-camp", "opp-bitcos", ttl_sec=60)
    assert again.status == "acquired" and again.lease is not None and again.lease.fencing_token == 5


def test_hip1403_types_dedup_key_and_4axis_transfer():
    hyp = HypothesisRecord(
        statement="2-bit LUT BITCOS beats scalar Q4_K by >= 1.25x",
        null_hypothesis="ratio_vs_q4k <= 1.0",
        gate_ref="gate:throughput_parity_v1",
        dataset_refs=["sha256:aaaa"],
        budget=ResearchBudget(max_compute_seconds=600.0, max_cost_usd=2.0),
        proposer="did:hanzo:agent:ml",
        registered_at="2026-11-22T00:00:00Z",
    )
    hyp.validate()
    assert hyp.hypothesis_id.startswith("sha256:")

    ce = CounterEvidence(
        counter_evidence_id="ce-1",
        claim_id="claim-9",
        experiment_id="exp-9",
        defect_kind="holdout_leakage",
        details="calibration overlapped test split",
        gate_ref="gate:leakage_v1",
        submitted_by="did:hanzo:auditor",
        submitted_at="2026-11-22T01:00:00Z",
    )
    assert len(ce.digest()) == 64

    y_pred = research_yield([0.20, 0.0, 0.10], [1.0, 2.0, 1.0])
    assert abs(y_pred - 0.075) < 1e-9
    y_succ = research_yield([0.30, 0.15], [1.0, 1.0])
    assert abs(successor_research_lift(y_succ, y_pred) - 3.0) < 1e-9

    comp = paired_comparison([100.0, 101.0, 99.0], [145.0, 146.0, 144.0], higher_is_better=True)
    win_exp = ExperimentRecordV2(
        project="default",
        study="bitcos-study",
        objective="Accelerate ternary GEMV",
        hypothesis=hyp.statement,
        hypothesis_id=hyp.hypothesis_id,
        null_hypothesis=hyp.null_hypothesis,
        gate_ref=hyp.gate_ref,
        experiment_id="ml:bitcos:bonsai2-2b",
        repo="hanzoai/ml",
        commit="51701f9a672c84d5220ae9a7d5576926d8907822",
        hardware=HardwareSpec(
            host="dgx",
            architecture="aarch64",
            gpu="NVIDIA GB10",
            backend="CUDA-GB10-sm121a",
            precision="TERNARY",
        ),
        hardware_class="CUDA-GB10-sm121a",
        config={"model": "Bonsai-2-2B", "workload_regime": "single-turn-decode"},
        workload_manifest=WorkloadManifest(
            manifest_id="wl-bitcos",
            dataset="bonsai2-shapes",
            split="bench",
            shapes=["4096x4096"],
            input_lengths=[512],
            batch_size=1,
            seed=17,
            manifest_sha256="c" * 64,
        ),
        baseline={"mean": comp["baseline"]["mean"]},
        candidate={"mean": comp["candidate"]["mean"]},
        statistical_comparison=StatisticalComparison(
            metric="throughput",
            unit="tok/s",
            higher_is_better=True,
            n=3,
            baseline_mean=comp["baseline"]["mean"],
            candidate_mean=comp["candidate"]["mean"],
            delta=comp["delta"],
            ratio=comp["ratio"],
            ratio_lo=comp["ratio_lo"],
            ratio_hi=comp["ratio_hi"],
            verdict="win",
        ),
        correctness=CorrectnessChecks(parity_passed=True, memory_integrity_passed=True),
        raw_samples={"baseline": [100.0, 101.0, 99.0], "candidate": [145.0, 146.0, 144.0]},
        conclusion="1.45x verified",
    )
    expected_dk = canonical.digest(
        {
            "project": "default",
            "hypothesis_id": hyp.hypothesis_id,
            "config_digest": canonical.digest(win_exp.config),
            "commit": win_exp.commit,
            "dataset_digest": "c" * 64,
            "hardware_class": "CUDA-GB10-sm121a",
        }
    )
    assert win_exp.dedup_key() == expected_dk
    assert epistemic_verdict(win_exp.verdict) == "proven"

    opps = generate_transfer_hypotheses(win_exp, TransferCatalog())
    rules = [o.trigger_rule for o in opps]
    assert any(r.startswith("transfer:model_scale:") for r in rules)
    assert any(r.startswith("transfer:seq_len:") for r in rules)
    assert any(r.startswith("transfer:backend:") for r in rules)
    assert any(r.startswith("transfer:workload_regime:") for r in rules)

    # Refuted experiment emits targeted mechanism-fix hypothesis instead of blind transfer.
    loss_exp = ExperimentRecordV2.load(win_exp.dump())
    loss_exp.experiment_id = "ml:bitcos:bad-tile"
    loss_exp.statistical_comparison.verdict = "loss"
    loss_exp.verdict = "refuted"
    loss_exp.failure_diagnosis = "shared memory bank conflict at stride 32"
    loss_exp.next_hypothesis = "Pad shared tile by +4 bytes to eliminate bank conflict"
    fix_opps = generate_transfer_hypotheses(loss_exp)
    assert len(fix_opps) == 1
    assert fix_opps[0].trigger_rule.startswith("mechanism_fix_after_refutation:")


def test_dual_plane_sync_readback_and_gb10_32k_query(server, tmp_path):
    r = _client(server)
    ledger = LocalResearchLedger.open(tmp_path / "ledger", run_id="gb10-sync")
    backfill_verified_history(ledger)

    # Query GB10 32K decode findings locally before sync.
    gb10_hits = ledger.query_experiments(search="32k gb10")
    assert len(gb10_hits) >= 2
    blob = " ".join(x.hypothesis + " " + x.conclusion for x in gb10_hits)
    for term in ("Split-KV", "PhasePolicy", "HybridPrefix", "ReplayGDN", "DFlash2"):
        assert term in blob

    # Also attach a custom multi-artifact experiment and verify byte-for-byte SHA-256 readback.
    comp = paired_comparison([100.0, 101.0, 99.0], [160.0, 161.0, 159.0], higher_is_better=True)
    rec = ExperimentRecordV2(
        project="default",
        study="custom-sync-study",
        objective="Verify multi-artifact byte-for-byte SHA-256 readback",
        hypothesis="Candidate achieves 1.6x speedup",
        experiment_id="ml:custom:multi-art",
        repo="hanzoai/ml",
        commit="51701f9a672c84d5220ae9a7d5576926d8907822",
        hardware=HardwareSpec(host="dgx", architecture="aarch64", gpu="NVIDIA GB10", backend="CUDA"),
        workload_manifest=WorkloadManifest(manifest_id="wl-1", dataset="synthetic", shapes=["4096x4096"]),
        baseline={"mean": 100.0},
        candidate={"mean": 160.0},
        statistical_comparison=StatisticalComparison(
            metric="throughput",
            unit="tok/s",
            higher_is_better=True,
            n=3,
            baseline_mean=100.0,
            candidate_mean=160.0,
            delta=60.0,
            ratio=1.6,
            ratio_lo=comp["ratio_lo"],
            ratio_hi=comp["ratio_hi"],
            verdict="win",
        ),
        correctness=CorrectnessChecks(parity_passed=True, memory_integrity_passed=True),
        raw_samples={"baseline": [100.0, 101.0, 99.0], "candidate": [160.0, 161.0, 159.0]},
        conclusion="1.60x verified",
    )
    raw_trace = b"nsys-kernel-trace-binary-\x00\x01\x02"
    raw_manifest = b'{"shapes":["4096x4096"],"seed":17}\n'
    ledger.record_experiment(rec, artifacts={"nsys_trace": raw_trace, "workload_json": raw_manifest})

    refuted_rec = ExperimentRecordV2.load(rec.dump())
    refuted_rec.experiment_id = "ml:custom:refuted-tile"
    refuted_rec.statistical_comparison.verdict = "loss"
    refuted_rec.verdict = "refuted"
    refuted_rec.failure_diagnosis = "shared memory bank conflict"
    ledger.record_experiment(refuted_rec, artifacts={"diag_json": b'{"reason":"bank_conflict"}\n'})

    receipts = ledger.sync_to_cloud(r)
    assert len(receipts) == len(ledger.query_all())
    assert all(rc.readback_verified for rc in receipts)

    custom_rc = next(rc for rc in receipts if rc.experiment_id == "ml:custom:multi-art")
    assert "nsys_trace" in custom_rc.uploaded_artifacts
    assert "workload_json" in custom_rc.uploaded_artifacts
    assert r.get_artifact(custom_rc.uploaded_artifacts["nsys_trace"]) == raw_trace
    assert r.get_artifact(custom_rc.uploaded_artifacts["workload_json"]) == raw_manifest

    # Verify cloud rich queries return proven & refuted experiments with failure_diagnosis.
    cloud_gb10 = r.query_experiments(search="32k")
    assert len(cloud_gb10) >= 2
    cloud_failures = r.prior_failures()
    assert len(cloud_failures) >= 1


def test_progressive_ab_checkpoint_resume_and_kai22_power_analysis(tmp_path):
    runner = ProgressiveAbRunner(ProgressiveAbPlan())
    s1 = [0]
    s2 = [0]
    s3 = [0]
    ckpt = tmp_path / "looks.ckpt.json"

    def crashing_stage(idx: int, stage: ProgressiveStage) -> ProgressiveStageOutput:
        if idx == 1:
            s1[0] += 1
            return ProgressiveStageOutput(
                stage_name=stage.name,
                baseline_samples=[100.0, 100.5, 99.5, 100.0],
                candidate_samples=[150.0, 151.0, 149.5, 150.5],
            )
        raise RuntimeError("simulated kill -9")

    with pytest.raises(RuntimeError, match="kill -9"):
        runner.run(crashing_stage, checkpoint_path=ckpt)
    assert ckpt.is_file() and s1[0] == 1

    def resuming_stage(idx: int, stage: ProgressiveStage) -> ProgressiveStageOutput:
        if idx == 1:
            s1[0] += 1
        elif idx == 2:
            s2[0] += 1
        else:
            s3[0] += 1
        return ProgressiveStageOutput(
            stage_name=stage.name,
            baseline_samples=[100.0, 100.2, 99.8, 100.1, 99.9],
            candidate_samples=[152.0, 151.8, 152.2, 152.1, 151.9],
        )

    resumed = runner.run(resuming_stage, checkpoint_path=ckpt)
    assert s1[0] == 1, "Look 1 must resume from checkpoint without re-running"
    assert s2[0] == 1 and s3[0] == 1
    assert resumed.verdict == "proven"

    # Kai#22 Monte Carlo calibration: N=1066, delta=+0.02, discordance=0.10 -> power >= 0.50, null FPR <= alpha!
    assert beta_binomial_e_value(0, 0) == 1.0
    pa = power_analysis(
        1066,
        0.02,
        0.10,
        alpha=0.05,
        task_arm_budget=4,
        simulations=3000,
        seed=42,
    )
    assert pa["power"] >= 0.50, f"expected power >= 0.50, got {pa['power']}"
    assert pa["null_false_positive_rate"] <= 0.05, f"null FPR exceeded alpha: {pa['null_false_positive_rate']}"


def test_cloud_938_timestamps_tags_artifacts_and_gpu_job(server):
    r = _client(server)
    art = ResearchArtifact(sha256="a" * 64, content="aGk=", kind="report", run_id="r1", tags=["gb10"])
    dumped = art.dump()
    assert dumped["ts"] > 1_700_000_000 and dumped["tags"] == ["gb10"] and "received_at" not in dumped

    with r.experiment("kernel-perf", "bitcos", "gb10", tags=["gb10", "ternary"], hypothesis="LUT wins") as exp:
        exp.conclude("proven", because="1.6x faster", value=1.6)

    rows = r.query()
    assert len(rows) >= 1
    assert rows[-1].ts > 1_700_000_000
    assert rows[-1].tags == ["gb10", "ternary"]

    raw_payload = b'{"tok_s":160.0}'
    r.upload_artifact(
        "report",
        "run-938",
        raw_payload,
        media_type="application/json",
        canonicalization="rfc8785",
        artifact_id="run-938:report",
    )
    arts = r.artifacts(run="run-938")
    assert len(arts) == 1
    assert arts[0].artifact_id == "run-938:report"
    assert arts[0].media_type == "application/json"
    assert arts[0].canonicalization == "rfc8785"
    assert arts[0].uncompressed_size == len(raw_payload)
    assert arts[0].received_at == 1700000999

    sub = r.submit_gpu_job({"cmd": "bitcos_profile"}, job_type="research.bench", gpu="gb10", job_id="job-gb10-py")
    assert sub["taskQueue"] == "gpu:gb10"
    done = r.wait_gpu_job("job-gb10-py", timeout_sec=5.0, poll_interval_sec=0.01)
    assert done["state"] == "ACTIVITY_TASK_STATE_COMPLETED"
    assert done["output"]["tok_per_sec"] == 182.4


def test_autonomous_controller_tick_loop_and_cli(server, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HANZO_API_KEY", HANZO)
    monkeypatch.setenv("RESEARCH_BASE", server.url)

    exec_script = tmp_path / "exec.py"
    exec_script.write_text(
        """#!/usr/bin/env python3
import argparse, json
p = argparse.ArgumentParser()
p.add_argument("phase")
p.add_argument("--request", required=True)
p.add_argument("--output", required=True)
args = p.parse_args()
req = json.load(open(args.request, encoding="utf-8"))
if req["variant"] == "z_bad":
    out = {
        "status": "complete",
        "trial_id": req["trial_id"],
        "objective_id": req["objective_id"],
        "baseline_samples": [100.0, 101.0, 99.0, 100.0],
        "candidate_samples": [70.0, 71.0, 69.0, 70.0],
        "parity_passed": True,
        "memory_integrity_passed": True,
        "gpu_time_sec": 0.05,
        "details": "regressed"
    }
else:
    out = {
        "status": "complete",
        "trial_id": req["trial_id"],
        "objective_id": req["objective_id"],
        "baseline_samples": [100.0, 100.5, 99.5, 100.2, 99.8],
        "candidate_samples": [165.0, 166.0, 164.5, 165.2, 164.8],
        "parity_passed": True,
        "memory_integrity_passed": True,
        "gpu_time_sec": 0.08,
        "details": "improved"
    }
json.dump(out, open(args.output, "w", encoding="utf-8"))
""",
        encoding="utf-8",
    )
    exec_script.chmod(0o755)

    reg = CampaignRegistry(
        campaign="py-auto-camp",
        repo="hanzoai/ml",
        plan=ProgressiveAbPlan(
            stages=[
                ProgressiveStage(name="micro", reps=4, prompt_len=64, gen_len=16),
                ProgressiveStage(name="qualification", reps=5, prompt_len=256, gen_len=64),
            ]
        ),
        objectives=[
            ObjectiveSpec(
                id="bitcos",
                study="bitcos",
                family="quant",
                metric="throughput",
                unit="tok/s",
                direction="higher",
                backends=["CPU", "CUDA"],
                shapes=["4096x4096"],
            )
        ],
        search_space={
            "quant": [
                SearchArm(arm="lut", variant="z_bad", hypothesis="Test z_bad"),
                SearchArm(arm="lut", variant="b_good", hypothesis="Test b_good"),
            ]
        },
    )
    camp_path = tmp_path / "campaign.json"
    camp_path.write_text(json.dumps(reg.dump(), indent=2), encoding="utf-8")

    ledger_dir = tmp_path / "ctrl_ledger"
    ctrl = AutonomousController(
        ledger_dir=ledger_dir,
        registry=reg,
        repo_dir=str(PKG_ROOT),
        worker_id="py-worker-1",
    )

    t1 = ctrl.tick(exec_script, auto_sync=True, client=_client(server))
    assert t1["verdict"] == "refuted" and t1["early_stopped"] is True and t1["stopped_stage"] == 1

    loop_res = ctrl.loop(
        exec_script,
        max_ticks=1,
        budget_minutes=5.0,
        idle_exit=True,
        auto_sync=True,
        client=_client(server),
    )
    assert loop_res["ticks"] == 1
    assert loop_res["outcomes"][0]["verdict"] == "proven"

    # CLI subcommands: impact, query, failures, next, controller status/validate
    lineage_file = tmp_path / "lineage.json"
    lineage_file.write_text(
        json.dumps(
            {
                "bitcos": {"paths": ["hanzo-ml/src/quantized/bitcos.rs"], "artifacts": []},
                "flash_attn": {"paths": ["hanzo-ml/src/flash_attn.rs"], "artifacts": []},
            }
        ),
        encoding="utf-8",
    )
    assert cli.main(["impact", "--lineage", str(lineage_file), "--changed-paths", "hanzo-ml/src/quantized/bitcos.rs"]) == 0
    imp = json.loads(capsys.readouterr().out)
    assert imp["tasks"] == ["bitcos"]

    assert cli.main(["failures", "--dir", str(ledger_dir)]) == 0
    fails = json.loads(capsys.readouterr().out)
    assert len(fails) == 1

    assert cli.main(["next", "--dir", str(ledger_dir), "--top-k", "5"]) == 0
    nxt = json.loads(capsys.readouterr().out)
    assert len(nxt) >= 1

    assert cli.main(["controller", "validate", "--campaign", str(camp_path)]) == 0
    val = json.loads(capsys.readouterr().out)
    assert val["campaign"] == "py-auto-camp"
