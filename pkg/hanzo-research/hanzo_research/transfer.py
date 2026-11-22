"""Automatic 4-axis transfer hypothesis generator and dead-end registry.

Every proven experiment automatically proposes concrete, falsifiable follow-up
opportunities across model scale, sequence length, GPU backend, and workload
regime. Every refuted experiment records its failure diagnosis in the dead-end
registry and emits only targeted mechanism-fix hypotheses, never blind transfer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .wire import Wire, now

if TYPE_CHECKING:
    from .protocol import ExperimentRecordV2, Opportunity

__all__ = [
    "TransferCatalog",
    "DeadEndEntry",
    "TransferEngine",
    "generate_transfer_hypotheses",
]

DEFAULT_MODEL_SCALES = (
    "Zen-Nano-0.6B",
    "Bonsai-2-2B",
    "Bonsai-2-9B",
    "Bonsai-2-27B",
    "Qwen3.8-27B",
)

DEFAULT_SEQUENCE_LENGTHS = (512, 4096, 8192, 16384, 32768)

DEFAULT_BACKENDS = (
    "CUDA-GB10-sm121a",
    "Vulkan-Wave32",
    "Vulkan-Wave64",
    "ROCm-gfx1151",
    "Metal-M4Max",
)

DEFAULT_WORKLOAD_REGIMES = (
    "single-turn-decode",
    "multiturn-agent-prefix",
    "speculative-dflash2",
    "batched-serving",
)


@dataclass
class TransferCatalog(Wire):
    model_scales: list[str] = field(default_factory=lambda: list(DEFAULT_MODEL_SCALES))
    sequence_lengths: list[int] = field(default_factory=lambda: list(DEFAULT_SEQUENCE_LENGTHS))
    backends: list[str] = field(default_factory=lambda: list(DEFAULT_BACKENDS))
    workload_regimes: list[str] = field(default_factory=lambda: list(DEFAULT_WORKLOAD_REGIMES))


@dataclass
class DeadEndEntry(Wire):
    experiment_id: str = ""
    study: str = ""
    repo: str = ""
    commit: str = ""
    backend: str = ""
    shapes: list[str] = field(default_factory=list)
    failure_diagnosis: str = ""
    next_hypothesis: str = ""
    recorded_at: str = field(default_factory=now)


def _norm_verdict(verdict: str) -> str:
    v = verdict.strip().lower()
    if v in ("win", "proven"):
        return "proven"
    if v in ("loss", "refuted"):
        return "refuted"
    return "inconclusive"


def _relative_gain(exp: ExperimentRecordV2) -> float:
    sc = exp.statistical_comparison
    if sc.ratio is not None and sc.ratio > 0:
        gain = (sc.ratio - 1.0) if sc.higher_is_better else (1.0 / sc.ratio - 1.0)
        if gain > 0:
            return round(gain, 4)
    base = abs(sc.baseline_mean)
    if base > 1e-9:
        raw = (sc.candidate_mean - sc.baseline_mean) if sc.higher_is_better else (sc.baseline_mean - sc.candidate_mean)
        if raw > 0:
            return round(raw / base, 4)
    return 0.10


def _match_next_scale(exp: ExperimentRecordV2, scales: list[str]) -> str | None:
    haystack = " ".join(
        [exp.experiment_id, exp.study, exp.workload_manifest.dataset, exp.workload_manifest.manifest_id]
    ).lower()
    matched_idx = -1
    for idx, scale in enumerate(scales):
        tok = scale.lower()
        short = tok.split("-")[-1]
        if tok in haystack or (short.endswith("b") and short in haystack):
            matched_idx = idx
            break
    if 0 <= matched_idx + 1 < len(scales):
        return scales[matched_idx + 1]
    for scale in scales:
        if scale.lower() not in haystack:
            return scale
    return None


def _match_next_seq_len(exp: ExperimentRecordV2, lengths: list[int]) -> int | None:
    cur = max(exp.workload_manifest.input_lengths) if exp.workload_manifest.input_lengths else 512
    for length in sorted(lengths):
        if length > cur:
            return length
    return None


def _match_sibling_backends(exp: ExperimentRecordV2, backends: list[str]) -> list[str]:
    cur_b = (exp.hardware.backend or "").lower()
    cur_g = (exp.hardware.gpu or "").lower()
    out: list[str] = []
    for target in backends:
        tl = target.lower()
        prefix = tl.split("-")[0]
        if cur_b and prefix in cur_b:
            continue
        if cur_g and prefix in cur_g:
            continue
        out.append(target)
    return out[:2]


def _match_next_regime(exp: ExperimentRecordV2, regimes: list[str]) -> str | None:
    haystack = " ".join([exp.study, exp.workload_manifest.split, exp.experiment_id]).lower()
    for idx, reg in enumerate(regimes):
        if reg.lower() in haystack or reg.split("-")[0] in haystack:
            if idx + 1 < len(regimes):
                return regimes[idx + 1]
    for reg in regimes:
        if reg.lower() not in haystack:
            return reg
    return None


class TransferEngine:
    """Deterministic 4-axis discovery transfer and refutation mechanism-fix engine."""

    def __init__(self, catalog: TransferCatalog | None = None):
        self.catalog = catalog or TransferCatalog()

    def dead_end_from(self, exp: ExperimentRecordV2) -> DeadEndEntry | None:
        if _norm_verdict(exp.statistical_comparison.verdict) != "refuted":
            return None
        return DeadEndEntry(
            experiment_id=exp.experiment_id,
            study=exp.study,
            repo=exp.repo,
            commit=exp.commit,
            backend=exp.hardware.backend or "CPU",
            shapes=list(exp.workload_manifest.shapes),
            failure_diagnosis=exp.failure_diagnosis or exp.conclusion,
            next_hypothesis=exp.next_hypothesis,
            recorded_at=exp.recorded_at or now(),
        )

    def generate(self, exp: ExperimentRecordV2) -> list[Opportunity]:
        from .protocol import Opportunity

        verdict = _norm_verdict(exp.statistical_comparison.verdict)
        if verdict == "refuted":
            if not exp.next_hypothesis.strip():
                return []
            diag = exp.failure_diagnosis.strip() or exp.conclusion.strip()
            return [
                Opportunity(
                    opportunity_id=f"{exp.experiment_id}->mechanism-fix",
                    domain=exp.study,
                    objective=f"{exp.study}:mechanism-fix",
                    current_best=exp.statistical_comparison.baseline_mean,
                    proposed_approach=(
                        f"Refuted mechanism diagnosis: {diag}. "
                        f"Falsifiable fix hypothesis: {exp.next_hypothesis.strip()}"
                    ),
                    expected_improvement=0.12,
                    compute_cost=max(0.5, exp.gpu_time_sec / 60.0 if exp.gpu_time_sec > 0 else 1.0),
                    related_experiments=[exp.experiment_id],
                    trigger_rule=f"mechanism_fix_after_refutation:{exp.experiment_id}",
                    status="open",
                )
            ]

        if verdict != "proven":
            return []

        gain = _relative_gain(exp)
        base_cost = max(0.5, exp.gpu_time_sec / 60.0 if exp.gpu_time_sec > 0 else 1.0)
        ops: list[Opportunity] = []

        next_scale = _match_next_scale(exp, self.catalog.model_scales)
        if next_scale is not None:
            ops.append(
                Opportunity(
                    opportunity_id=f"{exp.experiment_id}->scale:{next_scale}",
                    domain=exp.study,
                    objective=f"{exp.study}@{next_scale}",
                    current_best=exp.statistical_comparison.candidate_mean,
                    proposed_approach=(
                        f"Test whether {exp.study} mechanism from {exp.experiment_id} preserves "
                        f">={gain * 0.75:.2f}x relative gain at model scale {next_scale} with parity_passed=true"
                    ),
                    expected_improvement=round(gain * 0.85, 4),
                    compute_cost=round(base_cost * 1.8, 4),
                    related_experiments=[exp.experiment_id],
                    trigger_rule=f"transfer:model_scale:{exp.experiment_id}",
                    status="open",
                )
            )

        next_seq = _match_next_seq_len(exp, self.catalog.sequence_lengths)
        if next_seq is not None:
            ops.append(
                Opportunity(
                    opportunity_id=f"{exp.experiment_id}->seq:{next_seq}",
                    domain=exp.study,
                    objective=f"{exp.study}@seq{next_seq}",
                    current_best=exp.statistical_comparison.candidate_mean,
                    proposed_approach=(
                        f"Evaluate {exp.study} scaling to sequence length {next_seq} via progressive "
                        f"anytime-valid A/B screen without memory or precision regression"
                    ),
                    expected_improvement=round(gain * 0.80, 4),
                    compute_cost=round(base_cost * 1.5, 4),
                    related_experiments=[exp.experiment_id],
                    trigger_rule=f"transfer:seq_len:{exp.experiment_id}",
                    status="open",
                )
            )

        for target_backend in _match_sibling_backends(exp, self.catalog.backends):
            ops.append(
                Opportunity(
                    opportunity_id=f"{exp.experiment_id}->backend:{target_backend}",
                    domain=exp.study,
                    objective=f"{exp.study}@{target_backend}",
                    current_best=exp.statistical_comparison.candidate_mean,
                    proposed_approach=(
                        f"Verify {exp.study} portable kernel/runtime speedup on {target_backend} "
                        f"with bit-exact or bounded parity gate"
                    ),
                    expected_improvement=round(gain * 0.70, 4),
                    compute_cost=round(base_cost * 1.2, 4),
                    related_experiments=[exp.experiment_id],
                    trigger_rule=f"transfer:backend:{exp.experiment_id}",
                    status="open",
                )
            )

        next_regime = _match_next_regime(exp, self.catalog.workload_regimes)
        if next_regime is not None:
            ops.append(
                Opportunity(
                    opportunity_id=f"{exp.experiment_id}->regime:{next_regime}",
                    domain=exp.study,
                    objective=f"{exp.study}@{next_regime}",
                    current_best=exp.statistical_comparison.candidate_mean,
                    proposed_approach=(
                        f"Validate {exp.study} win from {exp.experiment_id} under workload regime "
                        f"{next_regime} using paired anytime-valid look schedule"
                    ),
                    expected_improvement=round(gain * 0.75, 4),
                    compute_cost=round(base_cost * 1.4, 4),
                    related_experiments=[exp.experiment_id],
                    trigger_rule=f"transfer:workload_regime:{exp.experiment_id}",
                    status="open",
                )
            )

        if exp.next_hypothesis.strip():
            ops.append(
                Opportunity(
                    opportunity_id=f"{exp.experiment_id}->followup",
                    domain=exp.study,
                    objective=f"{exp.study}:followup",
                    current_best=exp.statistical_comparison.candidate_mean,
                    proposed_approach=exp.next_hypothesis.strip(),
                    expected_improvement=round(gain * 0.90, 4),
                    compute_cost=round(base_cost, 4),
                    related_experiments=[exp.experiment_id],
                    trigger_rule=f"next_hypothesis:{exp.experiment_id}",
                    status="open",
                )
            )

        return ops


def generate_transfer_hypotheses(
    exp: ExperimentRecordV2,
    catalog: TransferCatalog | None = None,
) -> list[Opportunity]:
    """Generate 4-axis transfer opportunities for proven runs or mechanism-fix items for refuted runs."""
    return TransferEngine(catalog).generate(exp)
