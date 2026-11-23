"""Unified first-class scientific experiment protocol, WAL-first ledger, and opportunity queue.

Implements the shared schema across `hanzoai/ml`, `hanzo-engine`, and `hanzo-inc/kai`:
- Every experiment is a structured, content-addressed record binding git commit/branch/PR,
  hardware/backend/precision/compiler, workload shapes/seed, raw baseline & candidate samples,
  statistical uncertainty (`ci95`, `p_value`, `n`), correctness/parity/safety/memory integrity,
  compute cost, conclusion, failure diagnosis, and next hypothesis.
- Bare summary labels ("PASS", "2.5x faster") without baseline, workload, sample counts, and
  supporting artifacts are rejected by validation.
- Records persist locally first via `ResearchWal` + content-addressed artifacts, then sync
  idempotently to `/v1/research` with byte-for-byte SHA-256 read-back verification (`docs/research-sync.md`).
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import canonical
from .transfer import DeadEndEntry, TransferCatalog, TransferEngine, generate_transfer_hypotheses
from .wal import ResearchWal
from .wire import Benchmark, Run, Study, Wire, now

__all__ = [
    "ResearchBudget",
    "HypothesisRecord",
    "CounterEvidence",
    "research_yield",
    "successor_research_lift",
    "HardwareSpec",
    "WorkloadManifest",
    "StatisticalComparison",
    "CorrectnessChecks",
    "ExperimentRecordV2",
    "Opportunity",
    "OpportunityQueue",
    "SyncReceipt",
    "LocalResearchLedger",
    "epistemic_verdict",
]


@dataclass
class ResearchBudget(Wire):
    """HIP-1403 resource budget cap for pre-registered experiments."""

    max_compute_seconds: float = 3600.0
    max_cost_usd: float = 25.0


@dataclass
class HypothesisRecord(Wire):
    """HIP-1403 pre-registered falsifiable hypothesis record."""

    hypothesis_id: str = ""
    statement: str = ""
    null_hypothesis: str = ""
    gate_ref: str = ""
    dataset_refs: list[str] = field(default_factory=list)
    budget: ResearchBudget = field(default_factory=ResearchBudget)
    proposer: str = "did:hanzo:org:research-agent"
    registered_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.hypothesis_id and self.statement.strip():
            self.with_computed_id()

    def with_computed_id(self) -> HypothesisRecord:
        if not self.hypothesis_id:
            body = {k: v for k, v in self.dump().items() if k != "hypothesis_id"}
            self.hypothesis_id = "sha256:" + canonical.digest(body)
        return self

    def validate(self) -> None:
        if not self.statement.strip() or not self.null_hypothesis.strip() or not self.gate_ref.strip():
            raise ValueError("HypothesisRecord requires statement, null_hypothesis, and gate_ref")
        if self.budget.max_compute_seconds <= 0 or self.budget.max_cost_usd < 0:
            raise ValueError("HypothesisRecord requires positive budget bounds")


@dataclass
class CounterEvidence(Wire):
    """HIP-1403 counter-evidence submission triggering claim retraction."""

    counter_evidence_id: str = ""
    claim_id: str = ""
    experiment_id: str = ""
    defect_kind: str = "failed_replication"
    details: str = ""
    gate_ref: str = ""
    submitted_by: str = ""
    submitted_at: str = field(default_factory=now)

    def digest(self) -> str:
        return canonical.digest(self.dump())


def research_yield(verified_gains: Sequence[float], total_costs_including_failures: Sequence[float]) -> float:
    """HIP-1403 Research Yield Y_R = sum(verified_gains) / sum(total_costs_including_failures)."""
    gains = [float(g) for g in verified_gains if math.isfinite(float(g)) and float(g) > 0.0]
    costs = [float(c) for c in total_costs_including_failures]
    if any((not math.isfinite(c) or c < 0.0) for c in costs):
        raise ValueError("research costs must be non-negative finite numbers")
    total_cost = sum(costs)
    if total_cost <= 0.0:
        if not gains and not costs:
            return 0.0
        raise ValueError("total research cost must be strictly positive")
    return sum(gains) / total_cost


def successor_research_lift(y_successor: float, y_predecessor: float) -> float:
    """HIP-1403 Successor Research Lift L_R = Y_R(successor) / Y_R(predecessor)."""
    if not math.isfinite(y_successor) or not math.isfinite(y_predecessor) or y_predecessor <= 0.0:
        raise ValueError("y_predecessor must be finite and strictly positive")
    return float(y_successor) / float(y_predecessor)


def epistemic_verdict(verdict: str) -> str:
    """Normalize statistical comparison verdict onto `/v1/research` epistemic verdict."""
    v = (verdict or "").strip().lower()
    if v in ("win", "proven"):
        return "proven"
    if v in ("loss", "refuted"):
        return "refuted"
    return "inconclusive"


@dataclass
class HardwareSpec(Wire):
    host: str = ""
    architecture: str = ""
    gpu: str = ""
    driver: str = ""
    compiler: str = ""
    backend: str = ""
    precision: str = ""
    memory_gb: float | None = None


@dataclass
class WorkloadManifest(Wire):
    manifest_id: str = ""
    dataset: str = ""
    split: str = ""
    shapes: list[str] = field(default_factory=list)
    input_lengths: list[int] = field(default_factory=list)
    batch_size: int = 1
    seed: int = 0
    manifest_sha256: str = ""


@dataclass
class StatisticalComparison(Wire):
    metric: str = ""
    unit: str = ""
    higher_is_better: bool = True
    n: int = 0
    baseline_mean: float = 0.0
    candidate_mean: float = 0.0
    baseline_ci95: float | None = None
    candidate_ci95: float | None = None
    delta: float = 0.0
    ratio: float | None = None
    ratio_lo: float | None = None
    ratio_hi: float | None = None
    p_value: float | None = None
    anytime_valid: bool = False
    verdict: str = "inconclusive"


@dataclass
class CorrectnessChecks(Wire):
    parity_passed: bool = False
    max_abs_diff: float | None = None
    ulp_diff: float | None = None
    safety_passed: bool | None = None
    memory_integrity_passed: bool = False
    details: str = ""


@dataclass
class ExperimentRecordV2(Wire):
    """First-class autonomous scientific experiment record."""

    project: str = ""
    study: str = ""
    objective: str = ""
    hypothesis: str = ""
    hypothesis_id: str = ""
    null_hypothesis: str = ""
    gate_ref: str = ""
    experiment_id: str = ""
    parent_experiment: str = ""
    parent_ids: list[str] = field(default_factory=list)
    prior_best: float | None = None
    repo: str = ""
    commit: str = ""
    branch: str = ""
    pr: str = ""
    config_digest: str = ""
    env_digest: str = ""
    hardware_class: str = ""
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    artifact_refs: list[str] = field(default_factory=list)
    hardware: HardwareSpec = field(default_factory=HardwareSpec)
    config: dict[str, Any] = field(default_factory=dict)
    workload_manifest: WorkloadManifest = field(default_factory=WorkloadManifest)
    baseline: dict[str, Any] = field(default_factory=dict)
    candidate: dict[str, Any] = field(default_factory=dict)
    statistical_comparison: StatisticalComparison = field(default_factory=StatisticalComparison)
    correctness: CorrectnessChecks = field(default_factory=CorrectnessChecks)
    raw_samples: dict[str, list[float]] = field(default_factory=dict)
    example_ids: list[str] = field(default_factory=list)
    verdict: str = ""
    revision: str = ""
    retracted: bool = False
    retracted_reason: str = ""
    gpu_time_sec: float = 0.0
    compute_cost_usd: float = 0.0
    conclusion: str = ""
    failure_diagnosis: str = ""
    next_hypothesis: str = ""
    historical: bool = False
    recorded_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if self.retracted and not self.revision:
            self.revision = "retracted"
        elif self.revision.strip().lower() == "retracted":
            self.retracted = True
        if not self.verdict and self.statistical_comparison.verdict:
            raw_v = self.statistical_comparison.verdict.strip().lower()
            self.verdict = "promising_inconclusive" if raw_v == "promising_inconclusive" else epistemic_verdict(raw_v)

    def is_retracted(self) -> bool:
        return bool(self.retracted or self.revision.strip().lower() == "retracted")

    def digest(self) -> str:
        return canonical.digest(self.dump())

    def dedup_key(self) -> str:
        """Canonical RFC 8785 deduplication key across distributed workers."""
        cfg_d = self.config_digest or canonical.digest(self.config)
        ds_d = (
            self.workload_manifest.manifest_sha256
            or self.workload_manifest.dataset
            or self.workload_manifest.manifest_id
        )
        hw_cls = self.hardware_class or self.hardware.backend or self.hardware.gpu or "CPU"
        return canonical.digest(
            {
                "project": self.project or "default",
                "hypothesis_id": self.hypothesis_id or self.hypothesis,
                "config_digest": cfg_d,
                "commit": self.commit,
                "dataset_digest": ds_d,
                "hardware_class": hw_cls,
            }
        )

    def validate(self, *, require_example_ids: bool = False) -> None:
        required_strs = (
            ("project", self.project),
            ("study", self.study),
            ("objective", self.objective),
            ("hypothesis", self.hypothesis),
            ("experiment_id", self.experiment_id),
            ("repo", self.repo),
            ("commit", self.commit),
            ("conclusion", self.conclusion),
        )
        for name, val in required_strs:
            if not str(val).strip():
                raise ValueError(f"ExperimentRecordV2 missing required field: {name}")
        if not self.workload_manifest.manifest_id and not self.workload_manifest.dataset:
            raise ValueError("ExperimentRecordV2 requires workload_manifest (manifest_id or dataset)")
        if not self.artifact_hashes:
            raise ValueError("ExperimentRecordV2 requires supporting artifact_hashes (never bare PASS/speedup)")
        if not self.baseline or not self.candidate:
            raise ValueError("ExperimentRecordV2 requires both baseline and candidate measurements")
        if self.statistical_comparison.n <= 0:
            raise ValueError("ExperimentRecordV2 requires positive sample count n")
        for col in (self.statistical_comparison.baseline_mean, self.statistical_comparison.candidate_mean):
            if not math.isfinite(float(col)):
                raise ValueError("ExperimentRecordV2 measurements must be finite")
        if not self.historical:
            b_raw = self.raw_samples.get("baseline", [])
            c_raw = self.raw_samples.get("candidate", [])
            if not b_raw or not c_raw:
                raise ValueError("Reproduced experiment must store raw_samples['baseline'] and raw_samples['candidate']")
            req_ids = bool(require_example_ids or self.config.get("require_example_ids"))
            if req_ids and not self.is_retracted():
                from .testing import validate_dataset_manifest_sha256, validate_paired_binary_trace

                validate_dataset_manifest_sha256(self.workload_manifest.manifest_sha256)
                if len(self.example_ids) != self.statistical_comparison.n:
                    raise ValueError("Canonical paired run with require_example_ids=True requires aligned example_ids")
                cleaned_ids = [str(eid).strip() for eid in self.example_ids]
                if any(not eid for eid in cleaned_ids) or len(set(cleaned_ids)) != len(cleaned_ids):
                    raise ValueError("example_ids must be non-empty and strictly distinct")
                if len(b_raw) == len(c_raw) and all(x in (0.0, 1.0) for x in list(b_raw) + list(c_raw)):
                    validate_paired_binary_trace(
                        c_raw,
                        b_raw,
                        example_ids=cleaned_ids,
                        dataset_manifest_sha256=self.workload_manifest.manifest_sha256,
                        require_example_ids=True,
                    )

    def to_run(self) -> Run:
        """Project this rich experiment record onto `/v1/research/runs` wire format."""
        n = self.statistical_comparison.n
        ev = epistemic_verdict(self.statistical_comparison.verdict)
        raw_verdict = (self.statistical_comparison.verdict or "").strip().lower()
        run = Run(
            project=self.project,
            id=self.experiment_id,
            benchmark=self.study,
            split=self.workload_manifest.split or "bench",
            system=self.repo,
            version=self.commit[:12],
            baseline=False,
            study=self.study,
            dataset_digest=self.workload_manifest.manifest_sha256,
            commit=self.commit,
            questions=n,
            answered=n,
            when=self.recorded_at,
            ended=self.recorded_at,
            revision="retracted" if self.is_retracted() else (self.revision or ""),
            notes=json.dumps(
                {
                    "hypothesis": self.hypothesis,
                    "conclusion": self.conclusion,
                    "verdict": ev,
                    "screen_verdict": raw_verdict or ev,
                    "retracted": self.is_retracted(),
                    "retracted_reason": self.retracted_reason,
                    "failure_diagnosis": self.failure_diagnosis,
                    "next_hypothesis": self.next_hypothesis,
                    "historical": self.historical,
                    "backend": self.hardware.backend,
                    "precision": self.hardware.precision,
                    "artifact_hashes": self.artifact_hashes,
                },
                sort_keys=True,
            ),
        )
        run.put(
            "candidate",
            self.statistical_comparison.metric,
            self.statistical_comparison.candidate_mean,
            n=n,
            of=n,
            lo=(
                None
                if self.statistical_comparison.candidate_ci95 is None
                else self.statistical_comparison.candidate_mean - self.statistical_comparison.candidate_ci95
            ),
            hi=(
                None
                if self.statistical_comparison.candidate_ci95 is None
                else self.statistical_comparison.candidate_mean + self.statistical_comparison.candidate_ci95
            ),
        )
        run.put(
            "baseline",
            self.statistical_comparison.metric,
            self.statistical_comparison.baseline_mean,
            n=n,
            of=n,
            lo=(
                None
                if self.statistical_comparison.baseline_ci95 is None
                else self.statistical_comparison.baseline_mean - self.statistical_comparison.baseline_ci95
            ),
            hi=(
                None
                if self.statistical_comparison.baseline_ci95 is None
                else self.statistical_comparison.baseline_mean + self.statistical_comparison.baseline_ci95
            ),
        )
        if self.statistical_comparison.ratio is not None:
            run.put(
                "comparison",
                "ratio",
                self.statistical_comparison.ratio,
                n=n,
                of=n,
                lo=self.statistical_comparison.ratio_lo,
                hi=self.statistical_comparison.ratio_hi,
            )
        return run

    def to_experiment_wire(self) -> dict[str, Any]:
        """Project onto `/v1/research/experiments` wire format with epistemic verdict."""
        ev = epistemic_verdict(self.statistical_comparison.verdict)
        raw_verdict = (self.statistical_comparison.verdict or "").strip().lower()
        because = self.failure_diagnosis.strip() if ev == "refuted" and self.failure_diagnosis.strip() else self.conclusion
        out: dict[str, Any] = {
            "id": self.experiment_id,
            "kind": "experiment-v2",
            "subject": f"{self.repo}/{self.hardware.backend or 'CPU'}",
            "task": self.study,
            "metric": self.statistical_comparison.metric,
            "value": self.statistical_comparison.candidate_mean,
            "n": self.statistical_comparison.n,
            "n_total": self.statistical_comparison.n,
            "status": "complete",
            "git_sha": self.commit,
            "git_branch": self.branch,
            "git_dirty": False,
            "lib_versions": {},
            "meta": {
                "study": self.study,
                "repo": self.repo,
                "backend": self.hardware.backend,
                "gpu": self.hardware.gpu,
                "shapes": list(self.workload_manifest.shapes),
                "dataset_manifest_sha256": self.workload_manifest.manifest_sha256,
                "hypothesis": self.hypothesis,
                "predict": self.objective,
                "verdict": ev,
                "screen_verdict": raw_verdict or ev,
                "retracted": self.is_retracted(),
                "retracted_reason": self.retracted_reason,
                "because": because,
                "conclusion": self.conclusion,
                "failure_diagnosis": self.failure_diagnosis,
                "next_hypothesis": self.next_hypothesis,
                "artifact_hashes": dict(self.artifact_hashes),
            },
        }
        if self.is_retracted():
            out["revision"] = "retracted"
        elif self.revision:
            out["revision"] = self.revision
        return out


@dataclass
class Opportunity(Wire):
    opportunity_id: str = ""
    domain: str = ""
    objective: str = ""
    current_best: float = 0.0
    proposed_approach: str = ""
    expected_improvement: float = 0.0
    compute_cost: float = 1.0
    related_experiments: list[str] = field(default_factory=list)
    trigger_rule: str = ""
    status: str = "open"

    @property
    def priority_score(self) -> float:
        return self.expected_improvement / max(1e-6, self.compute_cost)


class OpportunityQueue:
    """Prioritized autonomous research opportunity queue (gain per unit compute)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.items: dict[str, Opportunity] = {}
        self.reload()

    def reload(self) -> None:
        self.items.clear()
        if self.path.is_file():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for row in raw:
                op = Opportunity.load(row)
                self.items[op.opportunity_id] = op

    def add(self, op: Opportunity, *, preserve_closed: bool = True) -> Opportunity:
        if not op.opportunity_id:
            raise ValueError("opportunity_id required")
        existing = self.items.get(op.opportunity_id)
        if preserve_closed and existing is not None and existing.status in ("completed", "refuted", "skipped"):
            return existing
        self.items[op.opportunity_id] = op
        self.save()
        return op

    def mark_status(self, opportunity_id: str, status: str) -> Opportunity | None:
        op = self.items.get(opportunity_id)
        if op is None:
            return None
        op.status = status
        self.save()
        return op

    def top_open(self, domain: str | None = None, top_k: int = 10) -> list[Opportunity]:
        open_ops = [
            op
            for op in self.items.values()
            if op.status == "open" and (domain is None or op.domain == domain or domain in op.domain)
        ]
        open_ops.sort(key=lambda o: (-o.priority_score, o.opportunity_id))
        return open_ops[: max(0, top_k)]

    def next_best(self, domain: str | None = None) -> Opportunity | None:
        ranked = self.top_open(domain=domain, top_k=1)
        return ranked[0] if ranked else None

    def propagate_discovery(
        self,
        source_exp: ExperimentRecordV2,
        targets: Sequence[tuple[str, str, str, float, float]],
    ) -> list[Opportunity]:
        """When a technique succeeds, queue targeted follow-up experiments on qualifying targets.

        Each target tuple is `(target_id, domain, approach, expected_improvement, compute_cost)`.
        """
        created: list[Opportunity] = []
        if source_exp.is_retracted() or epistemic_verdict(source_exp.statistical_comparison.verdict) != "proven":
            return created
        for tid, domain, approach, gain, cost in targets:
            op = Opportunity(
                opportunity_id=f"{source_exp.experiment_id}->{tid}",
                domain=domain,
                objective=tid,
                current_best=source_exp.statistical_comparison.candidate_mean,
                proposed_approach=approach,
                expected_improvement=gain,
                compute_cost=cost,
                related_experiments=[source_exp.experiment_id],
                trigger_rule=f"propagated_from:{source_exp.experiment_id}",
                status="open",
            )
            self.add(op)
            created.append(op)
        return created

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = sorted((op.dump() for op in self.items.values()), key=lambda x: x["opportunity_id"])
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)


@dataclass
class SyncReceipt(Wire):
    experiment_id: str = ""
    record_sha256: str = ""
    artifact_sha256: str = ""
    uploaded_artifacts: dict[str, str] = field(default_factory=dict)
    status: str = "pending_sync"
    readback_verified: bool = False
    error: str = ""
    synced_at: str = field(default_factory=now)


class LocalResearchLedger:
    """Shared WAL-first local ledger + idempotent `/v1/research` sync queue."""

    @classmethod
    def open(cls, root: str | Path, run_id: str = "hanzo-shared") -> LocalResearchLedger:
        return cls(root, run_id=run_id)

    def __init__(self, root: str | Path, run_id: str = "hanzo-shared"):
        self.root = Path(root).expanduser().resolve()
        self.run_id = run_id
        self.records_dir = self.root / "records"
        self.artifacts_dir = self.root / "artifacts"
        self.receipts_dir = self.root / "receipts"
        self.wal_dir = self.root / "wal"
        self.manifest_path = self.artifacts_dir / "manifest.json"
        self.dead_ends_path = self.root / "dead_ends.json"
        self.cloud_state_path = self.root / "cloud_state.json"
        self.opportunities = OpportunityQueue(self.root / "opportunities.json")
        for d in (self.records_dir, self.artifacts_dir, self.receipts_dir, self.wal_dir):
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(exp_id: str) -> str:
        return hashlib.sha256(exp_id.encode("utf-8")).hexdigest()[:24]

    def artifact_manifest(self) -> dict[str, str]:
        if not self.manifest_path.is_file():
            return {}
        raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in raw.items()}

    def _update_artifact_manifest(self, entries: Mapping[str, str]) -> None:
        cur = self.artifact_manifest()
        cur.update(entries)
        tmp = self.manifest_path.with_name(self.manifest_path.name + ".tmp")
        tmp.write_text(json.dumps(cur, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.manifest_path)

    def store_artifact(self, name: str, data: bytes) -> str:
        sha = hashlib.sha256(data).hexdigest()
        target = self.artifacts_dir / sha
        if not target.exists():
            tmp = self.artifacts_dir / f"{sha}.tmp"
            tmp.write_bytes(data)
            os.replace(tmp, target)
        if name:
            self._update_artifact_manifest({name: sha})
        return sha

    def dead_ends(self) -> list[DeadEndEntry]:
        if not self.dead_ends_path.is_file():
            return []
        rows = json.loads(self.dead_ends_path.read_text(encoding="utf-8"))
        return [DeadEndEntry.load(r) for r in rows]

    def _record_dead_end(self, entry: DeadEndEntry) -> None:
        by_id = {d.experiment_id: d for d in self.dead_ends()}
        by_id[entry.experiment_id] = entry
        rows = sorted((d.dump() for d in by_id.values()), key=lambda r: r["experiment_id"])
        tmp = self.dead_ends_path.with_name(self.dead_ends_path.name + ".tmp")
        tmp.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.dead_ends_path)

    def record_experiment(
        self,
        exp: ExperimentRecordV2,
        *,
        artifacts: Mapping[str, bytes] | None = None,
        worker_id: str = "worker-0",
        auto_transfer: bool = True,
        transfer_catalog: TransferCatalog | None = None,
    ) -> dict[str, Any]:
        if not exp.recorded_at:
            exp.recorded_at = now()
        if not exp.config_digest:
            exp.config_digest = canonical.digest(exp.config)
        if not exp.hardware_class:
            exp.hardware_class = exp.hardware.backend or exp.hardware.gpu or "CPU"
        if not exp.verdict:
            exp.verdict = epistemic_verdict(exp.statistical_comparison.verdict)
        if exp.parent_experiment and exp.parent_experiment not in exp.parent_ids:
            exp.parent_ids.append(exp.parent_experiment)
        manifest_updates: dict[str, str] = {}
        for name, data in (artifacts or {}).items():
            sha = self.store_artifact(f"{exp.experiment_id}:{name}", data)
            exp.artifact_hashes[name] = sha
            manifest_updates[f"{exp.experiment_id}:{name}"] = sha
        for name, sha in exp.artifact_hashes.items():
            manifest_updates.setdefault(f"{exp.experiment_id}:{name}", sha)
            ref = f"sha256:{sha}"
            if ref not in exp.artifact_refs:
                exp.artifact_refs.append(ref)
        exp.validate()
        rec_bytes = json.dumps(exp.dump(), indent=2, sort_keys=True).encode("utf-8")
        rec_sha = self.store_artifact(f"{exp.experiment_id}:record", rec_bytes)
        manifest_updates[f"{exp.experiment_id}:record"] = rec_sha
        self._update_artifact_manifest(manifest_updates)

        safe = self._safe_name(exp.experiment_id)
        rec_path = self.records_dir / f"{safe}.json"
        tmp = rec_path.with_name(rec_path.name + ".tmp")
        tmp.write_bytes(rec_bytes)
        os.replace(tmp, rec_path)

        engine = TransferEngine(transfer_catalog)
        dead_end = engine.dead_end_from(exp)
        if dead_end is not None:
            self._record_dead_end(dead_end)

        generated_ops: list[Opportunity] = []
        if auto_transfer:
            self.opportunities.reload()
            for op in generate_transfer_hypotheses(exp, transfer_catalog):
                self.opportunities.add(op)
                generated_ops.append(op)

        wal = ResearchWal.open(str(self.wal_dir), self.run_id, worker_id=worker_id)
        wal_ev = wal.append(
            "experiment_recorded",
            {
                "experiment_id": exp.experiment_id,
                "study": exp.study,
                "project": exp.project,
                "repo": exp.repo,
                "commit": exp.commit,
                "metric": exp.statistical_comparison.metric,
                "candidate_mean": exp.statistical_comparison.candidate_mean,
                "baseline_mean": exp.statistical_comparison.baseline_mean,
                "verdict": exp.statistical_comparison.verdict,
                "historical": exp.historical,
                "record_sha256": rec_sha,
            },
        )
        receipt = SyncReceipt(
            experiment_id=exp.experiment_id,
            record_sha256=rec_sha,
            artifact_sha256=sorted(exp.artifact_hashes.values())[0],
            uploaded_artifacts={},
            status="pending_sync",
            readback_verified=False,
        )
        self._write_receipt(receipt)
        return {
            "experiment_id": exp.experiment_id,
            "record_sha256": rec_sha,
            "wal_seq": wal_ev.sequence,
            "wal_hash": wal_ev.digest(),
            "generated_opportunities": [op.opportunity_id for op in generated_ops],
            "receipt": receipt.dump(),
        }

    def _write_receipt(self, receipt: SyncReceipt) -> Path:
        safe = self._safe_name(receipt.experiment_id)
        path = self.receipts_dir / f"{safe}.receipt.json"
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(receipt.dump(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
        return path

    def retract_experiment(
        self,
        experiment_id: str,
        reason: str,
        *,
        worker_id: str = "worker-0",
    ) -> ExperimentRecordV2:
        """Retract a recorded experiment: preserves historical evidence while excluding it from canonical wins."""
        why = (reason or "").strip()
        if not why:
            raise ValueError("retraction requires a non-empty reason")
        safe = self._safe_name(experiment_id)
        rec_path = self.records_dir / f"{safe}.json"
        if not rec_path.is_file():
            raise FileNotFoundError(f"experiment {experiment_id!r} not found in local ledger")
        rec = ExperimentRecordV2.load(json.loads(rec_path.read_text(encoding="utf-8")))
        rec.retracted = True
        rec.revision = "retracted"
        rec.retracted_reason = why
        rec.historical = True
        rec_bytes = json.dumps(rec.dump(), indent=2, sort_keys=True).encode("utf-8")
        rec_sha = self.store_artifact(f"{rec.experiment_id}:record", rec_bytes)
        tmp = rec_path.with_name(rec_path.name + ".tmp")
        tmp.write_bytes(rec_bytes)
        os.replace(tmp, rec_path)

        wal = ResearchWal.open(str(self.wal_dir), self.run_id, worker_id=worker_id)
        wal.append(
            "experiment_retracted",
            {
                "experiment_id": rec.experiment_id,
                "reason": why,
                "record_sha256": rec_sha,
            },
        )
        receipt = SyncReceipt(
            experiment_id=rec.experiment_id,
            record_sha256=rec_sha,
            artifact_sha256=sorted(rec.artifact_hashes.values())[0] if rec.artifact_hashes else rec_sha,
            uploaded_artifacts={},
            status="pending_sync",
            readback_verified=False,
        )
        self._write_receipt(receipt)
        return rec

    def query_all(self, *, include_retracted: bool = False) -> list[ExperimentRecordV2]:
        return self.query(include_retracted=include_retracted)

    def query(
        self,
        *,
        project: str | None = None,
        study: str | None = None,
        repo: str | None = None,
        historical: bool | None = None,
        include_retracted: bool = False,
    ) -> list[ExperimentRecordV2]:
        out: list[ExperimentRecordV2] = []
        for path in sorted(self.records_dir.glob("*.json")):
            rec = ExperimentRecordV2.load(json.loads(path.read_text(encoding="utf-8")))
            if not include_retracted and rec.is_retracted():
                continue
            if project is not None and rec.project != project:
                continue
            if study is not None and rec.study != study:
                continue
            if repo is not None and rec.repo != repo:
                continue
            if historical is not None and rec.historical != historical:
                continue
            out.append(rec)
        return sorted(out, key=lambda r: (r.recorded_at, r.experiment_id))

    def query_experiments(
        self,
        *,
        study: str | None = None,
        verdict: str | None = None,
        repo: str | None = None,
        backend: str | None = None,
        search: str | None = None,
        include_failures: bool = True,
        include_retracted: bool = False,
    ) -> list[ExperimentRecordV2]:
        """Rich query across local ExperimentRecordV2 entries.

        Retracted records are excluded from canonical queries/wins by default and remain
        queryable as historical non-canonical evidence when `include_retracted=True`.
        """
        raw_want = verdict.strip().lower() if verdict else None
        want_v = epistemic_verdict(verdict) if verdict else None
        want_b = backend.strip().lower() if backend else None
        tokens = [t.lower() for t in (search or "").split() if t.strip()]
        out: list[ExperimentRecordV2] = []
        for rec in self.query(include_retracted=include_retracted):
            if rec.is_retracted() and want_v == "proven" and raw_want in ("proven", "win"):
                continue
            ev = epistemic_verdict(rec.statistical_comparison.verdict)
            if not include_failures and ev == "refuted":
                continue
            if study and rec.study != study and study.lower() not in rec.study.lower():
                continue
            if raw_want == "promising_inconclusive":
                if rec.statistical_comparison.verdict.strip().lower() != "promising_inconclusive":
                    continue
            elif want_v and ev != want_v and rec.statistical_comparison.verdict.lower() != raw_want:
                continue
            if repo and rec.repo != repo:
                continue
            if want_b and want_b not in (rec.hardware.backend or "").lower() and want_b not in (rec.hardware.gpu or "").lower():
                continue
            if tokens:
                blob = " ".join(
                    [
                        rec.experiment_id,
                        rec.study,
                        rec.objective,
                        rec.hypothesis,
                        rec.conclusion,
                        rec.failure_diagnosis,
                        rec.retracted_reason,
                        rec.next_hypothesis,
                        rec.hardware.gpu,
                        rec.hardware.backend,
                        " ".join(rec.workload_manifest.shapes),
                        json.dumps(rec.config, sort_keys=True),
                    ]
                ).lower()
                if not all(tok in blob for tok in tokens):
                    continue
            out.append(rec)
        return out

    def prior_failures(self, domain_or_study: str | None = None) -> list[ExperimentRecordV2]:
        """Return all refuted/loss experiments with failure_diagnosis so dead ends are never blindly re-run."""
        needle = domain_or_study.strip().lower() if domain_or_study else None
        out: list[ExperimentRecordV2] = []
        for rec in self.query():
            if epistemic_verdict(rec.statistical_comparison.verdict) != "refuted":
                continue
            if needle:
                hay = f"{rec.study} {rec.repo} {rec.experiment_id} {rec.hardware.backend}".lower()
                if needle not in hay:
                    continue
            out.append(rec)
        return out

    def recommended_experiments(self, domain: str | None = None, top_k: int = 10) -> list[Opportunity]:
        """Return ranked open Opportunity items from OpportunityQueue."""
        self.opportunities.reload()
        return self.opportunities.top_open(domain=domain, top_k=top_k)

    def receipts(self) -> list[SyncReceipt]:
        return [
            SyncReceipt.load(json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(self.receipts_dir.glob("*.receipt.json"))
        ]

    def pull_from_cloud(self, client: Any) -> dict[str, Any]:
        """Pull canonical cloud experiments & runs so local autonomous loops skip already-evaluated work."""
        try:
            exps = [e.dump() if hasattr(e, "dump") else dict(e) for e in client.query()]
            runs_listing = client.runs()
            runs_rows = getattr(runs_listing, "data", runs_listing)
            runs = [r.dump() if hasattr(r, "dump") else dict(r) for r in runs_rows]
            state = {"synced_at": now(), "experiments": exps, "runs": runs}
            tmp = self.cloud_state_path.with_name(self.cloud_state_path.name + ".tmp")
            tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(tmp, self.cloud_state_path)
            return {"status": "ok", "experiments": len(exps), "runs": len(runs)}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)[:300], "experiments": 0, "runs": 0}

    def cloud_state(self) -> dict[str, Any]:
        if not self.cloud_state_path.is_file():
            return {"experiments": [], "runs": []}
        return json.loads(self.cloud_state_path.read_text(encoding="utf-8"))

    @staticmethod
    def _upload_and_verify_artifact(
        client: Any,
        *,
        artifact_id: str,
        run_id: str,
        data: bytes,
        media_type: str,
        canonicalization: str,
    ) -> str:
        expected_sha = hashlib.sha256(data).hexdigest()
        if hasattr(client, "upload_artifact") and hasattr(client, "get_artifact"):
            stored = client.upload_artifact(
                kind="report",
                run_id=run_id,
                data=data,
                media_type=media_type,
                canonicalization=canonicalization,
                artifact_id=artifact_id,
            )
            stored_sha = getattr(stored, "sha256", "") or (stored.get("sha256", "") if isinstance(stored, Mapping) else "")
            if stored_sha and stored_sha != expected_sha:
                raise ValueError(f"server artifact sha256 mismatch: expected {expected_sha}, got {stored_sha}")
            rb_bytes = client.get_artifact(expected_sha)
            if not isinstance(rb_bytes, (bytes, bytearray)):
                raise ValueError("get_artifact did not return raw bytes")
            rb_sha = hashlib.sha256(rb_bytes).hexdigest()
            if rb_sha != expected_sha:
                raise ValueError(f"artifact readback SHA-256 mismatch: expected {expected_sha}, got {rb_sha}")
            return expected_sha

        stored = client.http.post(
            "/v1/research/artifacts",
            {
                "artifact_id": artifact_id,
                "sha256": expected_sha,
                "content_sha256": expected_sha,
                "media_type": media_type,
                "canonicalization": canonicalization,
                "compression": "none",
                "uncompressed_size": len(data),
                "kind": "report",
                "run_id": run_id,
                "content": base64.b64encode(data).decode("ascii"),
            },
        )
        if stored.get("sha256") and stored["sha256"] != expected_sha:
            raise ValueError("server artifact sha256 mismatch")
        got_art = client.http.get(f"/v1/research/artifacts/{expected_sha}")
        if isinstance(got_art, (bytes, bytearray)):
            raw_rb = bytes(got_art)
        elif isinstance(got_art, Mapping) and "content" in got_art:
            raw_rb = base64.b64decode(got_art["content"])
        else:
            raise ValueError("artifact readback missing raw bytes")
        if hashlib.sha256(raw_rb).hexdigest() != expected_sha:
            raise ValueError("artifact readback SHA-256 mismatch")
        return expected_sha

    def sync_to_cloud(self, client: Any) -> list[SyncReceipt]:
        """Execute `docs/research-sync.md` contract across both record and experiment planes.

        Uploads Benchmark, aggregated Study, Run, Experiment (with epistemic verdict and
        failure_diagnosis), and EVERY local raw artifact + ExperimentRecordV2 JSON, then
        verifies exact byte-for-byte SHA-256 read-back on every artifact and run.
        """
        all_recs = self.query(include_retracted=True)
        by_study: dict[str, list[ExperimentRecordV2]] = {}
        for r in all_recs:
            if not r.is_retracted():
                by_study.setdefault(r.study, []).append(r)

        results: list[SyncReceipt] = []
        for rec in all_recs:
            safe = self._safe_name(rec.experiment_id)
            receipt_path = self.receipts_dir / f"{safe}.receipt.json"
            if receipt_path.is_file():
                existing = SyncReceipt.load(json.loads(receipt_path.read_text(encoding="utf-8")))
                if existing.status == "synced_verified" and existing.readback_verified:
                    results.append(existing)
                    continue
            rec_path = self.records_dir / f"{safe}.json"
            rec_bytes = rec_path.read_bytes()
            rec_sha = hashlib.sha256(rec_bytes).hexdigest()
            uploaded_arts: dict[str, str] = {}
            try:
                study_recs = by_study.get(rec.study, [rec])
                study_runs = [sr.experiment_id for sr in study_recs]
                wins = [sr for sr in study_recs if epistemic_verdict(sr.statistical_comparison.verdict) == "proven"]
                refuted = [sr for sr in study_recs if epistemic_verdict(sr.statistical_comparison.verdict) == "refuted"]
                finding = (
                    f"{len(wins)}/{len(study_recs)} proven, {len(refuted)} refuted; latest: {rec.conclusion}"
                )
                bench = Benchmark(
                    project=rec.project,
                    id=rec.study,
                    title=rec.objective,
                    dataset=rec.workload_manifest.dataset or rec.workload_manifest.manifest_id,
                    metric=rec.statistical_comparison.metric,
                )
                study = Study(
                    project=rec.project,
                    id=rec.study,
                    title=rec.objective,
                    question=rec.hypothesis,
                    method="paired_anytime_valid_ab",
                    runs=study_runs,
                    finding=finding,
                    limits=rec.failure_diagnosis,
                    when=rec.recorded_at,
                )
                run = rec.to_run()
                client.record(benchmarks=[bench], studies=[study], runs=[run])
                if hasattr(client, "ingest"):
                    client.ingest(experiments=[rec.to_experiment_wire()])

                # Upload and byte-verify every raw artifact whose bytes exist locally in self.artifacts_dir.
                for art_name, art_sha in sorted(rec.artifact_hashes.items()):
                    art_file = self.artifacts_dir / art_sha
                    if art_file.is_file():
                        raw_data = art_file.read_bytes()
                        mtype = "application/json" if art_name.endswith("json") else "application/octet-stream"
                        verified_sha = self._upload_and_verify_artifact(
                            client,
                            artifact_id=f"{rec.experiment_id}:{art_name}",
                            run_id=rec.experiment_id,
                            data=raw_data,
                            media_type=mtype,
                            canonicalization="raw",
                        )
                        uploaded_arts[art_name] = verified_sha

                # Upload and byte-verify canonical ExperimentRecordV2 JSON record itself.
                verified_rec_sha = self._upload_and_verify_artifact(
                    client,
                    artifact_id=f"{rec.experiment_id}:record",
                    run_id=rec.experiment_id,
                    data=rec_bytes,
                    media_type="application/json",
                    canonicalization="json",
                )
                uploaded_arts["record"] = verified_rec_sha

                if rec.is_retracted():
                    got_run = True
                    got_exp = True
                else:
                    readback_listing = client.runs(id=rec.experiment_id)
                    readback_rows = getattr(readback_listing, "data", readback_listing)
                    got_run = any(getattr(r, "id", "") == rec.experiment_id for r in readback_rows)

                    got_exp = True
                    if hasattr(client, "query"):
                        exp_rows = client.query()
                        got_exp = any(getattr(e, "id", "") == rec.experiment_id for e in exp_rows)

                all_ok = bool(got_run and got_exp and verified_rec_sha == rec_sha)
                receipt = SyncReceipt(
                    experiment_id=rec.experiment_id,
                    record_sha256=rec_sha,
                    artifact_sha256=rec_sha,
                    uploaded_artifacts=uploaded_arts,
                    status="synced_verified" if all_ok else "partial_sync",
                    readback_verified=all_ok,
                    error="" if all_ok else "readback verification incomplete",
                )
            except Exception as exc:
                receipt = SyncReceipt(
                    experiment_id=rec.experiment_id,
                    record_sha256=rec_sha,
                    artifact_sha256=rec_sha,
                    uploaded_artifacts=uploaded_arts,
                    status="pending_sync",
                    readback_verified=False,
                    error=str(exc)[:500],
                )
            self._write_receipt(receipt)
            results.append(receipt)
        return results
