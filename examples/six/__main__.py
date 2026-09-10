"""six — budget, policy, search, kb, graph and audit in one flow.

What a real caller does, in the order it does it: find out what it may spend,
ask whether it may write, look up what is already known, file what it learned,
record the fact, and then read the trail back to prove all of it happened.

The trail is what ties the flow together. Every answer carries the
``x-request-id`` the server stamped on it, and every row the server wrote
carries the same id, so the last step looks up this run's own calls by the ids
the earlier steps collected.

Refusals are printed, not caught. A budget that says no and a policy that says
no are answers with a shape — a code, a reason, and the cures that would clear
them — so the flow reads them and keeps going rather than dying on an exception.

    export HANZO_CLIENT_ID=...        # an IAM application's clientId
    export HANZO_CLIENT_SECRET=...    # and its clientSecret
    python -m examples.six

The credential is exchanged for a short-lived access token at
``https://hanzo.id/v1/iam/oauth/token``; nothing here takes a bearer.
"""

from __future__ import annotations

import sys
from typing import List
from datetime import datetime, timezone, timedelta

from hanzoai import Ok, Doc, Fact, Held, Client, Denied, Filter
from hanzoai.cloud.exceptions import ApiException

#: What this run claims to have learned, and where it files it.
ENTITY = "hanzoai/python-sdk"
RELATION = "example"
VALUE = "six"
PAGE = "six-example"


def main() -> None:
    c = Client()
    print("endpoint {0} · issuer {1}".format(c.base, c.issuer))
    started = datetime.now(timezone.utc) - timedelta(minutes=1)
    trail: List[str] = []

    money(c)
    subject = permission(c)
    look(c, trail)
    file(c, trail)
    record(c, trail)
    receipts(c, trail, started, subject)


def money(c: Client) -> None:
    """What may be spent before anything is spent."""
    allowance = c.budget.left()
    balance = c.budget.balance()
    plan = c.budget.plan()

    ceiling = "unbounded" if allowance.left is None else "{0} of {1}".format(allowance.left, allowance.limit)
    print("\nbudget")
    print("  plan {0} · {1} free calls left this {2}".format(plan.tier or allowance.plan, ceiling, allowance.window))
    print(
        "  wallet {0} {1} available in {2}".format(balance.available.cents, balance.available.currency, balance.account)
    )


def permission(c: Client) -> str:
    """Whether this caller may write, asked before it tries."""
    decision = c.policy.check("self", "write", "graph:" + ENTITY)
    print("\npolicy")
    print(
        "  {0} {1} {2} → {3}{4}".format(
            decision.sub,
            decision.act,
            decision.obj,
            "allow" if decision.allow else "deny",
            " ({0})".format(decision.reason) if decision.reason else "",
        )
    )
    return decision.sub


def look(c: Client, trail: List[str]) -> None:
    """What the org already knows, over every corpus it has."""
    a = c.search.find("python sdk capabilities", kinds=["page", "memory"], limit=5)
    trail.append(a.request)
    print("\nsearch")
    match a:
        case Ok(value=hits):
            print("  {0} in {1}ms, mode {2}".format(hits.status, int(hits.took.total_seconds() * 1000), hits.mode))
            for backend in hits.backends:
                print(
                    "    leg {0}: {1}{2}".format(
                        backend.name, backend.status, " — " + backend.error if backend.error else ""
                    )
                )
            for hit in hits.items:
                print("    {0:.4f}  {1} · {2}".format(hit.score, hit.kind or hit.corpus, hit.title or hit.id))
            if hits.partial:
                print("    these are the surviving legs' results, not the whole corpus")
            if not hits.items:
                print("    nothing matched")
        case Denied() as denied:
            refusal(denied)
        case Held() as held:
            hold(held)


def file(c: Client, trail: List[str]) -> None:
    """A page recording what this run did, written into the org's own corpus."""
    doc = Doc(
        kind="page",
        name=PAGE,
        title="Six capabilities, from the Python SDK",
        body="Written by examples/six at {0}.".format(datetime.now(timezone.utc).isoformat()),
    )
    a = c.kb.put(doc)
    trail.append(a.request)
    print("\nkb")
    match a:
        case Ok(value=written):
            print("  wrote kb.{0}/{1}".format(written.kind, written.name or doc.name))
        case Denied() as denied:
            refusal(denied)
            if denied.code == "entitlement_required":
                print("    the kb module may not be installed in this org: c.kb.install()")
        case Held() as held:
            hold(held)


def record(c: Client, trail: List[str]) -> None:
    """One assertion, with its provenance, and what now wins."""
    now = datetime.now(timezone.utc)
    fact = Fact(
        entity=ENTITY,
        relation=RELATION,
        value=VALUE,
        at=now,
        seen=now,
        source="examples/six",
        evidence="python -m examples.six",
        confidence=1.0,
    )
    a = c.graph.assert_([fact])
    trail.append(a.request)
    print("\ngraph")
    match a:
        case Ok(value=wrote):
            print("  recorded {0} · duplicate {1} · refused {2}".format(wrote.recorded, wrote.duplicate, wrote.refused))
            for reason in wrote.reasons:
                print("    refused: {0}".format(reason))
            resolution = c.graph.resolve(ENTITY, RELATION)
            if resolution.known and resolution.winner:
                print(
                    "  {0} {1} = {2} (from {3}){4}".format(
                        ENTITY,
                        RELATION,
                        resolution.winner.value,
                        resolution.winner.source or "an unnamed source",
                        ", contested" if resolution.contested else "",
                    )
                )
            else:
                print("  nothing is asserted about {0} {1} yet".format(ENTITY, RELATION))
        case Denied() as denied:
            refusal(denied)
        case Held() as held:
            hold(held)


def receipts(c: Client, trail: List[str], since: datetime, subject: str) -> None:
    """The trail, read back for this run's own calls.

    Cloud's audit filter declares no `requestId` although every row carries one,
    so `Filter.request` narrows on the client. That is why this asks for a
    window rather than for one row.
    """
    print("\naudit")
    wanted = [request for request in trail if request]
    if not wanted:
        print("  nothing to look up: no answer carried a request id")
        return

    found = {}
    for event in c.audit.all(Filter(since=since, size=200)):
        if event.request in wanted:
            found[event.request] = event

    for request in wanted:
        event = found.get(request)
        if event is None:
            print("  {0} · no row yet".format(request))
            continue
        print(
            "  {0} · {1} {2} {3} → {4} by {5}".format(
                request,
                event.at.isoformat() if event.at else "unstamped",
                event.action or event.method,
                event.resource or event.path,
                event.result,
                event.actor or subject,
            )
        )


def refusal(denied: Denied) -> None:
    print("  denied {0}: {1}".format(denied.code, denied.reason))
    for cure in denied.cures:
        print("    {0} → {1}".format(cure.kind, cure.url))


def hold(held: Held) -> None:
    print("  held on {0}: {1}".format(held.clause, held.reason))
    print("    approval {0}".format(held.id))


if __name__ == "__main__":
    try:
        main()
    except ApiException as e:
        # The status line alone says nothing. The server's explanation is what a
        # caller can act on.
        print("HTTP {0}: {1}".format(e.status, e.body or e.reason), file=sys.stderr)
        raise SystemExit(1) from e
