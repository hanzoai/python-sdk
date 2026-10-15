"""Lineage, contamination guards and evidence records: the crate's `lineage.rs`, field for field.

A child's lineage only ever narrows: its purpose is the most restrictive of its own and its
parents', and derivation is allowed only when every parent allows it and the purpose is not
an evaluation one. A record's `digest()` is the SHA-256 of its RFC 8785 bytes, the same
bytes the crate hashes, so a Rust harness and a Python one agree on every address whose
numbers are integers within 2**53 or floats from 1e-6 to 1e21 in magnitude (outside that,
the crate writes Rust's `Display`, not RFC 8785; see `canonical`).
"""

from __future__ import annotations

import enum
from typing import Any, Iterable
from dataclasses import field, dataclass

from . import canonical
from .wire import Wire

__all__ = [
    "DataPurpose",
    "LineagePolicy",
    "ContaminationError",
    "ArtifactRef",
    "EnvironmentV1",
    "DeterminismReport",
    "TeacherInteraction",
    "PairEvidence",
    "GateSpec",
    "Claim",
    "ResearchEvent",
    "derive_lineage_policy",
    "verify_promotion_eligibility",
]


class DataPurpose(enum.Enum):
    """What an item may be used for, least to most restrictive."""

    TRAIN = "train"
    TEACHER_MINING = "teacher_mining"
    DEV = "dev"
    EVAL_ONLY = "eval_only"
    SEALED_EVAL = "sealed_eval"

    @property
    def rank(self) -> int:
        return list(DataPurpose).index(self)

    @staticmethod
    def most_restrictive(a: DataPurpose, b: DataPurpose) -> DataPurpose:
        return a if a.rank >= b.rank else b

    def is_training_allowed(self) -> bool:
        return self in (DataPurpose.TRAIN, DataPurpose.TEACHER_MINING)

    def is_eval(self) -> bool:
        return self in (DataPurpose.DEV, DataPurpose.EVAL_ONLY, DataPurpose.SEALED_EVAL)


_SEALED = (DataPurpose.EVAL_ONLY, DataPurpose.SEALED_EVAL)


class ContaminationError(Exception):
    """STAGE_REJECTED_CONTAMINATION: an artifact whose lineage forbids training reached it."""

    def __init__(self, kind: str, artifact_id: str = "", purpose: DataPurpose | None = None, message: str = ""):
        self.kind, self.artifact_id, self.purpose, self.message = kind, artifact_id, purpose, message
        if kind == "contaminated_purpose" and purpose is not None:
            text = f"artifact {artifact_id} has purpose {purpose.name.title().replace('_', '')} (forbidden in training)"
        elif kind == "derivation_disallowed":
            text = f"artifact {artifact_id} has derivation_allowed = false"
        else:
            text = f"contamination detected in stage: {message}"
        super().__init__(f"STAGE_REJECTED_CONTAMINATION: {text}")


@dataclass
class LineagePolicy(Wire):
    """The purpose an artifact carries and whether anything may be derived from it."""

    purpose: DataPurpose = DataPurpose.TRAIN
    derivation_allowed: bool = False

    @classmethod
    def root(cls, purpose: DataPurpose, derivation_allowed: bool) -> LineagePolicy:
        """A source artifact's policy; an evaluation purpose never allows derivation."""
        return cls(purpose, False if purpose in _SEALED else derivation_allowed)

    @classmethod
    def derive(cls, purpose: DataPurpose, derivation_allowed: bool, parents: Iterable[LineagePolicy]) -> LineagePolicy:
        """A child's policy: never less restrictive than any parent."""
        ps = list(parents)
        top = purpose
        for p in ps:
            top = DataPurpose.most_restrictive(top, p.purpose)
        allowed = derivation_allowed and all(p.derivation_allowed for p in ps) and top not in _SEALED
        return cls(top, allowed)

    def assert_trainable(self, context: str) -> None:
        """Raise ContaminationError unless this policy permits training."""
        if not self.purpose.is_training_allowed():
            raise ContaminationError("contaminated_purpose", context, self.purpose)
        if not self.derivation_allowed:
            raise ContaminationError("derivation_disallowed", context)

    def digest(self) -> str:
        return canonical.digest(self)


def derive_lineage_policy(
    purpose: DataPurpose, derivation_allowed: bool, parents: Iterable[LineagePolicy]
) -> LineagePolicy:
    """`LineagePolicy.derive`, as the crate names it."""
    return LineagePolicy.derive(purpose, derivation_allowed, parents)


def verify_promotion_eligibility(artifact_id: str, policy: LineagePolicy, ancestors: Iterable[LineagePolicy]) -> None:
    """Raise unless the artifact and every transitive ancestor allow derivation and training."""
    if not policy.derivation_allowed:
        raise ContaminationError("derivation_disallowed", artifact_id)
    if not policy.purpose.is_training_allowed():
        raise ContaminationError("contaminated_purpose", artifact_id, policy.purpose)
    for i, a in enumerate(ancestors):
        where = f"{artifact_id}->transitive_ancestor[{i}]"
        if not a.derivation_allowed:
            raise ContaminationError("derivation_disallowed", where)
        if not a.purpose.is_training_allowed():
            raise ContaminationError("contaminated_purpose", where, a.purpose)


class _Digest(Wire):
    def digest(self) -> str:
        """Lowercase hex SHA-256 of the record's RFC 8785 bytes."""
        return canonical.digest(self)


@dataclass
class ArtifactRef(_Digest):
    """An immutable reference to an artifact at `/v1/research/artifacts/<sha256>`."""

    artifact_id: str = ""
    sha256: str = ""
    content_sha256: str = ""
    media_type: str = "application/octet-stream"
    canonicalization: str = "raw"
    compression: str = "none"
    uncompressed_size: int = 0
    ref_uri: str = ""
    lineage: LineagePolicy = field(default_factory=LineagePolicy)

    @classmethod
    def new(cls, sha256: str, lineage: LineagePolicy) -> ArtifactRef:
        return cls(f"artifact:{sha256}", sha256, sha256, ref_uri=f"sha256:{sha256}", lineage=lineage)


@dataclass
class EnvironmentV1(_Digest):
    """The reproducibility state of the host a result came from."""

    git_sha: str = ""
    git_branch: str = ""
    git_dirty: bool = False
    host: str = ""
    os: str = ""
    kernel_version: str = ""
    cargo_lock_hash: str = ""
    image_digest: str = ""
    precision_config: str = ""
    determinism_config: str = ""
    compiler_version: str = ""
    lib_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class DeterminismReport(_Digest):
    """A stepped determinism probe's result."""

    steps_compared: list[int] = field(default_factory=list)
    loss_exact_match: bool = False
    gradient_norm_exact_match: bool = False
    max_weight_divergence: float = 0.0
    passed: bool = False
    probe_duration_secs: float = 0.0
    notes: str = ""


@dataclass
class TeacherInteraction(_Digest):
    """One call harvested from a teacher model; money in integer nanodollars."""

    model: str = ""
    input_prompt_hash: str = ""
    output_text: str = ""
    tokens_prompt: int = 0
    tokens_completion: int = 0
    cost_nanodollars: int = 0
    latency_ms: int = 0
    lineage: LineagePolicy = field(default_factory=LineagePolicy)
    when: str = ""


@dataclass
class PairEvidence(_Digest):
    """A pairwise preference, chosen over rejected, by a margin."""

    prompt_hash: str = ""
    chosen_hash: str = ""
    rejected_hash: str = ""
    margin: float = 0.0
    cost_nanodollars: int = 0
    lineage: LineagePolicy = field(default_factory=LineagePolicy)


@dataclass
class GateSpec(_Digest):
    """A preregistered, immutable promotion gate."""

    gate_id: str = ""
    candidate_discovery_recall_floor: float = 0.0
    reranking_top1_min: float = 0.0
    reranking_mrr_min: float = 0.0
    conditional_reranking_top1_min: float = 0.0
    allow_loss_regression_pct: float = 0.0
    notes: str = ""


@dataclass
class Claim(_Digest):
    """A formal claim about a benchmark result, bound to the gate it was judged by."""

    id: str = ""
    run_id: str = ""
    benchmark_id: str = ""
    metric: str = ""
    claimed_value: float = 0.0
    verified: bool = False
    gate_sha256: str = ""
    lineage: LineagePolicy = field(default_factory=LineagePolicy)
    created_at: str = ""


@dataclass
class ResearchEvent(_Digest):
    """A WAL entry: ordered by `sequence`, chained by `previous_event_hash`, its payload hashed."""

    run_id: str = ""
    worker_id: str = "worker-0"
    event_id: str = ""
    sequence: int = 0
    previous_event_hash: str = ""
    payload_hash: str = ""
    payload: Any = None
    created_at: str = ""

    @classmethod
    def new(
        cls, run_id: str, worker_id: str, event_id: str, sequence: int, previous: str, payload: Any, created_at: str
    ) -> ResearchEvent:
        return cls(run_id, worker_id, event_id, sequence, previous, canonical.digest(payload), payload, created_at)
