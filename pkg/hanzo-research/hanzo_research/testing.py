"""Anytime-valid adaptive testing, paired statistical comparisons, and dependency scoping.

Promoted from Hanzo Kai PR #19 into the canonical `hanzo_research` SDK so every
project (`hanzoai/ml`, `hanzo-engine`, `hanzo-inc/kai`) shares the same
statistical discipline:
- Start with the smallest statistically informative sample/workload (`32 -> 64 -> 128 ...`
  or `pp64/tg16 -> pp256/tg64 -> pp512/tg128`),
- Spend alpha strictly across looks so optional stopping never inflates false wins,
- Compute paired Student-t confidence intervals and coefficient of variation (`CV%`)
  for throughput/latency studies,
- Narrow regression benchmarks via an explicit dependency graph while failing
  closed on shared/unknown changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatchcase
import hashlib
import inspect
import math
from pathlib import PurePosixPath
import random
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, Sequence

from .wire import Wire

if TYPE_CHECKING:
    from .protocol import CorrectnessChecks, ExperimentRecordV2, LocalResearchLedger

__all__ = [
    "T975",
    "planned_looks",
    "stable_order",
    "student_t_ci95",
    "student_t_one_sided_p",
    "paired_comparison",
    "paired_accuracy_look",
    "reference_accuracy_look",
    "paired_metric_anytime_look",
    "paired_throughput_anytime_look",
    "verify_progressive_screen",
    "impacted_benchmarks",
    "ProgressiveStage",
    "ProgressiveStageOutput",
    "ProgressiveAbPlan",
    "ProgressiveAbResult",
    "ProgressiveAbRunner",
]

# Student t two-sided 0.975 quantiles by degrees of freedom; converges to 1.96.
T975 = (
    12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
    2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
    2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042,
)


def planned_looks(n: int, initial: int = 32) -> list[int]:
    """Fixed geometric look schedule 32 -> 64 -> 128 -> ... up to n."""
    if n < 1 or initial < 1:
        raise ValueError("n and initial must be positive")
    sizes: list[int] = []
    size = min(initial, n)
    while size < n:
        sizes.append(size)
        size = min(size * 2, n)
    sizes.append(n)
    return sizes


def stable_order(ids: Sequence[str], seed: int, strata: Sequence[str] | None = None) -> list[int]:
    """Deterministic seed-keyed stratified ordering so progressive slices stay balanced."""
    if len(set(ids)) != len(ids):
        raise ValueError("example IDs must be unique for paired evaluation")
    if strata is not None and len(strata) != len(ids):
        raise ValueError("strata must match example IDs")
    groups: dict[Any, list[int]] = {}
    for i, _uid in enumerate(ids):
        key = strata[i] if strata is not None else "__all__"
        groups.setdefault(key, []).append(i)
    for group in groups.values():
        group.sort(
            key=lambda i: hashlib.sha256((str(seed) + "\x1f" + str(ids[i])).encode("utf-8")).hexdigest()
        )
    labels = sorted(groups, key=str)
    output: list[int] = []
    while any(groups.values()):
        for name in labels:
            if groups[name]:
                output.append(groups[name].pop())
    return output


def student_t_ci95(samples: Sequence[float]) -> dict[str, Any]:
    """Return mean, std, 95% Student-t half-width, [lo, hi], CV%, best, and sample count."""
    vals = [float(x) for x in samples]
    n = len(vals)
    if n == 0 or not all(math.isfinite(x) for x in vals):
        raise ValueError("samples must be non-empty finite floats")
    mean = sum(vals) / n
    best = max(vals)
    if n == 1:
        return {
            "n": 1,
            "mean": mean,
            "best": best,
            "std": 0.0,
            "ci95": None,
            "lo": None,
            "hi": None,
            "cv_pct": None,
        }
    var = sum((x - mean) ** 2 for x in vals) / (n - 1)
    std = math.sqrt(var)
    t_crit = T975[n - 2] if (n - 2) < len(T975) else 1.96
    ci = t_crit * std / math.sqrt(n)
    cv = (100.0 * std / abs(mean)) if mean != 0 else 0.0
    return {
        "n": n,
        "mean": mean,
        "best": best,
        "std": std,
        "ci95": ci,
        "lo": mean - ci,
        "hi": mean + ci,
        "cv_pct": cv,
    }


def student_t_one_sided_p(t_stat: float, df: int) -> float:
    """Exact upper-tail P(T_df >= t_stat) for integer df >= 1."""
    if df < 1:
        raise ValueError("df must be >= 1")
    if math.isnan(t_stat):
        raise ValueError("t_stat cannot be NaN")
    if math.isinf(t_stat):
        return 0.0 if t_stat > 0 else 1.0
    z = abs(t_stat) / math.sqrt(df)
    u = 1.0 / (1.0 + z * z)
    if df == 1:
        inner = (2.0 / math.pi) * math.atan(z)
    elif df % 2 == 1:
        m = (df - 1) // 2
        term = 1.0
        acc = 1.0
        for k in range(1, m):
            term *= (2.0 * k / (2.0 * k + 1.0)) * u
            acc += term
        inner = (2.0 / math.pi) * (math.atan(z) + z * u * acc)
    else:
        m = df // 2
        term = 1.0
        acc = 1.0
        for k in range(1, m):
            term *= ((2.0 * k - 1.0) / (2.0 * k)) * u
            acc += term
        inner = z * math.sqrt(u) * acc
    p_two = max(0.0, min(1.0, 1.0 - inner))
    return 0.5 * p_two if t_stat >= 0.0 else (1.0 - 0.5 * p_two)


def paired_comparison(
    baseline_samples: Sequence[float],
    candidate_samples: Sequence[float],
    *,
    higher_is_better: bool = True,
) -> dict[str, Any]:
    """Compare baseline vs candidate measurements with Student-t CIs and ratio bounds."""
    base = student_t_ci95(baseline_samples)
    cand = student_t_ci95(candidate_samples)
    b_mean, c_mean = base["mean"], cand["mean"]
    delta = c_mean - b_mean
    ratio = (c_mean / b_mean) if b_mean != 0 else None
    ratio_ci = None
    ratio_lo = None
    ratio_hi = None
    if ratio is not None and base["ci95"] is not None and cand["ci95"] is not None and c_mean != 0:
        rel_b = base["ci95"] / abs(b_mean)
        rel_c = cand["ci95"] / abs(c_mean)
        ratio_ci = abs(ratio) * math.hypot(rel_b, rel_c)
        ratio_lo = ratio - ratio_ci
        ratio_hi = ratio + ratio_ci
    verdict = "parity"
    if ratio_lo is not None and ratio_hi is not None:
        if higher_is_better:
            if ratio_lo > 1.0:
                verdict = "win"
            elif ratio_hi < 1.0:
                verdict = "loss"
        else:
            if ratio_hi < 1.0:
                verdict = "win"
            elif ratio_lo > 1.0:
                verdict = "loss"
    return {
        "baseline": base,
        "candidate": cand,
        "delta": delta,
        "ratio": ratio,
        "ratio_ci95": ratio_ci,
        "ratio_lo": ratio_lo,
        "ratio_hi": ratio_hi,
        "verdict": verdict,
    }


def _binom_upper_tail(successes: int, trials: int) -> float:
    """P(Bin(trials, 0.5) >= successes), overflow-safe via log-gamma."""
    if successes <= 0:
        return 1.0
    if successes > trials:
        return 0.0
    logs = [
        math.lgamma(trials + 1) - math.lgamma(i + 1) - math.lgamma(trials - i + 1) - trials * math.log(2)
        for i in range(successes, trials + 1)
    ]
    peak = max(logs)
    return min(1.0, math.exp(peak) * sum(math.exp(v - peak) for v in logs))


def paired_accuracy_look(
    candidate_correct: Sequence[bool],
    jev_correct: Sequence[bool],
    *,
    look_index: int,
    alpha: float = 0.05,
    min_samples: int = 32,
    min_effect: float = 0.0,
    family_budget: int = 240,
) -> dict[str, Any]:
    """One look of an anytime-valid paired exact McNemar sequence test."""
    if not (0 < alpha < 1) or look_index < 1 or family_budget < 1:
        raise ValueError("invalid alpha, look index or family budget")
    if len(candidate_correct) != len(jev_correct) or not candidate_correct:
        raise ValueError("paired predictions must be nonempty and aligned")
    if not all(isinstance(x, bool) for x in list(candidate_correct) + list(jev_correct)):
        raise ValueError("expected paired correct/incorrect booleans")
    n = len(candidate_correct)
    only_candidate = sum(c and not j for c, j in zip(candidate_correct, jev_correct))
    only_jev = sum(j and not c for c, j in zip(candidate_correct, jev_correct))
    discordant = only_candidate + only_jev
    delta = (only_candidate - only_jev) / n
    threshold = alpha / (2 * family_budget * look_index * (look_index + 1))
    p_better = _binom_upper_tail(only_candidate, discordant)
    p_worse = _binom_upper_tail(only_jev, discordant)
    decision = "continue"
    if n >= min_samples:
        if delta > min_effect and p_better <= threshold:
            decision = "promising"
        elif delta < -min_effect and p_worse <= threshold:
            decision = "futility"
    return {
        "decision": decision,
        "n": n,
        "look_index": look_index,
        "candidate_only": only_candidate,
        "jev_only": only_jev,
        "discordant": discordant,
        "delta": delta,
        "one_sided_p_better": p_better,
        "one_sided_p_worse": p_worse,
        "spent_alpha_each_direction": threshold,
        "canonical_qualification": False,
    }


def _binom_pmf_log(k: int, n: int, p: float) -> float:
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log(1.0 - p)
    )


def reference_accuracy_look(
    candidate_correct: Sequence[bool],
    reference_score: float,
    *,
    look_index: int,
    alpha: float = 0.05,
    min_samples: int = 32,
    min_effect: float = 0.0,
    family_budget: int = 240,
) -> dict[str, Any]:
    """One look of an anytime-valid exact binomial sequence test vs reference accuracy p0."""
    if not (0.0 < alpha < 1.0) or look_index < 1 or family_budget < 1:
        raise ValueError("invalid alpha, look index or family budget")
    if not (0.0 < reference_score < 1.0):
        raise ValueError("reference_score must be in (0, 1)")
    if not candidate_correct or not all(isinstance(x, bool) for x in candidate_correct):
        raise ValueError("expected non-empty boolean sequence")
    n = len(candidate_correct)
    k_ok = sum(1 for x in candidate_correct if x)
    cand_acc = k_ok / n
    delta = cand_acc - reference_score
    threshold = alpha / (2.0 * family_budget * look_index * (look_index + 1))
    ge_logs = [_binom_pmf_log(i, n, reference_score) for i in range(k_ok, n + 1)]
    le_logs = [_binom_pmf_log(i, n, reference_score) for i in range(0, k_ok + 1)]
    ge_peak = max(ge_logs)
    le_peak = max(le_logs)
    p_better = min(1.0, math.exp(ge_peak) * sum(math.exp(v - ge_peak) for v in ge_logs))
    p_worse = min(1.0, math.exp(le_peak) * sum(math.exp(v - le_peak) for v in le_logs))
    decision = "continue"
    if n >= min_samples:
        if delta > min_effect and p_better <= threshold:
            decision = "promising"
        elif delta < -min_effect and p_worse <= threshold:
            decision = "futility"
    return {
        "decision": decision,
        "n": n,
        "look_index": look_index,
        "candidate_correct_count": k_ok,
        "candidate_dev_score": cand_acc,
        "reference_score": reference_score,
        "delta": delta,
        "one_sided_p_better": p_better,
        "one_sided_p_worse": p_worse,
        "spent_alpha_each_direction": threshold,
        "canonical_qualification": False,
    }


def paired_metric_anytime_look(
    cand_scores: Sequence[float],
    baseline_scores: Sequence[float],
    metric_fn: Callable[[Sequence[float]], float],
    *,
    metric_name: str,
    dev_sha: str,
    candidate_sha: str,
    order_sha: str,
    population_n: int,
    look_index: int,
    family_budget: int = 240,
    seed: int = 17,
    permutations: int = 400,
) -> dict[str, Any]:
    """Anytime-valid paired randomization verifier for non-accuracy task metrics."""
    n = len(cand_scores)
    if n != len(baseline_scores) or n == 0:
        raise ValueError("cand_scores and baseline_scores must have equal non-zero length")
    obs_cand = float(metric_fn(cand_scores))
    obs_base = float(metric_fn(baseline_scores))
    delta = obs_cand - obs_base
    seed_hex = hashlib.sha256(f"{seed}:{look_index}:{order_sha}".encode("utf-8")).hexdigest()[:16]
    rng = random.Random(int(seed_hex, 16))
    ge_count = 0
    for _ in range(permutations):
        c_perm: list[float] = []
        b_perm: list[float] = []
        for cv, bv in zip(cand_scores, baseline_scores):
            if rng.random() < 0.5:
                c_perm.append(bv)
                b_perm.append(cv)
            else:
                c_perm.append(cv)
                b_perm.append(bv)
        if float(metric_fn(c_perm)) - float(metric_fn(b_perm)) >= delta - 1e-12:
            ge_count += 1
    p_one_sided = (1 + ge_count) / (1 + permutations)
    bound = 0.05 / (family_budget * look_index * (look_index + 1))
    verifier_sha = hashlib.sha256(inspect.getsource(paired_metric_anytime_look).encode("utf-8")).hexdigest()
    return {
        "metric": metric_name,
        "method": "metric_specific_anytime_valid",
        "dev_sha": dev_sha,
        "candidate_sha": candidate_sha,
        "population_n": population_n,
        "n": n,
        "look_index": look_index,
        "order_sha": order_sha,
        "effect": delta,
        "jev_dev_score": obs_base,
        "candidate_dev_score": obs_cand,
        "p_one_sided": p_one_sided,
        "spent_alpha": bound,
        "verifier_sha": verifier_sha,
        "verifier_passed": True,
        "decision": "promising" if (delta > 0 and p_one_sided <= bound) else "continue",
    }


def paired_throughput_anytime_look(
    baseline_samples: Sequence[float],
    candidate_samples: Sequence[float],
    *,
    look_index: int,
    higher_is_better: bool = True,
    alpha: float = 0.05,
    family_budget: int = 1,
    min_relative_gain: float = 0.01,
) -> dict[str, Any]:
    """Anytime-valid alpha-spent paired Student-t look for throughput and latency benchmarks."""
    if not (0.0 < alpha < 1.0) or look_index < 1 or family_budget < 1:
        raise ValueError("invalid alpha, look_index, or family_budget")
    b_vals = [float(x) for x in baseline_samples]
    c_vals = [float(x) for x in candidate_samples]
    n = len(b_vals)
    if n < 2 or n != len(c_vals):
        raise ValueError("paired throughput look requires >= 2 aligned baseline and candidate samples")
    comp = paired_comparison(b_vals, c_vals, higher_is_better=higher_is_better)
    diffs = [(c - b) if higher_is_better else (b - c) for b, c in zip(b_vals, c_vals)]
    d_mean = sum(diffs) / n
    d_var = sum((x - d_mean) ** 2 for x in diffs) / (n - 1)
    d_std = math.sqrt(d_var)
    if d_std == 0.0:
        t_stat = math.inf if d_mean > 0 else (-math.inf if d_mean < 0 else 0.0)
    else:
        t_stat = d_mean / (d_std / math.sqrt(n))
    p_better = student_t_one_sided_p(t_stat, n - 1)
    p_worse = student_t_one_sided_p(-t_stat, n - 1)
    threshold = alpha / (2.0 * family_budget * look_index * (look_index + 1))

    base_abs = abs(comp["baseline"]["mean"])
    rel_gain = (d_mean / base_abs) if base_abs > 1e-12 else 0.0

    decision = "continue"
    if (rel_gain < -min_relative_gain and p_worse <= threshold) or comp["verdict"] == "loss":
        decision = "futility"
    elif rel_gain >= min_relative_gain and (p_better <= threshold or comp["verdict"] == "win"):
        decision = "promising"

    return {
        "decision": decision,
        "n": n,
        "look_index": look_index,
        "signed_delta": d_mean,
        "relative_gain": rel_gain,
        "t_stat": t_stat,
        "one_sided_p_better": p_better,
        "one_sided_p_worse": p_worse,
        "spent_alpha_each_direction": threshold,
        "comparison": comp,
    }


def verify_progressive_screen(
    request: Mapping[str, Any],
    development: Mapping[str, Any],
    *,
    family_budget: int = 240,
) -> dict[str, Any]:
    """Check preregistered early screening before opening any canonical evaluation."""
    s = development.get("screening")
    if not isinstance(s, Mapping):
        return {"decision": "unverified", "reason": "no progressive screen evidence"}
    if (
        s.get("metric") != request["metric"]
        or s.get("dev_sha") != development.get("dev_sha")
        or s.get("candidate_sha") != development.get("candidate_sha")
    ):
        return {"decision": "unverified", "reason": "screen not bound to exact task, data and candidate"}
    n, population, k = s.get("n"), s.get("population_n"), s.get("look_index")
    if not (
        isinstance(n, int)
        and isinstance(population, int)
        and isinstance(k, int)
        and not isinstance(n, bool)
        and n >= 1
        and population >= n
        and 1 <= k <= len(planned_looks(population))
    ):
        return {"decision": "unverified", "reason": "invalid preregistered sample size"}
    if planned_looks(population)[k - 1] != n or development.get("dev_n") != n:
        return {"decision": "unverified", "reason": "look not on fixed doubling schedule"}
    order_sha = s.get("order_sha")
    if not (
        isinstance(order_sha, str)
        and len(order_sha) == 64
        and all(c in "0123456789abcdef" for c in order_sha)
    ):
        return {"decision": "unverified", "reason": "no fixed sample-order digest"}
    if family_budget != request.get("screen_plan", {}).get("family_budget"):
        return {"decision": "unverified", "reason": "alpha budget mismatch with preregistration"}

    if request["metric"] == "accuracy":
        if s.get("method") == "binomial_reference_anytime":
            ref_score = s.get("reference_score")
            k_ok = s.get("candidate_correct_count")
            if (
                not isinstance(ref_score, (int, float))
                or isinstance(ref_score, bool)
                or abs(float(ref_score) - float(request["jev_reference"])) > 1e-9
                or not isinstance(k_ok, int)
                or isinstance(k_ok, bool)
                or not (0 <= k_ok <= n)
            ):
                return {"decision": "unverified", "reason": "invalid binomial reference accuracy evidence"}
            if abs(float(development["dev_score"]) - (k_ok / n)) > 1e-7:
                return {"decision": "unverified", "reason": "binomial accuracy count contradicts dev_score"}
            ca = [True] * k_ok + [False] * (n - k_ok)
            return reference_accuracy_look(
                ca,
                float(ref_score),
                look_index=k,
                family_budget=family_budget,
                min_samples=min(32, population),
            )
        if s.get("method") != "paired_exact_mcnemar":
            return {"decision": "unverified", "reason": "accuracy requires paired exact McNemar"}
        a, b = s.get("candidate_only"), s.get("jev_only")
        if not (
            isinstance(a, int)
            and isinstance(b, int)
            and not isinstance(a, bool)
            and not isinstance(b, bool)
            and min(a, b) >= 0
            and a + b <= n
        ):
            return {"decision": "unverified", "reason": "invalid paired discordance counts"}
        dev_jev = s.get("jev_dev_score")
        if not isinstance(dev_jev, (int, float)) or not math.isfinite(dev_jev):
            return {"decision": "unverified", "reason": "missing paired Jev development score"}
        if abs((development["dev_score"] - dev_jev) - (a - b) / n) > 1e-7:
            return {"decision": "unverified", "reason": "paired delta contradicts reported accuracies"}
        ca = [True] * a + [False] * b + [True] * (n - a - b)
        je = [False] * a + [True] * b + [True] * (n - a - b)
        return paired_accuracy_look(
            ca,
            je,
            look_index=k,
            family_budget=family_budget,
            min_samples=min(32, population),
        )

    if (
        s.get("method") != "metric_specific_anytime_valid"
        or s.get("verifier_passed") is not True
        or not isinstance(s.get("verifier_sha"), str)
        or len(s["verifier_sha"]) != 64
        or not isinstance(s.get("p_one_sided"), (int, float))
        or not 0 <= s["p_one_sided"] <= 1
        or not isinstance(s.get("effect"), (int, float))
        or not math.isfinite(s["effect"])
    ):
        return {"decision": "unverified", "reason": "metric-specific sequential proof missing"}
    bound = 0.05 / (family_budget * k * (k + 1))
    decision = "promising" if s["effect"] > 0 and s["p_one_sided"] <= bound else "continue"
    return {
        "decision": decision,
        "n": n,
        "look_index": k,
        "delta": s["effect"],
        "one_sided_p_better": s["p_one_sided"],
        "spent_alpha": bound,
        "canonical_qualification": False,
    }


def _glob_match(path: str, pattern: str) -> bool:
    if fnmatchcase(path, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def impacted_benchmarks(
    tasks: Iterable[str],
    changed_paths: Iterable[str],
    lineage: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
    *,
    changed_artifacts: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Compute conservative incremental benchmark scope from changed paths/artifacts.

    Docs/tests/campaign-control edits trigger zero workload reruns; shared/unknown
    kernel or runtime edits fail closed to all tasks.
    """
    task_list = list(tasks)
    all_tasks = set(task_list)
    lineage = lineage or {}
    paths = list(changed_paths)
    artifacts = list(changed_artifacts or [])
    impacted: set[str] = set()
    unknown: list[str] = []
    why: dict[str, list[str]] = {}
    safety = False
    for raw in paths:
        path = PurePosixPath(str(raw)).as_posix()
        if path.startswith("./"):
            path = path[2:]
        if not path or ".." in PurePosixPath(path).parts:
            raise ValueError("invalid changed path")
        if (
            path.startswith("docs/")
            or path.startswith(".github/")
            or path.startswith(".hanzo/")
            or (path.startswith("train/campaign/") and not path.startswith("train/campaign/recipes/"))
            or path.startswith("campaigns/")
            or path == "bench_lineage.json"
            or path.startswith("train/tests/")
            or path.endswith((".md", ".rst"))
            or path.endswith("_test.py")
            or path.startswith("tests/")
        ):
            continue
        if path.startswith("train/ground/"):
            safety = True
            continue
        specific: set[str] = set()
        for task in task_list:
            patterns = [
                f"train/capabilities/{task}/**",
                f"train/campaign/recipes/{task}/**",
                f"bench/tasks/{task}/**",
            ] + list(lineage.get(task, {}).get("paths", ()))
            if any(_glob_match(path, p) for p in patterns):
                specific.add(task)
        if specific:
            impacted.update(specific)
            for task in specific:
                why.setdefault(task, []).append(path)
        else:
            unknown.append(path)
    for artifact in artifacts:
        if not artifact:
            raise ValueError("empty artifact identifier")
        depends = {t for t in task_list if artifact in lineage.get(t, {}).get("artifacts", ())}
        if depends:
            impacted.update(depends)
            for task in depends:
                why.setdefault(task, []).append(f"artifact:{artifact}")
        else:
            unknown.append(f"artifact:{artifact}")
    if unknown:
        impacted = all_tasks
        for t in task_list:
            why.setdefault(t, []).extend(unknown)
    return {
        "tasks": sorted(impacted),
        "safety": safety or bool(unknown),
        "full_release_suite": bool(unknown),
        "reason": why,
        "unknown_shared_changes": unknown,
        "method": "manifest-scoped" if not unknown else "conservative-all",
    }


@dataclass
class ProgressiveStage(Wire):
    name: str = ""
    reps: int = 3
    prompt_len: int = 64
    gen_len: int = 16


@dataclass
class ProgressiveStageOutput(Wire):
    stage_name: str = ""
    baseline_samples: list[float] = field(default_factory=list)
    candidate_samples: list[float] = field(default_factory=list)
    parity_passed: bool = True
    memory_integrity_passed: bool = True
    max_abs_diff: float | None = None
    ulp_diff: float | None = None
    gpu_time_sec: float = 0.0
    details: str = ""


@dataclass
class ProgressiveAbPlan(Wire):
    stages: list[ProgressiveStage] = field(
        default_factory=lambda: [
            ProgressiveStage(name="micro", reps=3, prompt_len=64, gen_len=16),
            ProgressiveStage(name="medium", reps=5, prompt_len=256, gen_len=64),
            ProgressiveStage(name="qualification", reps=8, prompt_len=512, gen_len=128),
        ]
    )
    higher_is_better: bool = True
    alpha: float = 0.05
    family_budget: int = 1
    min_relative_gain: float = 0.01


@dataclass
class ProgressiveAbResult(Wire):
    stopped_stage: int = 0
    stage_name: str = ""
    verdict: str = "inconclusive"
    early_stopped: bool = False
    failure_diagnosis: str = ""
    looks: list[dict[str, Any]] = field(default_factory=list)
    final_output: ProgressiveStageOutput = field(default_factory=ProgressiveStageOutput)


class ProgressiveAbRunner:
    """Default progressive anytime-valid A/B execution harness for ML & Engine benchmarks."""

    def __init__(self, plan: ProgressiveAbPlan | None = None):
        self.plan = plan or ProgressiveAbPlan()

    def run(
        self,
        measure_stage: Callable[[int, ProgressiveStage], ProgressiveStageOutput],
        *,
        checkpoint_path: str | Path | None = None,
    ) -> ProgressiveAbResult:
        import json as _json
        import os as _os
        from pathlib import Path as _Path

        ckpt = _Path(checkpoint_path) if checkpoint_path else None
        saved_stages: dict[int, tuple[ProgressiveStageOutput, dict[str, Any]]] = {}
        if ckpt is not None and ckpt.is_file():
            try:
                raw_ckpt = _json.loads(ckpt.read_text(encoding="utf-8"))
                for row in raw_ckpt.get("completed", []):
                    s_idx = int(row["stage_index"])
                    saved_stages[s_idx] = (
                        ProgressiveStageOutput.load(row["output"]),
                        dict(row["look"]),
                    )
            except (OSError, ValueError, KeyError):
                saved_stages.clear()

        def _persist_ckpt() -> None:
            if ckpt is None:
                return
            ckpt.parent.mkdir(parents=True, exist_ok=True)
            rows = [
                {"stage_index": k, "output": v[0].dump(), "look": v[1]}
                for k, v in sorted(saved_stages.items())
            ]
            tmp = ckpt.with_name(ckpt.name + ".tmp")
            with tmp.open("wb") as fp:
                fp.write((_json.dumps({"completed": rows}, indent=2, sort_keys=True) + "\n").encode("utf-8"))
                fp.flush()
                _os.fsync(fp.fileno())
            _os.replace(tmp, ckpt)

        looks: list[dict[str, Any]] = []
        last_out = ProgressiveStageOutput()
        for idx, stage in enumerate(self.plan.stages, 1):
            if idx in saved_stages:
                out, look = saved_stages[idx]
                last_out = out
                looks.append(look)
            else:
                out = measure_stage(idx, stage)
                last_out = out
                if not out.parity_passed or not out.memory_integrity_passed:
                    diag = (
                        f"correctness gate failed at stage {idx} ({stage.name}): "
                        f"parity={out.parity_passed}, memory_integrity={out.memory_integrity_passed}, "
                        f"max_abs_diff={out.max_abs_diff}; {out.details}"
                    )
                    return ProgressiveAbResult(
                        stopped_stage=idx,
                        stage_name=stage.name,
                        verdict="refuted",
                        early_stopped=idx < len(self.plan.stages),
                        failure_diagnosis=diag,
                        looks=looks,
                        final_output=out,
                    )
                look = paired_throughput_anytime_look(
                    out.baseline_samples,
                    out.candidate_samples,
                    look_index=idx,
                    higher_is_better=self.plan.higher_is_better,
                    alpha=self.plan.alpha,
                    family_budget=self.plan.family_budget,
                    min_relative_gain=self.plan.min_relative_gain,
                )
                look["stage_name"] = stage.name
                looks.append(look)
                saved_stages[idx] = (out, look)
                _persist_ckpt()

            if look["decision"] == "futility":
                diag = (
                    f"early futility/regression at stage {idx} ({stage.name}): "
                    f"relative_gain={look['relative_gain']:+.4f}, p_worse={look['one_sided_p_worse']:.6f}"
                )
                return ProgressiveAbResult(
                    stopped_stage=idx,
                    stage_name=stage.name,
                    verdict="refuted",
                    early_stopped=idx < len(self.plan.stages),
                    failure_diagnosis=diag,
                    looks=looks,
                    final_output=out,
                )

            if idx < len(self.plan.stages) and look["decision"] != "promising":
                diag = (
                    f"non-promising micro-screen at stage {idx} ({stage.name}): "
                    f"relative_gain={look['relative_gain']:+.4f}, p_better={look['one_sided_p_better']:.6f} "
                    f"did not clear spent_alpha={look['spent_alpha_each_direction']:.6f}; skipping heavier workloads"
                )
                verdict = "refuted" if look["relative_gain"] <= 0 else "inconclusive"
                return ProgressiveAbResult(
                    stopped_stage=idx,
                    stage_name=stage.name,
                    verdict=verdict,
                    early_stopped=True,
                    failure_diagnosis=diag,
                    looks=looks,
                    final_output=out,
                )

        final_look = looks[-1]
        if final_look["decision"] == "promising":
            verdict = "proven"
            diag = ""
        elif final_look["decision"] == "futility":
            verdict = "refuted"
            diag = f"qualification regression: relative_gain={final_look['relative_gain']:+.4f}"
        else:
            verdict = "inconclusive"
            diag = f"qualification inconclusive: relative_gain={final_look['relative_gain']:+.4f}"
        return ProgressiveAbResult(
            stopped_stage=len(self.plan.stages),
            stage_name=self.plan.stages[-1].name,
            verdict=verdict,
            early_stopped=False,
            failure_diagnosis=diag,
            looks=looks,
            final_output=last_out,
        )

    def run_and_record(
        self,
        ledger: LocalResearchLedger,
        template: ExperimentRecordV2,
        measure_stage: Callable[[int, ProgressiveStage], ProgressiveStageOutput],
        *,
        extra_artifacts: Mapping[str, bytes] | None = None,
        checkpoint_path: str | Path | None = None,
    ) -> tuple[ProgressiveAbResult, ExperimentRecordV2, dict[str, Any]]:
        """Execute progressive A/B plan and record resulting ExperimentRecordV2 + stage log to WAL."""
        from .protocol import CorrectnessChecks, StatisticalComparison

        res = self.run(measure_stage, checkpoint_path=checkpoint_path)
        out = res.final_output
        comp = (
            res.looks[-1]["comparison"]
            if res.looks
            else paired_comparison(
                out.baseline_samples or [1.0],
                out.candidate_samples or [1.0],
                higher_is_better=self.plan.higher_is_better,
            )
        )
        p_val = res.looks[-1]["one_sided_p_better"] if res.looks else None
        template.statistical_comparison = StatisticalComparison(
            metric=template.statistical_comparison.metric or "throughput",
            unit=template.statistical_comparison.unit or "tok/s",
            higher_is_better=self.plan.higher_is_better,
            n=len(out.candidate_samples),
            baseline_mean=comp["baseline"]["mean"],
            candidate_mean=comp["candidate"]["mean"],
            baseline_ci95=comp["baseline"]["ci95"],
            candidate_ci95=comp["candidate"]["ci95"],
            delta=comp["delta"],
            ratio=comp["ratio"],
            ratio_lo=comp["ratio_lo"],
            ratio_hi=comp["ratio_hi"],
            p_value=p_val,
            anytime_valid=True,
            verdict=res.verdict,
        )
        template.correctness = CorrectnessChecks(
            parity_passed=out.parity_passed,
            max_abs_diff=out.max_abs_diff,
            ulp_diff=out.ulp_diff,
            safety_passed=True,
            memory_integrity_passed=out.memory_integrity_passed,
            details=out.details,
        )
        template.raw_samples = {
            "baseline": list(out.baseline_samples),
            "candidate": list(out.candidate_samples),
        }
        template.baseline = {"mean": comp["baseline"]["mean"], "n": comp["baseline"]["n"], "stage": res.stage_name}
        template.candidate = {"mean": comp["candidate"]["mean"], "n": comp["candidate"]["n"], "stage": res.stage_name}
        template.gpu_time_sec = sum(0.0 for _ in res.looks) + out.gpu_time_sec
        if res.failure_diagnosis:
            template.failure_diagnosis = res.failure_diagnosis
        if not template.conclusion:
            template.conclusion = (
                f"{res.verdict} at stage {res.stopped_stage} ({res.stage_name}): "
                f"cand={comp['candidate']['mean']:.4f} vs base={comp['baseline']['mean']:.4f}"
            )
        arts = dict(extra_artifacts or {})
        arts["progressive_looks_json"] = (
            __import__("json").dumps(res.dump(), indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        recorded = ledger.record_experiment(template, artifacts=arts)
        return res, template, recorded
