"""Tests for hanzo_memory.graph_links — mirror of @hanzo/bot-graph-links TS suite."""

from hanzo_memory.graph_links import Edge, extract_edges, reconcile, slugify


# ── slugify ─────────────────────────────────────────────────────────


def test_slugify_lowercases_dashes_ascii() -> None:
    assert slugify("Acme AI Inc.") == "acme-ai-inc"
    assert slugify("José's Pizza") == "jose-s-pizza"
    assert slugify("Slack & Discord") == "slack-and-discord"


# ── extract_edges ───────────────────────────────────────────────────


def _has(edges: list[Edge], **fields: object) -> bool:
    return any(all(getattr(e, k) == v for k, v in fields.items()) for e in edges)


def test_mentions_from_md_links() -> None:
    edges = extract_edges("originals/idea-1", "Inspired by [Alice](people/alice) at Acme.")
    assert _has(edges, target="people/alice", type="mentions")


def test_meeting_emits_attended_not_mentions() -> None:
    edges = extract_edges(
        "meetings/2026-05-10",
        "Met with [Bob](people/bob) and [Carol](people/carol).",
        page_type="meeting",
    )
    types = {e.type for e in edges}
    assert "attended" in types
    assert "mentions" not in types


def test_founded_inference() -> None:
    edges = extract_edges("people/alice", "Alice co-founded Acme AI. She also runs Beta Co.")
    assert _has(edges, type="founded", target="companies/acme-ai")


def test_invested_in_inference() -> None:
    e1 = extract_edges("people/dan", "Dan invested in Foobar.")
    assert _has(e1, type="invested_in", target="companies/foobar")

    e2 = extract_edges("people/erin", "Erin led Quux's seed round.")
    assert _has(e2, type="invested_in", target="companies/quux")


def test_advises_inference() -> None:
    edges = extract_edges("people/frank", "Frank is an advisor to Globex.")
    assert _has(edges, type="advises", target="people/globex")


def test_works_at_inference() -> None:
    e1 = extract_edges("people/grace", "Grace is the CEO of Acme.")
    assert _has(e1, type="works_at", target="companies/acme")

    e2 = extract_edges("people/henry", "Henry joined Initech in 2024.")
    assert _has(e2, type="works_at", target="companies/initech")


def test_strip_code_fences() -> None:
    edges = extract_edges(
        "concepts/snippet",
        "Normal: [link](people/real). Code:\n```\nfake = [should](people/fake)\n```\n",
    )
    targets = {e.target for e in edges}
    assert "people/real" in targets
    assert "people/fake" not in targets


def test_dedup_same_target_same_type() -> None:
    edges = extract_edges("originals/x", "[Alice](people/alice) and again [Alice](people/alice).")
    alice = [e for e in edges if e.target == "people/alice" and e.type == "mentions"]
    assert len(alice) == 1


def test_bare_slug_refs() -> None:
    edges = extract_edges("concepts/note", "See people/alice and companies/acme-ai.")
    targets = {e.target for e in edges}
    assert "people/alice" in targets
    assert "companies/acme-ai" in targets


# ── reconcile ───────────────────────────────────────────────────────


def test_reconcile_add_remove() -> None:
    prior = [Edge("a", "x", "mentions"), Edge("a", "y", "mentions")]
    next_ = [Edge("a", "y", "mentions"), Edge("a", "z", "mentions")]
    add, remove = reconcile(prior, next_)
    assert [e.target for e in add] == ["z"]
    assert [e.target for e in remove] == ["x"]


def test_reconcile_no_change() -> None:
    same = [Edge("a", "x", "mentions")]
    add, remove = reconcile(same, same)
    assert add == [] and remove == []


# ── recipes ─────────────────────────────────────────────────────────


def test_recipes_list_and_load() -> None:
    from hanzo_memory.recipes import list_recipes, load_recipe

    names = list_recipes()
    assert "email" in names

    email = load_recipe("email")
    assert email["recipe"] == "email"
    assert email["version"] == 1
    assert email["cron"].startswith("*/30")
