"""Cross-machine cloud lease manager with monotonic fencing tokens over `/v1/research/evidence`.

Coordinates distributed GPU workers (DGX, desktop, CI) via versioned evidence URIs:
- `uri = research://leases/<campaign>/<opportunity_id>`
- Server-assigned monotonic `version` acts as the fencing token.
- Concurrent acquisition races resolve cleanly by re-GETting the canonical latest record.
- Expired leases are reclaimed with `reclaimed_from` audit lineage and incremented fencing token.
- Offline fallback persists local leases and queues evidence events when cloud is unreachable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Callable, Mapping

from . import canonical
from .errors import Error, Unavailable
from .wal import ResearchWal
from .wire import Evidence, Source, Wire, now

__all__ = [
    "Lease",
    "LeaseOutcome",
    "LeaseLostError",
    "CloudLeaseManager",
]


class LeaseLostError(RuntimeError):
    """Raised when a worker's lease was superseded by a higher fencing token."""


@dataclass
class Lease(Wire):
    uri: str = ""
    campaign: str = ""
    opportunity_id: str = ""
    fencing_token: int = 0
    owner_worker_id: str = ""
    host: str = ""
    acquired_at_unix: int = 0
    expires_at_unix: int = 0
    reclaimed_from: str = ""
    offline_local: bool = False


@dataclass
class LeaseOutcome(Wire):
    status: str = "busy"  # "acquired" | "busy"
    lease: Lease | None = None
    holder_worker_id: str = ""
    expires_at_unix: int = 0
    fencing_token: int = 0


def _sanitize_segment(seg: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".", ":") else "_" for c in seg)


def _latest_version(rows: list[Evidence]) -> Evidence | None:
    if not rows:
        return None
    return max(rows, key=lambda e: e.version)


def _hydrate_latest(
    client: Any,
    rows: list[Evidence],
    *,
    filed: Evidence | None = None,
) -> Evidence | None:
    latest = _latest_version(rows)
    if filed is not None and (latest is None or latest.version < filed.version):
        return filed
    if latest is None:
        return None
    if isinstance(latest.content, Mapping) and latest.content:
        return latest
    if filed is not None and latest.id and latest.id == filed.id and isinstance(filed.content, Mapping):
        return filed
    if latest.id and hasattr(client, "get_evidence"):
        return client.get_evidence(latest.id)
    return latest


class CloudLeaseManager:
    """Distributed lease manager backed by `/v1/research/evidence` + offline WAL fallback."""

    def __init__(
        self,
        client: Any | None,
        *,
        worker_id: str,
        commit: str = "",
        host: str | None = None,
        clock_skew_grace_sec: int = 5,
        local_dir: str | Path | None = None,
        clock_fn: Callable[[], int] | None = None,
    ):
        self.client = client
        self.worker_id = worker_id
        self.commit = commit
        self.host = host or platform.node() or "unknown-host"
        self.clock_skew_grace_sec = max(0, int(clock_skew_grace_sec))
        self.local_dir = Path(local_dir).expanduser().resolve() if local_dir else None
        if self.local_dir:
            (self.local_dir / "leases").mkdir(parents=True, exist_ok=True)
        self._clock = clock_fn or (lambda: int(time.time()))

    @staticmethod
    def lease_uri(campaign: str, opportunity_id: str) -> str:
        return f"research://leases/{_sanitize_segment(campaign)}/{_sanitize_segment(opportunity_id)}"

    def _now(self) -> int:
        return int(self._clock())

    def _local_path(self, uri: str) -> Path | None:
        if not self.local_dir:
            return None
        key = canonical.digest(uri)[:24]
        return self.local_dir / "leases" / f"{key}.json"

    def _acquire_offline(self, uri: str, campaign: str, opportunity_id: str, ttl_sec: int) -> LeaseOutcome:
        p = self._local_path(uri)
        now_u = self._now()
        prev_ver = 0
        reclaimed_from = ""
        if p and p.is_file():
            cur = json.loads(p.read_text(encoding="utf-8"))
            prev_ver = int(cur.get("fencing_token", 0))
            if (
                cur.get("state") == "held"
                and cur.get("owner_worker_id") != self.worker_id
                and now_u < int(cur.get("expires_at_unix", 0)) + self.clock_skew_grace_sec
            ):
                return LeaseOutcome(
                    status="busy",
                    lease=None,
                    holder_worker_id=str(cur.get("owner_worker_id", "")),
                    expires_at_unix=int(cur.get("expires_at_unix", 0)),
                    fencing_token=prev_ver,
                )
            if cur.get("state") == "held" and cur.get("owner_worker_id") != self.worker_id:
                reclaimed_from = str(cur.get("owner_worker_id", ""))
        fencing = prev_ver + 1
        lease = Lease(
            uri=uri,
            campaign=campaign,
            opportunity_id=opportunity_id,
            fencing_token=fencing,
            owner_worker_id=self.worker_id,
            host=self.host,
            acquired_at_unix=now_u,
            expires_at_unix=now_u + ttl_sec,
            reclaimed_from=reclaimed_from,
            offline_local=True,
        )
        if p:
            payload = dict(lease.dump(), state="held", updated_at=now())
            tmp = p.with_name(p.name + ".tmp")
            tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(tmp, p)
        if self.local_dir:
            wal = ResearchWal.open(str(self.local_dir / "wal"), "lease-offline", worker_id=self.worker_id)
            wal.append("lease_acquired_offline", lease.dump())
        return LeaseOutcome(
            status="acquired",
            lease=lease,
            holder_worker_id=self.worker_id,
            expires_at_unix=lease.expires_at_unix,
            fencing_token=fencing,
        )

    def acquire_lease(
        self,
        campaign: str,
        opportunity_id: str,
        *,
        ttl_sec: int = 600,
    ) -> LeaseOutcome:
        """Acquire or reclaim a cross-machine lease with server-verified monotonic fencing token."""
        uri = self.lease_uri(campaign, opportunity_id)
        if self.client is None:
            return self._acquire_offline(uri, campaign, opportunity_id, ttl_sec)

        now_u = self._now()
        try:
            existing = self.client.evidence_versions(uri)
        except (Unavailable, OSError, Error):
            if self.local_dir is not None:
                return self._acquire_offline(uri, campaign, opportunity_id, ttl_sec)
            raise

        latest = _hydrate_latest(self.client, existing)
        prev_ver = latest.version if latest else 0
        reclaimed_from = ""
        if latest is not None and isinstance(latest.content, Mapping):
            c = latest.content
            state = str(c.get("state") or "")
            holder = str(c.get("owner_worker_id") or "")
            exp_u = int(c.get("expires_at_unix") or 0)
            if state == "held" and holder != self.worker_id and now_u < exp_u + self.clock_skew_grace_sec:
                return LeaseOutcome(
                    status="busy",
                    lease=None,
                    holder_worker_id=holder,
                    expires_at_unix=exp_u,
                    fencing_token=latest.version,
                )
            if state == "held" and holder != self.worker_id and now_u >= exp_u + self.clock_skew_grace_sec:
                reclaimed_from = holder

        content = {
            "campaign": campaign,
            "opportunity_id": opportunity_id,
            "owner_worker_id": self.worker_id,
            "host": self.host,
            "acquired_at_unix": now_u,
            "expires_at_unix": now_u + ttl_sec,
            "ttl_sec": ttl_sec,
            "expected_prev_version": prev_ver,
            "reclaimed_from": reclaimed_from,
            "state": "held",
        }
        ev = Evidence(
            uri=uri,
            hash=canonical.digest(content),
            kind="element",
            source=Source(system="hanzo-research-lease", revision=self.commit),
            content=content,
        )
        filed = self.client.evidence(ev)

        # Re-GET canonical latest record to resolve concurrent acquisition races deterministically.
        verified_rows = self.client.evidence_versions(uri)
        winner = _hydrate_latest(self.client, verified_rows, filed=filed)
        if winner is None or not isinstance(winner.content, Mapping):
            raise RuntimeError(f"lease verification failed: no evidence returned for {uri}")
        w_holder = str(winner.content.get("owner_worker_id") or "")
        w_exp = int(winner.content.get("expires_at_unix") or 0)
        w_state = str(winner.content.get("state") or "")
        if w_holder != self.worker_id or w_state != "held":
            return LeaseOutcome(
                status="busy",
                lease=None,
                holder_worker_id=w_holder,
                expires_at_unix=w_exp,
                fencing_token=winner.version,
            )

        lease = Lease(
            uri=uri,
            campaign=campaign,
            opportunity_id=opportunity_id,
            fencing_token=winner.version,
            owner_worker_id=self.worker_id,
            host=self.host,
            acquired_at_unix=now_u,
            expires_at_unix=w_exp,
            reclaimed_from=reclaimed_from,
            offline_local=False,
        )
        if reclaimed_from and self.local_dir:
            wal = ResearchWal.open(str(self.local_dir / "wal"), campaign, worker_id=self.worker_id)
            wal.append("lease_reclaimed", lease.dump())
        return LeaseOutcome(
            status="acquired",
            lease=lease,
            holder_worker_id=self.worker_id,
            expires_at_unix=w_exp,
            fencing_token=winner.version,
        )

    def renew_lease(self, lease: Lease, *, ttl_sec: int = 600) -> Lease:
        """Heartbeat renewal; raises LeaseLostError if another worker fenced this lease."""
        now_u = self._now()
        if lease.offline_local or self.client is None:
            p = self._local_path(lease.uri)
            if p and p.is_file():
                cur = json.loads(p.read_text(encoding="utf-8"))
                if (
                    cur.get("owner_worker_id") != self.worker_id
                    or int(cur.get("fencing_token", 0)) != lease.fencing_token
                ):
                    raise LeaseLostError(f"offline lease lost on {lease.uri}")
            renewed = Lease(
                uri=lease.uri,
                campaign=lease.campaign,
                opportunity_id=lease.opportunity_id,
                fencing_token=lease.fencing_token + 1,
                owner_worker_id=self.worker_id,
                host=self.host,
                acquired_at_unix=lease.acquired_at_unix,
                expires_at_unix=now_u + ttl_sec,
                reclaimed_from=lease.reclaimed_from,
                offline_local=True,
            )
            if p:
                payload = dict(renewed.dump(), state="held", updated_at=now())
                tmp = p.with_name(p.name + ".tmp")
                tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                os.replace(tmp, p)
            return renewed

        latest = _hydrate_latest(self.client, self.client.evidence_versions(lease.uri))
        if (
            latest is None
            or not isinstance(latest.content, Mapping)
            or latest.content.get("owner_worker_id") != self.worker_id
            or latest.version != lease.fencing_token
            or latest.content.get("state") != "held"
        ):
            raise LeaseLostError(
                f"lease fenced on {lease.uri}: expected token {lease.fencing_token} ({self.worker_id})"
            )

        content = {
            "campaign": lease.campaign,
            "opportunity_id": lease.opportunity_id,
            "owner_worker_id": self.worker_id,
            "host": self.host,
            "acquired_at_unix": lease.acquired_at_unix,
            "expires_at_unix": now_u + ttl_sec,
            "ttl_sec": ttl_sec,
            "expected_prev_version": lease.fencing_token,
            "reclaimed_from": lease.reclaimed_from,
            "state": "held",
        }
        filed = self.client.evidence(
            Evidence(
                uri=lease.uri,
                hash=canonical.digest(content),
                kind="element",
                source=Source(system="hanzo-research-lease", revision=self.commit),
                content=content,
            )
        )
        after = _hydrate_latest(self.client, self.client.evidence_versions(lease.uri), filed=filed)
        if (
            after is None
            or not isinstance(after.content, Mapping)
            or after.content.get("owner_worker_id") != self.worker_id
        ):
            raise LeaseLostError(f"lease lost during renewal race on {lease.uri}")
        return Lease(
            uri=lease.uri,
            campaign=lease.campaign,
            opportunity_id=lease.opportunity_id,
            fencing_token=after.version,
            owner_worker_id=self.worker_id,
            host=self.host,
            acquired_at_unix=lease.acquired_at_unix,
            expires_at_unix=now_u + ttl_sec,
            reclaimed_from=lease.reclaimed_from,
            offline_local=False,
        )

    def verify_fencing(self, lease: Lease) -> None:
        """Assert this worker still holds the canonical lease version before mutating shared state."""
        if lease.offline_local or self.client is None:
            p = self._local_path(lease.uri)
            if p and p.is_file():
                cur = json.loads(p.read_text(encoding="utf-8"))
                if (
                    cur.get("owner_worker_id") != self.worker_id
                    or int(cur.get("fencing_token", 0)) != lease.fencing_token
                    or cur.get("state") != "held"
                ):
                    raise LeaseLostError(f"offline fencing token superseded on {lease.uri}")
            return
        latest = _hydrate_latest(self.client, self.client.evidence_versions(lease.uri))
        if (
            latest is None
            or not isinstance(latest.content, Mapping)
            or latest.content.get("owner_worker_id") != self.worker_id
            or latest.version != lease.fencing_token
            or latest.content.get("state") != "held"
        ):
            raise LeaseLostError(f"fencing token {lease.fencing_token} superseded on {lease.uri}")

    def reclaim_stale(
        self,
        campaign: str,
        opportunity_id: str,
        *,
        ttl_sec: int = 600,
    ) -> LeaseOutcome:
        """Reclaim an expired lease, advancing fencing_token and recording reclaimed_from."""
        return self.acquire_lease(campaign, opportunity_id, ttl_sec=ttl_sec)

    def release_lease(self, lease: Lease, *, final_state: str = "released") -> Evidence | None:
        """Immediately release a held lease (`released` or `completed`) so idle workers hold none."""
        if final_state not in ("released", "completed"):
            raise ValueError("final_state must be 'released' or 'completed'")
        now_u = self._now()
        if lease.offline_local or self.client is None:
            p = self._local_path(lease.uri)
            if p and p.is_file():
                cur = json.loads(p.read_text(encoding="utf-8"))
                if cur.get("owner_worker_id") == self.worker_id:
                    cur["state"] = final_state
                    cur["expires_at_unix"] = now_u
                    cur["fencing_token"] = int(cur.get("fencing_token", lease.fencing_token)) + 1
                    tmp = p.with_name(p.name + ".tmp")
                    tmp.write_text(json.dumps(cur, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    os.replace(tmp, p)
            return None

        latest = _hydrate_latest(self.client, self.client.evidence_versions(lease.uri))
        if (
            latest is None
            or not isinstance(latest.content, Mapping)
            or latest.content.get("owner_worker_id") != self.worker_id
        ):
            return None
        content = {
            "campaign": lease.campaign,
            "opportunity_id": lease.opportunity_id,
            "owner_worker_id": self.worker_id,
            "host": self.host,
            "acquired_at_unix": lease.acquired_at_unix,
            "expires_at_unix": now_u,
            "ttl_sec": 0,
            "expected_prev_version": latest.version,
            "reclaimed_from": lease.reclaimed_from,
            "state": final_state,
        }
        return self.client.evidence(
            Evidence(
                uri=lease.uri,
                hash=canonical.digest(content),
                kind="element",
                source=Source(system="hanzo-research-lease", revision=self.commit),
                content=content,
            )
        )
