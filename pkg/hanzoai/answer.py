"""The answer a gated call gives, and the one rule that reads it off the wire.

Budgets and policies refuse. A refusal is something the caller can act on — top
up, ask for the entitlement, wait for a person to approve — so it is a value
here, never an exception. One type carries all three outcomes::

    a = c.search.find("q3 incident postmortems")
    if a.denied:
        for cure in a.denied.cures:
            offer(cure.kind, cure.url)
    else:
        hits = a.value

Three arms and nothing else. :class:`Ok` holds what ran, :class:`Denied` names
the code and the way out, :class:`Held` names the approval a person still has to
give. Every arm carries `request`, the ``x-request-id`` that finds the call in
:mod:`hanzoai.audit`.

Reading `.value` off a refusal raises it, so a caller who skips the branch stops
at the refusal rather than reading past it. That is the whole safety property:
you cannot reach the value without acknowledging which arm you got.

Statuses with no decision in them — 401, a bare 403, any other 4xx, every 5xx,
a transport failure — are not arms. Nothing was decided, so there is nothing to
read, and they raise :class:`~hanzoai.cloud.exceptions.ApiException`.
"""

from __future__ import annotations

from typing import Any, Tuple, Union, Generic, TypeVar, Callable, NoReturn
from dataclasses import dataclass
from typing_extensions import Literal

from hanzoai.wire import Reply, rows, text

__all__ = ["Cure", "Ok", "Denied", "Held", "Answer", "read", "value", "fault", "error", "held", "REFUSED"]

T = TypeVar("T")

#: The codes that make a 403 a refusal rather than an unauthenticated call.
#:
#: Cloud spells "no validated principal" as 403 forbidden, so status alone
#: cannot separate "authenticated and refused" from "not signed in". These four
#: codes do. The set is deliberately small and closed: it is the workaround for
#: that one defect, not a vocabulary. `Denied.code` itself stays a plain string,
#: so a code cloud adds tomorrow arrives as data.
REFUSED = frozenset({"policy_denied", "entitlement_required", "spend_cap_exceeded", "insufficient_balance"})


@dataclass(frozen=True)
class Cure:
    """A way to clear a refusal. `kind` says what it is, `url` is where it happens."""

    kind: str
    url: str


@dataclass(frozen=True)
class Ok(Generic[T]):
    """The call ran. `value` is what it produced."""

    value: T
    request: str = ""
    status: Literal["ok"] = "ok"

    @property
    def denied(self) -> None:
        """Nothing refused this call."""
        return None

    @property
    def held(self) -> None:
        """Nothing held this call."""
        return None


@dataclass(frozen=True)
class Denied(Exception):
    """The call was refused, and this says why and what would clear it.

    `code` is cloud's own word for the refusal — ``insufficient_balance`` (the
    wallet is empty) and ``spend_cap_exceeded`` (the wallet has money and a cap
    says no) are different facts with different cures and are never collapsed.
    `product` is set when the gate is product-scoped.
    """

    code: str = ""
    reason: str = ""
    product: str = ""
    cures: Tuple[Cure, ...] = ()
    request: str = ""
    status: Literal["denied"] = "denied"

    @property
    def value(self) -> NoReturn:
        """Raises, because a refusal produced no value."""
        raise self

    @property
    def denied(self) -> "Denied":
        """Itself. The branch a caller tests."""
        return self

    @property
    def held(self) -> None:
        """A refusal is not a hold: nobody is being asked."""
        return None

    def __str__(self) -> str:
        return "{0}: {1}".format(self.code or "denied", self.reason)

    @classmethod
    def read(cls, body: Any, request: str = "") -> "Denied":
        """Reads either shape cloud answers a refusal with.

        Most refusals are the RFC 9457 envelope — ``{type, title, status,
        detail, code}`` — and the money gate answers ``{error, product, reason,
        message, cure}``. Both are read here, once, so no capability learns
        that there are two.
        """
        cures = []
        for c in rows(body, "cure") + rows(body, "cures"):
            if isinstance(c, dict):
                cures.append(Cure(kind=text(c, "kind"), url=text(c, "url")))
            elif isinstance(c, str):
                cures.append(Cure(kind=c, url=""))
        return cls(
            code=text(body, "code") or text(body, "error"),
            reason=text(body, "detail") or text(body, "reason") or text(body, "message") or text(body, "title"),
            product=text(body, "product"),
            cures=tuple(cures),
            request=request,
        )


@dataclass(frozen=True)
class Held(Exception):
    """A person was asked. Nothing ran, and `id` is the handle to the approval.

    `clause` names the policy clause that stopped the call — the same clause
    :meth:`hanzoai.policy.Policy.check` would have refused on, so a caller can
    tell which of its own checks it should have run first.
    """

    id: str = ""
    clause: str = ""
    reason: str = ""
    request: str = ""
    status: Literal["held"] = "held"

    @property
    def value(self) -> NoReturn:
        """Raises, because a held call produced no value."""
        raise self

    @property
    def denied(self) -> None:
        """A hold is not a refusal: the question is open."""
        return None

    @property
    def held(self) -> "Held":
        """Itself. The branch a caller tests."""
        return self

    def __str__(self) -> str:
        return "held on {0}: {1}".format(self.clause or "a policy clause", self.reason)

    @classmethod
    def read(cls, body: Any, request: str = "") -> "Held":
        return cls(
            id=text(body, "id"),
            clause=text(body, "clause"),
            reason=text(body, "reason"),
            request=request,
        )


#: What a gated call answers. The three arms share `request` and `status` and
#: nothing else, so reading `value` off the wrong one raises instead of handing
#: back a half-answer.
Answer = Union[Ok[T], Denied, Held]


def held(reply: Reply) -> bool:
    """True when this reply is an approval hold.

    The body decides, never the status code: a dozen long-running operations
    answer 202 for "accepted, working on it" and carry their own schema. Only
    ``status: "held"`` is a hold.
    """
    return reply.status == 202 and isinstance(reply.body, dict) and reply.body.get("status") == "held"


def read(reply: Reply, decode: Callable[[Any], T]) -> Answer[T]:
    """The one rule that turns an HTTP answer into an arm.

    2xx runs `decode` and answers :class:`Ok`. A hold answers :class:`Held`.
    402, and 403 carrying one of :data:`REFUSED`, answer :class:`Denied`.
    Everything else decided nothing and raises.
    """
    if held(reply):
        return Held.read(reply.body, reply.request)
    if 200 <= reply.status <= 299:
        return Ok(decode(reply.body), reply.request)
    if reply.status == 402 or (reply.status == 403 and text(reply.body, "code") in REFUSED):
        return Denied.read(reply.body, reply.request)
    raise fault(reply)


def value(reply: Reply) -> Any:
    """What a call no gate refuses produced, or the reason there is nothing.

    The two-outcome rule, beside the three-arm one. A read that cannot be
    refused has no arms to branch on, so it answers its body or it raises.
    """
    if 200 <= reply.status <= 299:
        return reply.body
    raise fault(reply)


def fault(reply: Reply) -> Exception:
    """The error for a reply that decided nothing, naming the call in the trail."""
    detail = text(reply.body, "detail") or text(reply.body, "title") or text(reply.body, "error")
    if not detail:
        detail = reply.body if isinstance(reply.body, str) else "no readable body"
    return error(
        reply.status,
        "{0} (request {1})".format(detail, reply.request or "unstamped"),
        reply.body if isinstance(reply.body, str) else "",
    )


def error(status: int, reason: str, body: str = "") -> Exception:
    """The SDK's one HTTP error, built in the one place that builds it.

    :class:`~hanzoai.cloud.exceptions.ApiException` is imported here rather than
    at the top of the module, so describing a failure does not pull the
    generated client in behind it. The six capabilities are written over the
    wire, not over the 2,479 generated operations; only
    :class:`hanzoai.Client` bridges the two.
    """
    from hanzoai.cloud.exceptions import ApiException

    return ApiException(status=status, reason=reason, body=body or None)
