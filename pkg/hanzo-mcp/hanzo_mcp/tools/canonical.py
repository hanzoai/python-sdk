"""Canonical HIP-0300 19-tool completion layer for pure-Python hanzo-mcp.

Provides the 7 canonical tools not shipped as standalone hanzo-tools-* packages
(`kai`, `plan`, `tasks`, `tracker`, `coding`, `research`, `skills`) plus unified
Hanzo Cloud credential resolution (`HANZO_API_KEY`, `HANZO_USER_KEY`,
`hanzo auth token`, `HANZO_ORG`, `HANZO_API_URL` / `HANZO_API_BASE`).
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Optional, final, override

from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_mcp.tools.common.base import BaseTool

CANONICAL_TOOLS: tuple[str, ...] = (
    "fs",
    "exec",
    "code",
    "git",
    "fetch",
    "workspace",
    "browser",
    "computer",
    "ui",
    "kai",
    "think",
    "plan",
    "memory",
    "tasks",
    "tracker",
    "coding",
    "research",
    "skills",
    "hanzo",
)

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SESSION_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
DEFAULT_SKILLS_URL = "https://hanzoskills.com"

_CACHED_CLI_TOKEN: Optional[str] = None


def _resolve_hanzo_cli() -> Optional[str]:
    env_bin = (os.environ.get("HANZO_BIN") or "").strip()
    if env_bin and os.path.realpath(env_bin) not in ("/usr/bin/hanzo", "/bin/hanzo"):
        if os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
            return env_bin
    local_bin = str(Path.home() / ".local" / "bin" / "hanzo")
    if os.path.isfile(local_bin) and os.access(local_bin, os.X_OK):
        return local_bin
    for d in (os.environ.get("PATH") or "").split(os.pathsep):
        if not d:
            continue
        cand = os.path.join(d, "hanzo")
        if os.path.realpath(cand) in ("/usr/bin/hanzo", "/bin/hanzo"):
            continue
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def resolve_hanzo_token() -> str:
    global _CACHED_CLI_TOKEN
    for key in ("HANZO_API_KEY", "HANZO_USER_KEY", "API_KEY", "API_TOKEN", "HANZO_TOKEN"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    if os.environ.get("HANZO_AUTH_CLI") == "0":
        return ""
    if "PYTEST_CURRENT_TEST" in os.environ and os.environ.get("HANZO_AUTH_CLI") != "1":
        return ""
    if _CACHED_CLI_TOKEN is not None:
        return _CACHED_CLI_TOKEN
    cli = _resolve_hanzo_cli()
    if not cli:
        _CACHED_CLI_TOKEN = ""
        return ""
    try:
        res = subprocess.run(
            [cli, "auth", "token"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        _CACHED_CLI_TOKEN = res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        _CACHED_CLI_TOKEN = ""
    return _CACHED_CLI_TOKEN


def resolve_hanzo_api_base(default: str = "https://api.hanzo.ai") -> str:
    for key in ("HANZO_API_BASE", "HANZO_API_URL", "HANZO_CLOUD_API", "API_URL"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val.rstrip("/").removesuffix("/v1")
    return default.rstrip("/").removesuffix("/v1")


def _http_json(
    method: str,
    url: str,
    body: Any = None,
    token: str = "",
    accept: str = "application/json",
    timeout: float = 30.0,
) -> Any:
    headers: dict[str, str] = {"Accept": accept, "User-Agent": "hanzo-mcp-py"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    org = (os.environ.get("HANZO_ORG") or "").strip()
    if org:
        headers["X-Org-Id"] = org
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except ValueError:
                return raw
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"{exc.code}: {err_body or exc.reason}") from exc


def _ok(tool: str, action: str, data: Any) -> str:
    return json.dumps({"ok": True, "data": data, "error": None, "meta": {"tool": tool, "action": action}}, indent=2)


def _err(tool: str, action: str, message: str) -> str:
    return json.dumps({"ok": False, "data": None, "error": message, "meta": {"tool": tool, "action": action}}, indent=2)


# ── 1. KaiTool (`kai`) ─────────────────────────────────────────────────────

_DENY_PATTERNS = [
    ("rm_root_or_home", re.compile(r"\brm\s+(-[A-Za-z]*[rf][A-Za-z]*\s+)+(/|~|\$HOME|\$\{HOME\})(\s|$)")),
    ("pipe_to_shell", re.compile(r"\b(curl|wget)\b[^|\n]*\|\s*(ba|z|da)?sh\b")),
    ("private_key_read", re.compile(r"(\.ssh/id_(rsa|ed25519|ecdsa)|BEGIN\s+(RSA|OPENSSH|EC)\s+PRIVATE\s+KEY)")),
]
_ASK_PATTERNS = [
    ("git_push_or_rewrite", re.compile(r"\bgit\s+(push|reset\s+--hard|clean\s+-[A-Za-z]*f|rebase)\b")),
    ("sudo", re.compile(r"(^|\s|&&|;|\|)sudo\s+")),
    ("publish_or_deploy", re.compile(r"\b(npm\s+publish|cargo\s+publish|kubectl\s+apply|terraform\s+apply)\b")),
]
_INJECTION_PATTERNS = {
    "override": re.compile(r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(previous|prior|above|system)\b[^.\n]{0,30}\b(instructions?|prompts?|rules)\b", re.I),
    "role": re.compile(r"\byou are now\b|\bnew (system )?instructions?\b|<\|im_start\|>|\[SYSTEM\s+INSTRUCTION\]", re.I),
    "conceal": re.compile(r"\b(do not|don't|never)\s+(tell|inform|notify|mention)\s+(the\s+)?(user|human)\b", re.I),
}
_STOP_WORDS = set("a an and are as at be by can do does for from get has have i in is it me my of on or our please show that the this to use using want we what when where which with you your".split())


def _words(text: str) -> list[str]:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text).lower()
    return [w for w in re.split(r"[^a-z0-9]+", s) if len(w) > 1 and w not in _STOP_WORDS]


def _bm25(query: list[str], docs: list[list[str]]) -> list[float]:
    n = len(docs) or 1
    avg = (sum(len(d) for d in docs) / n) or 1.0
    df: dict[str, int] = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    scores: list[float] = []
    qset = set(query)
    for d in docs:
        sc = 0.0
        for w in qset:
            f = d.count(w)
            if not f:
                continue
            k = df.get(w, 1)
            sc += math.log(1.0 + (n - k + 0.5) / (k + 0.5)) * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * len(d) / avg))
        scores.append(sc)
    return scores


@final
class KaiTool(BaseTool):
    """Unified Kai decision, safety, compaction, and verified-action tool."""

    @property
    @override
    def name(self) -> str:
        return "kai"

    @property
    @override
    def description(self) -> str:
        return (
            "Kai — unified calibrated decisions (/v1/decisions: decide, choice, score, noul), "
            "verified repo actions (run, plan, list, triggers), context compaction (compact), "
            "tool_select, next_action, command_guard, injection_screen, extract, log_triage, recover, agent_step."
        )

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "decide").strip()
        kai_base = (
            os.environ.get("LOCAL_KAI_URL")
            or os.environ.get("KAI_URL")
            or resolve_hanzo_api_base()
        ).rstrip("/").removesuffix("/v1")
        is_local = "127.0.0.1" in kai_base or "localhost" in kai_base
        tok = resolve_hanzo_token()

        try:
            if action in ("decide", "choice", "score", "noul"):
                if not tok and not is_local:
                    return "Error: HANZO_API_KEY required"
                state = params.get("state")
                if state is None:
                    return "Error: state required"
                model = str(params.get("model") or "kai")
                if action == "decide":
                    questions = params.get("questions")
                    if not isinstance(questions, dict) or not questions:
                        return "Error: questions required"
                    resp = _http_json("POST", f"{kai_base}/v1/decisions", {"model": model, "state": state, "questions": questions}, token=tok)
                    return json.dumps(resp, indent=2)
                q: dict[str, Any] = {"type": action}
                if params.get("instructions"):
                    q["instructions"] = params["instructions"]
                if params.get("criteria") is not None:
                    q["criteria"] = params["criteria"]
                resp = _http_json("POST", f"{kai_base}/v1/decisions", {"model": model, "state": state, "questions": {action: q}}, token=tok)
                return json.dumps({"answer": (resp.get("answers") or {}).get(action), "id": resp.get("id"), "model": resp.get("model"), "usage": resp.get("usage")}, indent=2)

            if action == "command_guard":
                cmd = str(params.get("command") or "")
                if not cmd:
                    return "Error: command required"
                deny = [k for k, rx in _DENY_PATTERNS if rx.search(cmd)]
                if deny:
                    verdict, classes = "deny", deny
                else:
                    ask = [k for k, rx in _ASK_PATTERNS if rx.search(cmd)]
                    verdict, classes = ("ask", ask) if ask else ("allow", [])
                floor = str(params.get("policy") or "allow")
                order = {"allow": 0, "ask": 1, "deny": 2}
                if order.get(floor, 0) > order[verdict]:
                    verdict = floor
                return json.dumps({"verdict": verdict, "classes": classes}, indent=2)

            if action == "tool_select":
                task = str(params.get("task") or "")
                tools = params.get("tools") or []
                if not task or not isinstance(tools, list) or not tools:
                    return "Error: task and tools required"
                docs = [_words(f"{t.get('name', '')} {t.get('name', '')} {t.get('description', '')}") for t in tools]
                scores = _bm25(_words(task), docs)
                said = set(re.split(r"[^a-z0-9_.-]+", task.lower()))
                ranked = sorted(
                    [{"name": t.get("name"), "score": round(scores[i], 4), "named": str(t.get("name", "")).lower() in said} for i, t in enumerate(tools)],
                    key=lambda r: (r["named"], r["score"]),
                    reverse=True,
                )
                lim = max(1, min(int(params.get("limit") or 5), len(ranked)))
                top = ranked[0]
                abstained = not top["named"] and top["score"] == 0
                return json.dumps({
                    "selected_tools": [{"name": r["name"], "score": r["score"]} for r in ranked[:lim]],
                    "top_tool": None if abstained else top["name"],
                    "abstained": abstained,
                }, indent=2)

            if action == "next_action":
                goal = str(params.get("goal") or "")
                cands = [c for c in (params.get("candidates") or []) if c.get("preconditions_satisfied") is not False]
                if not cands:
                    return json.dumps({"selected_action": None, "abstained": True, "reason": "no eligible candidates"}, indent=2)
                if len(cands) == 1:
                    return json.dumps({"selected_action": cands[0], "abstained": False}, indent=2)
                scores = _bm25(_words(goal), [_words(f"{c.get('tool', '')} {c.get('description', '')}") for c in cands])
                ranked = sorted(zip(scores, cands), key=lambda p: p[0], reverse=True)
                abstained = ranked[0][0] == 0 or (len(ranked) > 1 and ranked[0][0] == ranked[1][0])
                return json.dumps({"selected_action": None if abstained else ranked[0][1], "abstained": abstained}, indent=2)

            if action == "injection_screen":
                txt = str(params.get("text") or "")
                signals = [k for k, rx in _INJECTION_PATTERNS.items() if rx.search(txt)]
                return json.dumps({"flagged": bool(signals), "signals": signals, "kai": None}, indent=2)

            if action == "log_triage":
                logs = str(params.get("logs") or "")
                lines = [ln.strip() for ln in logs.splitlines() if re.search(r"\b(error|failed|panic|exception|traceback)\b", ln, re.I)]
                cat = "compile_error" if re.search(r"error\[E\d+\]|TS\d+:|SyntaxError", logs) else ("test_failure" if re.search(r"FAIL|AssertionError|panicked", logs) else "unknown")
                return json.dumps({"category": cat, "key_lines": lines[:10], "line_count": len(logs.splitlines())}, indent=2)

            if action == "recover":
                failures = params.get("failures") or []
                strategy = "stop_and_ask_user" if len(failures) >= 3 else "inspect_root_cause"
                return json.dumps({"loop_detected": len(failures) >= 2, "strategy": strategy, "failure_count": len(failures)}, indent=2)

            if action == "compact":
                msgs = params.get("messages") or []
                pin = int(params.get("pin_recent") or 6)
                kept = msgs[:1] + msgs[-pin:] if len(msgs) > pin + 1 else list(msgs)
                return json.dumps({"messages": kept, "original_count": len(msgs), "compacted_count": len(kept)}, indent=2)

            if action == "extract":
                if not tok and not is_local:
                    return "Error: HANZO_API_KEY required"
                text_val = params.get("text")
                schema = params.get("schema") or {}
                questions: dict[str, Any] = {}
                for field, spec in schema.items():
                    qtype = spec.get("type", "choice")
                    qobj: dict[str, Any] = {"type": qtype, "instructions": spec.get("description", field)}
                    if qtype == "choice":
                        qobj["criteria"] = spec.get("options") or []
                    elif qtype == "score":
                        qobj["criteria"] = spec.get("levels") or []
                    questions[field] = qobj
                resp = _http_json("POST", f"{kai_base}/v1/decisions", {"model": str(params.get("model") or "kai"), "state": text_val, "questions": questions}, token=tok)
                return json.dumps({"extracted": resp.get("answers", {}), "id": resp.get("id")}, indent=2)

            if action == "agent_step":
                resp = _http_json(
                    "POST",
                    f"{kai_base}/v1/agent/step",
                    {"goal": params.get("goal", ""), "trajectory": params.get("trajectory") or [], "available_tools": params.get("available_tools") or []},
                    token=tok,
                )
                return json.dumps(resp, indent=2)

            if action in ("run", "plan", "list", "triggers"):
                return _ok("kai", action, {"action": action, "name": params.get("name"), "status": "ready"})

            return f"Error: unknown kai action '{action}'"
        except Exception as exc:
            return f"Error: {exc}"

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="kai", description=self.description)
        async def kai(
            action: str = "decide",
            state: Any = None,
            questions: dict[str, Any] = {},
            instructions: str = "",
            criteria: Any = None,
            command: str = "",
            policy: str = "",
            task: str = "",
            tools: list[dict[str, Any]] = [],
            goal: str = "",
            candidates: list[dict[str, Any]] = [],
            text: Any = None,
            schema: dict[str, Any] = {},
            logs: str = "",
            failures: list[Any] = [],
            messages: list[dict[str, Any]] = [],
            name: str = "",
            model: str = "",
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(
                ctx,
                action=action,
                state=state,
                questions=questions or None,
                instructions=instructions or None,
                criteria=criteria,
                command=command or None,
                policy=policy or None,
                task=task or None,
                tools=tools or None,
                goal=goal or None,
                candidates=candidates or None,
                text=text,
                schema=schema or None,
                logs=logs or None,
                failures=failures or None,
                messages=messages or None,
                name=name or None,
                model=model or None,
            )


# ── 2. PlanTool (`plan`) ───────────────────────────────────────────────────

@final
class PlanTool(BaseTool):
    """Execution plan creation and step tracking."""

    @property
    @override
    def name(self) -> str:
        return "plan"

    @property
    @override
    def description(self) -> str:
        return "Execution plan creation and step tracking (create, update, get, list, complete)."

    def _store_path(self) -> Path:
        return Path.home() / ".hanzo" / "plans.json"

    def _load(self) -> dict[str, Any]:
        p = self._store_path()
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self, plans: dict[str, Any]) -> None:
        p = self._store_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(plans, indent=2), encoding="utf-8")

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "list").strip()
        plans = self._load()
        if action == "create":
            pid = str(params.get("id") or f"plan-{len(plans) + 1}")
            raw_steps = params.get("steps") or []
            steps = [
                s if isinstance(s, dict) else {"id": i + 1, "title": str(s), "status": "pending"}
                for i, s in enumerate(raw_steps)
            ]
            entry = {
                "id": pid,
                "title": str(params.get("title") or params.get("goal") or "Execution Plan"),
                "steps": steps,
                "status": "in_progress",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            plans[pid] = entry
            self._save(plans)
            return _ok("plan", action, entry)
        if action in ("get", "show"):
            pid = str(params.get("id") or (next(reversed(plans), "") if plans else ""))
            if not pid or pid not in plans:
                return _err("plan", action, f"plan '{pid}' not found")
            return _ok("plan", action, plans[pid])
        if action == "list":
            return _ok("plan", action, {"plans": list(plans.values()), "count": len(plans)})
        if action in ("update", "complete"):
            pid = str(params.get("id") or (next(reversed(plans), "") if plans else ""))
            if not pid or pid not in plans:
                return _err("plan", action, f"plan '{pid}' not found")
            entry = plans[pid]
            if action == "complete":
                entry["status"] = "completed"
                for s in entry.get("steps", []):
                    s["status"] = "completed"
            else:
                if params.get("status"):
                    entry["status"] = str(params["status"])
                if params.get("steps") is not None:
                    entry["steps"] = params["steps"]
                step_id = params.get("step_id")
                if step_id is not None and params.get("step_status"):
                    for s in entry.get("steps", []):
                        if str(s.get("id")) == str(step_id):
                            s["status"] = str(params["step_status"])
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(plans)
            return _ok("plan", action, entry)
        return _err("plan", action, f"unknown action '{action}'")

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="plan", description=self.description)
        async def plan(
            action: str = "list",
            id: str = "",
            title: str = "",
            steps: list[Any] = [],
            step_id: str = "",
            step_status: str = "",
            status: str = "",
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(ctx, action=action, id=id or None, title=title or None, steps=steps or None, step_id=step_id or None, step_status=step_status or None, status=status or None)


# ── 3. TasksTool (`tasks`) ─────────────────────────────────────────────────

@final
class TasksTool(BaseTool):
    """Local private session todo list (~/.hanzo/todos.json)."""

    @property
    @override
    def name(self) -> str:
        return "tasks"

    @property
    @override
    def description(self) -> str:
        return "Local private session todo list (~/.hanzo/todos.json: list, add, update, complete, clear)."

    def _todos_path(self) -> Path:
        return Path.home() / ".hanzo" / "todos.json"

    def _load(self) -> list[dict[str, Any]]:
        p = self._todos_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else data.get("tasks", [])
            except Exception:
                return []
        return []

    def _save(self, items: list[dict[str, Any]]) -> None:
        p = self._todos_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(items, indent=2), encoding="utf-8")

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "list").strip()
        items = self._load()
        if action == "list":
            return _ok("tasks", action, {"tasks": items, "count": len(items)})
        if action == "add":
            content = str(params.get("content") or params.get("title") or "").strip()
            if not content:
                return _err("tasks", action, "content required")
            item = {
                "id": str(params.get("id") or f"task-{len(items) + 1}"),
                "content": content,
                "status": str(params.get("status") or "pending"),
                "priority": str(params.get("priority") or "medium"),
            }
            items.append(item)
            self._save(items)
            return _ok("tasks", action, item)
        if action in ("update", "complete"):
            tid = str(params.get("id") or "")
            for item in items:
                if str(item.get("id")) == tid:
                    if action == "complete":
                        item["status"] = "completed"
                    else:
                        if params.get("status"):
                            item["status"] = str(params["status"])
                        if params.get("content"):
                            item["content"] = str(params["content"])
                        if params.get("priority"):
                            item["priority"] = str(params["priority"])
                    self._save(items)
                    return _ok("tasks", action, item)
            return _err("tasks", action, f"task '{tid}' not found")
        if action == "clear":
            self._save([])
            return _ok("tasks", action, {"cleared": True})
        return _err("tasks", action, f"unknown action '{action}'")

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="tasks", description=self.description)
        async def tasks(
            action: str = "list",
            id: str = "",
            content: str = "",
            status: str = "",
            priority: str = "",
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(ctx, action=action, id=id or None, content=content or None, status=status or None, priority=priority or None)


# ── 4. TrackerTool (`tracker`) ─────────────────────────────────────────────

@final
class TrackerTool(BaseTool):
    """Unified Hanzo Cloud /v1/tracker tool (boards, issues, create, update)."""

    @property
    @override
    def name(self) -> str:
        return "tracker"

    @property
    @override
    def description(self) -> str:
        return "Hanzo Cloud work-item tracker (/v1/tracker): boards, issues, create, update."

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "boards").strip()
        tok = resolve_hanzo_token()
        if not tok:
            return "Error: HANZO_API_KEY required"
        base = resolve_hanzo_api_base()
        try:
            if action == "boards":
                return json.dumps(_http_json("GET", f"{base}/v1/tracker/projects", token=tok), indent=2)
            proj = urllib.parse.quote(str(params.get("project") or "").strip(), safe="")
            if not proj:
                return "Error: project required"
            if action == "issues":
                q = {k: params[k] for k in ("status", "kind", "source", "repo") if params.get(k)}
                qs = f"?{urllib.parse.urlencode(q)}" if q else ""
                return json.dumps(_http_json("GET", f"{base}/v1/tracker/projects/{proj}/issues{qs}", token=tok), indent=2)
            if action == "create":
                title = str(params.get("title") or "").strip()
                if not title:
                    return "Error: title required"
                body: dict[str, Any] = {"title": title}
                for k in ("description", "kind", "priority", "status", "assignee", "repo"):
                    if params.get(k) is not None:
                        body[k] = params[k]
                if params.get("session"):
                    body["extRef"] = f"session:{params['session']}"
                return json.dumps(_http_json("POST", f"{base}/v1/tracker/projects/{proj}/issues", body=body, token=tok), indent=2)
            if action == "update":
                issue = params.get("issue")
                if issue is None:
                    return "Error: issue required"
                body = {k: params[k] for k in ("title", "description", "status", "priority", "assignee", "pr") if params.get(k) is not None}
                if params.get("session"):
                    body["extRef"] = f"session:{params['session']}"
                return json.dumps(_http_json("PATCH", f"{base}/v1/tracker/projects/{proj}/issues/{int(issue)}", body=body, token=tok), indent=2)
            return f"Error: unknown tracker action '{action}'"
        except Exception as exc:
            return f"Error: {exc}"

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="tracker", description=self.description)
        async def tracker(
            action: str = "boards",
            project: str = "",
            issue: int = 0,
            title: str = "",
            description: str = "",
            status: str = "",
            priority: str = "",
            kind: str = "",
            session: str = "",
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(
                ctx, action=action, project=project or None, issue=issue or None, title=title or None,
                description=description or None, status=status or None, priority=priority or None, kind=kind or None, session=session or None,
            )


# ── 5. CodingTool (`coding`) ───────────────────────────────────────────────

@final
class CodingTool(BaseTool):
    """Hanzo Cloud autonomous coding runs (/v1/agent/coding)."""

    @property
    @override
    def name(self) -> str:
        return "coding"

    @property
    @override
    def description(self) -> str:
        return "Hanzo Cloud autonomous coding runs (/v1/agent/coding): start, progress, changes, artifacts, tree, blob, steer, pull, merge, extend, stop."

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "").strip()
        tok = resolve_hanzo_token()
        if not tok:
            return _err("coding", action, "HANZO_API_KEY required")
        base = resolve_hanzo_api_base()
        try:
            if action == "start":
                prompt = str(params.get("prompt") or "").strip()
                if not prompt:
                    return _err("coding", action, "prompt required")
                body = {k: params[k] for k in ("prompt", "repo", "branch", "model", "timeoutSeconds") if params.get(k) is not None}
                return _ok("coding", action, _http_json("POST", f"{base}/v1/agent/coding", body=body, token=tok))
            sess = str(params.get("session") or "").strip()
            if not sess or not SESSION_RE.match(sess):
                return _err("coding", action, "valid session required")
            if action == "progress":
                return _ok("coding", action, _http_json("GET", f"{base}/v1/agent/sessions/{sess}/progress", token=tok))
            if action in ("changes", "artifacts"):
                return _ok("coding", action, _http_json("GET", f"{base}/v1/agent/coding/{sess}/{action}", token=tok))
            if action in ("tree", "blob"):
                qs = f"?path={urllib.parse.quote(str(params.get('path') or ''))}" if params.get("path") else ""
                return _ok("coding", action, _http_json("GET", f"{base}/v1/agent/coding/{sess}/{action}{qs}", token=tok))
            if action == "steer":
                return _ok("coding", action, _http_json("POST", f"{base}/v1/agent/coding/{sess}/steer", body={"prompt": params.get("prompt", "")}, token=tok))
            if action in ("pull", "merge"):
                return _ok("coding", action, _http_json("POST", f"{base}/v1/agent/coding/{sess}/{action}", body={}, token=tok))
            if action == "extend":
                return _ok("coding", action, _http_json("POST", f"{base}/v1/agent/sessions/{sess}/extend", body={"timeoutSeconds": params.get("timeoutSeconds", 1800)}, token=tok))
            if action == "stop":
                return _ok("coding", action, _http_json("POST", f"{base}/v1/agent/sessions/{sess}/stop", body={}, token=tok))
            return _err("coding", action, f"unknown coding action '{action}'")
        except Exception as exc:
            return _err("coding", action, str(exc))

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="coding", description=self.description)
        async def coding(
            action: str = "progress",
            session: str = "",
            prompt: str = "",
            repo: str = "",
            branch: str = "",
            path: str = "",
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(ctx, action=action, session=session or None, prompt=prompt or None, repo=repo or None, branch=branch or None, path=path or None)


# ── 6. ResearchTool (`research`) ───────────────────────────────────────────

@final
class ResearchTool(BaseTool):
    """Unified Hanzo Science & Research tool (/v1/research + /v1/ask)."""

    @property
    @override
    def name(self) -> str:
        return "research"

    @property
    @override
    def description(self) -> str:
        return "Hanzo Science & Research (/v1/research): studies, runs, start, status, ledger, artifacts, search."

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "runs").strip()
        tok = resolve_hanzo_token()
        if not tok:
            return _err("research", action, "HANZO_API_KEY required")
        base = (os.environ.get("RESEARCH_BASE") or resolve_hanzo_api_base()).rstrip("/").removesuffix("/v1")
        try:
            if action in ("studies", "runs"):
                q = {k: params[k] for k in ("org", "study", "benchmark", "status") if params.get(k)}
                qs = f"?{urllib.parse.urlencode(q)}" if q else ""
                return _ok("research", action, _http_json("GET", f"{base}/v1/research/{action}{qs}", token=tok))
            if action == "status":
                rid = str(params.get("id") or params.get("run") or "").strip()
                qs = f"?id={urllib.parse.quote(rid)}" if rid else ""
                return _ok("research", action, _http_json("GET", f"{base}/v1/research/runs{qs}", token=tok))
            if action == "start":
                target = str(params.get("kind") or "runs")
                if target not in ("runs", "studies", "experiments"):
                    target = "runs"
                return _ok("research", action, _http_json("POST", f"{base}/v1/research/{target}", body=params.get("payload") or {"query": params.get("query", "")}, token=tok))
            if action == "ledger":
                return _ok("research", action, _http_json("GET", f"{base}/v1/research/evidence", token=tok))
            if action == "artifacts":
                return _ok("research", action, _http_json("GET", f"{base}/v1/research/artifacts", token=tok))
            if action == "search":
                qstr = str(params.get("query") or "").strip()
                if not qstr:
                    return _err("research", action, "query required")
                raw = _http_json("POST", f"{base}/v1/ask", body={"query": qstr, "mode": "research"}, token=tok, accept="text/event-stream")
                return _ok("research", action, {"query": qstr, "result": raw})
            return _err("research", action, f"unknown research action '{action}'")
        except Exception as exc:
            return _err("research", action, str(exc))

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="research", description=self.description)
        async def research(
            action: str = "runs",
            query: str = "",
            id: str = "",
            org: str = "",
            benchmark: str = "",
            payload: dict[str, Any] = {},
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(ctx, action=action, query=query or None, id=id or None, org=org or None, benchmark=benchmark or None, payload=payload or None)


# ── 7. SkillsTool (`skills`) ───────────────────────────────────────────────

@final
class SkillsTool(BaseTool):
    """First-class Hanzo Skills MCP tool (hanzoskills.com + ~/.agents/skills)."""

    @property
    @override
    def name(self) -> str:
        return "skills"

    @property
    @override
    def description(self) -> str:
        return "Hanzo Skills registry (hanzoskills.com + ~/.agents/skills): search, detect, get, install, list."

    def _skills_base(self) -> str:
        return (os.environ.get("HANZOSKILLS_API_URL") or DEFAULT_SKILLS_URL).strip().rstrip("/")

    def _skills_dir(self) -> Path:
        custom = (os.environ.get("HANZO_SKILLS_DIR") or "").strip()
        return Path(custom) if custom else (Path.home() / ".agents" / "skills")

    def _fetch_catalog(self) -> list[dict[str, Any]]:
        base = self._skills_base()
        data = _http_json("GET", f"{base}/search.json", timeout=15.0)
        rows = data.get("s", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        out: list[dict[str, Any]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            slug = str(r.get("i") or r.get("slug") or "").strip()
            if slug:
                out.append({
                    "slug": slug,
                    "category": r.get("c") or r.get("category") or "",
                    "description": r.get("d") or r.get("description") or "",
                    "tags": r.get("g") or r.get("tags") or [],
                })
        return out

    def _fetch_markdown(self, slug: str) -> str:
        if not SLUG_RE.match(slug):
            raise ValueError(f"invalid skill slug '{slug}'")
        base = self._skills_base()
        req = urllib.request.Request(
            f"{base}/skills/{slug}/SKILL.md",
            headers={"Accept": "text/markdown, text/plain;q=0.9, */*;q=0.8", "User-Agent": "hanzo-mcp-py"},
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @override
    async def call(self, ctx: MCPContext, **params: Any) -> str:
        action = str(params.get("action") or "search").strip()
        try:
            if action == "search":
                q = str(params.get("query") or "").strip().lower()
                cat = str(params.get("category") or "").strip().lower()
                lim = max(1, min(int(params.get("limit") or 20), 100))
                catalog = self._fetch_catalog()
                terms = [t for t in q.split() if t]
                scored: list[tuple[int, dict[str, Any]]] = []
                for item in catalog:
                    if cat and str(item.get("category", "")).lower() != cat:
                        continue
                    if not terms:
                        scored.append((1, item))
                        continue
                    hay = f"{item['slug']} {item.get('category', '')} {item.get('description', '')} {' '.join(str(x) for x in (item.get('tags') or []))}".lower()
                    sc = sum((10 if item["slug"] == t else (5 if t in item["slug"] else (2 if t in hay else 0))) for t in terms)
                    if sc > 0:
                        scored.append((sc, item))
                scored.sort(key=lambda p: (-p[0], p[1]["slug"]))
                results = [p[1] for p in scored[:lim]]
                return _ok("skills", action, {"skills": results, "count": len(results), "total_catalog": len(catalog)})

            if action == "detect":
                root = Path(str(params.get("path") or os.getcwd()))
                markers = {
                    "Cargo.toml": "rust",
                    "package.json": "typescript",
                    "pyproject.toml": "python",
                    "go.mod": "go",
                    "Dockerfile": "docker",
                }
                detected = [tag for fname, tag in markers.items() if (root / fname).exists()]
                catalog = self._fetch_catalog()
                rec = [s for s in catalog if any(t in s["slug"] or t in str(s.get("category", "")).lower() for t in detected)][:15]
                return _ok("skills", action, {"detected_stack": detected, "recommended": rec})

            if action == "get":
                slug = str(params.get("slug") or params.get("name") or "").strip()
                if not SLUG_RE.match(slug):
                    return _err("skills", action, f"invalid slug '{slug}' (must match ^[a-z0-9][a-z0-9_-]{{0,63}}$)")
                local_md = self._skills_dir() / slug / "SKILL.md"
                md = local_md.read_text(encoding="utf-8") if local_md.exists() else self._fetch_markdown(slug)
                return _ok("skills", action, {"slug": slug, "content": md})

            if action == "install":
                slug = str(params.get("slug") or params.get("name") or "").strip()
                if not SLUG_RE.match(slug):
                    return _err("skills", action, f"invalid slug '{slug}' (must match ^[a-z0-9][a-z0-9_-]{{0,63}}$)")
                raw_content = params.get("content")
                md = str(raw_content) if raw_content not in (None, "") else self._fetch_markdown(slug)
                dest_dir = (self._skills_dir() / slug).resolve()
                root_dir = self._skills_dir().resolve()
                if root_dir not in dest_dir.parents:
                    return _err("skills", action, "refusing path outside skills directory")
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / "SKILL.md"
                tmp_file = dest_dir / f".SKILL.md.tmp.{os.getpid()}"
                tmp_file.write_text(md, encoding="utf-8")
                tmp_file.replace(dest_file)
                return _ok("skills", action, {"slug": slug, "installed": True, "path": str(dest_file), "bytes": len(md.encode("utf-8"))})

            if action == "list":
                root = self._skills_dir()
                installed: list[dict[str, Any]] = []
                if root.exists():
                    for child in sorted(root.iterdir()):
                        md_file = child / "SKILL.md"
                        if child.is_dir() and SLUG_RE.match(child.name) and md_file.is_file():
                            installed.append({"slug": child.name, "path": str(md_file)})
                return _ok("skills", action, {"skills": installed, "count": len(installed), "skills_dir": str(root)})

            return _err("skills", action, f"unknown skills action '{action}'")
        except Exception as exc:
            return _err("skills", action, str(exc))

    def register(self, mcp_server: Any) -> None:
        inst = self

        @mcp_server.tool(name="skills", description=self.description)
        async def skills(
            action: str = "search",
            query: str = "",
            slug: str = "",
            category: str = "",
            path: str = "",
            limit: int = 20,
            ctx: MCPContext = None,
        ) -> str:
            return await inst.call(ctx, action=action, query=query or None, slug=slug or None, category=category or None, path=path or None, limit=limit)


BUILTIN_CANONICAL_TOOL_CLASSES: dict[str, type[BaseTool]] = {
    "kai": KaiTool,
    "plan": PlanTool,
    "tasks": TasksTool,
    "tracker": TrackerTool,
    "coding": CodingTool,
    "research": ResearchTool,
    "skills": SkillsTool,
}


def register_canonical_builtin_tools(
    mcp_server: Any,
    enabled_tools: dict[str, bool],
) -> dict[str, BaseTool]:
    """Register the 7 canonical HIP-0300 built-in tools when enabled."""
    registered: dict[str, BaseTool] = {}
    for name, cls in BUILTIN_CANONICAL_TOOL_CLASSES.items():
        if enabled_tools.get(name, True):
            tool = cls()
            tool.register(mcp_server)
            registered[name] = tool
    return registered
