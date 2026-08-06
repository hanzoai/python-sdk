"""The engine's wire shapes, as Python values.

Field names on the wire are camelCase and an activity is keyed by a pair —
``execution.workflowId`` (the activity id) and ``execution.runId``. These
classes flatten that pair to ``id``/``run_id`` and keep the decoded body in
``raw``, so a field this version does not model is carried rather than lost.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

SCHEDULED = "ACTIVITY_TASK_STATE_SCHEDULED"
STARTED = "ACTIVITY_TASK_STATE_STARTED"
COMPLETED = "ACTIVITY_TASK_STATE_COMPLETED"
FAILED = "ACTIVITY_TASK_STATE_FAILED"
CANCELED = "ACTIVITY_TASK_STATE_CANCELED"

TERMINAL = frozenset({COMPLETED, FAILED, CANCELED})


@dataclass(frozen=True)
class RetryPolicy:
    """Retry knobs the engine stores against a dispatched activity.

    Durations are Go duration strings — ``"5s"``, ``"1m30s"``.
    """

    initial_interval: str | None = None
    backoff_coefficient: float | None = None
    maximum_interval: str | None = None
    maximum_attempts: int | None = None
    non_retryable_error_types: list[str] | None = None

    def wire(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.initial_interval is not None:
            out["initialInterval"] = self.initial_interval
        if self.backoff_coefficient is not None:
            out["backoffCoefficient"] = self.backoff_coefficient
        if self.maximum_interval is not None:
            out["maximumInterval"] = self.maximum_interval
        if self.maximum_attempts is not None:
            out["maximumAttempts"] = self.maximum_attempts
        if self.non_retryable_error_types is not None:
            out["nonRetryableErrorTypes"] = list(self.non_retryable_error_types)
        return out


@dataclass(frozen=True)
class Activity:
    """One standalone activity: a unit of work the engine tracks durably."""

    id: str
    run_id: str
    type: str
    status: str
    task_queue: str = ""
    attempt: int = 0
    maximum_attempts: int = 0
    input: Any = None
    result: Any = None
    failure_cause: str = ""
    identity: str = ""
    lease_expiry: str = ""
    heartbeat_timeout: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL

    @classmethod
    def from_wire(cls, body: dict[str, Any]) -> Activity:
        execution = body.get("execution") or {}
        activity_type = body.get("type") or {}
        return cls(
            id=execution.get("workflowId", ""),
            run_id=execution.get("runId", ""),
            type=activity_type.get("name", ""),
            status=body.get("status", ""),
            task_queue=body.get("taskQueue", ""),
            attempt=body.get("attempt", 0),
            maximum_attempts=body.get("maximumAttempts", 0),
            input=body.get("input"),
            result=body.get("result"),
            failure_cause=body.get("failureCause", ""),
            identity=body.get("identity", ""),
            lease_expiry=body.get("leaseExpiry", ""),
            heartbeat_timeout=body.get("heartbeatTimeout", ""),
            raw=body,
        )


@dataclass(frozen=True)
class Event:
    """One durable record in an activity's history."""

    id: int
    time: str
    type: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_wire(cls, body: dict[str, Any]) -> Event:
        return cls(
            id=body.get("eventId", 0),
            time=body.get("eventTime", ""),
            type=body.get("eventType", ""),
            attributes=body.get("attributes") or {},
        )


@dataclass(frozen=True)
class Page:
    """One page of activities, with the cursor that continues it."""

    activities: list[Activity]
    cursor: str = ""

    def __iter__(self) -> Iterator[Activity]:
        return iter(self.activities)

    def __len__(self) -> int:
        return len(self.activities)
