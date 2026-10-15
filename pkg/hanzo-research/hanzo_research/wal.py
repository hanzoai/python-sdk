"""A write-ahead log of research events: appended, fsynced, hash-chained (the crate's `wal.rs`).

Each line is one `ResearchEvent`; its `previous_event_hash` is the digest of the line before
(64 zeros for the first), so editing, dropping or reordering a line breaks the chain, which
`verify` finds. A log written by the Rust crate reads and verifies here, and the reverse,
wherever their canonical bytes agree: every payload of strings, integers within 2**53 and
floats from 1e-6 to 1e21 in magnitude. A number outside that range hashes differently,
since the crate writes it with Rust's `Display` rather than RFC 8785.
"""

from __future__ import annotations

import os
import json
from typing import Any, Iterable

from .wire import now
from .lineage import ResearchEvent

__all__ = ["ResearchWal", "GENESIS", "read", "verify", "ordered"]

GENESIS = "0" * 64


class ResearchWal:
    """One worker's log for one run, at `<dir>/wal.jsonl` (`wal-<worker>.jsonl` past worker-0)."""

    def __init__(self, path: str, run_id: str, worker_id: str, sequence: int, last: str):
        self.path, self.run_id, self.worker_id = path, run_id, worker_id
        self.sequence, self.last_event_hash = sequence, last

    @classmethod
    def open(cls, run_dir: str, run_id: str, worker_id: str = "worker-0") -> ResearchWal:
        """Open or create the log, resuming its sequence and chain from what is on disk."""
        os.makedirs(run_dir, exist_ok=True)
        name = "wal.jsonl" if worker_id in ("", "worker-0") else f"wal-{worker_id}.jsonl"
        path = os.path.join(run_dir, name)
        _mend(path)
        sequence, last = 0, GENESIS
        for event in read(path):
            sequence, last = event.sequence, event.digest()
        return cls(path, run_id, worker_id, sequence, last)

    def append(self, event_type: str, payload: Any) -> ResearchEvent:
        """Append one event and fsync it before returning."""
        plain = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
        seq = self.sequence + 1
        event = ResearchEvent.new(
            self.run_id,
            self.worker_id,
            f"{self.run_id}-{self.worker_id}-{seq}-{event_type}",
            seq,
            self.last_event_hash,
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


def _mend(path: str) -> None:
    """Mend the last line a crash left: a torn one (not JSON) is cut, a whole one missing its
    newline gets it, so the next append starts on its own line. A torn line anywhere else
    is corruption, which `read` reports."""
    if not os.path.exists(path):
        return
    with open(path, "rb") as f:
        data = f.read()
    if not data or data.endswith(b"\n"):
        return
    end = data.rfind(b"\n") + 1
    try:
        json.loads(data[end:])
    except ValueError:
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
