"""Durable WAL-to-cloud spooler with fsynced cursor and Idempotency-Key deduplication.

Drains `ResearchWal` entries to `/v1/research/evidence` (`wal://<run_id>/<seq>`) with
`Idempotency-Key = event.digest()`, exponential backoff when offline, and crash-safe
fsynced cursor commits so restarts resume at-least-once without duplicates or loss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import time
from typing import Any

from . import wal
from .wire import Evidence, Source, Wire, now

__all__ = ["SpoolCursor", "SpoolReport", "Spooler"]


@dataclass
class SpoolCursor(Wire):
    run_id: str = ""
    committed_seq: int = 0
    last_digest: str = wal.GENESIS
    updated_at: str = field(default_factory=now)


@dataclass
class SpoolReport(Wire):
    drained: int = 0
    committed_seq: int = 0
    pending: int = 0
    offline: bool = False
    error: str = ""


def _write_cursor_fsync(path: Path, cursor: SpoolCursor) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    raw = (json.dumps(cursor.dump(), indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tmp.open("wb") as fp:
        fp.write(raw)
        fp.flush()
        os.fsync(fp.fileno())
    os.replace(tmp, path)


class Spooler:
    """Durable background/foreground spooler from local `ResearchWal` to `/v1/research`."""

    @staticmethod
    def load_cursor(cursor_path: str | Path) -> SpoolCursor:
        p = Path(cursor_path)
        if not p.is_file():
            return SpoolCursor()
        return SpoolCursor.load(json.loads(p.read_text(encoding="utf-8")))

    @classmethod
    def drain(
        cls,
        client: Any,
        wal_path: str | Path,
        cursor_path: str | Path,
        *,
        max_retries: int = 3,
        base_backoff_sec: float = 0.05,
    ) -> SpoolReport:
        wpath = str(wal_path)
        cpath = Path(cursor_path)
        wal.verify(wpath)
        events = wal.read(wpath)
        cursor = cls.load_cursor(cpath)
        uncommitted = [e for e in events if e.sequence > cursor.committed_seq]
        if not uncommitted:
            return SpoolReport(
                drained=0,
                committed_seq=cursor.committed_seq,
                pending=0,
                offline=False,
            )

        drained = 0
        for idx, ev in enumerate(uncommitted):
            ev_digest = ev.digest()
            record = Evidence(
                uri=f"wal://{ev.run_id}/{ev.sequence}",
                hash=ev_digest,
                kind="element",
                source=Source(system="hanzo-research-wal", revision=ev.worker_id),
                content=ev.dump(),
            )
            attempt = 0
            while True:
                try:
                    client.evidence(record, idempotency_key=ev_digest)
                    break
                except Exception as exc:
                    attempt += 1
                    if attempt > max_retries:
                        return SpoolReport(
                            drained=drained,
                            committed_seq=cursor.committed_seq,
                            pending=len(uncommitted) - idx,
                            offline=True,
                            error=str(exc)[:300],
                        )
                    if base_backoff_sec > 0:
                        time.sleep(base_backoff_sec * (2 ** (attempt - 1)))

            cursor = SpoolCursor(
                run_id=ev.run_id,
                committed_seq=ev.sequence,
                last_digest=ev_digest,
                updated_at=now(),
            )
            _write_cursor_fsync(cpath, cursor)
            drained += 1

        return SpoolReport(
            drained=drained,
            committed_seq=cursor.committed_seq,
            pending=0,
            offline=False,
        )
