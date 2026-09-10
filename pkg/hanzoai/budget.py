"""What you may spend, what is left, and what it cost.

Allowance and money never stand in for each other. :meth:`Budget.left` answers
a count of free calls; :meth:`Budget.balance` answers a sum of money. A product
that shows "17 of 20 left today" is reading the first; a gate that admits a paid
request is reading the second. Collapsing them is how a funded account reads as
broke, and a broke one as funded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional
from datetime import datetime
from dataclasses import field, dataclass

from hanzoai.page import Page
from hanzoai.wire import flag, rows, text, number, instant

if TYPE_CHECKING:  # the capability layer is written over the wire, not the generated client
    from hanzoai.client import Client

__all__ = ["Money", "Allowance", "Balance", "Plan", "Charge", "Budget"]


@dataclass(frozen=True)
class Money:
    """An amount in the currency's minor units. Never a float, anywhere, ever.

    `minor` counts minor units as ISO 4217 defines them: hundredths for USD,
    whole yen for JPY, thousandths for KWD. Not "cents", which is false for two
    of those three. Cloud answers USD today. A float dollar amount cannot
    represent 0.1, and a page of sub-cent calls sums to something nobody was
    charged.
    """

    minor: int = 0
    currency: str = "USD"


@dataclass(frozen=True)
class Allowance:
    """The free-call ceiling this period, and when the count starts again.

    `window` is which ceiling these numbers describe — ``"hour"`` or ``"day"``,
    the one that will stop you next. `spent` says the subject is at the limit.

    `limit == 0` means unbounded, and then `left` and `resets` are `None`
    rather than zero: there is no remainder to report and no period to end.
    """

    plan: str = ""
    limit: int = 0
    used: int = 0
    left: Optional[int] = None
    spent: bool = False
    window: str = ""
    resets: Optional[datetime] = None

    @classmethod
    def read(cls, body: Any) -> "Allowance":
        limit = number(body, "limit")
        used = number(body, "used")
        return cls(
            plan=text(body, "plan"),
            limit=limit,
            used=used,
            left=max(limit - used, 0) if limit else None,
            spent=flag(body, "spent"),
            window=text(body, "window"),
            resets=instant(body.get("resets")) if limit and isinstance(body, dict) else None,
        )


@dataclass(frozen=True)
class Balance:
    """The wallet this caller bills from.

    `account` echoes which wallet the money belongs to. A caller could only guess
    its own payer by decoding its own token, and a guess that disagrees with the
    server is how money lands in an account the gate never reads.
    """

    available: Money = Money()
    #: What a reservation has claimed and not yet posted. The wire spells it
    #: ``holds``; the name here is `reserved` because `held` is an arm of an
    #: answer, and one word for two facts is what the naming rule prevents.
    reserved: Money = Money()
    account: str = ""

    @classmethod
    def read(cls, body: Any) -> "Balance":
        return cls(
            available=Money(number(body, "available")),
            reserved=Money(number(body, "holds")),
            account=text(body, "account"),
        )


@dataclass(frozen=True)
class Plan:
    """The org's tier and which apps it opens.

    An app is `False` both when the plan does not grant it and when the licence
    authority could not be reached. A read that decides what to show fails to
    locked, never to an error.
    """

    tier: str = ""
    apps: Mapping[str, bool] = field(default_factory=dict)

    def opens(self, app: str) -> bool:
        """Whether `app` may be opened. An app nobody mentioned is locked."""
        return self.apps.get(app, False)

    @classmethod
    def read(cls, body: Any) -> "Plan":
        apps = body.get("apps") if isinstance(body, dict) else None
        return cls(
            tier=text(body, "tier"),
            apps={k: v is True for k, v in apps.items()} if isinstance(apps, dict) else {},
        )


@dataclass(frozen=True)
class Charge:
    """One billed call. `model` is the metered unit the debit recorded.

    Modelled here because cloud declares no response schema for this route.
    """

    id: str = ""
    at: Optional[datetime] = None
    model: str = ""
    amount: Money = Money()

    @classmethod
    def read(cls, body: Any) -> "Charge":
        meta = body.get("metadata") if isinstance(body, dict) else None
        return cls(
            id=text(body, "transactionId"),
            at=instant(body.get("createdAt")) if isinstance(body, dict) else None,
            model=text(meta, "model"),
            amount=Money(number(body, "amount")),
        )


class Budget:
    """`c.budget`."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def left(self) -> Allowance:
        """The free-call allowance this period. Asking does not spend."""
        return Allowance.read(self.client.read("GET", "/v1/allowance"))

    def balance(self) -> Balance:
        """The spendable prepaid balance."""
        return Balance.read(self.client.read("GET", "/v1/billing/balance"))

    def plan(self) -> Plan:
        """The tier, and which apps it opens."""
        return Plan.read(self.client.read("GET", "/v1/entitlement"))

    def spent(
        self,
        *,
        product: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Page[Charge]:
        """One row per billed call, newest first. The charged ledger, not a rollup."""
        body = self.client.read(
            "GET",
            "/v1/billing/usage",
            query={"product": product, "start": since, "end": until},
        )
        charges = tuple(Charge.read(r) for r in rows(body, "usage"))
        return Page(items=charges, total=number(body, "count") or len(charges))
