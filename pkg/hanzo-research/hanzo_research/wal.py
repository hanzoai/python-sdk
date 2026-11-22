"""A write-ahead log of research events: appended, fsynced, hash-chained (the crate's `wal.rs`).

Each line is one `ResearchEvent`; its `previous_event_hash` is the digest of the line before
(64 zeros for the first), so editing, dropping or reordering a line breaks the chain, which
`verify` finds on `open` and on demand. Advisory `flock` on `<wal>.lock` serializes writers
across OS processes, and `append_idempotent` deduplicates retries by RFC 8785 `event_id`.
"""

from __future__ import annotations

import fcntl
import json
import os
from typing import Any, Iterable

from . import canonical
from .lineage import ResearchEvent
from .wire import now

__all__ = ["ResearchWal", "GENESIS", "read", "verify", "ordered", "default_event_id"]

GENESIS = "0" * 64


def default_event_id(run_id: str, worker_id: str, event_type: str, payload: Any) -> str:
    """Compute canonical RFC 8785 idempotent event_id matching Rust `default_event_id`."""
    plain = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    return canonical.digest(
        {
            "run_id": run_id,
            "worker_id": worker_id,
            "type": event_type,
            "payload": plain,
        }
    )


class ResearchWal:
    """One worker's log for one run, at `<dir>/wal.jsonl` (`wal-<worker>.jsonl` past worker-0)."""

    def __init__(self, path: str, run_id: str, worker_id: str, sequence: int, last: str):
        self.path, self.run_id, self.worker_id = path, run_id, worker_id
        self.sequence, self.last_event_hash = sequence, last

    @property
    def lock_path(self) -> str:
        return self.path + ".lock"

    @classmethod
    def open(cls, run_dir: str, run_id: str, worker_id: str = "worker-0") -> ResearchWal:
        """Open or create the log, mending only a torn tail and verifying the entire hash chain."""
        os.makedirs(run_dir, exist_ok=True)
        name = "wal.jsonl" if worker_id in ("", "worker-0") else f"wal-{worker_id}.jsonl"
        path = os.path.join(run_dir, name)
        lock_path = path + ".lock"
        with open(lock_path, "a+b") as lfp:
            fcntl.flock(lfp.fileno(), fcntl.LOCK_EX)
            _mend(path)
            last = verify(path)
            events = read(path)
            sequence = events[-1].sequence if events else 0
        return cls(path, run_id, worker_id, sequence, last)

    def append(self, event_type: str, payload: Any) -> ResearchEvent:
        """Append one event under advisory flock and fsync it before returning."""
        plain = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
        with open(self.lock_path, "a+b") as lfp:
            fcntl.flock(lfp.fileno(), fcntl.LOCK_EX)
            _mend(self.path)
            tail = _read_tail(self.path)
            if tail is not None:
                seq = tail.sequence + 1
                prev = tail.digest()
            else:
                seq = 1
                prev = GENESIS
            event = ResearchEvent.new(
                self.run_id,
                self.worker_id,
                f"{self.run_id}-{self.worker_id}-{seq}-{event_type}",
                seq,
                prev,
                plain,
                now(),
            )
            line = json.dumps(event.dump(), ensure_ascii=False, separators=(",", ":"))
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
            self.sequence, self.last_event_hash = seq, event.digest()
            return event

    def append_idempotent(
        self,
        event_type: str,
        payload: Any,
        *,
        event_id: str | None = None,
    ) -> ResearchEvent:
        """Append idempotently under flock; returns existing event on matching retry or raises on collision."""
        plain = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
        eid = event_id or default_event_id(self.run_id, self.worker_id, event_type, plain)
        want_payload_hash = canonical.digest(plain)
        with open(self.lock_path, "a+b") as lfp:
            fcntl.flock(lfp.fileno(), fcntl.LOCK_EX)
            _mend(self.path)
            events = read(self.path)
            for existing in events:
                if existing.event_id == eid:
                    if existing.payload_hash != want_payload_hash or existing.run_id != self.run_id:
                        raise ValueError(f"idempotent event_id collision with different payload: {eid}")
                    self.sequence = events[-1].sequence
                    self.last_event_hash = events[-1].digest()
                    return existing
            if events:
                seq = events[-1].sequence + 1
                prev = events[-1].digest()
            else:
                seq = 1
                prev = GENESIS
            event = ResearchEvent.new(
                self.run_id,
                self.worker_id,
                eid,
                seq,
                prev,
                plain,
                now(),
            )
            line = json.dumps(event.dump(), ensure_ascii=False, separators=(",", ":"))
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
            self.sequence, self.last_event_hash = seq, event.digest()
            return event


def read(path: str) -> list[ResearchEvent]:
    """Every event of a log, in file order; a missing file is an empty log, a blank line is skipped."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    out.append(ResearchEvent.load(json.loads(line)))
                except ValueError:
                    raise ValueError(f"{path}: line {n} is not an event") from None
    return out


def _read_tail(path: str) -> ResearchEvent | None:
    """Read only the last ResearchEvent line from a log in O(1) tail chunks."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if size == 0:
            return None
        chunk_size = min(8192, size)
        while True:
            f.seek(size - chunk_size, os.SEEK_SET)
            buf = f.read(chunk_size)
            stripped = buf.rstrip()
            if stripped:
                nl = stripped.rfind(b"\n")
                if nl >= 0:
                    line = stripped[nl + 1 :].decode("utf-8")
                    return ResearchEvent.load(json.loads(line))
                if chunk_size == size:
                    return ResearchEvent.load(json.loads(stripped.decode("utf-8")))
            elif chunk_size == size:
                return None
            chunk_size = min(chunk_size * 2, size)


def _mend(path: str) -> None:
    """Mend the last line a crash left: a torn one (not a valid ResearchEvent) is cut, a whole one
    missing its newline gets it, so the next append starts on its own line. A torn line anywhere
    else is corruption, which `read` and `verify` report."""
    if not os.path.exists(path):
        return
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if size == 0:
            return
        f.seek(size - 1, os.SEEK_SET)
        if f.read(1) == b"\n":
            return
        f.seek(0, os.SEEK_SET)
        data = f.read()
    end = data.rfind(b"\n") + 1
    try:
        ResearchEvent.load(json.loads(data[end:].decode("utf-8")))
    except (ValueError, UnicodeDecodeError):
        with open(path, "r+b") as f:
            f.truncate(end)
            os.fsync(f.fileno())
        return
    with open(path, "ab") as f:
        f.write(b"\n")
        os.fsync(f.fileno())


def verify(path: str) -> str:
    """Check the chain and every payload hash; the last event's digest, or ValueError at the first break."""
    last = GENESIS
    for i, event in enumerate(read(path), 1):
        if event.sequence != i:
            raise ValueError(f"{path}: line {i} has sequence {event.sequence}")
        if event.previous_event_hash != last:
            raise ValueError(f"{path}: line {i} does not chain to the line before it")
        if (
            ResearchEvent.new(
                event.run_id, event.worker_id, event.event_id, event.sequence, last, event.payload, event.created_at
            ).payload_hash
            != event.payload_hash
        ):
            raise ValueError(f"{path}: line {i}'s payload does not hash to its payload_hash")
        last = event.digest()
    return last


def ordered(events: Iterable[ResearchEvent]) -> list[ResearchEvent]:
    """Several workers' events in the run's one order: sequence, time, worker, payload hash."""
    return sorted(events, key=lambda e: (e.sequence, e.created_at, e.worker_id, e.payload_hash))
