"""The six capabilities: the request each one builds, and what it makes of the answer.

Nothing here touches the network. `Calls` gives a capability the same two
methods :class:`hanzoai.Client` gives it — `send` for a call that can be
refused, `read` for one that cannot — so these exercise the real capability
code and only the socket is missing. The bodies are the shapes cloud's own
schemas declare.
"""

from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

import pytest

from hanzoai import Ok, Held, Denied, answer
from hanzoai.kb import Kb, Doc, Link, Sync, Reindex
from hanzoai.wire import Reply, query as asked
from hanzoai.audit import Audit, Filter
from hanzoai.graph import Fact, Graph
from hanzoai.budget import Money, Budget
from hanzoai.policy import Policy
from hanzoai.search import Search


@dataclass(frozen=True)
class Ask:
    """What a capability asked for."""

    method: str
    path: str
    query: dict
    body: object
    media: str


class Calls:
    """Answers each call with the next staged reply, and records what it was asked."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.asked = []

    def send(self, method, path, *, query=None, body=None, media="application/json"):
        self.asked.append(Ask(method, path, asked(query), body, media))
        assert self.replies, "the capability made more calls than the test staged"
        return self.replies.pop(0)

    def read(self, method, path, **call):
        # The one line `Client.read` is, so the rule cannot drift between them.
        return answer.value(self.send(method, path, **call))

    @property
    def asked_once(self):
        assert len(self.asked) == 1, "expected one call, got {0}".format(len(self.asked))
        return self.asked[0]


def ok(body, request="req_1"):
    return Reply(status=200, body=body, request=request)


REFUSED = Reply(
    status=402,
    body={
        "code": "insufficient_balance",
        "detail": "the wallet is empty",
        "cure": [{"kind": "credit", "url": "/v1/billing"}],
    },
    request="req_2",
)

HELD = Reply(
    status=202,
    body={"status": "held", "id": "apr_7f3", "clause": "graph.assert", "reason": "a person reviews graph writes"},
    request="req_3",
)


# --------------------------------------------------------------------------
# budget — a count and a sum, which never stand in for each other
# --------------------------------------------------------------------------


def test_left_reads_the_allowance_and_computes_what_remains():
    """`left` is not on the wire. `limit - used` is, and it never goes negative."""
    calls = Calls(ok({"plan": "pro", "limit": 20, "used": 17, "spent": False, "window": "day", "resets": 1789084800}))
    allowance = Budget(calls).left()

    assert calls.asked_once == Ask("GET", "/v1/allowance", {}, None, "application/json")
    assert (allowance.plan, allowance.limit, allowance.used, allowance.left) == ("pro", 20, 17, 3)
    assert allowance.window == "day"
    assert allowance.resets == datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc)


def test_an_unbounded_allowance_has_no_remainder_and_no_reset():
    """`limit == 0` is unbounded. Reporting `left` as 0 would read as "none left"."""
    allowance = Budget(Calls(ok({"plan": "enterprise", "limit": 0, "used": 4831, "window": "day"}))).left()

    assert allowance.left is None
    assert allowance.resets is None
    assert allowance.used == 4831


def test_balance_is_integer_cents_and_says_which_wallet():
    calls = Calls(ok({"balance": 14991307, "holds": 250, "available": 14991057, "account": "org_acme"}))
    balance = Budget(calls).balance()

    assert calls.asked_once.path == "/v1/billing/balance"
    assert balance.available == Money(cents=14991057, currency="USD")
    assert balance.held == Money(cents=250, currency="USD")
    assert balance.account == "org_acme"
    assert isinstance(balance.available.cents, int), "money is never a float"


def test_a_plan_fails_to_locked_for_an_app_nobody_mentioned():
    plan = Budget(Calls(ok({"tier": "pro", "apps": {"console": True, "o11y": False}}))).plan()

    assert plan.tier == "pro"
    assert plan.opens("console") is True
    assert plan.opens("o11y") is False
    assert plan.opens("commerce") is False, "an app the answer never mentioned is locked, not an error"


def test_spent_pages_the_charged_ledger():
    calls = Calls(
        ok(
            {
                "user": "org_acme",
                "count": 2,
                "usage": [
                    {
                        "transactionId": "tx_1",
                        "amount": 137,
                        "metadata": {"model": "zen4"},
                        "createdAt": "2026-09-01T10:00:00Z",
                    },
                    {
                        "transactionId": "tx_2",
                        "amount": 4,
                        "metadata": {"model": "zen4-mini"},
                        "createdAt": "2026-09-01T11:30:00Z",
                    },
                ],
            }
        )
    )
    page = Budget(calls).spent(product="inference", since=datetime(2026, 9, 1, tzinfo=timezone.utc))

    assert calls.asked_once.query == {"product": "inference", "start": "2026-09-01T00:00:00Z"}
    assert page.total == 2
    assert page.items[0].id == "tx_1"
    assert page.items[0].model == "zen4"
    assert page.items[0].amount == Money(cents=137, currency="USD")
    assert page.items[1].at == datetime(2026, 9, 1, 11, 30, tzinfo=timezone.utc)
    assert list(page) == list(page.items) and len(page) == 2


# --------------------------------------------------------------------------
# policy — a denial is a value, and the question rides beside the verdict
# --------------------------------------------------------------------------


def test_check_takes_the_sentence_order_and_sends_the_route_s_member_names():
    """A person says subject, verb, object. The route reads `{subject, verb, path}`.

    The difference is spelled once, here, and nowhere a caller can see it.
    """
    calls = Calls(ok({"allow": True, "subject": "usr_7", "path": "acme/graph", "verb": "write"}))
    decision = Policy(calls).check("usr_7", "write", "acme/graph")

    assert calls.asked_once.body == {"subject": "usr_7", "verb": "write", "path": "acme/graph"}
    assert decision.allow is True
    assert (decision.sub, decision.act, decision.obj) == ("usr_7", "write", "acme/graph")


def test_a_denial_is_a_verdict_not_a_refusal():
    """Asking whether you may is a question with an answer. `allow` is False, and that is all."""
    decision = Policy(Calls(ok({"allow": False, "reason": "no grant at or above acme/graph"}))).check(
        "usr_7", "write", "acme/graph"
    )
    assert decision.allow is False
    assert decision.reason == "no grant at or above acme/graph"
    assert decision.obj == "acme/graph", "the question survives even when cloud echoes nothing"


# --------------------------------------------------------------------------
# audit — read-only, and the join back to a call
# --------------------------------------------------------------------------

ROW = {
    "seq": 41,
    "org": "acme",
    "sub": "usr_7",
    "email": "z@acme.example",
    "action": "graph.assert",
    "resource": "graph",
    "resourceId": "acme",
    "method": "POST",
    "path": "/v1/graph",
    "result": "success",
    "status": 200,
    "time": "2026-09-10T21:00:00Z",
    "requestId": "req_1",
    "sourceIp": "203.0.113.7",
    "userAgent": "hanzoai-python",
}


def test_a_row_is_read_in_the_names_the_reader_wants():
    calls = Calls(ok({"data": [ROW], "total": 1, "status": "ok"}))
    page = Audit(calls).list()

    assert calls.asked_once.query == {"pageSize": 100, "p": 1}
    event = page.items[0]
    assert event.actor == "usr_7", "`sub` is token jargon; the reader wants who did it"
    assert event.id == "acme", "`resourceId` sits beside `resource` and the compound says nothing more"
    assert event.request == "req_1", "the same word as Answer.request — this is what joins them"
    assert event.ip == "203.0.113.7" and event.agent == "hanzoai-python"
    assert event.at == datetime(2026, 9, 10, 21, 0, tzinfo=timezone.utc)


def test_a_filter_is_sent_in_cloud_s_own_spelling():
    calls = Calls(ok({"data": [], "total": 0}))
    Audit(calls).list(Filter(actor="usr_7", action="graph.assert", id="acme", result="success", size=25, page=2))

    assert calls.asked_once.query == {
        "sub": "usr_7",
        "action": "graph.assert",
        "resourceId": "acme",
        "result": "success",
        "pageSize": 25,
        "p": 2,
    }


def test_the_audit_has_no_write():
    """The server writes the trail. An SDK that offered a write would let a caller forge evidence."""
    assert not [m for m in dir(Audit) if m in ("put", "write", "post", "record", "append")]


def test_request_narrows_on_the_client_because_cloud_s_filter_cannot():
    """Every row carries `requestId`; the filter declares no such field.

    Until it does, the join is a scan. `total` still reports what the server
    counted for the filter the server applied.
    """
    other = dict(ROW, seq=42, requestId="req_9")
    calls = Calls(ok({"data": [ROW, other], "total": 2}))
    page = Audit(calls).list(Filter(request="req_1"))

    assert "requestId" not in calls.asked_once.query
    assert [e.seq for e in page.items] == [41]
    assert page.total == 2


def test_all_walks_pages_until_the_server_s_own_count_is_reached():
    calls = Calls(
        ok({"data": [ROW, ROW], "total": 3}),
        ok({"data": [ROW], "total": 3}),
    )
    assert len(list(Audit(calls).all(Filter(size=2)))) == 3
    assert [a.query["p"] for a in calls.asked] == [1, 2]


def test_all_keeps_walking_past_a_page_where_nothing_matched():
    """A page whose rows all failed a client-side narrowing is not the end of the trail.

    The count that decides is the server's, not the narrowed one. Deciding on
    the narrowed count would stop the walk at the first page of misses.
    """
    miss = dict(ROW, requestId="req_9")
    calls = Calls(ok({"data": [miss], "total": 2}), ok({"data": [ROW], "total": 2}))

    assert [e.request for e in Audit(calls).all(Filter(request="req_1", size=1))] == ["req_1"]
    assert len(calls.asked) == 2


def test_all_stops_on_an_empty_page():
    calls = Calls(ok({"data": [ROW], "total": 0}), ok({"data": [], "total": 0}))
    assert len(list(Audit(calls).all())) == 1
    assert len(calls.asked) == 2


# --------------------------------------------------------------------------
# search — one result set, and degradation stated rather than implied
# --------------------------------------------------------------------------

FUSION = {
    "status": "partial",
    "mode": "hybrid",
    "took_ms": 214,
    "hits": [
        {
            "id": "q3-postmortem",
            "corpus": "kb",
            "doctype": "kb.page",
            "title": "Q3 incident postmortem",
            "url": "/kb/q3-postmortem",
            "project": "ops",
            "score": 0.0312,
            "matched": [{"backend": "index", "rank": 1, "score": 0.0}, {"backend": "vector", "rank": 3, "score": 0.81}],
        }
    ],
    "backends": [
        {"name": "index", "status": "ok", "hits": 12, "took_ms": 40},
        {"name": "vector", "status": "degraded", "hits": 0, "took_ms": 174, "error": "qdrant: connection refused"},
    ],
}


def test_find_asks_in_retrieval_words_and_addresses_the_doctypes():
    calls = Calls(ok(FUSION))
    Search(calls).find("q3 incident postmortems", mode="hybrid", kinds=["page", "memory"], limit=10, project="ops")

    assert calls.asked_once.method == "POST"
    assert calls.asked_once.path == "/v1/search"
    assert calls.asked_once.body == {
        "query": "q3 incident postmortems",
        "mode": "hybrid",
        "project": "ops",
        "doctypes": ["kb.page", "kb.memory"],
        "index": None,
        "limit": 10,
        "offset": None,
    }


def test_a_leg_that_is_down_is_a_field_not_an_exception():
    """A caller that ignores `partial` reads a truncated corpus as a complete one."""
    a = Search(Calls(ok(FUSION))).find("q3")
    hits = a.value

    assert isinstance(a, Ok)
    assert hits.status == "partial"
    assert hits.partial is True
    assert hits.took == timedelta(milliseconds=214)
    assert [(b.name, b.status, b.error) for b in hits.backends] == [
        ("index", "ok", ""),
        ("vector", "degraded", "qdrant: connection refused"),
    ]


def test_a_hit_keeps_each_leg_s_own_score_out_of_the_ranking():
    hit = Search(Calls(ok(FUSION))).find("q3").value.items[0]

    assert hit.kind == "page", "`kind` is the same word kb uses; the address is cloud's"
    assert hit.score == pytest.approx(0.0312)
    assert [(m.backend, m.rank) for m in hit.matched] == [("index", 1), ("vector", 3)]
    assert hit.matched[1].score == pytest.approx(0.81), "the leg's native score, reported and never ranked on"


def test_a_search_refused_on_money_comes_back_as_an_arm_carrying_the_way_out():
    """The rerank leg runs through the metered AI gateway, so search can be refused."""
    a = Search(Calls(REFUSED)).find("q3")

    assert isinstance(a, Denied)
    assert a.denied.code == "insufficient_balance"
    assert [(c.kind, c.url) for c in a.cures] == [("credit", "/v1/billing")]
    assert a.request == "req_2"
    with pytest.raises(Denied):
        _ = a.value


# --------------------------------------------------------------------------
# kb — one capability over cloud's two apps and three doctypes
# --------------------------------------------------------------------------


def test_a_page_is_written_by_slug_and_a_named_document_is_replaced():
    calls = Calls(ok({"name": "runbook", "title": "Runbook", "body": "restart it", "project": "ops"}))
    a = Kb(calls).put(Doc(kind="page", name="runbook", title="Runbook", body="restart it", project="ops"))

    assert calls.asked_once.method == "PUT"
    assert calls.asked_once.path == "/v1/framework/kb.page/runbook"
    assert calls.asked_once.body == {"title": "Runbook", "body": "restart it", "project": "ops", "slug": "runbook"}
    assert a.value == Doc(kind="page", name="runbook", title="Runbook", body="restart it", project="ops")


def test_a_document_with_no_name_is_created_and_cloud_names_it():
    calls = Calls(Reply(status=201, body={"name": "a3f9", "title": "What we decided", "content": "gold tier"}))
    a = Kb(calls).put(Doc(kind="memory", title="What we decided", body="gold tier"))

    assert calls.asked_once.method == "POST"
    assert calls.asked_once.path == "/v1/framework/kb.memory"
    assert a.value.name == "a3f9"


def test_a_memory_keeps_its_text_where_the_doctype_keeps_it():
    """`page` and `source` call it `body`; `memory` calls it `content`.

    One `Doc.body` covers all three, and the mapping happens once.
    """
    calls = Calls(ok({"name": "a3f9", "content": "gold tier"}))
    assert Kb(calls).put(Doc(kind="memory", body="gold tier")).value.body == "gold tier"
    assert calls.asked_once.body["content"] == "gold tier"
    assert "body" not in calls.asked_once.body


def test_a_kind_that_is_not_one_of_the_three_is_refused_before_a_request():
    with pytest.raises(ValueError) as caught:
        Kb(Calls()).get("wiki", "runbook")
    assert "page, memory, source" in str(caught.value)


def test_list_narrows_by_project_through_the_framework_s_own_filter():
    calls = Calls(ok({"data": [{"name": "runbook", "title": "Runbook", "body": "x", "project": "ops"}]}))
    page = Kb(calls).list("page", project="ops", limit=50)

    assert calls.asked_once.query == {"filters": '{"project": "ops"}', "limit": 50}
    assert page.total == 1, "the document list reports no total of its own; an invented one would be a lie"
    assert page.items[0].kind == "page"


def test_a_connector_is_read_in_full_and_connect_only_answers_where_to_send_a_person():
    calls = Calls(
        ok(
            {
                "connectors": [
                    {
                        "provider": "github",
                        "kind": "code",
                        "status": "connected",
                        "account": "hanzoai",
                        "configured": True,
                        "docCount": 812,
                        "lastSync": "2026-09-10T06:00:00Z",
                    }
                ]
            }
        ),
        ok({"authorizeUrl": "https://github.com/login/oauth/authorize?..."}),
    )
    kb = Kb(calls)
    (connector,) = kb.connectors()
    assert connector.docs == 812
    assert connector.synced == datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc)

    assert kb.connect("github") == Link(url="https://github.com/login/oauth/authorize?...")


def test_a_sync_and_a_reindex_answer_what_they_moved():
    assert Kb(Calls(ok({"provider": "slack", "ingested": 44}))).sync("slack").value == Sync("slack", 44)
    assert Kb(Calls(ok({"lexical": 900, "vectors": 900, "removed": 3, "failed": 0}))).reindex().value == Reindex(
        900, 900, 3, 0
    )


def test_an_import_sends_the_export_verbatim_with_the_normalizer_named():
    calls = Calls(ok({"imported": 412}))
    a = Kb(calls).import_(b"PK\x03\x04vault", format="obsidian", project="ops")

    assert calls.asked_once.query == {"format": "obsidian", "project": "ops"}
    assert calls.asked_once.body == b"PK\x03\x04vault"
    assert calls.asked_once.media == "application/octet-stream"
    assert a.value.imported == 412


def test_the_corpus_map_states_its_own_incompleteness():
    links = Kb(
        Calls(
            ok(
                {
                    "nodes": [{"id": "kb.page/runbook", "name": "runbook", "title": "Runbook", "type": "kb.page"}],
                    "edges": [{"from": "kb.page/runbook", "to": "kb.page/ops", "kind": "parent"}],
                    "degraded": True,
                }
            )
        )
    ).links()

    assert links.partial is True
    assert links.nodes[0].name == "runbook"
    assert (links.edges[0].from_, links.edges[0].to, links.edges[0].kind) == (
        "kb.page/runbook",
        "kb.page/ops",
        "parent",
    )


def test_a_drop_answers_an_arm_with_nothing_in_it():
    a = Kb(Calls(Reply(status=204, body=None, request="req_4"))).drop("page", "runbook")
    assert a.value is None
    assert a.request == "req_4"


# --------------------------------------------------------------------------
# graph — assertions with provenance and time
# --------------------------------------------------------------------------

WHEN = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def test_an_assertion_carries_its_provenance_and_its_two_instants():
    calls = Calls(ok({"recorded": 1, "duplicate": 0, "refused": 0, "reasons": []}))
    facts = [
        Fact(
            entity="acme",
            relation="tier",
            value="gold",
            at=WHEN,
            seen=WHEN,
            source="crm",
            evidence="contract-2026-09",
            confidence=0.9,
        )
    ]
    a = Graph(calls).assert_(facts)

    assert calls.asked_once.path == "/v1/graph"
    assert calls.asked_once.body == {
        "assertions": [
            {
                "entity": "acme",
                "relation": "tier",
                "value": "gold",
                "names": False,
                "at": "2026-09-10T12:00:00Z",
                "seen": "2026-09-10T12:00:00Z",
                "source": "crm",
                "evidence": "contract-2026-09",
                "confidence": 0.9,
            }
        ]
    }
    assert a.value.recorded == 1


def test_each_member_is_judged_on_its_own():
    """One malformed fact does not discard the batch, and the reasons say which."""
    calls = Calls(ok({"recorded": 1, "duplicate": 1, "refused": 1, "reasons": ["relation is empty"]}))
    wrote = Graph(calls).assert_([Fact(entity="a"), Fact(entity="b"), Fact(entity="c")]).value

    assert (wrote.recorded, wrote.duplicate, wrote.refused) == (1, 1, 1)
    assert wrote.reasons == ("relation is empty",)


def test_a_batch_that_does_not_add_up_is_a_fault_not_an_answer():
    """Three counts that miss the batch size mean the answer is about a different set of facts."""
    calls = Calls(ok({"recorded": 1, "duplicate": 0, "refused": 0}))
    with pytest.raises(Exception) as caught:
        Graph(calls).assert_([Fact(entity="a"), Fact(entity="b")])
    assert "2 assertions sent, 1 accounted for" in str(caught.value)


def test_a_held_graph_write_names_the_clause_a_person_has_to_clear():
    a = Graph(Calls(HELD)).assert_([Fact(entity="acme")])

    assert isinstance(a, Held)
    assert (a.id, a.clause) == ("apr_7f3", "graph.assert")
    with pytest.raises(Held):
        _ = a.value


def test_read_takes_the_key_and_withholds_nothing():
    calls = Calls(
        ok(
            {
                "assertions": [
                    {"entity": "acme", "relation": "tier", "value": "silver", "at": "2026-01-01T00:00:00Z"},
                    {"entity": "acme", "relation": "tier", "value": "gold", "at": "2026-09-10T12:00:00Z"},
                ]
            }
        )
    )
    facts = Graph(calls).read(entity="acme", relation="tier", at=WHEN, limit=50)

    assert calls.asked_once.method == "GET"
    assert calls.asked_once.query == {
        "entity": "acme",
        "relation": "tier",
        "as_of": "2026-09-10T12:00:00Z",
        "limit": 50,
    }
    assert [f.value for f in facts] == ["silver", "gold"], "a superseded claim and its successor both appear"


def test_find_reads_the_same_corpus_by_text():
    calls = Calls(ok({"assertions": [{"entity": "acme", "relation": "tier", "value": "gold"}]}))
    Graph(calls).find("gold tier", relation="tier", limit=5)
    assert calls.asked_once.path == "/v1/graph/search"
    assert calls.asked_once.query == {"q": "gold tier", "relation": "tier", "limit": 5}


def test_resolve_answers_which_claim_wins_and_whether_it_is_contested():
    calls = Calls(
        ok(
            {
                "entity": "acme",
                "relation": "tier",
                "as_of": "2026-09-10T12:00:00Z",
                "known": True,
                "winner": {"entity": "acme", "relation": "tier", "value": "gold", "source": "crm"},
                "conflicts": [{"entity": "acme", "relation": "tier", "value": "silver", "source": "billing"}],
                "contested": True,
            }
        )
    )
    resolution = Graph(calls).resolve("acme", "tier", WHEN)

    assert calls.asked_once.body == {"entity": "acme", "relation": "tier", "as_of": "2026-09-10T12:00:00Z"}
    assert resolution.known is True
    assert resolution.winner.value == "gold"
    assert resolution.contested is True
    assert resolution.conflicts[0].source == "billing"


def test_an_entity_nobody_has_asserted_is_an_answer_not_an_error():
    resolution = Graph(Calls(ok({"entity": "ghost", "relation": "tier", "known": False}))).resolve("ghost", "tier")
    assert resolution.known is False
    assert resolution.winner is None


def test_a_walk_follows_edges_in_the_direction_it_was_given():
    calls = Calls(ok({"entities": ["acme", "acme-eu"], "depth": 2, "bound": 1000, "truncated": False}))
    walk = Graph(calls).walk(["acme"], relation="owns", direction="both", depth=2)

    assert calls.asked_once.body == {
        "seeds": ["acme"],
        "relation": "owns",
        "direction": "both",
        "depth": 2,
    }, "an instant nobody set is left off the body, not sent as an empty timestamp"
    assert walk.entities == ("acme", "acme-eu")


def test_extract_reads_what_a_document_states_without_recording_it():
    calls = Calls(
        ok({"triples": [{"subject": "acme", "predicate": "tier", "object": "gold", "names": False, "section": 2}]})
    )
    (triple,) = Graph(calls).extract("Acme is on the gold tier.", source="crm-note", subject="acme", at=WHEN)

    assert calls.asked_once.path == "/v1/graph/extract"
    assert calls.asked_once.body == {
        "text": "Acme is on the gold tier.",
        "source": "crm-note",
        "subject": "acme",
        "at": "2026-09-10T12:00:00Z",
    }
    assert (triple.subject, triple.predicate, triple.object, triple.section) == ("acme", "tier", "gold", 2)


def test_ingest_extracts_and_records_in_one_call():
    calls = Calls(ok({"recorded": 3, "duplicate": 0, "refused": 0}))
    a = Graph(calls).ingest("Acme is on the gold tier.", source="crm-note")

    assert calls.asked_once.path == "/v1/graph/ingest"
    assert a.value.recorded == 3


def test_the_vocabulary_says_what_decides_a_conflict():
    vocabulary = Graph(
        Calls(ok({"relations": ["tier", "owns"], "rule": ["at", "confidence"], "bound": 1000}))
    ).vocabulary()
    assert vocabulary.relations == ("tier", "owns")
    assert vocabulary.rule == ("at", "confidence")


# --------------------------------------------------------------------------
# what the six share
# --------------------------------------------------------------------------


def test_no_method_takes_an_org():
    """The tenant is the validated principal, everywhere.

    A method that took an org would be a cross-tenant read the caller asserted
    for itself.
    """
    import inspect

    for capability in (Budget, Policy, Audit, Search, Kb, Graph):
        for name, method in inspect.getmembers(capability, inspect.isfunction):
            if name.startswith("_"):
                continue
            assert "org" not in inspect.signature(method).parameters, "{0}.{1}".format(capability.__name__, name)


def test_the_six_are_written_over_the_wire_and_not_over_the_generated_client():
    """Importing a capability must not drag 2,700 generated modules in behind it."""
    import sys
    import subprocess

    proof = subprocess.run(
        [
            sys.executable,
            "-c",
            "import hanzoai.budget, hanzoai.policy, hanzoai.audit, hanzoai.search, hanzoai.kb, hanzoai.graph, sys;"
            "print('hanzoai.cloud' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proof.stdout.strip() == "False", proof.stderr
