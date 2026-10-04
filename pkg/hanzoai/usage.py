"""Plan usage: where a priced call stands, and the refusals it can meet.

Every answer from a priced model carries the standing in headers::

    r = AiApi(c).post_chat_completions_with_http_info(req)
    u = read_usage(r.headers)
    u.paid_by  # "plan", "credits" or "free"; None when the answer named none

A refused call raises one class per refusal code, all under
:class:`UsageLimitError`, from :meth:`hanzoai.Client.send` and from every
generated operation the client runs::

    try:
        AiApi(c).post_decisions(req)
    except FreePlanCapError as e:
        e.resets_at, [a.url for a in e.actions]

The refusal states shares and ways on, never an amount: no field here is a
price, a count or a cap. The body is the AI router's, ``{"error": {message,
type, code, class, model, fallback, resets_at, upgrade_url, actions}}``; the
money gate's flat refusal is :class:`hanzoai.Denied`, and a body with neither
shape stays the fault it was. The class names are the ones the JavaScript and
Go SDKs use.
"""

from __future__ import annotations

from typing import Any, Dict, Type, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from hanzoai.wire import Reply, instant
from hanzoai.answer import Fault

__all__ = [
    "Usage",
    "Action",
    "read_usage",
    "refusal",
    "UsageLimitError",
    "PlanAllowanceUsedError",
    "PaidPlanRequiredError",
    "FreePlanCapError",
    "ModelCapError",
    "UsageCapExceededError",
    "InsufficientBalanceError",
]


@dataclass(frozen=True)
class Usage:
    """The standing one answer reported, read from its ``X-Hanzo-*`` headers.

    A header the answer did not carry reads `None`. A free model's answer
    carries only `served`, so its `paid_by` is unknown, not ``""``.
    """

    #: ``X-Hanzo-Usage``: ok, near or limited, where the class stands.
    usage: Optional[str] = None
    #: ``X-Hanzo-Usage-Class``: premium, ours or free.
    usage_class: Optional[str] = None
    #: ``X-Hanzo-Paid-By``: plan, credits or free.
    paid_by: Optional[str] = None
    #: ``X-Hanzo-Fallback``: the model that answered instead of the one asked for.
    fallback: Optional[str] = None
    #: ``X-Hanzo-Served``: the model that answered.
    served: Optional[str] = None
    #: ``X-Hanzo-Usage-Reason``: the refusal code that sent the call to `fallback`.
    reason: Optional[str] = None


#: Header name, lowercased, to the field it fills.
HEADERS = {
    "x-hanzo-usage": "usage",
    "x-hanzo-usage-class": "usage_class",
    "x-hanzo-paid-by": "paid_by",
    "x-hanzo-fallback": "fallback",
    "x-hanzo-served": "served",
    "x-hanzo-usage-reason": "reason",
}


def read_usage(headers: Any) -> Usage:
    """The :class:`Usage` in `headers`, matched without regard to case.

    `headers` is any mapping (a dict, urllib3's or httpx's headers, a generated
    ``ApiResponse.headers``) or a sequence of name, value pairs. `None` reads
    as no headers. An empty value is absent.
    """
    pairs = headers.items() if hasattr(headers, "items") else (headers or ())
    found: Dict[str, str] = {}
    for name, v in pairs:
        field = HEADERS.get(str(name).lower())
        if field and isinstance(v, str) and v.strip():
            found[field] = v.strip()
    return Usage(**found)


@dataclass(frozen=True)
class Action:
    """One way on from a refusal.

    `kind` is upgrade (`url`, `plan`), switch (`model`), credits (`url` is
    ``/v1/ai/limits``; a PUT with ``creditsAfterAllowance`` turns it on) or
    topup (`url` is the pay page). A field the action did not carry is `None`.
    """

    kind: str
    label: Optional[str] = None
    url: Optional[str] = None
    plan: Optional[str] = None
    model: Optional[str] = None

    @classmethod
    def read(cls, body: Any) -> "Action":
        return cls(kind=_text(body, "kind") or "", **{k: _text(body, k) for k in ("label", "url", "plan", "model")})


class UsageLimitError(Fault):
    """A priced call the plan, the wallet or a cap refused, and the ways on.

    `status` is the HTTP status and `code` the refusal. `usage_class` is the
    model class it concerns (the body's ``class``); `model` and `fallback` name
    the model refused and the one that would answer instead; `resets_at` is
    when the refusal lifts; `actions` are the ways on, in the order the server
    gave them. It is a :class:`hanzoai.Fault`, so it also carries `request`
    and `retry_after`, and ``except Fault`` still catches it.
    """

    #: The refusal code a subclass answers; the base class names none.
    CODE = ""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        type: Optional[str] = None,
        usage_class: Optional[str] = None,
        model: Optional[str] = None,
        fallback: Optional[str] = None,
        resets_at: Optional[datetime] = None,
        upgrade_url: Optional[str] = None,
        actions: Tuple[Action, ...] = (),
        request: str = "",
        retry_after: float = 0,
    ) -> None:
        super().__init__(status, code, message, request, retry_after)
        self.message = message
        self.type = type
        self.usage_class = usage_class
        self.model = model
        self.fallback = fallback
        self.resets_at = resets_at
        self.upgrade_url = upgrade_url
        self.actions = actions


class PlanAllowanceUsedError(UsageLimitError):
    """402: the plan's included usage of the class is used and nothing else may pay."""

    CODE = "plan_allowance_used"


class PaidPlanRequiredError(UsageLimitError):
    """402: the model needs a paid plan or prepaid balance."""

    CODE = "paid_plan_required"


class FreePlanCapError(UsageLimitError):
    """429: the free plan's daily share of the model is used; `resets_at` says when it returns."""

    CODE = "free_plan_cap"


class ModelCapError(UsageLimitError):
    """402: the model used its share of the plan; `fallback` is the model that answers instead."""

    CODE = "model_cap"


class UsageCapExceededError(UsageLimitError):
    """429: a session or day request window is spent."""

    CODE = "usage_cap_exceeded"


class InsufficientBalanceError(UsageLimitError):
    """402: the wallet's known balance cannot cover the call."""

    CODE = "insufficient_balance"


#: Refusal code to the class raised for it.
CODES: Dict[str, Type[UsageLimitError]] = {
    c.CODE: c
    for c in (
        PlanAllowanceUsedError,
        PaidPlanRequiredError,
        FreePlanCapError,
        ModelCapError,
        UsageCapExceededError,
        InsufficientBalanceError,
    )
}


def refusal(reply: Reply) -> Optional[UsageLimitError]:
    """The :class:`UsageLimitError` `reply` carries, or `None` when it carries none.

    Only a non-2xx whose body is ``{"error": {"code": ...}}`` with one of the
    six codes is one; every other answer is left to the rule that already reads
    it.
    """
    if 200 <= reply.status <= 299 or not isinstance(reply.body, dict):
        return None
    e = reply.body.get("error")
    if not isinstance(e, dict):
        return None
    cls = CODES.get(_text(e, "code") or "")
    if cls is None:
        return None
    acts = e.get("actions")
    return cls(
        reply.status,
        cls.CODE,
        _text(e, "message") or "",
        type=_text(e, "type"),
        usage_class=_text(e, "class"),
        model=_text(e, "model"),
        fallback=_text(e, "fallback"),
        resets_at=instant(e.get("resets_at")),
        upgrade_url=_text(e, "upgrade_url"),
        actions=tuple(Action.read(a) for a in acts if isinstance(a, dict)) if isinstance(acts, list) else (),
        request=reply.request,
        retry_after=reply.retry_after,
    )


def _text(body: Any, key: str) -> Optional[str]:
    """The non-empty string at `key`, or `None`."""
    v = body.get(key) if isinstance(body, dict) else None
    return v if isinstance(v, str) and v else None
