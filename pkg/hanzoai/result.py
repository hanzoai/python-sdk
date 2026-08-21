"""The outcome of an approval-gated call.

Some calls are sensitive enough that the platform stops them for a human
decision instead of running them. That answer arrives as HTTP 202 carrying the
approval verbatim — the same field names `GET /v1/approvals/{id}` returns, so
there is one shape to learn.

A 202 is a 2xx, which is exactly the trap: a client that only checks "did it
throw" reads a queued call as a completed one. Nothing here lets that happen.
Through :class:`hanzoai.Client` a held call raises :class:`Held`, which names
the approval; :func:`result` turns that raise into a value you must destructure
before you can read anything out of it.

    from hanzoai import is_held, result, unwrap

    r = result(memory.post_memory_remember, body)
    if is_held(r):
        print(r.id, r.clause, r.reason)   # queued, nothing ran
    else:
        fact = unwrap(r)                  # raises Held if it was not done
"""

from __future__ import annotations

import json
from typing import Any, Union, Generic, TypeVar, Callable, Optional
from dataclasses import dataclass
from typing_extensions import Literal, TypeGuard

from hanzoai.cloud.exceptions import ApiException

__all__ = [
    "Approval",
    "Done",
    "Held",
    "Result",
    "is_done",
    "is_held",
    "result",
    "unwrap",
]

T = TypeVar("T")


@dataclass(frozen=True)
class Approval:
    """A call the platform stopped for a human decision.

    `id` is the handle to poll or resolve by, `clause` names the policy clause
    that held the call, and `reason` says why. `status` is always ``"held"``.
    """

    id: str
    clause: str
    reason: str
    status: Literal["held"] = "held"

    @classmethod
    def held(cls, body: Any) -> Optional["Approval"]:
        """Reads a body as a hold, or returns `None` when it is not one.

        The body is the discriminator, not the status code: 202 also means
        "accepted, working on it" on a dozen long-running operations, and those
        carry their own schema. Only ``status: "held"`` is an approval.

        Serves a 202 and `GET /v1/approvals/{id}` alike — the field names are
        the same, and a resolved approval no longer says `held`. The server
        omits an empty field, so each one reads as ``""`` rather than `None`.
        """
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", "replace")
        if isinstance(body, str):
            try:
                body = json.loads(body) if body else None
            except ValueError:
                return None
        if not isinstance(body, dict) or body.get("status") != "held":
            return None
        return cls(
            id=_text(body.get("id")),
            clause=_text(body.get("clause")),
            reason=_text(body.get("reason")),
        )


@dataclass(frozen=True)
class Done(Generic[T]):
    """A call that ran. `value` is what it returned."""

    value: T
    status: Literal["done"] = "done"


#: What an approval-gated call produced. The two arms share no member: an
#: `Approval` has no `value` and a `Done` has no `id`, so reading either one
#: without checking `status` first fails at the attribute rather than quietly
#: handing back a half-answer.
Result = Union[Done[T], Approval]


class Held(ApiException):
    """Raised for a call the platform held. Carries the approval that gates it.

    It is an :class:`ApiException` because a held call is an HTTP outcome that
    produced no value: `status` is 202 and `body` is the response verbatim. A
    caller who catches `ApiException` at the edge already treats it as "no
    result", which is the safe direction; catch `Held` to treat it as "queued".
    """

    def __init__(self, approval: Approval, *, body: Optional[str] = None) -> None:
        super().__init__(
            status=202,
            reason="held on {0}: {1}".format(approval.clause, approval.reason),
            body=body,
        )
        self.approval = approval


def is_held(r: Result[T]) -> TypeGuard[Approval]:
    """True when the call was held. The explicit check."""
    return r.status == "held"


def is_done(r: Result[T]) -> TypeGuard[Done[T]]:
    """True when the call ran."""
    return r.status == "done"


def unwrap(r: Result[T]) -> T:
    """Returns the value of a `Done`, or raises :class:`Held` naming the approval."""
    if isinstance(r, Approval):
        raise Held(r)
    return r.value


def result(call: Callable[..., T], *args: Any, **kwargs: Any) -> Result[T]:
    """Runs an approval-gated call and returns its outcome as a value.

    Every operation on a :class:`hanzoai.Client` raises :class:`Held` when the
    platform holds it. Wrap the call here when you want to handle the hold
    rather than let it propagate.
    """
    try:
        return Done(call(*args, **kwargs))
    except Held as held:
        return held.approval


def _text(v: Any) -> str:
    return v if isinstance(v, str) else ""
