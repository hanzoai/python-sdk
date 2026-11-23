"""Native `hanzoai/tasks` scheduling and linked-machine (`hanzod` / `hanzo link`) orchestration.

Routes recurring research schedules, targeted durable runs (`evo`, `dgx`, `evo,dgx`),
cross-architecture fan-out, busy-aware deferral retries, and SSE completion streaming through
`/v1/workflow/namespaces/<ns>`, `/v1/workflow/events`, `/v1/compute/fleet/workers`, and `/v1/agent/targets`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
import time
from typing import TYPE_CHECKING, Any, Mapping, Sequence
import urllib.error
from urllib.parse import quote

from . import canonical
from .errors import Error
from .wire import Wire

if TYPE_CHECKING:
    from .client import Research

__all__ = [
    "DEFAULT_RETRY_POLICY",
    "LinkedMachine",
    "infer_machine_backends",
    "parse_targets",
    "resolve_task_queue",
    "list_machines",
    "dispatch_task",
    "wait_gpu_job",
    "release_gpu_job",
    "orchestrate_across_machines",
    "ensure_workflow_namespace",
    "create_schedule",
    "list_schedules",
    "describe_schedule",
    "trigger_schedule",
    "pause_schedule",
    "resume_schedule",
    "delete_schedule",
]

DEFAULT_RETRY_POLICY: dict[str, Any] = {
    "initialInterval": "5s",
    "backoffCoefficient": 2.0,
    "maximumInterval": "60s",
    "maximumAttempts": 8,
}

_ONLINE_STATES = {"online", "ready", "idle", "busy", "running", "active"}
_TERMINAL_ACTIVITY_STATES = {
    "ACTIVITY_TASK_STATE_COMPLETED",
    "ACTIVITY_TASK_STATE_FAILED",
    "ACTIVITY_TASK_STATE_CANCELED",
    "ACTIVITY_TASK_STATE_TIMED_OUT",
}
_TERMINAL_SSE_EVENTS = {
    "activity.completed",
    "activity.failed",
    "activity.canceled",
    "activity.timedout",
}


@dataclass
class LinkedMachine(Wire):
    """A linked compute or Desktop (`hanzod` / `hanzo link` / `/v1/agent/targets`) machine."""

    id: str = ""
    hostname: str = ""
    status: str = ""
    os: str = ""
    arch: str = ""
    cpus: int = 0
    memory_bytes: int = 0
    memory_gb: float = 0.0
    capacity: str = ""
    gpus: list[dict[str, Any]] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    backends: list[str] = field(default_factory=list)
    job_queue: str = ""
    task_queue: str = ""
    busy: bool = False
    busy_reason: str = ""


def parse_targets(target: str | Sequence[str] | None) -> list[str]:
    """Parse single or comma-separated target names (e.g. `'evo,dgx'` -> `['evo', 'dgx']`)."""
    if target is None:
        return []
    if isinstance(target, str):
        return [part.strip() for part in target.split(",") if part.strip()]
    out: list[str] = []
    for item in target:
        for part in str(item).split(","):
            cleaned = part.strip()
            if cleaned:
                out.append(cleaned)
    return out


def _parse_mem_bytes(val: Any) -> int:
    if isinstance(val, bool) or val is None:
        return 0
    if isinstance(val, (int, float)):
        return max(0, int(val))
    text = str(val).strip()
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]*)$", text)
    if not m:
        return 0
    num = float(m.group(1))
    unit = m.group(2).lower()
    if unit in ("tib", "tb"):
        return int(num * (1024**4))
    if unit in ("gib", "gb", "g"):
        return int(num * (1024**3))
    if unit in ("mib", "mb", "m"):
        return int(num * (1024**2))
    if unit in ("kib", "kb", "k"):
        return int(num * 1024)
    return int(num)


def _parse_capacity_hint(capacity: str) -> tuple[int, int]:
    cpus = 0
    mem_bytes = 0
    cpu_match = re.search(r"(\d+)\s*(?:vcpu|cpu|cores?)", capacity, flags=re.IGNORECASE)
    if cpu_match:
        cpus = int(cpu_match.group(1))
    mem_match = re.search(r"(\d+(?:\.\d+)?)\s*([tgm]i?b?)\b", capacity, flags=re.IGNORECASE)
    if mem_match:
        mem_bytes = _parse_mem_bytes(f"{mem_match.group(1)} {mem_match.group(2)}")
    return cpus, mem_bytes


def infer_machine_backends(row: Mapping[str, Any]) -> list[str]:
    """Infer supported execution backends (`CUDA`, `ROCM`, `METAL`, `VULKAN`, `CPU`) from worker/target metadata."""
    found: set[str] = {"CPU"}
    spec = row.get("spec") if isinstance(row.get("spec"), Mapping) else {}
    os_name = str(row.get("os") or spec.get("os") or "").strip().lower()
    caps = [str(x).strip().lower() for x in (row.get("capabilities") or []) if x]
    explicit = [str(x).strip().upper() for x in (row.get("backends") or []) if x]
    for b in explicit:
        if b:
            found.add(b)
    hint_blob = " ".join(
        [
            " ".join(caps),
            str(row.get("capacity") or ""),
            str(row.get("label") or ""),
            str(row.get("cpuModel") or ""),
        ]
    ).lower()
    if any(k in hint_blob for k in ("cuda", "nvidia", "gb10", "gh200", "h100", "h200", "a100", "b200", "rtx")):
        found.add("CUDA")
    if "metal" in hint_blob or os_name in ("darwin", "macos", "ios") or any(
        k in hint_blob for k in ("apple m1", "apple m2", "apple m3", "apple m4", "m1 max", "m4 max")
    ):
        found.add("METAL")
    if any(k in hint_blob for k in ("rocm", "hip", "strix", "gfx11", "radeon", "instinct", "ryzen ai max")):
        found.add("ROCM")
    if any(k in hint_blob for k in ("vulkan", "strix", "gfx11", "radeon", "ryzen ai max")):
        found.add("VULKAN")

    gpus = list(row.get("gpus") or spec.get("gpus") or [])
    for gpu in gpus:
        if not isinstance(gpu, Mapping):
            continue
        blob = f"{gpu.get('name', '')} {gpu.get('arch', '')} {gpu.get('vendor', '')}".lower()
        if any(
            k in blob
            for k in ("nvidia", "cuda", "gb10", "gh200", "h100", "h200", "a100", "b200", "rtx", "geforce", "tesla", "sm_")
        ):
            found.add("CUDA")
        if any(k in blob for k in ("apple", "metal", "m1", "m2", "m3", "m4")):
            found.add("METAL")
        if any(k in blob for k in ("amd", "radeon", "instinct", "rocm", "gfx", "mi2", "mi3", "strix")):
            found.add("ROCM")
        if any(k in blob for k in ("vulkan", "radeon", "gfx", "strix")):
            found.add("VULKAN")

    order = ("CUDA", "ROCM", "METAL", "VULKAN", "CPU")
    return [b for b in order if b in found] + sorted(found - set(order))


def resolve_task_queue(target: str | None) -> str:
    """Map `None` or `'any'` to shared `'gpu-jobs'`, and `<machine_id>` to targeted `'gpu:<machine_id>'`."""
    cleaned = (target or "").strip()
    if not cleaned or cleaned.lower() == "any" or cleaned == "gpu-jobs":
        return "gpu-jobs"
    if cleaned.startswith("gpu:"):
        return cleaned
    return f"gpu:{cleaned}"


def _extract_busy(source: Mapping[str, Any]) -> tuple[bool | None, str]:
    reason = str(
        source.get("busyReason")
        or source.get("busy_reason")
        or source.get("lastBusyReason")
        or ""
    ).strip()
    if "busy" in source and isinstance(source.get("busy"), bool):
        return bool(source["busy"]), reason
    running = source.get("running")
    if isinstance(running, int) and not isinstance(running, bool) and running > 0:
        return True, reason or f"active_sessions:{running}"
    status = str(source.get("status") or source.get("state") or "").strip().lower()
    if status == "busy":
        return True, reason or "busy"
    if reason:
        return True, reason
    return None, ""


def _canonical_target_handle(item: Mapping[str, Any]) -> str:
    label = str(item.get("label") or "").strip()
    host = str(item.get("host") or item.get("hostname") or "").strip()
    raw_id = str(item.get("id") or "").strip()
    if label and re.match(r"^[a-zA-Z0-9._-]+$", label):
        return label
    if host:
        return host
    return raw_id or label


def list_machines(
    client: Research,
    *,
    only_online: bool = True,
    capability: str | None = None,
    backend: str | None = None,
    exclude_busy: bool = False,
) -> list[LinkedMachine]:
    """Discover linked machines by merging `/v1/compute/fleet/workers` and `/v1/agent/targets` (`evo`, `dgx`, etc.)."""
    fleet_rows: list[Any] = []
    try:
        resp = client.http.get("/v1/compute/fleet/workers")
        if isinstance(resp, Mapping):
            fleet_rows = list(resp.get("workers") or resp.get("data") or [])
        elif isinstance(resp, list):
            fleet_rows = resp
    except Exception:
        fleet_rows = []

    target_rows: list[Any] = []
    try:
        t_resp = client.http.get("/v1/agent/targets")
        if isinstance(t_resp, Mapping):
            target_rows = list(t_resp.get("targets") or t_resp.get("data") or [])
        elif isinstance(t_resp, list):
            target_rows = t_resp
    except Exception:
        target_rows = []

    by_key: dict[str, LinkedMachine] = {}
    alias_to_key: dict[str, str] = {}

    for item in fleet_rows:
        if not isinstance(item, Mapping):
            continue
        mid = str(item.get("id") or item.get("hostname") or "").strip()
        if not mid:
            continue
        hostname = str(item.get("hostname") or mid).strip()
        status = str(item.get("status") or "unknown").strip()

        busy_flag, busy_reason = _extract_busy(item)
        if busy_flag is None:
            enc_id = quote(mid, safe="")
            try:
                pres = client.http.get(f"/v1/workflow/namespaces/fleet/activities/{enc_id}/{enc_id}")
                if isinstance(pres, Mapping):
                    for sub in (pres, pres.get("input"), pres.get("details"), pres.get("result")):
                        if isinstance(sub, Mapping):
                            b_sub, r_sub = _extract_busy(sub)
                            if b_sub is not None:
                                busy_flag = b_sub
                                busy_reason = r_sub
                                break
            except Exception:
                pass

        gpus = [dict(g) for g in (item.get("gpus") or []) if isinstance(g, Mapping)]
        mem_bytes = _parse_mem_bytes(item.get("memory"))
        if mem_bytes == 0 and gpus:
            mem_bytes = max((_parse_mem_bytes(g.get("memoryTotal")) for g in gpus), default=0)
        mem_gb = round(mem_bytes / float(1024**3), 2) if mem_bytes > 0 else 0.0
        caps = [str(c).strip() for c in (item.get("capabilities") or []) if str(c).strip()]
        backends = infer_machine_backends(item)
        queue = str(item.get("jobQueue") or item.get("taskQueue") or "").strip() or f"gpu:{mid}"

        m = LinkedMachine(
            id=mid,
            hostname=hostname,
            status=status,
            os=str(item.get("os") or ""),
            arch=str(item.get("arch") or ""),
            cpus=int(item.get("cpus") or 0),
            memory_bytes=mem_bytes,
            memory_gb=mem_gb,
            capacity=str(item.get("capacity") or ""),
            gpus=gpus,
            capabilities=caps,
            backends=backends,
            job_queue=queue,
            task_queue=queue,
            busy=bool(busy_flag),
            busy_reason=busy_reason,
        )
        key = mid.lower()
        by_key[key] = m
        alias_to_key[key] = key
        alias_to_key[hostname.lower()] = key
        if key.endswith("-hanzod"):
            alias_to_key[key.removesuffix("-hanzod")] = key

    for item in target_rows:
        if not isinstance(item, Mapping):
            continue
        handle = _canonical_target_handle(item)
        if not handle:
            continue
        host = str(item.get("host") or handle).strip()
        raw_id = str(item.get("id") or "").strip()
        spec = item.get("spec") if isinstance(item.get("spec"), Mapping) else {}
        cap_str = str(item.get("capacity") or "").strip()
        cap_cpus, cap_mem = _parse_capacity_hint(cap_str)

        existing_key = (
            alias_to_key.get(handle.lower())
            or alias_to_key.get(host.lower())
            or (alias_to_key.get(raw_id.lower()) if raw_id else None)
        )
        t_busy, t_reason = _extract_busy(item)
        t_backends = infer_machine_backends(item)
        t_gpus = [dict(g) for g in (spec.get("gpus") or item.get("gpus") or []) if isinstance(g, Mapping)]
        t_mem = _parse_mem_bytes(spec.get("memory")) or cap_mem
        if t_mem == 0 and t_gpus:
            t_mem = max((_parse_mem_bytes(g.get("memoryTotal")) for g in t_gpus), default=0)
        t_cpus = int(spec.get("cpus") or item.get("cpus") or cap_cpus or 0)

        if existing_key and existing_key in by_key:
            m = by_key[existing_key]
            if not m.capacity and cap_str:
                m.capacity = cap_str
            if m.cpus == 0 and t_cpus > 0:
                m.cpus = t_cpus
            if m.memory_bytes == 0 and t_mem > 0:
                m.memory_bytes = t_mem
                m.memory_gb = round(t_mem / float(1024**3), 2)
            if not m.gpus and t_gpus:
                m.gpus = t_gpus
            for b in t_backends:
                if b not in m.backends:
                    m.backends.append(b)
            if not m.busy and t_busy:
                m.busy = True
                m.busy_reason = t_reason
            continue

        status = str(item.get("status") or "offline").strip()
        caps = [
            str(c).strip()
            for c in (item.get("capabilities") or ["research.bench", "research.tick", "hanzod.run"])
            if str(c).strip()
        ]
        queue = f"gpu:{handle}"
        m = LinkedMachine(
            id=handle,
            hostname=host,
            status=status,
            os=str(spec.get("os") or item.get("os") or ""),
            arch=str(spec.get("arch") or item.get("arch") or ""),
            cpus=t_cpus,
            memory_bytes=t_mem,
            memory_gb=round(t_mem / float(1024**3), 2) if t_mem > 0 else 0.0,
            capacity=cap_str,
            gpus=t_gpus,
            capabilities=caps,
            backends=t_backends,
            job_queue=queue,
            task_queue=queue,
            busy=bool(t_busy),
            busy_reason=t_reason,
        )
        key = handle.lower()
        by_key[key] = m
        alias_to_key[key] = key
        alias_to_key[host.lower()] = key
        if raw_id:
            alias_to_key[raw_id.lower()] = key

    want_cap = capability.strip().lower() if (capability and capability.strip()) else None
    want_backend = backend.strip().upper() if (backend and backend.strip()) else None
    filtered: list[LinkedMachine] = []
    for m in by_key.values():
        if only_online and m.status.lower() not in _ONLINE_STATES:
            continue
        if exclude_busy and m.busy:
            continue
        if want_cap and want_cap not in {c.lower() for c in m.capabilities}:
            continue
        if want_backend and want_backend not in m.backends:
            continue
        filtered.append(m)
    return filtered


def _lookup_machine_status_map(client: Research) -> dict[str, str]:
    status_map: dict[str, str] = {}
    try:
        all_machines = list_machines(client, only_online=False)
    except Exception:
        return status_map
    for m in all_machines:
        state = "online" if m.status.lower() in _ONLINE_STATES else "queued_until_online"
        for k in (m.id, m.hostname, m.id.removesuffix("-hanzod")):
            if k:
                status_map[k.lower()] = state
    return status_map


def dispatch_task(
    client: Research,
    payload: Mapping[str, Any],
    *,
    target: str | None = None,
    activity_type: str = "research.bench",
    when_idle_only: bool = True,
    required_backend: str | None = None,
    min_memory_gb: float | None = None,
    job_id: str | None = None,
    run_id: str | None = None,
    namespace: str = "gpu-jobs",
    retry_policy: Mapping[str, Any] | None = None,
    heartbeat_timeout: str = "60s",
    start_to_close_timeout: str = "1800s",
    schedule_to_close_timeout: str | None = None,
    request_id: str | None = None,
    identity: str = "",
    machine_status_hint: str | None = None,
) -> dict[str, Any]:
    """Dispatch a durable, busy-aware standalone activity to `hanzoai/tasks` (never rejects offline targets)."""
    ns = (namespace or "").strip() or "gpu-jobs"
    raw_target = (target or "").strip()
    is_targeted = bool(raw_target and raw_target.lower() != "any" and raw_target != "gpu-jobs")
    machine_name = raw_target.removeprefix("gpu:") if is_targeted else "any"
    queue = resolve_task_queue(raw_target)
    act_type = (activity_type or "").strip() or "research.bench"
    sched_to_close = (schedule_to_close_timeout or "").strip() or ("72h" if is_targeted else "24h")

    if machine_status_hint:
        m_status = machine_status_hint
    elif is_targeted:
        known = _lookup_machine_status_map(client)
        m_status = known.get(machine_name.lower(), "queued_until_online")
    else:
        m_status = "online"

    enriched_input = dict(payload)
    enriched_input.setdefault("when_idle_only", bool(when_idle_only))
    enriched_input.setdefault("allow_when_busy", not bool(enriched_input["when_idle_only"]))
    if is_targeted:
        enriched_input.setdefault("target_machine", machine_name)
    if required_backend and required_backend.strip():
        enriched_input["required_backend"] = required_backend.strip().upper()
    if min_memory_gb is not None:
        enriched_input["min_memory_gb"] = float(min_memory_gb)

    canon_seed = canonical.canonicalize(
        {
            "namespace": ns,
            "taskQueue": queue,
            "activityType": act_type,
            "jobId": (job_id or "").strip(),
            "input": enriched_input,
        }
    )
    seed_hex = hashlib.sha256(canon_seed).hexdigest()
    jid = (job_id or "").strip() or f"job-{int(time.time() * 1000)}-{seed_hex[:12]}"
    rid = (run_id or "").strip() or jid
    req_id = (request_id or "").strip() or f"req-{seed_hex[:24]}"

    body: dict[str, Any] = {
        "id": jid,
        "activityId": jid,
        "runId": rid,
        "type": act_type,
        "activityType": {"name": act_type},
        "taskQueue": queue,
        "input": enriched_input,
        "retryPolicy": dict(retry_policy or DEFAULT_RETRY_POLICY),
        "heartbeatTimeout": heartbeat_timeout,
        "startToCloseTimeout": start_to_close_timeout,
        "scheduleToCloseTimeout": sched_to_close,
        "requestId": req_id,
    }
    if identity.strip():
        body["identity"] = identity.strip()

    resp = client.http.post(f"/v1/workflow/namespaces/{quote(ns, safe='')}/activities", body)
    out = dict(resp) if isinstance(resp, Mapping) else {}
    exec_ref = out.get("execution") if isinstance(out.get("execution"), Mapping) else {}
    resolved_id = str(exec_ref.get("workflowId") or out.get("activityId") or out.get("id") or jid)
    resolved_run = str(exec_ref.get("runId") or out.get("runId") or rid)
    out.setdefault("id", resolved_id)
    out.setdefault("activityId", resolved_id)
    out.setdefault("activity_id", resolved_id)
    out.setdefault("runId", resolved_run)
    out.setdefault("run_id", resolved_run)
    out.setdefault("taskQueue", queue)
    out.setdefault("task_queue", queue)
    out.setdefault("machine", machine_name)
    out.setdefault("machine_status", m_status)
    out.setdefault("scheduleToCloseTimeout", sched_to_close)
    out.setdefault("requestId", req_id)
    out.setdefault("input", enriched_input)
    return out


def _describe_activity(client: Research, ns: str, job_id: str, run_id: str) -> dict[str, Any]:
    enc_ns = quote(ns, safe="")
    enc_aid = quote(job_id, safe="")
    enc_rid = quote(run_id, safe="")
    resp = client.http.get(f"/v1/workflow/namespaces/{enc_ns}/activities/{enc_aid}/{enc_rid}")
    data = dict(resp) if isinstance(resp, Mapping) else {}
    state = str(data.get("status") or data.get("state") or "")
    data.setdefault("id", job_id)
    if state:
        data.setdefault("status", state)
        data.setdefault("state", state)
    return data


def _consume_sse_until_terminal(
    stream: Any,
    ns: str,
    job_id: str,
    run_id: str,
    on_defer: Any,
) -> str | None:
    event_kind = ""
    data_lines: list[str] = []
    while True:
        raw_line = stream.readline()
        if not raw_line:
            return None
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if line.startswith(":"):
            continue
        if not line:
            if data_lines:
                payload_txt = "\n".join(data_lines)
                data_lines.clear()
                try:
                    ev = json.loads(payload_txt)
                except ValueError:
                    ev = {}
                if isinstance(ev, Mapping):
                    kind = str(ev.get("kind") or event_kind or "")
                    ev_ns = str(ev.get("namespace") or "")
                    ev_wf = str(ev.get("workflow_id") or ev.get("activityId") or ev.get("id") or "")
                    ev_run = str(ev.get("run_id") or ev.get("runId") or "")
                    if (not ev_ns or ev_ns == ns) and ev_wf == job_id and (not ev_run or ev_run == run_id):
                        if kind == "activity.deferred":
                            ev_data = ev.get("data") if isinstance(ev.get("data"), Mapping) else {}
                            on_defer(int(ev_data.get("deferCount") or 1))
                        elif kind in _TERMINAL_SSE_EVENTS:
                            return kind
            event_kind = ""
            continue
        if line.startswith("event:"):
            event_kind = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())


def wait_gpu_job(
    client: Research,
    job_id: str,
    *,
    run_id: str | None = None,
    namespace: str = "gpu-jobs",
    timeout_sec: float = 600.0,
    poll_interval_sec: float = 2.0,
) -> dict[str, Any]:
    """Wait for activity completion via `GET /v1/workflow/events` SSE stream (reconnect backoff only on drop)."""
    ns = (namespace or "").strip() or "gpu-jobs"
    aid = job_id.strip()
    rid = (run_id or job_id).strip()

    start = time.monotonic()
    base_budget = max(0.05, float(timeout_sec))
    deadline = start + base_budget
    hard_deadline = start + max(base_budget * 3.0, base_budget + 120.0)
    seen_defers = 0
    sse_supported = True
    reconnect_attempt = 0

    def _note_defer(defer_count: int) -> None:
        nonlocal deadline, seen_defers
        if defer_count > seen_defers:
            extra = min(30.0, max(0.05, base_budget * 0.25)) * (defer_count - seen_defers)
            deadline = min(hard_deadline, deadline + extra)
            seen_defers = defer_count

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            snap = _describe_activity(client, ns, aid, rid)
            st = str(snap.get("status") or snap.get("state") or "")
            if st in _TERMINAL_ACTIVITY_STATES:
                return snap
            dc = int(snap.get("deferCount") or seen_defers)
            busy_note = snap.get("lastBusyReason") or ""
            suffix = f", deferCount={dc}, lastBusyReason={busy_note!r}" if dc or busy_note else ""
            raise Error(f"timed out waiting for gpu job {aid!r} (last state: {st!r}{suffix})")

        if sse_supported:
            snap0 = _describe_activity(client, ns, aid, rid)
            st0 = str(snap0.get("status") or snap0.get("state") or "")
            if st0 in _TERMINAL_ACTIVITY_STATES:
                return snap0
            _note_defer(int(snap0.get("deferCount") or 0))
            stream = None
            try:
                stream = client.http.open_stream("/v1/workflow/events", timeout=max(0.1, remaining))
                term_event = _consume_sse_until_terminal(stream, ns, aid, rid, _note_defer)
                snap = _describe_activity(client, ns, aid, rid)
                st = str(snap.get("status") or snap.get("state") or "")
                if st in _TERMINAL_ACTIVITY_STATES or term_event is not None:
                    return snap
                reconnect_attempt += 1
            except urllib.error.HTTPError as http_err:
                if http_err.code in (404, 405, 501):
                    sse_supported = False
                else:
                    reconnect_attempt += 1
            except (TimeoutError, urllib.error.URLError, ConnectionError, OSError):
                snap = _describe_activity(client, ns, aid, rid)
                st = str(snap.get("status") or snap.get("state") or "")
                if st in _TERMINAL_ACTIVITY_STATES:
                    return snap
                _note_defer(int(snap.get("deferCount") or 0))
                reconnect_attempt += 1
            finally:
                if stream is not None:
                    try:
                        stream.close()
                    except Exception:
                        pass

            if sse_supported:
                rem = deadline - time.monotonic()
                if rem <= 0:
                    continue
                backoff = min(rem, min(15.0, 0.25 * (2 ** min(reconnect_attempt, 5))))
                time.sleep(backoff)
                continue

        # Fallback only if server endpoint does not expose `/v1/workflow/events` SSE.
        snap = _describe_activity(client, ns, aid, rid)
        st = str(snap.get("status") or snap.get("state") or "")
        if st in _TERMINAL_ACTIVITY_STATES:
            return snap
        _note_defer(int(snap.get("deferCount") or 0))
        rem = deadline - time.monotonic()
        if rem > 0:
            time.sleep(min(rem, max(0.01, float(poll_interval_sec))))


def release_gpu_job(
    client: Research,
    activity_id: str,
    run_id: str | None = None,
    *,
    reason: str = "busy",
    identity: str = "",
    delay_seconds: int = 10,
    namespace: str = "gpu-jobs",
) -> dict[str, Any]:
    """Release/defer a claimed activity without failing it (`POST .../activities/<id>/<run>/release`)."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    aid = quote(activity_id.strip(), safe="")
    rid = quote((run_id or activity_id).strip(), safe="")
    body = {
        "reason": reason,
        "identity": identity,
        "delaySeconds": max(0, int(delay_seconds)),
    }
    resp = client.http.post(f"/v1/workflow/namespaces/{ns}/activities/{aid}/{rid}/release", body)
    return dict(resp) if isinstance(resp, Mapping) else {"status": "released"}


def _normalize_task_items(tasks_or_command: str | Mapping[str, Any] | Sequence[str | Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(tasks_or_command, str):
        return [{"command": tasks_or_command}]
    if isinstance(tasks_or_command, Mapping):
        return [dict(tasks_or_command)]
    items: list[dict[str, Any]] = []
    for entry in tasks_or_command:
        if isinstance(entry, str):
            items.append({"command": entry})
        elif isinstance(entry, Mapping):
            items.append(dict(entry))
        else:
            raise TypeError(f"unsupported task item: {entry!r}")
    return items


def orchestrate_across_machines(
    client: Research,
    tasks_or_command: str | Mapping[str, Any] | Sequence[str | Mapping[str, Any]],
    *,
    target: str | Sequence[str] | None = None,
    capability: str | None = "research.bench",
    backend: str | None = None,
    activity_type: str = "research.bench",
    fanout: bool = False,
    wait: bool = False,
    when_idle_only: bool = True,
    min_memory_gb: float | None = None,
    namespace: str = "gpu-jobs",
    timeout_sec: float = 600.0,
    poll_interval_sec: float = 2.0,
) -> list[dict[str, Any]]:
    """Orchestrate research runs across linked machines (`--target evo,dgx`, `fanout`, or best-idle)."""
    items = _normalize_task_items(tasks_or_command)
    if not items:
        return []

    explicit_targets = [t for t in parse_targets(target) if t.lower() != "any"]
    dispatched: list[dict[str, Any]] = []

    if explicit_targets:
        status_map = _lookup_machine_status_map(client)
        for idx, item in enumerate(items):
            for t_id in explicit_targets:
                payload = dict(item)
                clean_t = t_id.removeprefix("gpu:")
                payload.setdefault("target_machine", clean_t)
                explicit_id = str(payload.pop("job_id", "") or "").strip()
                jid = (
                    f"{explicit_id}-{clean_t}"
                    if (explicit_id and len(explicit_targets) > 1)
                    else (explicit_id or None)
                )
                m_state = status_map.get(clean_t.lower(), "queued_until_online")
                dispatched.append(
                    dispatch_task(
                        client,
                        payload,
                        target=clean_t,
                        activity_type=activity_type,
                        when_idle_only=when_idle_only,
                        required_backend=backend,
                        min_memory_gb=min_memory_gb,
                        job_id=jid,
                        namespace=namespace,
                        schedule_to_close_timeout="72h",
                        request_id=(
                            f"target-{idx}-{clean_t}-{hashlib.sha256(canonical.canonicalize(payload)).hexdigest()[:16]}"
                        ),
                        machine_status_hint=m_state,
                    )
                )
    else:
        machines = list_machines(
            client,
            only_online=True,
            capability=capability,
            backend=backend,
            exclude_busy=False,
        )
        if min_memory_gb is not None:
            machines = [m for m in machines if m.memory_gb <= 0.0 or m.memory_gb >= float(min_memory_gb)]

        if fanout:
            targets = [m.id for m in machines] if machines else ["any"]
            for idx, item in enumerate(items):
                for t_id in targets:
                    payload = dict(item)
                    if t_id != "any":
                        payload.setdefault("target_machine", t_id)
                    explicit_id = str(payload.pop("job_id", "") or "").strip()
                    jid = f"{explicit_id}-{t_id}" if (explicit_id and t_id != "any") else (explicit_id or None)
                    dispatched.append(
                        dispatch_task(
                            client,
                            payload,
                            target=t_id,
                            activity_type=activity_type,
                            when_idle_only=when_idle_only,
                            required_backend=backend,
                            min_memory_gb=min_memory_gb,
                            job_id=jid,
                            namespace=namespace,
                            request_id=(
                                f"fanout-{idx}-{t_id}-{hashlib.sha256(canonical.canonicalize(payload)).hexdigest()[:16]}"
                            ),
                            machine_status_hint="online" if t_id != "any" else "online",
                        )
                    )
        else:
            idle = sorted(
                [m for m in machines if not m.busy],
                key=lambda m: (len(m.gpus) > 0, m.memory_gb, m.cpus, m.id),
                reverse=True,
            )
            for idx, item in enumerate(items):
                payload = dict(item)
                explicit_id = str(payload.pop("job_id", "") or "").strip() or None
                chosen_target = idle[idx % len(idle)].id if idle else "any"
                if chosen_target != "any":
                    payload.setdefault("target_machine", chosen_target)
                dispatched.append(
                    dispatch_task(
                        client,
                        payload,
                        target=chosen_target,
                        activity_type=activity_type,
                        when_idle_only=when_idle_only,
                        required_backend=backend,
                        min_memory_gb=min_memory_gb,
                        job_id=explicit_id,
                        namespace=namespace,
                        machine_status_hint="online" if chosen_target != "any" else "queued_until_online",
                    )
                )

    if not wait:
        return dispatched

    completed: list[dict[str, Any]] = []
    for d in dispatched:
        completed.append(
            wait_gpu_job(
                client,
                str(d["id"]),
                run_id=str(d.get("runId") or d["id"]),
                namespace=namespace,
                timeout_sec=timeout_sec,
                poll_interval_sec=poll_interval_sec,
            )
        )
    return completed


def ensure_workflow_namespace(client: Research, namespace: str = "gpu-jobs") -> None:
    """Best-effort registration of `/v1/workflow/namespaces` before creating schedules."""
    ns = (namespace or "").strip() or "gpu-jobs"
    body = {
        "name": ns,
        "namespaceInfo": {
            "name": ns,
            "state": "NAMESPACE_STATE_REGISTERED",
            "description": "Hanzo autonomous research and GPU task queue",
        },
        "config": {"workflowExecutionRetentionTtl": "720h"},
        "isActive": True,
    }
    try:
        client.http.post("/v1/workflow/namespaces", body)
    except Exception:
        pass


def create_schedule(
    client: Research,
    schedule_id: str,
    *,
    interval: str | None = None,
    cron: str | None = None,
    target: str | Sequence[str] | None = None,
    activity_type: str = "research.tick",
    workflow_type: str | None = None,
    input_payload: Mapping[str, Any] | None = None,
    command: str | None = None,
    campaign: str | None = None,
    executor: str | None = None,
    max_compute_seconds: int | None = None,
    when_idle_only: bool = True,
    required_backend: str | None = None,
    paused: bool = False,
    note: str = "",
    namespace: str = "gpu-jobs",
    retry_policy: Mapping[str, Any] | None = None,
    heartbeat_timeout: str = "60s",
    start_to_close_timeout: str = "1800s",
) -> dict[str, Any]:
    """Create durable native `hanzoai/tasks` schedule(s) (`--target evo`, `--target dgx`, or `--target evo,dgx`)."""
    sid = schedule_id.strip()
    if not sid:
        raise ValueError("schedule_id is required")
    ivl = (interval or "").strip()
    crn = (cron or "").strip()
    if not ivl and not crn:
        raise ValueError("create_schedule requires interval (e.g. '30m') and/or cron (e.g. '0 */2 * * *')")

    targets = parse_targets(target)
    if len(targets) > 1:
        created: list[dict[str, Any]] = []
        for t in targets:
            clean_t = t.removeprefix("gpu:")
            created.append(
                create_schedule(
                    client,
                    f"{sid}-{clean_t}",
                    interval=interval,
                    cron=cron,
                    target=clean_t,
                    activity_type=activity_type,
                    workflow_type=workflow_type,
                    input_payload=input_payload,
                    command=command,
                    campaign=campaign,
                    executor=executor,
                    max_compute_seconds=max_compute_seconds,
                    when_idle_only=when_idle_only,
                    required_backend=required_backend,
                    paused=paused,
                    note=note,
                    namespace=namespace,
                    retry_policy=retry_policy,
                    heartbeat_timeout=heartbeat_timeout,
                    start_to_close_timeout=start_to_close_timeout,
                )
            )
        return {
            "schedules": created,
            "scheduleIds": [str(s.get("scheduleId") or "") for s in created],
        }

    single_target = targets[0] if targets else None
    is_targeted = bool(single_target and single_target.lower() != "any" and single_target != "gpu-jobs")
    ns = (namespace or "").strip() or "gpu-jobs"
    ensure_workflow_namespace(client, ns)

    spec: dict[str, Any] = {}
    if crn:
        spec["cronString"] = [crn]
    if ivl:
        spec["interval"] = [{"interval": ivl}]

    act_input: dict[str, Any] = dict(input_payload or {})
    act_input["when_idle_only"] = bool(when_idle_only)
    if is_targeted and single_target:
        act_input.setdefault("target_machine", single_target.removeprefix("gpu:"))
    if command is not None and command.strip():
        act_input["command"] = command.strip()
    if campaign is not None and campaign.strip():
        act_input["campaign"] = campaign.strip()
    if executor is not None and executor.strip():
        act_input["executor"] = executor.strip()
    if max_compute_seconds is not None:
        act_input["max_compute_seconds"] = int(max_compute_seconds)
    if required_backend and required_backend.strip():
        act_input["required_backend"] = required_backend.strip().upper()

    action: dict[str, Any] = {
        "taskQueue": resolve_task_queue(single_target),
        "input": act_input,
        "retryPolicy": dict(retry_policy or DEFAULT_RETRY_POLICY),
        "heartbeatTimeout": heartbeat_timeout,
        "startToCloseTimeout": start_to_close_timeout,
        "scheduleToCloseTimeout": "72h" if is_targeted else "24h",
    }
    if workflow_type and workflow_type.strip():
        action["workflowType"] = {"name": workflow_type.strip()}
    if activity_type and activity_type.strip():
        action["activityType"] = {"name": activity_type.strip()}

    body: dict[str, Any] = {
        "scheduleId": sid,
        "namespace": ns,
        "spec": spec,
        "action": action,
        "state": {"paused": bool(paused), "note": note},
    }
    resp = client.http.post(f"/v1/workflow/namespaces/{quote(ns, safe='')}/schedules", body)
    return dict(resp) if isinstance(resp, Mapping) else body


def list_schedules(client: Research, *, namespace: str = "gpu-jobs") -> list[dict[str, Any]]:
    """List schedules in `/v1/workflow/namespaces/<ns>/schedules`."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    resp = client.http.get(f"/v1/workflow/namespaces/{ns}/schedules")
    if isinstance(resp, Mapping):
        rows = resp.get("schedules") or resp.get("data") or []
        return [dict(r) for r in rows if isinstance(r, Mapping)]
    return []


def describe_schedule(client: Research, schedule_id: str, *, namespace: str = "gpu-jobs") -> dict[str, Any]:
    """Describe one schedule (`GET /v1/workflow/namespaces/<ns>/schedules/<id>`)."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    sid = quote(schedule_id.strip(), safe="")
    resp = client.http.get(f"/v1/workflow/namespaces/{ns}/schedules/{sid}")
    return dict(resp) if isinstance(resp, Mapping) else {}


def trigger_schedule(
    client: Research,
    schedule_id: str,
    *,
    request_id: str = "",
    overlap_policy: str = "",
    namespace: str = "gpu-jobs",
) -> dict[str, Any]:
    """Trigger an immediate schedule execution (`POST /v1/workflow/namespaces/<ns>/schedules/<id>/trigger`)."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    sid = quote(schedule_id.strip(), safe="")
    body: dict[str, Any] = {"requestId": request_id.strip() or f"trig-{sid}-{int(time.time() * 1000)}"}
    if overlap_policy.strip():
        body["overlapPolicy"] = overlap_policy.strip()
    resp = client.http.post(f"/v1/workflow/namespaces/{ns}/schedules/{sid}/trigger", body)
    return dict(resp) if isinstance(resp, Mapping) else {"status": "triggered"}


def pause_schedule(
    client: Research,
    schedule_id: str,
    *,
    note: str = "",
    namespace: str = "gpu-jobs",
) -> dict[str, Any]:
    """Pause a schedule (`POST /v1/workflow/namespaces/<ns>/schedules/<id>/pause`)."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    sid = quote(schedule_id.strip(), safe="")
    resp = client.http.post(f"/v1/workflow/namespaces/{ns}/schedules/{sid}/pause", {"note": note})
    return dict(resp) if isinstance(resp, Mapping) else {"status": "paused"}


def resume_schedule(
    client: Research,
    schedule_id: str,
    *,
    namespace: str = "gpu-jobs",
) -> dict[str, Any]:
    """Resume/unpause a schedule (`POST /v1/workflow/namespaces/<ns>/schedules/<id>/unpause`)."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    sid = quote(schedule_id.strip(), safe="")
    resp = client.http.post(f"/v1/workflow/namespaces/{ns}/schedules/{sid}/unpause", {})
    return dict(resp) if isinstance(resp, Mapping) else {"status": "running"}


def delete_schedule(
    client: Research,
    schedule_id: str,
    *,
    namespace: str = "gpu-jobs",
) -> dict[str, Any]:
    """Delete a schedule (`DELETE /v1/workflow/namespaces/<ns>/schedules/<id>`)."""
    ns = quote((namespace or "").strip() or "gpu-jobs", safe="")
    sid = quote(schedule_id.strip(), safe="")
    resp = client.http.delete(f"/v1/workflow/namespaces/{ns}/schedules/{sid}")
    return dict(resp) if isinstance(resp, Mapping) else {"status": "deleted"}
