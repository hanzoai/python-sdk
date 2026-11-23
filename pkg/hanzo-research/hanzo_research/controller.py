"""Domain-agnostic autonomous research controller promoted from Kai PR #19.

Drives self-improving R&D across `hanzoai/ml`, `hanzoai/engine`, and `hanzo-inc/kai`:
- Objective and search-space registry with protected winners/baselines,
- UCB1 + forced-coverage arm selection skipping refuted `(commit, backend, shape)` dead ends,
- Progressive anytime-valid A/B execution (`micro -> medium -> qualification`),
- Write-ahead sealed final-qualification exposure ledger (`ExposureLedger`),
- Non-blocking file-locked (`flock`) single-GPU mutual exclusion + `ResearchWal` crash recovery,
- Turnkey `tick` and `loop` modes syncing canonical state and enqueuing 4-axis follow-ups.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Any, Iterator, Mapping, Sequence

from . import canonical, provenance
from .client import Research
from .lease import CloudLeaseManager, LeaseLostError
from .protocol import (
    CorrectnessChecks,
    ExperimentRecordV2,
    HardwareSpec,
    LocalResearchLedger,
    Opportunity,
    StatisticalComparison,
    WorkloadManifest,
    epistemic_verdict,
)
from .testing import (
    ProgressiveAbPlan,
    ProgressiveAbRunner,
    ProgressiveStage,
    ProgressiveStageOutput,
    impacted_benchmarks,
)
from .wal import ResearchWal
from .wire import Wire, now, token

__all__ = [
    "ObjectiveSpec",
    "SearchArm",
    "CampaignRegistry",
    "ExposureRecord",
    "ExposureLedger",
    "TrialSummary",
    "AutonomousController",
    "arm_candidates",
    "detect_host_backends",
    "gpu_lock",
    "execute_subprocess",
]


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _canon_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


@contextlib.contextmanager
def gpu_lock(state_dir: str | Path) -> Iterator[None]:
    """Acquire non-blocking exclusive GPU lock (`gpu.lock`) so benchmark runs never contend."""
    root = Path(state_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / "gpu.lock"
    with lock_path.open("w", encoding="utf-8") as fp:
        try:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("GPU campaign already has an active tick; refusing concurrent execution") from exc
        yield


def detect_host_backends() -> set[str]:
    """Detect available compute backends on this host without importing heavy frameworks."""
    override = os.environ.get("RESEARCH_HOST_BACKENDS", "").strip()
    if override:
        return {x.strip().upper() for x in override.split(",") if x.strip()}
    backends = {"CPU"}
    sysname = platform.system().lower()
    if sysname == "darwin":
        backends.add("METAL")
    if shutil.which("nvidia-smi") or Path("/dev/nvidia0").exists() or Path("/usr/local/cuda").exists():
        backends.add("CUDA")
    if shutil.which("rocminfo") or Path("/dev/kfd").exists() or Path("/opt/rocm").exists():
        backends.add("ROCM")
    if shutil.which("vulkaninfo") or Path("/usr/share/vulkan").exists() or Path("/etc/vulkan").exists():
        backends.add("VULKAN")
    return backends


def arm_candidates(
    arms: Sequence[tuple[str, str]],
    trials: Sequence[tuple[str, str, float | None, str | None]],
    cap: int,
    *,
    higher_is_better: bool = True,
    blocked_arms: set[tuple[str, str]] | None = None,
) -> list[tuple[float, int, str, str]]:
    """UCB1 + forced-coverage arm selection promoted from Kai PR #19.

    Unexplored arms receive `+inf` priority first; repeatedly failing arms are
    deprioritized; arms in `blocked_arms` (already refuted at the same commit,
    backend, and shape) are skipped completely.
    """
    if not arms:
        return []
    blocked = blocked_arms or set()
    counts: dict[tuple[str, str], int] = {(a, s): 0 for a, s in arms}
    failures: dict[tuple[str, str], int] = {(a, s): 0 for a, s in arms}
    best: dict[tuple[str, str], float] = {(a, s): -float("inf") for a, s in arms}
    for row in trials:
        arm, sup, dev = row[0], row[1], row[2]
        state = row[3] if len(row) > 3 else None
        if (arm, sup) in counts:
            counts[(arm, sup)] += 1
            if dev is not None and math.isfinite(float(dev)):
                signed = float(dev) if higher_is_better else -float(dev)
                best[(arm, sup)] = max(best[(arm, sup)], signed)
            elif state in ("failed", "blocked", "refuted", "loss"):
                failures[(arm, sup)] += 1
    total = sum(counts.values())
    if total >= cap:
        return []
    candidates: list[tuple[float, int, int, str, str]] = []
    for idx, (arm, sup) in enumerate(arms):
        if (arm, sup) in blocked:
            continue
        n = counts[(arm, sup)]
        f = failures[(arm, sup)]
        if n == 0:
            ucb = float("inf")
        elif best[(arm, sup)] == -float("inf"):
            ucb = -1e6 - f if f >= 2 else -1.0 + 0.05 * math.sqrt(math.log(total + 2) / n)
        else:
            ucb = best[(arm, sup)] + 0.12 * math.sqrt(math.log(total + 2) / n) - (0.25 if f >= 2 else 0.0)
        candidates.append((ucb, -n, -idx, arm, sup))
    candidates.sort(reverse=True)
    return [(ucb, neg_n, arm, sup) for ucb, neg_n, _, arm, sup in candidates]


def execute_subprocess(
    executor: str | Path,
    phase: str,
    request: Mapping[str, Any],
    state_dir: str | Path,
    timeout_minutes: int = 60,
    *,
    job_filename_prefix: str | None = None,
    on_pid: Any = None,
    on_heartbeat: Any = None,
) -> dict[str, Any]:
    """Fail-closed subprocess executor bridge (never invokes a shell, verifies trial identity)."""
    exec_path = Path(executor).expanduser().resolve()
    if not exec_path.is_file():
        return {"status": "failed", "reason": f"executor missing: {exec_path}"}
    state_root = Path(state_dir).expanduser().resolve()
    trial_id = str(request["trial_id"])
    job_dir = state_root / "jobs" / trial_id
    job_dir.mkdir(parents=True, exist_ok=True)
    prefix = job_filename_prefix or phase
    req_path = job_dir / f"{prefix}.request.json"
    out_path = job_dir / f"{prefix}.result.json"
    log_path = job_dir / f"{prefix}.log"
    _write_atomic(req_path, _canon_bytes(dict(request, phase=phase)))

    if phase == "development" and out_path.is_file():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            if (
                existing.get("trial_id") == trial_id
                and existing.get("task", existing.get("objective_id")) == request.get("task", request.get("objective_id"))
                and existing.get("status") == "complete"
            ):
                return existing
        except (OSError, ValueError):
            pass
    if phase in ("final", "qualification") and out_path.exists():
        return {"status": "failed", "reason": "sealed qualification output exists: manual reconciliation required"}

    out_path.unlink(missing_ok=True)
    cmd = (
        [sys.executable, str(exec_path)] if exec_path.suffix == ".py" else [str(exec_path)]
    ) + [phase, "--request", str(req_path), "--output", str(out_path)]
    deadline = time.monotonic() + max(1, int(timeout_minutes)) * 60.0
    rc = -1
    with log_path.open("ab") as log_fp:
        try:
            proc = subprocess.Popen(cmd, stdout=log_fp, stderr=subprocess.STDOUT)
        except OSError as exc:
            return {"status": "failed", "reason": str(exc)}
        if on_pid is not None:
            on_pid(proc.pid)
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    proc.kill()
                    proc.wait(timeout=10)
                    return {"status": "failed", "reason": f"{phase} exceeded {timeout_minutes}m"}
                try:
                    rc = proc.wait(timeout=min(15.0, remaining))
                    break
                except subprocess.TimeoutExpired:
                    if on_heartbeat is not None:
                        on_heartbeat()
        finally:
            if on_pid is not None:
                on_pid(None)
    if rc != 0 or not out_path.is_file():
        return {"status": "failed", "reason": f"{phase} executor exit={rc}; log={log_path}"}
    try:
        result = json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "failed", "reason": f"invalid JSON from executor: {out_path}"}
    expected_obj = request.get("task") or request.get("objective_id")
    got_obj = result.get("task") or result.get("objective_id")
    if result.get("trial_id") != trial_id or (expected_obj and got_obj != expected_obj):
        return {"status": "failed", "reason": "executor result identity mismatch"}
    return result


@dataclass
class ObjectiveSpec(Wire):
    id: str = ""
    study: str = ""
    objective: str = ""
    metric: str = "tok_per_sec"
    unit: str = "tok/s"
    direction: str = "higher"
    family: str = "default"
    protected: bool = False
    baseline: float | None = None
    reference_score: float | None = None
    backends: list[str] = field(default_factory=list)
    shapes: list[str] = field(default_factory=list)
    dataset: str = ""
    eval_sha: str = ""


@dataclass
class SearchArm(Wire):
    arm: str = ""
    variant: str = "default"
    hypothesis: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignRegistry(Wire):
    campaign: str = ""
    repo: str = ""
    objectives: list[ObjectiveSpec] = field(default_factory=list)
    search_space: dict[str, list[SearchArm]] = field(default_factory=dict)
    plan: ProgressiveAbPlan = field(default_factory=ProgressiveAbPlan)

    @classmethod
    def from_file(cls, path: str | Path) -> CampaignRegistry:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        # Support both `objectives` (ML/Engine) and `tasks` (Kai PR #19) schemas.
        if "objectives" not in raw and "tasks" in raw:
            converted_objs = []
            for t in raw["tasks"]:
                converted_objs.append(
                    {
                        "id": t["id"],
                        "study": t.get("study", t["id"]),
                        "objective": t.get("objective", f"Improve {t['id']} ({t['metric']})"),
                        "metric": t["metric"],
                        "unit": t.get("unit", ""),
                        "direction": t.get("direction", "higher"),
                        "family": t.get("family", "default"),
                        "protected": bool(t.get("protected", False)),
                        "baseline": t.get("baseline"),
                        "reference_score": t.get("jev_reference", t.get("reference_score")),
                        "backends": t.get("backends", []),
                        "shapes": t.get("shapes", []),
                        "dataset": t.get("dataset", t["id"]),
                        "eval_sha": t.get("eval_sha", ""),
                    }
                )
            converted_space: dict[str, list[dict[str, Any]]] = {}
            for fam, pairs in raw.get("search_space", {}).items():
                converted_space[fam] = [
                    (
                        {"arm": item[0], "variant": item[1]}
                        if isinstance(item, list) and len(item) >= 2
                        else dict(item)
                    )
                    for item in pairs
                ]
            raw = {
                "campaign": raw.get("campaign", "campaign"),
                "repo": raw.get("repo", ""),
                "objectives": converted_objs,
                "search_space": converted_space,
                "plan": raw.get("plan", ProgressiveAbPlan().dump()),
            }
        else:
            norm_space: dict[str, list[dict[str, Any]]] = {}
            for fam, items in raw.get("search_space", {}).items():
                norm_space[fam] = [
                    {"arm": item[0], "variant": item[1]} if isinstance(item, list) and len(item) >= 2 else dict(item)
                    for item in items
                ]
            raw = dict(raw, search_space=norm_space)
        reg = cls.load(raw)
        reg.validate()
        return reg

    def validate(self) -> None:
        if not self.campaign.strip():
            raise ValueError("CampaignRegistry requires non-empty campaign id")
        ids = [o.id for o in self.objectives]
        if len(ids) != len(set(ids)):
            raise ValueError("CampaignRegistry contains duplicate objective ids")
        for obj in self.objectives:
            if obj.direction not in ("higher", "lower"):
                raise ValueError(f"Unsupported direction {obj.direction!r} for {obj.id}")
            if not obj.protected and obj.family not in self.search_space:
                raise ValueError(f"Objective {obj.id} references unknown search_space family {obj.family!r}")


@dataclass
class ExposureRecord(Wire):
    objective_id: str = ""
    eval_sha: str = ""
    candidate_sha: str = ""
    trial_id: str = ""
    exposed_at: str = field(default_factory=now)


class ExposureLedger:
    """Write-ahead sealed final-qualification exposure guard."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.records: dict[tuple[str, str], ExposureRecord] = {}
        self.reload()

    def reload(self) -> None:
        self.records.clear()
        if self.path.is_file():
            rows = json.loads(self.path.read_text(encoding="utf-8"))
            for row in rows:
                rec = ExposureRecord.load(row)
                self.records[(rec.objective_id, rec.eval_sha)] = rec

    def is_exposed(self, objective_id: str, eval_sha: str) -> bool:
        self.reload()
        return (objective_id, eval_sha) in self.records

    def record_exposure(self, objective_id: str, eval_sha: str, candidate_sha: str, trial_id: str) -> ExposureRecord:
        if not eval_sha or len(eval_sha) < 8:
            raise ValueError("sealed qualification requires immutable eval_sha")
        self.reload()
        if (objective_id, eval_sha) in self.records:
            raise RuntimeError(f"sealed qualification for {objective_id} ({eval_sha[:12]}) already exposed")
        rec = ExposureRecord(
            objective_id=objective_id,
            eval_sha=eval_sha,
            candidate_sha=candidate_sha,
            trial_id=trial_id,
            exposed_at=now(),
        )
        self.records[(objective_id, eval_sha)] = rec
        rows = sorted((r.dump() for r in self.records.values()), key=lambda x: (x["objective_id"], x["eval_sha"]))
        _write_atomic(self.path, (json.dumps(rows, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        return rec


@dataclass
class TrialSummary(Wire):
    trial_id: str = ""
    objective_id: str = ""
    arm: str = ""
    variant: str = ""
    commit: str = ""
    backend: str = ""
    shapes: list[str] = field(default_factory=list)
    state: str = "running"
    phase: str = "micro"
    score: float | None = None
    verdict: str = "inconclusive"
    opportunity_id: str = ""
    started_at: str = field(default_factory=_utc_iso)
    finished_at: str = ""
    message: str = ""


class AutonomousController:
    """Turnkey autonomous experiment controller for ML, Engine, and Kai."""

    def __init__(
        self,
        ledger_dir: str | Path,
        *,
        state_dir: str | Path | None = None,
        registry: CampaignRegistry | None = None,
        repo_dir: str | Path = ".",
        max_trials_per_objective: int = 64,
        worker_id: str | None = None,
    ):
        self.ledger = LocalResearchLedger(ledger_dir)
        self.state_dir = Path(state_dir or (self.ledger.root / "controller")).expanduser().resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.trials_path = self.state_dir / "trials.json"
        self.checkpoints_dir = self.state_dir / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.exposures = ExposureLedger(self.state_dir / "exposures.json")
        self.registry = registry
        self.repo_dir = str(Path(repo_dir).expanduser().resolve())
        self.max_trials_per_objective = max_trials_per_objective
        self.worker_id = worker_id or f"{platform.node() or 'host'}-{os.getpid()}"

    def trials(self) -> list[TrialSummary]:
        if not self.trials_path.is_file():
            return []
        rows = json.loads(self.trials_path.read_text(encoding="utf-8"))
        return [TrialSummary.load(r) for r in rows]

    def _save_trial(self, trial: TrialSummary) -> None:
        by_id = {t.trial_id: t for t in self.trials()}
        by_id[trial.trial_id] = trial
        rows = sorted((t.dump() for t in by_id.values()), key=lambda r: (r["started_at"], r["trial_id"]))
        _write_atomic(self.trials_path, (json.dumps(rows, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    def _wal_emit(self, event_type: str, payload: Mapping[str, Any]) -> None:
        wal = ResearchWal.open(str(self.ledger.wal_dir), self.ledger.run_id)
        wal.append(event_type, dict(payload))

    def _refuted_signatures(self) -> set[tuple[str, str, str, str]]:
        """Collect `(study_or_obj, arm_or_id, commit_prefix, backend)` already refuted locally or in cloud."""
        sigs: set[tuple[str, str, str, str]] = set()
        for rec in self.ledger.prior_failures():
            arm = str(rec.config.get("arm", rec.experiment_id))
            var = str(rec.config.get("variant", ""))
            key_arm = f"{arm}:{var}" if var else arm
            sigs.add((rec.study, key_arm, rec.commit[:12], (rec.hardware.backend or "CPU").upper()))
        for t in self.trials():
            if t.state in ("refuted", "failed", "blocked") or t.verdict in ("refuted", "loss"):
                sigs.add((t.objective_id, f"{t.arm}:{t.variant}", t.commit[:12], (t.backend or "CPU").upper()))
        cstate = self.ledger.cloud_state()
        for exp in cstate.get("experiments", []):
            meta = exp.get("meta") if isinstance(exp.get("meta"), Mapping) else {}
            if epistemic_verdict(str(meta.get("verdict") or "")) == "refuted":
                study = str(meta.get("study") or exp.get("task") or "")
                backend = str(meta.get("backend") or "CPU").upper()
                git_sha = str(exp.get("git_sha") or "")[:12]
                sigs.add((study, str(exp.get("id") or ""), git_sha, backend))
        return sigs

    def _already_completed_ids(self) -> set[str]:
        done = {r.experiment_id for r in self.ledger.query()}
        for exp in self.ledger.cloud_state().get("experiments", []):
            if exp.get("status") == "complete" and exp.get("id"):
                done.add(str(exp["id"]))
        return done

    def _backend_compatible(self, required_backends: Sequence[str], host_backends: set[str]) -> bool:
        if not required_backends:
            return True
        for b in required_backends:
            prefix = b.split("-")[0].strip().upper()
            if prefix in host_backends:
                return True
        return False

    def status(self) -> dict[str, Any]:
        trials = self.trials()
        recs = self.ledger.query()
        open_ops = self.ledger.recommended_experiments(top_k=50)
        wins = [r for r in recs if epistemic_verdict(r.statistical_comparison.verdict) == "proven"]
        failures = [r for r in recs if epistemic_verdict(r.statistical_comparison.verdict) == "refuted"]
        return {
            "campaign": self.registry.campaign if self.registry else self.ledger.run_id,
            "host_backends": sorted(detect_host_backends()),
            "total_experiments": len(recs),
            "proven_experiments": len(wins),
            "refuted_experiments": len(failures),
            "open_opportunities": len(open_ops),
            "top_opportunities": [dict(op.dump(), priority_score=op.priority_score) for op in open_ops[:5]],
            "exposures_count": len(self.exposures.records),
            "trials_count": len(trials),
        }

    def select_next_work(
        self,
        *,
        impacted_ids: set[str] | None = None,
        host_backends: set[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select highest-priority eligible work from OpportunityQueue or CampaignRegistry."""
        backends = host_backends or detect_host_backends()
        git_info = provenance.git_state(self.repo_dir)
        commit_full = git_info.get("git_sha") or "0" * 40
        commit12 = commit_full[:12]
        refuted_sigs = self._refuted_signatures()
        completed_ids = self._already_completed_ids()

        # 1. Check open OpportunityQueue items matching campaign/host/impact scope.
        for op in self.ledger.recommended_experiments(top_k=100):
            if impacted_ids is not None and op.domain not in impacted_ids and op.objective not in impacted_ids:
                continue
            target_backend = ""
            if "->backend:" in op.opportunity_id:
                target_backend = op.opportunity_id.split("->backend:", 1)[1]
                if not self._backend_compatible([target_backend], backends):
                    continue
            chosen_backend = (
                target_backend.split("-")[0].upper()
                if target_backend
                else next((b for b in ("CUDA", "ROCM", "VULKAN", "METAL", "CPU") if b in backends), "CPU")
            )
            if (op.domain, op.opportunity_id, commit12, chosen_backend) in refuted_sigs:
                continue
            # If registry exists, bind opportunity to matching objective spec if present.
            matched_obj = None
            if self.registry:
                matched_obj = next(
                    (o for o in self.registry.objectives if o.id == op.domain or o.study == op.domain),
                    None,
                )
                if matched_obj is None:
                    continue
            exp_id = f"{op.domain}:opp:{_sha256(op.opportunity_id.encode('utf-8'))[:10]}:{commit12}"
            if exp_id in completed_ids:
                self.ledger.opportunities.mark_status(op.opportunity_id, "completed")
                continue
            return {
                "source": "opportunity",
                "opportunity": op,
                "objective": matched_obj
                or ObjectiveSpec(
                    id=op.domain,
                    study=op.domain,
                    objective=op.objective,
                    metric="throughput",
                    unit="tok/s",
                    direction="higher",
                    dataset=op.domain,
                ),
                "arm": SearchArm(
                    arm="opportunity_transfer",
                    variant=op.opportunity_id,
                    hypothesis=op.proposed_approach,
                    config={"opportunity_id": op.opportunity_id, "trigger_rule": op.trigger_rule},
                ),
                "backend": chosen_backend,
                "commit": commit_full,
                "branch": git_info.get("git_branch") or "main",
                "experiment_id": exp_id,
            }

        # 2. Otherwise select from CampaignRegistry via UCB1 + forced coverage.
        if not self.registry:
            return None

        trials = self.trials()
        options: list[tuple[tuple[int, str], dict[str, Any]]] = []
        for obj in self.registry.objectives:
            if obj.protected:
                continue
            if impacted_ids is not None and obj.id not in impacted_ids and obj.study not in impacted_ids:
                continue
            if not self._backend_compatible(obj.backends, backends):
                continue
            chosen_backend = next(
                (
                    b.split("-")[0].upper()
                    for b in (obj.backends or ["CUDA", "ROCM", "VULKAN", "METAL", "CPU"])
                    if b.split("-")[0].upper() in backends
                ),
                "CPU",
            )
            # Skip objectives already qualified/proven at current commit & backend.
            already_won = any(
                t.objective_id == obj.id
                and t.state == "qualified"
                and t.verdict == "proven"
                and t.backend.upper() == chosen_backend
                for t in trials
            )
            if already_won:
                continue
            arms_list = self.registry.search_space.get(obj.family, [])
            arm_pairs = [(a.arm, a.variant) for a in arms_list]
            seen_rows = [
                (t.arm, t.variant, t.score, t.state)
                for t in trials
                if t.objective_id == obj.id
            ]
            blocked = {
                (a, v)
                for a, v in arm_pairs
                if (obj.id, f"{a}:{v}", commit12, chosen_backend) in refuted_sigs
                or (obj.study or obj.id, f"{a}:{v}", commit12, chosen_backend) in refuted_sigs
                or f"{obj.id}:{a}:{v}:{commit12}" in completed_ids
            }
            ranked = arm_candidates(
                arm_pairs,
                seen_rows,
                self.max_trials_per_objective,
                higher_is_better=(obj.direction == "higher"),
                blocked_arms=blocked,
            )
            if not ranked:
                continue
            _, _, best_arm_name, best_var = ranked[0]
            arm_spec = next(a for a in arms_list if a.arm == best_arm_name and a.variant == best_var)
            exp_id = f"{obj.id}:{arm_spec.arm}:{arm_spec.variant}:{commit12}"
            options.append(
                (
                    (len(seen_rows), obj.id),
                    {
                        "source": "registry",
                        "opportunity": None,
                        "objective": obj,
                        "arm": arm_spec,
                        "backend": chosen_backend,
                        "commit": commit_full,
                        "branch": git_info.get("git_branch") or "main",
                        "experiment_id": exp_id,
                    },
                )
            )
        if not options:
            return None
        options.sort(key=lambda item: item[0])
        return options[0][1]

    def tick(
        self,
        executor: str | Path,
        *,
        changed_paths: Sequence[str] | None = None,
        lineage: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
        changed_artifacts: Sequence[str] | None = None,
        timeout_minutes: int = 30,
        auto_sync: bool = True,
        client: Research | None = None,
        lease_ttl_sec: int = 600,
        via_tasks: bool = False,
        remote_target: str | None = None,
        poll_interval_sec: float = 1.0,
    ) -> dict[str, Any]:
        """Run one full autonomous research cycle: pull -> lease -> progressive A/B -> WAL -> transfer -> sync."""
        use_tasks = bool(via_tasks or (remote_target and remote_target.strip()))
        resolved_target = (remote_target or "").strip() or ("any" if use_tasks else "")

        # Step 1: Recover interrupted trials in state_dir before starting new work.
        for t in self.trials():
            if t.state == "running":
                if t.phase == "qualification":
                    t.state = "blocked"
                    t.finished_at = _utc_iso()
                    t.message = "interrupted during sealed qualification; manual reconciliation required"
                    self._save_trial(t)
                    self._wal_emit("trial_blocked", {"trial_id": t.trial_id, "objective_id": t.objective_id})
                else:
                    t.state = "failed"
                    t.finished_at = _utc_iso()
                    t.message = "interrupted during screening; checkpoint retained for lease reclamation"
                    self._save_trial(t)

        # Step 2: Pull cloud state if credentials or an explicit client exist.
        active_client = client
        if active_client is None and (auto_sync or use_tasks):
            try:
                tok = token()
                if tok or use_tasks:
                    active_client = Research(api_key=tok or None, repo=self.repo_dir)
            except Exception:
                active_client = None
        if use_tasks and active_client is None:
            raise RuntimeError("remote hanzoai/tasks execution (--via-tasks / --remote-target) requires a Research client")
        if active_client is not None:
            self.ledger.pull_from_cloud(active_client)

        # Step 3: Dependency-scoped regression filter if changed_paths/artifacts provided.
        impacted_ids: set[str] | None = None
        if changed_paths is not None or changed_artifacts is not None:
            all_task_ids = (
                [o.id for o in self.registry.objectives]
                if self.registry
                else list((lineage or {}).keys())
            )
            scope = impacted_benchmarks(
                all_task_ids,
                changed_paths or [],
                lineage,
                changed_artifacts=changed_artifacts,
            )
            impacted_ids = set(scope["tasks"])
            if not impacted_ids:
                return {"status": "skipped_unimpacted", "impacted_tasks": []}

        # Step 4: Select highest-priority eligible work (matching remote linked machines when via_tasks is set).
        eligible_backends: set[str] | None = None
        if use_tasks and active_client is not None:
            try:
                machines = active_client.list_machines(only_online=True)
                if resolved_target and resolved_target.lower() != "any":
                    machines = [
                        m for m in machines if m.id == resolved_target or m.hostname == resolved_target
                    ]
                discovered = {b for m in machines for b in m.backends}
                eligible_backends = discovered or {"CUDA", "ROCM", "METAL", "VULKAN", "CPU"}
            except Exception:
                eligible_backends = {"CUDA", "ROCM", "METAL", "VULKAN", "CPU"}

        work = self.select_next_work(impacted_ids=impacted_ids, host_backends=eligible_backends)
        if work is None:
            return {"status": "idle", "reason": "no eligible open opportunities or unexplored campaign arms"}

        obj: ObjectiveSpec = work["objective"]
        arm: SearchArm = work["arm"]
        op: Opportunity | None = work["opportunity"]
        backend: str = work["backend"]
        commit: str = work["commit"]
        branch: str = work["branch"]
        exp_id: str = work["experiment_id"]
        campaign_name = self.registry.campaign if self.registry else self.ledger.run_id
        lease_target_id = op.opportunity_id if op is not None else exp_id

        # Step 5: Acquire cross-machine cloud lease with monotonic fencing token.
        lease_mgr = CloudLeaseManager(
            active_client,
            worker_id=self.worker_id,
            commit=commit[:12],
            local_dir=self.ledger.root,
        )
        lease_out = lease_mgr.acquire_lease(campaign_name, lease_target_id, ttl_sec=lease_ttl_sec)
        if lease_out.status != "acquired" or lease_out.lease is None:
            return {
                "status": "lease_busy",
                "holder_worker_id": lease_out.holder_worker_id,
                "fencing_token": lease_out.fencing_token,
                "expires_at_unix": lease_out.expires_at_unix,
            }
        active_lease = lease_out.lease
        final_lease_state = "released"

        plan = (
            ProgressiveAbPlan.load(self.registry.plan.dump())
            if self.registry
            else ProgressiveAbPlan()
        )
        plan.higher_is_better = obj.direction == "higher"

        trial_id = _sha256(_canon_bytes([exp_id, arm.arm, arm.variant, backend, active_lease.fencing_token]))[:20]
        ckpt_key = _sha256(_canon_bytes([exp_id, arm.arm, arm.variant, backend]))[:24]
        ckpt_path = self.checkpoints_dir / f"{ckpt_key}.looks.json"
        trial = TrialSummary(
            trial_id=trial_id,
            objective_id=obj.id,
            arm=arm.arm,
            variant=arm.variant,
            commit=commit,
            backend=backend,
            shapes=list(obj.shapes),
            state="running",
            phase="micro",
            opportunity_id=op.opportunity_id if op else "",
        )

        # Step 6: Acquire exclusive non-blocking GPU lock and run progressive anytime-valid A/B plan.
        try:
            with gpu_lock(self.state_dir):
                self._save_trial(trial)
                self._wal_emit(
                    "trial_started",
                    {
                        "trial_id": trial_id,
                        "experiment_id": exp_id,
                        "objective_id": obj.id,
                        "arm": arm.arm,
                        "variant": arm.variant,
                        "backend": backend,
                        "commit": commit,
                        "fencing_token": active_lease.fencing_token,
                        "reclaimed_from": active_lease.reclaimed_from,
                    },
                )
                stage_artifacts: dict[str, bytes] = {}
                exec_failed_reason = ""

                def measure_stage(stage_idx: int, stage: ProgressiveStage) -> ProgressiveStageOutput:
                    nonlocal exec_failed_reason, active_lease
                    is_final = stage_idx == len(plan.stages)
                    eval_sha = obj.eval_sha or _sha256(
                        _canon_bytes({"objective": obj.id, "stage": stage.name, "dataset": obj.dataset or obj.id})
                    )
                    candidate_sha = _sha256(_canon_bytes({"commit": commit, "arm": arm.arm, "variant": arm.variant}))
                    # Renew / verify fencing token before every live stage and sealed qualification!
                    active_lease = lease_mgr.renew_lease(active_lease, ttl_sec=lease_ttl_sec)
                    if is_final:
                        lease_mgr.verify_fencing(active_lease)
                        if self.exposures.is_exposed(obj.id, f"{eval_sha}:{candidate_sha[:16]}"):
                            exec_failed_reason = "sealed qualification already exposed for candidate"
                            return ProgressiveStageOutput(
                                stage_name=stage.name,
                                baseline_samples=[1.0, 1.0],
                                candidate_samples=[1.0, 1.0],
                                parity_passed=False,
                                memory_integrity_passed=True,
                                details=exec_failed_reason,
                            )
                        trial.phase = "qualification"
                        self._save_trial(trial)
                        self.exposures.record_exposure(
                            obj.id,
                            f"{eval_sha}:{candidate_sha[:16]}",
                            candidate_sha,
                            trial_id,
                        )
                    else:
                        trial.phase = stage.name
                        self._save_trial(trial)

                    req = {
                        "trial_id": trial_id,
                        "experiment_id": exp_id,
                        "campaign": campaign_name,
                        "objective_id": obj.id,
                        "study": obj.study or obj.id,
                        "metric": obj.metric,
                        "unit": obj.unit,
                        "direction": obj.direction,
                        "arm": arm.arm,
                        "variant": arm.variant,
                        "config": arm.config,
                        "backend": backend,
                        "shapes": obj.shapes,
                        "stage_index": stage_idx,
                        "stage_name": stage.name,
                        "reps": stage.reps,
                        "prompt_len": stage.prompt_len,
                        "gen_len": stage.gen_len,
                        "commit": commit,
                        "eval_sha": eval_sha,
                        "candidate_sha": candidate_sha,
                        "fencing_token": active_lease.fencing_token,
                    }
                    if use_tasks and active_client is not None:
                        dispatched = active_client.dispatch_task(
                            dict(req, executor=str(executor), phase="stage"),
                            target=resolved_target,
                            activity_type="research.bench",
                            when_idle_only=True,
                            required_backend=backend,
                            job_id=f"trial-{trial_id}-s{stage_idx}-{stage.name}",
                        )
                        completed = active_client.wait_gpu_job(
                            str(dispatched["id"]),
                            run_id=str(dispatched.get("runId") or dispatched["id"]),
                            timeout_sec=max(1, int(timeout_minutes)) * 60.0,
                            poll_interval_sec=poll_interval_sec,
                        )
                        c_state = str(completed.get("status") or completed.get("state") or "")
                        raw_out = completed.get("result") or completed.get("output") or {}
                        if c_state == "ACTIVITY_TASK_STATE_COMPLETED" and isinstance(raw_out, Mapping):
                            res = dict(raw_out)
                            res.setdefault("status", "complete")
                        else:
                            res = {
                                "status": "failed",
                                "reason": str(
                                    completed.get("failureCause")
                                    or (raw_out.get("reason") if isinstance(raw_out, Mapping) else "")
                                    or f"remote task ended with {c_state}"
                                ),
                            }
                    else:
                        res = execute_subprocess(
                            executor,
                            "stage",
                            req,
                            self.state_dir,
                            timeout_minutes=timeout_minutes,
                            job_filename_prefix=f"stage_{stage_idx}_{stage.name}",
                        )
                    stage_artifacts[f"stage_{stage_idx}_{stage.name}_json"] = (
                        json.dumps(res, indent=2, sort_keys=True) + "\n"
                    ).encode("utf-8")
                    if res.get("status") != "complete":
                        exec_failed_reason = str(res.get("reason", "stage execution failed"))
                        return ProgressiveStageOutput(
                            stage_name=stage.name,
                            baseline_samples=[1.0, 1.0],
                            candidate_samples=[1.0, 1.0],
                            parity_passed=False,
                            memory_integrity_passed=False,
                            details=exec_failed_reason,
                        )
                    return ProgressiveStageOutput(
                        stage_name=stage.name,
                        baseline_samples=[float(x) for x in res["baseline_samples"]],
                        candidate_samples=[float(x) for x in res["candidate_samples"]],
                        parity_passed=bool(res.get("parity_passed", True)),
                        memory_integrity_passed=bool(res.get("memory_integrity_passed", True)),
                        max_abs_diff=res.get("max_abs_diff"),
                        ulp_diff=res.get("ulp_diff"),
                        gpu_time_sec=float(res.get("gpu_time_sec", 0.0)),
                        details=str(res.get("details", "")),
                    )

                host_info = provenance.host()
                template = ExperimentRecordV2(
                    project="default",
                    study=obj.study or obj.id,
                    objective=obj.objective or f"Optimize {obj.id} ({obj.metric})",
                    hypothesis=arm.hypothesis or f"{arm.arm}/{arm.variant} improves {obj.metric} on {obj.id}",
                    experiment_id=exp_id,
                    parent_experiment=f"{obj.id}:baseline",
                    prior_best=obj.baseline,
                    repo=(self.registry.repo if self.registry and self.registry.repo else "hanzoai/research"),
                    commit=commit,
                    branch=branch,
                    hardware=HardwareSpec(
                        host=str(host_info.get("hostname", "")),
                        architecture=platform.machine(),
                        gpu=os.environ.get("RESEARCH_GPU_MODEL", backend),
                        backend=backend,
                        precision=str(arm.config.get("precision", "BF16")),
                    ),
                    config=dict(
                        arm.config,
                        arm=arm.arm,
                        variant=arm.variant,
                        fencing_token=active_lease.fencing_token,
                    ),
                    workload_manifest=WorkloadManifest(
                        manifest_id=f"{obj.id}:{arm.arm}:{arm.variant}",
                        dataset=obj.dataset or obj.id,
                        split="progressive-ab",
                        shapes=list(obj.shapes) or ["default"],
                        input_lengths=[s.prompt_len for s in plan.stages],
                        batch_size=1,
                        seed=17,
                    ),
                    statistical_comparison=StatisticalComparison(
                        metric=obj.metric,
                        unit=obj.unit,
                        higher_is_better=(obj.direction == "higher"),
                    ),
                    correctness=CorrectnessChecks(),
                    next_hypothesis=str(arm.config.get("next_hypothesis", "")),
                )

                runner = ProgressiveAbRunner(plan)
                try:
                    ab_res, recorded_exp, rec_meta = runner.run_and_record(
                        self.ledger,
                        template,
                        measure_stage,
                        extra_artifacts=stage_artifacts,
                        checkpoint_path=ckpt_path,
                    )
                except LeaseLostError as lease_exc:
                    trial.state = "fenced"
                    trial.finished_at = _utc_iso()
                    trial.message = str(lease_exc)
                    self._save_trial(trial)
                    return {"status": "fenced", "trial_id": trial_id, "reason": str(lease_exc)}

                if exec_failed_reason and not ab_res.looks:
                    trial.state = "failed"
                    trial.verdict = "inconclusive"
                    trial.finished_at = _utc_iso()
                    trial.message = exec_failed_reason
                    self._save_trial(trial)
                    return {
                        "status": "failed",
                        "trial_id": trial_id,
                        "experiment_id": exp_id,
                        "reason": exec_failed_reason,
                    }

                ev = epistemic_verdict(ab_res.verdict)
                trial.state = "qualified" if ev == "proven" else ("refuted" if ev == "refuted" else "explored")
                trial.verdict = ev
                trial.score = recorded_exp.statistical_comparison.candidate_mean
                trial.finished_at = _utc_iso()
                trial.message = ab_res.failure_diagnosis or recorded_exp.conclusion
                self._save_trial(trial)
                final_lease_state = "completed"

                if op is not None:
                    self.ledger.opportunities.mark_status(
                        op.opportunity_id,
                        "completed" if ev == "proven" else ("refuted" if ev == "refuted" else "explored"),
                    )

                sync_receipts = []
                if active_client is not None and auto_sync:
                    sync_receipts = [rc.dump() for rc in self.ledger.sync_to_cloud(active_client)]

                return {
                    "status": trial.state,
                    "trial_id": trial_id,
                    "experiment_id": exp_id,
                    "verdict": ev,
                    "fencing_token": active_lease.fencing_token,
                    "reclaimed_from": active_lease.reclaimed_from,
                    "stopped_stage": ab_res.stopped_stage,
                    "early_stopped": ab_res.early_stopped,
                    "candidate_mean": recorded_exp.statistical_comparison.candidate_mean,
                    "baseline_mean": recorded_exp.statistical_comparison.baseline_mean,
                    "generated_opportunities": rec_meta["generated_opportunities"],
                    "sync_receipts": sync_receipts,
                }
        finally:
            try:
                lease_mgr.release_lease(active_lease, final_state=final_lease_state)
            except Exception:
                pass

    def loop(
        self,
        executor: str | Path,
        *,
        max_ticks: int = 10,
        budget_minutes: float = 60.0,
        idle_exit: bool = True,
        sleep_seconds: float = 0.0,
        changed_paths: Sequence[str] | None = None,
        lineage: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
        changed_artifacts: Sequence[str] | None = None,
        auto_sync: bool = True,
        client: Research | None = None,
        via_tasks: bool = False,
        remote_target: str | None = None,
        poll_interval_sec: float = 1.0,
    ) -> dict[str, Any]:
        """Run autonomous `tick` cycles continuously until budget, tick cap, or queue exhaustion."""
        deadline = time.monotonic() + max(0.1, float(budget_minutes)) * 60.0
        ticks_run = 0
        outcomes: list[dict[str, Any]] = []
        stop_reason = "completed"
        while True:
            if max_ticks > 0 and ticks_run >= max_ticks:
                stop_reason = "max_ticks_reached"
                break
            if time.monotonic() >= deadline:
                stop_reason = "budget_exhausted"
                break
            rem_minutes = max(1, int(math.ceil((deadline - time.monotonic()) / 60.0)))
            res = self.tick(
                executor=executor,
                changed_paths=changed_paths,
                lineage=lineage,
                changed_artifacts=changed_artifacts,
                timeout_minutes=rem_minutes,
                auto_sync=auto_sync,
                client=client,
                via_tasks=via_tasks,
                remote_target=remote_target,
                poll_interval_sec=poll_interval_sec,
            )
            ticks_run += 1
            outcomes.append(res)
            if res["status"] in ("idle", "skipped_unimpacted") and idle_exit:
                stop_reason = res["status"]
                break
            if sleep_seconds > 0 and time.monotonic() < deadline:
                time.sleep(min(sleep_seconds, max(0.0, deadline - time.monotonic())))
        return {
            "ticks": ticks_run,
            "stop_reason": stop_reason,
            "outcomes": outcomes,
            "status_summary": self.status(),
        }
