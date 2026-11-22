"""`hanzo-research`: file, grant, read, compare, and autonomously run research from a shell.

    hanzo-research post runs.jsonl --grant public --publishable
    hanzo-research list runs --benchmark decision.latency
    hanzo-research query --dir ~/.hanzo/research --study bitcos --verdict proven
    hanzo-research failures --dir ~/.hanzo/research --domain bitcos
    hanzo-research next --dir ~/.hanzo/research --top-k 5
    hanzo-research impact --lineage bench_lineage.json --changed-paths changed.txt
    hanzo-research tick --dir ~/.hanzo/research --campaign campaigns/ml_kernels_and_quant.json --executor scripts/ml_research_executor.py
    hanzo-research loop --dir ~/.hanzo/research --campaign campaigns/ml_kernels_and_quant.json --executor scripts/ml_research_executor.py --max-ticks 10 --budget-minutes 60 --idle-exit
    hanzo-research sync --dir ~/.hanzo/research

Every answer is JSON on stdout. The token is HANZO_API_KEY, else `hanzo auth token`.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

from .benchmark import Arena
from .client import Research
from .controller import AutonomousController, CampaignRegistry
from .errors import Error
from .protocol import LocalResearchLedger
from .provenance import capture
from .testing import impacted_benchmarks
from .wire import dump

KINDS = {"run": "runs", "benchmark": "benchmarks", "study": "studies", "paper": "papers"}
DEFAULT_LEDGER = os.path.expanduser("~/.hanzo/research")


def read(path: str) -> Any:
    """A JSON document, or the records of a JSON Lines file, from a path or `-` for stdin."""
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def _read_lines_arg(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    p = Path(raw)
    if p.is_file():
        return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [x.strip() for x in raw.split(",") if x.strip()]


def plan(doc: Any, kind: str) -> dict[str, list[Any]]:
    """What a document files, by kind: a plan's keys, else its records as one kind."""
    if isinstance(doc, dict) and any(k in doc for k in KINDS.values()):
        return {k: list(doc[k]) for k in ("benchmarks", "studies", "runs", "papers") if doc.get(k)}
    return {KINDS[kind]: doc if isinstance(doc, list) else [doc]}


def _add_auto_args(s: argparse.ArgumentParser, *, require_executor: bool = False) -> None:
    s.add_argument("--dir", default=DEFAULT_LEDGER, help="local shared research ledger directory")
    s.add_argument("--state", help="controller state directory (default: <dir>/controller)")
    s.add_argument("--campaign", "--registry", dest="campaign", help="campaign registry JSON")
    s.add_argument("--executor", required=require_executor, help="progressive A/B stage executor binary or script")
    s.add_argument("--repo-dir", default=".", help="repository checkout directory")
    s.add_argument("--changed-paths", help="newline file or comma list of changed repo paths")
    s.add_argument("--changed-artifacts", help="newline file or comma list of changed artifact hashes")
    s.add_argument("--lineage", help="bench_lineage.json dependency manifest")
    s.add_argument("--max-trials", type=int, default=64, help="maximum trials per objective")
    s.add_argument("--timeout-minutes", type=int, default=30, help="per-stage timeout in minutes")
    s.add_argument("--auto-sync", action=argparse.BooleanOptionalAction, default=True)


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="hanzo-research", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--base", help="API base (RESEARCH_BASE, else https://api.hanzo.ai)")
    p.add_argument("--org", help="act in this org (X-Org-Id); the token must belong to it")
    p.add_argument("--project", help="the token's project (default: its claim)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("post", help="file records from a JSON or JSON Lines file")
    s.add_argument("file")
    s.add_argument("--kind", choices=KINDS, default="run", help="what a bare record or list is (default run)")
    s.add_argument("--grant", choices=("private", "org", "public"), help="then set the filed runs' visibility")
    s.add_argument("--publishable", action=argparse.BooleanOptionalAction, help="with the grant: commons consent")
    s.add_argument("--trainable", action=argparse.BooleanOptionalAction, help="with the grant: training consent")
    s.add_argument("--dry", action="store_true", help="print the bodies, file nothing")

    s = sub.add_parser("list", help="canonical records")
    s.add_argument(
        "what",
        nargs="?",
        default="runs",
        choices=("runs", "benchmarks", "studies", "papers", "experiments", "artifacts", "projects", "totals"),
    )
    for f in ("id", "benchmark", "system", "study", "completion", "since", "until", "kind", "run", "cites"):
        s.add_argument(f"--{f}")
    s.add_argument("--public", metavar="ORG", help="runs: that org's public runs, read with no credential")
    s.add_argument("--in", dest="scope", help="narrow to one project of the org")

    s = sub.add_parser("get", help="one record's canonical version")
    s.add_argument("id")
    s.add_argument("--kind", choices=KINDS, default="run")
    s.add_argument("--public", metavar="ORG", help="a run of that org's public runs, read with no credential")

    s = sub.add_parser("grant", help="visibility and consent for runs, or an artifact by --sha256")
    s.add_argument("ids", nargs="*")
    s.add_argument("--sha256")
    s.add_argument("--visibility", choices=("private", "org", "public"))
    s.add_argument("--publishable", action=argparse.BooleanOptionalAction)
    s.add_argument("--trainable", action=argparse.BooleanOptionalAction)

    s = sub.add_parser("retract", help="withdraw a run: a version marked retracted")
    s.add_argument("id")
    s.add_argument("--why", required=True)

    s = sub.add_parser("compare", help="two runs side by side")
    s.add_argument("a")
    s.add_argument("b")

    s = sub.add_parser("provenance", help="print what capture() reads here")
    s.add_argument("--repo")
    s.add_argument("--model", default="")
    s.add_argument("--weights")
    s.add_argument("--device", default="")
    s.add_argument("--dtype", default="")
    s.add_argument("--package", action="append", help="a distribution whose version pins the result")
    s.add_argument("--no-gpu", action="store_true")

    s = sub.add_parser("arena", help="the /v1/benchmark arena")
    s.add_argument("what", choices=("catalog", "leaderboard", "claims", "history", "compare", "presets"))
    s.add_argument("models", nargs="*", help="compare: two model ids")
    for f in ("benchmark", "model", "provider", "source", "protocol"):
        s.add_argument(f"--{f}")
    s.add_argument("--of", dest="owner", help="claims: only this org's")

    s = sub.add_parser("ledger", help="query the local shared WAL-backed research ledger")
    s.add_argument("--dir", required=True, help="shared ledger directory")
    s.add_argument("--repo")
    s.add_argument("--study")
    s.add_argument("--historical", action="store_true", default=None)

    s = sub.add_parser("query", help="rich query of experiments across local ledger (--dir) or /v1/research")
    s.add_argument("--dir", help="local ledger directory (omit to query cloud /v1/research)")
    s.add_argument("--study")
    s.add_argument("--verdict")
    s.add_argument("--repo")
    s.add_argument("--backend")
    s.add_argument("--search", help="free-text search tokens (e.g. 'gb10 32k decode')")
    s.add_argument("--include-failures", action=argparse.BooleanOptionalAction, default=True)

    s = sub.add_parser("failures", help="list refuted experiments with failure_diagnosis before proposing new runs")
    s.add_argument("--dir", help="local ledger directory (omit to query cloud /v1/research)")
    s.add_argument("--domain", help="study, repo, or domain substring filter")

    s = sub.add_parser("next", help="rank highest-ROI open research opportunities")
    s.add_argument("--dir", help="local ledger directory (omit to query cloud /v1/research)")
    s.add_argument("--domain", help="optional domain filter")
    s.add_argument("--top-k", type=int, default=10)

    s = sub.add_parser("impact", help="compute dependency-scoped regression benchmarks for changed paths")
    s.add_argument("--lineage", help="path to bench_lineage.json")
    s.add_argument("--tasks", help="comma-separated benchmark IDs (defaults to keys of --lineage)")
    s.add_argument("--changed-paths", help="newline file or comma-separated changed repo paths")
    s.add_argument("--changed-artifacts", help="newline file or comma-separated changed artifact hashes")

    s = sub.add_parser("sync-wal", help="upload local ledger experiments/artifacts to /v1/research with SHA-256 readback")
    s.add_argument("--dir", required=True, help="shared ledger directory")

    s = sub.add_parser("sync", help="sync local ledger to /v1/research across record and experiment planes")
    s.add_argument("--dir", default=DEFAULT_LEDGER, help="shared ledger directory")

    s = sub.add_parser("spool", help="drain local ResearchWal to /v1/research/evidence with fsynced cursor")
    s.add_argument("--wal", required=True, help="path to wal.jsonl")
    s.add_argument("--cursor", required=True, help="path to spool cursor json")

    s = sub.add_parser("opportunities", help="inspect prioritized research opportunities")
    s.add_argument("--dir", required=True, help="shared ledger directory")
    s.add_argument("--domain")

    s = sub.add_parser("tick", help="run one autonomous research cycle (pull -> select -> progressive A/B -> sync)")
    _add_auto_args(s, require_executor=True)

    s = sub.add_parser("loop", help="run continuous autonomous research cycles until budget or queue exhaustion")
    _add_auto_args(s, require_executor=True)
    s.add_argument("--max-ticks", type=int, default=10, help="maximum ticks (0 for unlimited)")
    s.add_argument("--budget-minutes", type=float, default=60.0, help="wall-clock budget in minutes")
    s.add_argument("--idle-exit", action=argparse.BooleanOptionalAction, default=True)
    s.add_argument("--sleep-seconds", type=float, default=0.0)

    s = sub.add_parser("controller", help="inspect, validate, or drive the autonomous controller")
    s.add_argument("action", choices=("status", "validate", "tick", "loop"))
    _add_auto_args(s, require_executor=False)
    s.add_argument("--max-ticks", type=int, default=10)
    s.add_argument("--budget-minutes", type=float, default=60.0)
    s.add_argument("--idle-exit", action=argparse.BooleanOptionalAction, default=True)
    s.add_argument("--sleep-seconds", type=float, default=0.0)

    a = p.parse_args(list(argv) if argv is not None else None)
    try:
        out = run(a)
    except Error as e:
        print(f"hanzo-research: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError) as e:
        print(f"hanzo-research: {e}", file=sys.stderr)
        return 2
    try:
        json.dump(dump(out), sys.stdout, indent=1, ensure_ascii=False)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0


def _build_controller(a: argparse.Namespace) -> tuple[AutonomousController, dict[str, Any] | None]:
    reg = CampaignRegistry.from_file(a.campaign) if getattr(a, "campaign", None) else None
    lin = (
        json.loads(Path(a.lineage).read_text(encoding="utf-8"))
        if getattr(a, "lineage", None)
        else None
    )
    ctrl = AutonomousController(
        ledger_dir=a.dir,
        state_dir=a.state,
        registry=reg,
        repo_dir=a.repo_dir,
        max_trials_per_objective=a.max_trials,
    )
    return ctrl, lin


def run(a: argparse.Namespace) -> Any:
    if a.cmd == "ledger":
        ledger = LocalResearchLedger(a.dir)
        return [x.dump() for x in ledger.query(repo=a.repo, study=a.study, historical=a.historical)]
    if a.cmd == "opportunities":
        ledger = LocalResearchLedger(a.dir)
        ops = [
            dict(op.dump(), priority_score=op.priority_score)
            for op in ledger.opportunities.items.values()
            if a.domain is None or op.domain == a.domain
        ]
        return sorted(ops, key=lambda o: (-o["priority_score"], o["opportunity_id"]))
    if a.cmd == "query" and a.dir:
        ledger = LocalResearchLedger(a.dir)
        return [
            x.dump()
            for x in ledger.query_experiments(
                study=a.study,
                verdict=a.verdict,
                repo=a.repo,
                backend=a.backend,
                search=a.search,
                include_failures=a.include_failures,
            )
        ]
    if a.cmd == "failures" and a.dir:
        ledger = LocalResearchLedger(a.dir)
        return [x.dump() for x in ledger.prior_failures(a.domain)]
    if a.cmd == "next" and a.dir:
        ledger = LocalResearchLedger(a.dir)
        return [
            dict(op.dump(), priority_score=op.priority_score)
            for op in ledger.recommended_experiments(domain=a.domain, top_k=a.top_k)
        ]
    if a.cmd == "impact":
        lin = json.loads(Path(a.lineage).read_text(encoding="utf-8")) if a.lineage else {}
        tasks = [x.strip() for x in a.tasks.split(",") if x.strip()] if a.tasks else sorted(lin.keys())
        if not tasks:
            raise ValueError("impact requires --tasks or --lineage with benchmark entries")
        return impacted_benchmarks(
            tasks,
            _read_lines_arg(a.changed_paths) or [],
            lin,
            changed_artifacts=_read_lines_arg(a.changed_artifacts),
        )
    if a.cmd in ("tick", "loop", "controller"):
        action = a.action if a.cmd == "controller" else a.cmd
        if action == "validate":
            if not a.campaign:
                raise ValueError("controller validate requires --campaign")
            reg = CampaignRegistry.from_file(a.campaign)
            return {
                "campaign": reg.campaign,
                "objectives": len(reg.objectives),
                "protected": sum(1 for o in reg.objectives if o.protected),
                "families": sorted(reg.search_space.keys()),
            }
        ctrl, lin = _build_controller(a)
        if action == "status":
            return ctrl.status()
        if not a.executor:
            raise ValueError(f"{action} requires --executor")
        opt_client = Research(base=a.base, project=a.project, org=a.org, repo=a.repo_dir) if a.base else None
        if action == "tick":
            return ctrl.tick(
                executor=a.executor,
                changed_paths=_read_lines_arg(a.changed_paths),
                lineage=lin,
                changed_artifacts=_read_lines_arg(a.changed_artifacts),
                timeout_minutes=a.timeout_minutes,
                auto_sync=a.auto_sync,
                client=opt_client,
            )
        return ctrl.loop(
            executor=a.executor,
            max_ticks=a.max_ticks,
            budget_minutes=a.budget_minutes,
            idle_exit=a.idle_exit,
            sleep_seconds=a.sleep_seconds,
            changed_paths=_read_lines_arg(a.changed_paths),
            lineage=lin,
            changed_artifacts=_read_lines_arg(a.changed_artifacts),
            auto_sync=a.auto_sync,
            client=opt_client,
        )

    r = Research(base=a.base, project=a.project, org=a.org, repo=".")
    if a.cmd in ("sync-wal", "sync"):
        ledger = LocalResearchLedger(a.dir)
        return [rc.dump() for rc in ledger.sync_to_cloud(r)]
    if a.cmd == "spool":
        from .spool import Spooler

        return Spooler.drain(r, a.wal, a.cursor).dump()
    if a.cmd == "query":
        return [
            x.dump()
            for x in r.query_experiments(
                study=a.study,
                verdict=a.verdict,
                repo=a.repo,
                backend=a.backend,
                search=a.search,
                include_failures=a.include_failures,
            )
        ]
    if a.cmd == "failures":
        return [x.dump() for x in r.prior_failures(a.domain)]
    if a.cmd == "next":
        return [
            dict(op.dump(), priority_score=op.priority_score)
            for op in r.recommended_experiments(domain=a.domain, top_k=a.top_k)
        ]
    if a.cmd == "post":
        filed = plan(read(a.file), a.kind)
        if a.dry:
            return filed
        out: dict[str, Any] = dict(r.record(**filed))
        if a.grant or a.publishable is not None or a.trainable is not None:
            ids = [dump(x)["id"] for x in filed.get("runs", [])]
            out["granted"] = {
                i: r.grant(i, visibility=a.grant, publishable=a.publishable, trainable=a.trainable) for i in ids
            }
        return out
    if a.cmd == "list":
        w = a.what
        if w == "runs":
            return r.runs(
                id=a.id,
                benchmark=a.benchmark,
                system=a.system,
                study=a.study,
                completion=a.completion,
                since=a.since,
                until=a.until,
                project=a.scope,
                org=a.public,
            )
        if w == "benchmarks":
            return r.benchmarks(id=a.id, project=a.scope)
        if w == "studies":
            return r.studies(id=a.id, project=a.scope)
        if w == "papers":
            return r.papers(id=a.id, study=a.study, cites=a.cites, project=a.scope)
        if w == "experiments":
            return r.query(project=a.scope, kind=a.kind)
        if w == "artifacts":
            return r.artifacts(run=a.run, project=a.scope)
        if w == "projects":
            return r.projects()
        return r.totals(project=a.scope)
    if a.cmd == "get":
        if a.public and a.kind != "run":
            raise ValueError("--public reads runs only")
        if a.kind == "run":
            return r.get_run(a.id, org=a.public)
        if a.kind == "benchmark":
            return r.get_benchmark(a.id)
        rows: list[Any] = list(r.studies(id=a.id)) if a.kind == "study" else list(r.papers(id=a.id))
        if not rows:
            raise Error(f"no canonical {a.kind} {a.id!r}", 404)
        return rows[0]
    if a.cmd == "grant":
        if a.visibility is None and a.publishable is None and a.trainable is None:
            raise ValueError("grant needs --visibility, --publishable or --trainable")
        if a.sha256:
            return {a.sha256: r.grant(sha256=a.sha256, visibility=a.visibility)}
        if not a.ids:
            raise ValueError("grant needs run ids or --sha256")
        return {i: r.grant(i, visibility=a.visibility, publishable=a.publishable, trainable=a.trainable) for i in a.ids}
    if a.cmd == "retract":
        return r.retract(a.id, a.why)
    if a.cmd == "compare":
        return r.compare(a.a, a.b)
    if a.cmd == "provenance":
        return capture(
            repo=a.repo,
            model=a.model,
            weights=a.weights,
            device=a.device,
            dtype=a.dtype,
            packages=a.package,
            gpu=not a.no_gpu,
        )
    arena = Arena(transport=r.http)
    bench = a.benchmark or "gpqa_diamond"
    if a.what == "catalog":
        return arena.catalog()
    if a.what == "leaderboard":
        return arena.leaderboard(bench)
    if a.what == "claims":
        return arena.claims(
            benchmark=a.benchmark, model=a.model, provider=a.provider, source=a.source, protocol=a.protocol, org=a.owner
        )
    if a.what == "history":
        return arena.history(bench, a.model)
    if a.what == "compare":
        if len(a.models) != 2:
            raise ValueError("arena compare needs two model ids")
        return arena.compare(a.models[0], a.models[1], bench)
    return arena.presets()


if __name__ == "__main__":
    sys.exit(main())
