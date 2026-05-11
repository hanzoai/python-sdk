"""Cross-runtime parity tests for the algorithm port.

Mirrors `packages/memory/parity.test.ts` in @hanzo/bot-memory. Any algorithm
that's in both ports MUST produce the same outputs on identical inputs (modulo
floating-point noise for cosine-based code).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hanzo_memory.algorithms import (
    CaptionSegment,
    CircuitBreaker,
    CircuitOpenError,
    MmrInput,
    QueryEval,
    RuntimeConfig,
    SearchHit,
    WeightedEdge,
    bbox_around,
    characterize,
    cjk_bigrams,
    classify_link_rule,
    coarse_dim,
    content_range,
    cosine,
    decode_address,
    dedup_hits,
    detect_doc_type,
    detect_script,
    emoji_trigrams,
    encode_address,
    estimate_tokens,
    format_slug,
    get_doc_type,
    get_embedding_model,
    haversine_km,
    in_box,
    l2_normalize,
    list_doc_types,
    louvain,
    mean_reciprocal_rank,
    mmr_rerank,
    mrl_truncate,
    ndcg_at_k,
    normalize_edges,
    parse_range,
    parse_slug,
    parse_websearch,
    pfnet_infinity,
    precision_at_k,
    prefix_for,
    range_bounds,
    recall_at_k,
    reciprocal_rank,
    render_rttm,
    render_srt,
    render_vtt,
    retry,
    rrf_fuse,
    rsf_fuse,
    select_rrf_k,
    select_weights,
    snn_score,
    to_fts5_match,
    truncate_to_tokens,
    v7_ceiling,
    v7_floor,
)


def hit(slug: str, score: float) -> SearchHit:
    return SearchHit(slug=slug, score=score, excerpt=slug, source="keyword")


# ── Fusion ────────────────────────────────────────────────────────────


def test_rrf_normalizes_top_to_one():
    r = rrf_fuse([[hit("a", 1), hit("b", 0.5)]], 10)
    assert r[0].slug == "a"
    assert abs(r[0].score - 1.0) < 0.01


def test_rrf_rewards_multi_list_consensus():
    r = rrf_fuse([[hit("a", 1)], [hit("a", 1), hit("b", 0.5)]], 10)
    assert r[0].slug == "a"


def test_rsf_preserves_magnitude():
    r = rsf_fuse([[hit("a", 100), hit("b", 50)], [hit("a", 1), hit("c", 0.5)]], 10)
    assert r[0].slug == "a"
    assert len(r) == 3


def test_query_characterize_and_select():
    assert select_rrf_k(characterize('"hello world"')) == 10
    assert select_rrf_k(characterize("foo AND bar")) == 15
    assert select_rrf_k(characterize("rust")) == 15
    assert select_rrf_k(characterize("a b c d e f g h i j")) == 40


def test_select_weights_lean_short_to_fts():
    sw = select_weights(characterize("rust"))
    assert sw["fts"] > sw["semantic"]
    lw = select_weights(characterize("how do retrieval augmented generation systems typically work in production scale"))
    assert lw["semantic"] > lw["fts"]


# ── Rerank ────────────────────────────────────────────────────────────


def test_cosine_basic():
    assert abs(cosine([1, 0], [1, 0]) - 1) < 1e-6
    assert abs(cosine([1, 0], [0, 1])) < 1e-6


def test_mmr_picks_diverse_second():
    hits = [
        MmrInput(slug="a", score=0.9, embedding=[1, 0]),
        MmrInput(slug="b", score=0.85, embedding=[1, 0.01]),
        MmrInput(slug="c", score=0.6, embedding=[0, 1]),
    ]
    out = mmr_rerank(hits, lambda_=0.2, limit=2)
    assert out[0].slug == "a"
    assert out[1].slug == "c"


# ── Dedup ─────────────────────────────────────────────────────────────


def test_dedup_keeps_best_chunk():
    out = dedup_hits([
        hit("page/foo#chunk-0", 0.5),
        hit("page/foo#chunk-1", 0.8),
        hit("page/bar", 0.6),
    ])
    slugs = sorted([h.slug for h in out])
    assert slugs == ["page/bar", "page/foo#chunk-1"]


# ── Script / FTS ──────────────────────────────────────────────────────


def test_detect_script_cjk_and_emoji():
    assert detect_script("こんにちは世界")["primary"] == "cjk"
    assert detect_script("Hello world")["primary"] == "latin"
    assert detect_script("Привет")["primary"] == "cyrillic"


def test_cjk_bigrams_round_trip():
    out = cjk_bigrams("hello 世界 こんにちは")
    assert "hello" in out
    assert "世界" in out
    assert "こん" in out


def test_emoji_trigrams_emit():
    out = emoji_trigrams("hi 🚀🌌🌟")
    assert len(out) > 0


def test_parse_websearch():
    p = parse_websearch('"hello world" foo OR bar -baz qux')
    assert p["phrases"] == ["hello world"]
    assert p["optional"][0] == ["foo", "bar"]
    assert p["excluded"] == ["baz"]
    assert "qux" in p["required"]


def test_to_fts5_match():
    sql = to_fts5_match(parse_websearch("apple OR orange -spoil"))
    assert "apple OR orange" in sql
    assert "NOT spoil" in sql


# ── Embed / MRL ───────────────────────────────────────────────────────


def test_embed_registry_known_models():
    assert get_embedding_model("ollama:nomic-embed-text").dim == 768
    assert get_embedding_model("openai:text-embedding-3-small").dim == 1536


def test_prefix_for_e5_vs_nomic():
    e5 = get_embedding_model("intfloat/e5-large-v2")
    nomic = get_embedding_model("ollama:nomic-embed-text")
    assert prefix_for(e5, "query", "x") == "query: x"
    assert prefix_for(e5, "passage", "x") == "passage: x"
    assert prefix_for(nomic, "query", "x") == "x"


def test_mrl_truncate_and_normalize():
    v = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    t = mrl_truncate(v, 4)
    assert len(t) == 4
    norm = sum(x * x for x in t) ** 0.5
    assert abs(norm - 1) < 1e-6


def test_coarse_dim_one_eighth():
    e3 = get_embedding_model("openai:text-embedding-3-large")
    cd = coarse_dim(e3)
    assert 256 <= cd <= 512


def test_l2_normalize_zero():
    assert l2_normalize([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


# ── Temporal ──────────────────────────────────────────────────────────


def test_v7_bounds_order():
    t = int(__import__("time").time() * 1000)
    assert v7_floor(t) < v7_ceiling(t)


def test_range_bounds():
    r = range_bounds("2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z")
    assert r["floor"] < r["ceiling"]


# ── Captions ──────────────────────────────────────────────────────────


def test_caption_rendering():
    segs = [
        CaptionSegment(start_secs=0, end_secs=1.5, text="hi", speaker="S0"),
        CaptionSegment(start_secs=1.5, end_secs=3, text="world", speaker="S1"),
    ]
    assert render_vtt(segs).startswith("WEBVTT")
    assert "00:00:00,000 --> 00:00:01,500" in render_srt(segs)
    assert render_rttm(segs).startswith("SPEAKER")


# ── Tokenizer ─────────────────────────────────────────────────────────


def test_estimate_tokens_grows():
    assert estimate_tokens("hi there friend") > estimate_tokens("hi")


def test_estimate_cjk_one_per_char():
    assert estimate_tokens("こんにちは") == 5


def test_truncate_within_budget():
    long = "alpha " * 100
    t = truncate_to_tokens(long, 20)
    assert estimate_tokens(t) <= 20


# ── Eval ──────────────────────────────────────────────────────────────


def _q():
    return QueryEval(predicted=["a", "b", "c", "d"], relevant=["c", "d"])


def test_reciprocal_rank():
    assert abs(reciprocal_rank(_q()) - 1 / 3) < 1e-6


def test_recall_grows_with_k():
    q = _q()
    assert recall_at_k(q, 2) == 0
    assert recall_at_k(q, 4) == 1


def test_precision_at_k():
    assert abs(precision_at_k(_q(), 4) - 0.5) < 1e-6


def test_ndcg_graded():
    graded = QueryEval(predicted=["a", "b"], relevant={"a": 3, "b": 1})
    assert ndcg_at_k(graded, 2) > 0.9


def test_mrr():
    assert mean_reciprocal_rank([_q()]) > 0


# ── Spatial / Range ───────────────────────────────────────────────────


def test_haversine_zero():
    assert abs(haversine_km((0, 0), (0, 0))) < 1e-6


def test_haversine_nyc_la():
    d = haversine_km((40.7128, -74.006), (34.0522, -118.2437))
    assert abs(d - 3935) < 50


def test_bbox_around_round_trip():
    center = (37.77, -122.42)
    box = bbox_around(center, 10)
    assert in_box(center, box)


def test_parse_range_closed():
    assert parse_range("bytes=0-99", 1000) == (0, 99)


def test_parse_range_suffix():
    assert parse_range("bytes=-100", 1000) == (900, 999)


def test_parse_range_unsatisfiable():
    assert parse_range("bytes=2000-3000", 1000) == "unsatisfiable"


def test_content_range_fmt():
    assert content_range(0, 99, 1000) == "bytes 0-99/1000"


# ── Address ───────────────────────────────────────────────────────────


def test_address_round_trip():
    pk = bytes(range(32))
    addr = encode_address(pk)
    assert addr.startswith("hanzo:")
    out = decode_address(addr)
    assert out["prefix"] == "hanzo"
    assert out["version"] == 1


def test_address_bad_checksum():
    with pytest.raises(ValueError):
        decode_address("hanzo:11111111111111111111111111")


def test_address_mm_prefix():
    pk = bytes([1] + [0] * 31)
    addr = encode_address(pk, prefix="mm")
    assert addr.startswith("mm:")


# ── Graph maintenance ─────────────────────────────────────────────────


def test_normalize_edges():
    out = normalize_edges([WeightedEdge("a", "b", 10), WeightedEdge("b", "c", 5)])
    assert abs(out[0].weight - 1) < 1e-6
    assert abs(out[1].weight - 0) < 1e-6


def test_snn_score_bounds():
    edges = [WeightedEdge("a", "b", 0.9), WeightedEdge("a", "c", 0.8), WeightedEdge("b", "c", 0.7)]
    for e in snn_score(edges, 2):
        assert 0 <= e.weight <= 1


def test_pfnet_drops_dominated():
    out = pfnet_infinity([
        WeightedEdge("a", "b", 0.9),
        WeightedEdge("b", "c", 0.9),
        WeightedEdge("a", "c", 0.5),
    ])
    assert not any(e.source == "a" and e.target == "c" for e in out)


def test_louvain_returns_mapping():
    edges = [WeightedEdge("a", "b", 1), WeightedEdge("b", "c", 1), WeightedEdge("a", "c", 1)]
    out = louvain(edges)
    assert set(out.keys()) == {"a", "b", "c"}


# ── Doc types ─────────────────────────────────────────────────────────


def test_detect_doc_type_meeting():
    dt = detect_doc_type(filename="meeting-2026-05-11.md", body="Attendees:\nAction Items:")
    assert dt.slug == "meeting/notes"


def test_detect_doc_type_code():
    assert detect_doc_type(filename="main.rs").slug == "code/source"


def test_doc_types_listed():
    types = list_doc_types()
    assert len(types) >= 10
    assert get_doc_type("note/plain") is not None


# ── Circuit breaker / retry ───────────────────────────────────────────


def test_circuit_breaker_opens():
    cb = CircuitBreaker(failure_threshold=2, cooldown_ms=100)
    fail = lambda: (_ for _ in ()).throw(RuntimeError("x"))
    with pytest.raises(RuntimeError):
        cb.run(fail)
    with pytest.raises(RuntimeError):
        cb.run(fail)
    assert cb.state() == "open"
    with pytest.raises(CircuitOpenError):
        cb.run(fail)


def test_retry_success_after_transient():
    state = {"n": 0}

    def f():
        state["n"] += 1
        if state["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    assert retry(f, attempts=5, base_ms=1, sleep_fn=lambda _s: None) == "ok"
    assert state["n"] == 3


# ── Inference / slug / runtime config ─────────────────────────────────


def test_parse_slug_explicit():
    assert parse_slug("openai:gpt-4o") == {"provider": "openai", "model": "gpt-4o"}


def test_parse_slug_implicit():
    assert parse_slug("qwen3:8b") == {"provider": "ollama", "model": "qwen3:8b"}


def test_format_slug_round_trip():
    assert format_slug({"provider": "openai", "model": "gpt-4o"}) == "openai:gpt-4o"


def test_runtime_config_precedence():
    rc = RuntimeConfig(defaults={"K": "default"}, env={"K": "env"})
    assert rc.get("K") == "env"
    rc.set("K", "override")
    assert rc.get("K") == "override"
    assert rc.source("K") == "db_override"
    rc.clear("K")
    assert rc.get("K") == "env"


# ── Link types ────────────────────────────────────────────────────────


def test_classify_link_rule():
    assert classify_link_rule("Alice founded Acme") == "founded"
    assert classify_link_rule("Alice invested in Acme") == "invested_in"
    assert classify_link_rule("worked together") == "mentions"
