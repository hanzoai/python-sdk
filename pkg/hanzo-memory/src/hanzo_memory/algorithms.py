"""Hanzo Brain pure-CPU algorithms — Python port.

Mirrors the TypeScript canonical surface in `@hanzo/bot-memory`:

  - Fusion: RRF, RSF, adaptive RRF k, adaptive weights
  - Rerank: MMR
  - Dedup: chunk-aware deduplication
  - Script: Unicode script detection
  - Embed: model registry + Matryoshka truncation
  - Temporal: UUIDv7 floor/ceiling + named ranges
  - Captions: WebVTT / SRT / RTTM
  - FTS: CJK bigrams + emoji trigrams + websearch_to_tsquery
  - Tokenizer: BPE estimator
  - Eval: MRR / recall / precision / NDCG
  - Spatial: haversine + bbox
  - Range: HTTP Range header
  - Address: wallet-style content-addressable id
  - Captions: VTT/SRT/RTTM

Mirrors the algorithm surface in `hanzoai/brain` (Go) and `@hanzo/bot-memory` (TS).
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable

# ── Fusion ────────────────────────────────────────────────────────────

RRF_K_DEFAULT = 20


@dataclass
class SearchHit:
    slug: str
    score: float
    excerpt: str = ""
    source: str = "keyword"


def rrf_fuse(lists: list[list[SearchHit]], limit: int, k: float = RRF_K_DEFAULT) -> list[SearchHit]:
    scores: dict[str, float] = {}
    meta: dict[str, SearchHit] = {}
    num = len(lists)
    for lst in lists:
        for rank, hit in enumerate(lst):
            scores[hit.slug] = scores.get(hit.slug, 0.0) + 1.0 / (k + rank + 1)
            meta.setdefault(hit.slug, hit)
    if not scores:
        return []
    max_possible = num / (k + 1)
    out: list[SearchHit] = []
    for slug, s in scores.items():
        m = meta[slug]
        out.append(SearchHit(slug=slug, score=min(s / max_possible, 1.0) if max_possible > 0 else 0.0, excerpt=m.excerpt, source="fused"))
    out.sort(key=lambda h: h.score, reverse=True)
    return out[:limit]


def rsf_fuse(lists: list[list[SearchHit]], limit: int, weights: list[float] | None = None) -> list[SearchHit]:
    n = len(lists)
    w = weights if weights is not None else [1 / n if n else 0] * n
    if len(w) != n:
        raise ValueError("rsf_fuse: weights length must match lists length")
    scores: dict[str, float] = {}
    meta: dict[str, SearchHit] = {}
    for i, lst in enumerate(lists):
        if not lst:
            continue
        lo = min(h.score for h in lst)
        hi = max(h.score for h in lst)
        span = hi - lo
        for h in lst:
            norm = (h.score - lo) / span if span > 0 else 1.0
            scores[h.slug] = scores.get(h.slug, 0.0) + w[i] * norm
            meta.setdefault(h.slug, h)
    out = [SearchHit(slug=s, score=v, excerpt=meta[s].excerpt, source="fused") for s, v in scores.items()]
    out.sort(key=lambda h: h.score, reverse=True)
    return out[:limit]


@dataclass
class QueryCharacteristics:
    token_count: int
    is_phrase: bool
    is_boolean: bool


def characterize(query: str) -> QueryCharacteristics:
    t = query.strip()
    is_phrase = bool(re.fullmatch(r'"[^"]+"|\'[^\']+\'', t))
    is_boolean = bool(re.search(r"\b(AND|OR|NOT)\b", t)) or bool(re.search(r"\s-\S", t))
    tokens = [tok for tok in re.split(r"\s+", t) if tok]
    return QueryCharacteristics(token_count=len(tokens), is_phrase=is_phrase, is_boolean=is_boolean)


def select_rrf_k(q: QueryCharacteristics) -> int:
    if q.is_phrase:
        return 10
    if q.is_boolean:
        return 15
    if q.token_count <= 2:
        return 15
    if q.token_count >= 10:
        return 40
    return RRF_K_DEFAULT


def select_weights(q: QueryCharacteristics) -> dict[str, float]:
    if q.is_phrase:
        return {"fts": 0.8, "semantic": 0.2}
    if q.is_boolean:
        return {"fts": 0.7, "semantic": 0.3}
    if q.token_count <= 2:
        return {"fts": 0.65, "semantic": 0.35}
    if q.token_count >= 10:
        return {"fts": 0.3, "semantic": 0.7}
    return {"fts": 0.5, "semantic": 0.5}


# ── Rerank (MMR) ──────────────────────────────────────────────────────


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na * nb > 0 else 0.0


@dataclass
class MmrInput(SearchHit):
    embedding: list[float] | None = None


def mmr_rerank(hits: list[MmrInput], lambda_: float = 0.5, limit: int | None = None) -> list[MmrInput]:
    limit = limit if limit is not None else len(hits)
    embedded = [h for h in hits if h.embedding]
    orphans = [h for h in hits if not h.embedding]
    selected: list[MmrInput] = []
    cands = list(embedded)
    while len(selected) < limit and cands:
        best_idx = -1
        best_score = -math.inf
        for i, c in enumerate(cands):
            rel = c.score
            max_sim = 0.0
            for s in selected:
                sim = cosine(c.embedding or [], s.embedding or [])
                if sim > max_sim:
                    max_sim = sim
            mmr = lambda_ * rel - (1 - lambda_) * max_sim
            if mmr > best_score:
                best_score = mmr
                best_idx = i
        if best_idx < 0:
            break
        selected.append(cands.pop(best_idx))
    for o in orphans:
        if len(selected) >= limit:
            break
        selected.append(o)
    return selected


# ── Dedup ─────────────────────────────────────────────────────────────


def dedup_hits(hits: list[SearchHit], per_chain: int = 1) -> list[SearchHit]:
    buckets: dict[str, list[SearchHit]] = {}
    for h in hits:
        chain = re.sub(r"(#chunk-\d+|::\d+)$", "", h.slug)
        buckets.setdefault(chain, []).append(h)
    out: list[SearchHit] = []
    for lst in buckets.values():
        lst.sort(key=lambda h: h.score, reverse=True)
        out.extend(lst[:per_chain])
    out.sort(key=lambda h: h.score, reverse=True)
    return out


# ── Script detection ──────────────────────────────────────────────────


def _is_cjk(cp: int) -> bool:
    return (
        0x4E00 <= cp <= 0x9FFF
        or 0x3400 <= cp <= 0x4DBF
        or 0x3040 <= cp <= 0x30FF
        or 0xAC00 <= cp <= 0xD7AF
    )


def _is_emoji(cp: int) -> bool:
    return 0x2600 <= cp <= 0x27BF or 0x1F300 <= cp <= 0x1FAFF


def has_cjk(text: str) -> bool:
    return any(_is_cjk(ord(c)) for c in text)


def has_emoji(text: str) -> bool:
    return any(_is_emoji(ord(c)) for c in text)


def detect_script(text: str) -> dict:
    counts: dict[str, int] = {k: 0 for k in [
        "latin", "cjk", "emoji", "cyrillic", "arabic", "hebrew", "greek", "devanagari", "other"
    ]}
    total = 0
    for ch in text:
        cp = ord(ch)
        if 0x0030 <= cp <= 0x0039:
            continue
        s = _classify(cp)
        if s is None:
            continue
        counts[s] += 1
        total += 1
    primary = max(counts.items(), key=lambda x: x[1])[0] if total > 0 else "other"
    fractions = {k: (v / total) if total > 0 else 0.0 for k, v in counts.items()}
    return {"primary": primary, "fractions": fractions, "has_cjk": counts["cjk"] > 0, "has_emoji": counts["emoji"] > 0}


def _classify(cp: int) -> str | None:
    if _is_cjk(cp):
        return "cjk"
    if _is_emoji(cp):
        return "emoji"
    if 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A:
        return "latin"
    if 0x00C0 <= cp <= 0x024F:
        return "latin"
    if 0x0370 <= cp <= 0x03FF:
        return "greek"
    if 0x0400 <= cp <= 0x04FF:
        return "cyrillic"
    if 0x0590 <= cp <= 0x05FF:
        return "hebrew"
    if 0x0600 <= cp <= 0x06FF:
        return "arabic"
    if 0x0900 <= cp <= 0x097F:
        return "devanagari"
    if cp <= 0x002F or 0x003A <= cp <= 0x0040 or 0x005B <= cp <= 0x0060 or 0x007B <= cp <= 0x007E:
        return None
    return "other"


# ── FTS helpers ───────────────────────────────────────────────────────


def cjk_bigrams(text: str) -> list[str]:
    out: list[str] = []
    cjk_buf = ""
    latin_buf = ""

    def flush_cjk() -> None:
        nonlocal cjk_buf
        if not cjk_buf:
            return
        if len(cjk_buf) == 1:
            out.append(cjk_buf)
        else:
            for i in range(len(cjk_buf) - 1):
                out.append(cjk_buf[i:i + 2])
        cjk_buf = ""

    def flush_latin() -> None:
        nonlocal latin_buf
        if latin_buf:
            out.append(latin_buf)
            latin_buf = ""

    for ch in text:
        if _is_cjk(ord(ch)):
            flush_latin()
            cjk_buf += ch
        elif ch.isspace():
            flush_cjk()
            flush_latin()
        else:
            flush_cjk()
            latin_buf += ch
    flush_cjk()
    flush_latin()
    return [t for t in out if t]


def emoji_trigrams(text: str) -> list[str]:
    chars = list(text)
    out: list[str] = []
    for i, ch in enumerate(chars):
        if not _is_emoji(ord(ch)):
            continue
        a = chars[i]
        b = chars[i + 1] if i + 1 < len(chars) else ""
        c = chars[i + 2] if i + 2 < len(chars) else ""
        out.append(a + b + c)
    return out


def parse_websearch(query: str) -> dict:
    required: list[str] = []
    excluded: list[str] = []
    optional: list[list[str]] = []
    phrases: list[str] = []

    tokens: list[tuple[str, str]] = []
    for m in re.finditer(r'"([^"]+)"|(\S+)', query):
        if m.group(1) is not None:
            tokens.append(("phrase", m.group(1)))
        else:
            tokens.append(("word", m.group(2)))

    i = 0
    while i < len(tokens):
        kind, val = tokens[i]
        if kind == "phrase":
            phrases.append(val)
            required.append(val)
            i += 1
            continue
        if i + 1 < len(tokens) and tokens[i + 1][0] == "word" and tokens[i + 1][1] == "OR":
            group = [val]
            j = i + 1
            while j + 1 < len(tokens) and tokens[j][1] == "OR" and tokens[j][0] == "word":
                group.append(tokens[j + 1][1])
                j += 2
            optional.append(group)
            i = j
            continue
        if val.startswith("-") and len(val) > 1:
            excluded.append(val[1:])
            i += 1
            continue
        required.append(val)
        i += 1
    return {"required": required, "excluded": excluded, "optional": optional, "phrases": phrases}


def to_fts5_match(parsed: dict) -> str:
    parts: list[str] = []
    for r in parsed["required"]:
        parts.append(_quote_fts5(r))
    for group in parsed["optional"]:
        parts.append("(" + " OR ".join(_quote_fts5(g) for g in group) + ")")
    s = " AND ".join(parts)
    for e in parsed["excluded"]:
        s += f" NOT {_quote_fts5(e)}"
    return s.strip()


def _quote_fts5(term: str) -> str:
    if " " in term or not re.fullmatch(r"[\wÀ-￿]+", term):
        return '"' + term.replace('"', '""') + '"'
    return term


# ── Embed registry + MRL ──────────────────────────────────────────────


@dataclass
class EmbeddingModel:
    slug: str
    dim: int
    mrl_dims: list[int] = field(default_factory=list)
    prefix_query: str | None = None
    prefix_passage: str | None = None
    family: str | None = None


_EMBED_REGISTRY: dict[str, EmbeddingModel] = {}


def register_embedding_model(m: EmbeddingModel) -> None:
    _EMBED_REGISTRY[m.slug] = m


def get_embedding_model(slug: str) -> EmbeddingModel | None:
    return _EMBED_REGISTRY.get(slug)


def list_embedding_models() -> list[EmbeddingModel]:
    return list(_EMBED_REGISTRY.values())


register_embedding_model(EmbeddingModel(slug="ollama:nomic-embed-text", dim=768, mrl_dims=[128, 256, 512, 768], family="nomic"))
register_embedding_model(EmbeddingModel(slug="intfloat/e5-large-v2", dim=1024, prefix_query="query: ", prefix_passage="passage: ", family="e5"))
register_embedding_model(EmbeddingModel(slug="openai:text-embedding-3-small", dim=1536, mrl_dims=[256, 512, 768, 1024, 1536], family="openai"))
register_embedding_model(EmbeddingModel(slug="openai:text-embedding-3-large", dim=3072, mrl_dims=[256, 512, 1024, 2048, 3072], family="openai"))


def prefix_for(model: EmbeddingModel, task: str, text: str) -> str:
    if task == "symmetric" or (model.prefix_query is None and model.prefix_passage is None):
        return text
    if task == "query":
        return (model.prefix_query or "") + text
    return (model.prefix_passage or "") + text


def l2_normalize(v: list[float]) -> list[float]:
    s = math.sqrt(sum(x * x for x in v))
    if s == 0:
        return v
    return [x / s for x in v]


def mrl_truncate(embedding: list[float], target_dim: int) -> list[float]:
    if target_dim <= 0:
        raise ValueError("target_dim must be positive")
    if target_dim >= len(embedding):
        return l2_normalize(list(embedding))
    return l2_normalize(embedding[:target_dim])


def coarse_dim(model: EmbeddingModel) -> int:
    if not model.mrl_dims:
        return model.dim
    target = model.dim / 8
    for d in model.mrl_dims:
        if d >= target:
            return d
    return model.mrl_dims[-1]


# ── Temporal (UUIDv7) ─────────────────────────────────────────────────


def v7_floor(epoch_ms: int) -> str:
    return _v7(epoch_ms, ceiling=False)


def v7_ceiling(epoch_ms: int) -> str:
    return _v7(epoch_ms, ceiling=True)


def _v7(epoch_ms: int, ceiling: bool) -> str:
    ts = max(0, int(epoch_ms))
    hex_ts = format(ts, "012x")[-12:]
    th = hex_ts[:8]
    tl = hex_ts[8:12]
    if ceiling:
        return f"{th}-{tl}-7fff-bfff-ffffffffffff"
    return f"{th}-{tl}-7000-8000-000000000000"


def range_bounds(from_iso: str | None = None, to_iso: str | None = None) -> dict:
    from_ms = int(datetime.fromisoformat(from_iso.replace("Z", "+00:00")).timestamp() * 1000) if from_iso else 0
    to_ms = int(datetime.fromisoformat(to_iso.replace("Z", "+00:00")).timestamp() * 1000) if to_iso else int(datetime.now(timezone.utc).timestamp() * 1000) + 86_400_000
    return {"floor": v7_floor(from_ms), "ceiling": v7_ceiling(to_ms)}


# ── Captions ──────────────────────────────────────────────────────────


@dataclass
class CaptionSegment:
    start_secs: float
    end_secs: float
    text: str
    speaker: str | None = None


def render_vtt(segs: list[CaptionSegment]) -> str:
    out = "WEBVTT\n\n"
    for i, s in enumerate(segs):
        out += f"{i + 1}\n"
        out += f"{_vtt_time(s.start_secs)} --> {_vtt_time(s.end_secs)}\n"
        if s.speaker:
            out += f"<v {s.speaker}>{s.text}</v>\n\n"
        else:
            out += f"{s.text}\n\n"
    return out


def render_srt(segs: list[CaptionSegment]) -> str:
    out = ""
    for i, s in enumerate(segs):
        out += f"{i + 1}\n"
        out += f"{_srt_time(s.start_secs)} --> {_srt_time(s.end_secs)}\n"
        if s.speaker:
            out += f"{s.speaker}: {s.text}\n\n"
        else:
            out += f"{s.text}\n\n"
    return out


def render_rttm(segs: list[CaptionSegment], uri: str = "audio") -> str:
    lines: list[str] = []
    for s in segs:
        if not s.speaker:
            continue
        dur = s.end_secs - s.start_secs
        lines.append(f"SPEAKER {uri} 1 {s.start_secs:.3f} {dur:.3f} <NA> <NA> {s.speaker} <NA> <NA>")
    return "\n".join(lines)


def _vtt_time(secs: float) -> str:
    return _fmt_time(secs, ms_sep=".")


def _srt_time(secs: float) -> str:
    return _fmt_time(secs, ms_sep=",")


def _fmt_time(secs: float, ms_sep: str) -> str:
    ms = int((secs - int(secs)) * 1000)
    total = int(secs)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}{ms_sep}{ms:03d}"


# ── Tokenizer ─────────────────────────────────────────────────────────


def estimate_tokens(text: str) -> int:
    total = 0
    ascii_run = ""

    def flush_ascii() -> None:
        nonlocal ascii_run, total
        if not ascii_run:
            return
        for w in ascii_run.split():
            total += max(1, math.ceil(len(w) / 4))
        ascii_run = ""

    for ch in text:
        cp = ord(ch)
        if _is_cjk(cp) or _is_emoji(cp):
            flush_ascii()
            total += 1
        else:
            ascii_run += ch
    flush_ascii()
    return total


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    if estimate_tokens(text) <= max_tokens:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if estimate_tokens(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo]


# ── Eval ──────────────────────────────────────────────────────────────


@dataclass
class QueryEval:
    predicted: list[str]
    relevant: list[str] | dict[str, int]


def _rel_set(q: QueryEval) -> set[str]:
    if isinstance(q.relevant, dict):
        return {k for k, v in q.relevant.items() if v > 0}
    return set(q.relevant)


def reciprocal_rank(q: QueryEval) -> float:
    rel = _rel_set(q)
    for i, p in enumerate(q.predicted):
        if p in rel:
            return 1.0 / (i + 1)
    return 0.0


def mean_reciprocal_rank(queries: list[QueryEval]) -> float:
    return sum(reciprocal_rank(q) for q in queries) / len(queries) if queries else 0.0


def recall_at_k(q: QueryEval, k: int) -> float:
    rel = _rel_set(q)
    if not rel:
        return 0.0
    head = q.predicted[:k]
    hits = sum(1 for p in head if p in rel)
    return hits / len(rel)


def precision_at_k(q: QueryEval, k: int) -> float:
    rel = _rel_set(q)
    head = q.predicted[:k]
    if not head:
        return 0.0
    hits = sum(1 for p in head if p in rel)
    return hits / len(head)


def ndcg_at_k(q: QueryEval, k: int) -> float:
    grades = q.relevant if isinstance(q.relevant, dict) else {s: 1 for s in q.relevant}

    def dcg(slugs: list[str]) -> float:
        s = 0.0
        for i, slug in enumerate(slugs):
            g = grades.get(slug, 0)
            s += (2 ** g - 1) / math.log2(i + 2)
        return s

    ideal = [s for s, _ in sorted(grades.items(), key=lambda kv: kv[1], reverse=True)][:k]
    idcg = dcg(ideal)
    actual = dcg(q.predicted[:k])
    return actual / idcg if idcg > 0 else 0.0


# ── Spatial ───────────────────────────────────────────────────────────


_EARTH = 6371.0088


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1 = a
    lat2, lng2 = b
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    r1 = math.radians(lat1)
    r2 = math.radians(lat2)
    x = math.sin(d_lat / 2) ** 2 + math.sin(d_lng / 2) ** 2 * math.cos(r1) * math.cos(r2)
    return 2 * _EARTH * math.asin(math.sqrt(x))


def bbox_around(center: tuple[float, float], radius_km: float) -> dict:
    lat, lng = center
    d_lat = radius_km / 111
    d_lng = radius_km / (111 * math.cos(math.radians(lat)))
    return {"min_lat": lat - d_lat, "max_lat": lat + d_lat, "min_lng": lng - d_lng, "max_lng": lng + d_lng}


def in_box(point: tuple[float, float], box: dict) -> bool:
    lat, lng = point
    return box["min_lat"] <= lat <= box["max_lat"] and box["min_lng"] <= lng <= box["max_lng"]


# ── HTTP Range ────────────────────────────────────────────────────────


def parse_range(header: str, total: int) -> tuple[int, int] | str | None:
    if not header or not header.startswith("bytes="):
        return None
    spec = header[6:].split(",")[0].strip()
    if not spec:
        return None
    if spec.startswith("-"):
        try:
            suffix = int(spec[1:])
        except ValueError:
            return None
        if suffix <= 0:
            return None
        return max(0, total - suffix), total - 1
    parts = spec.split("-", 1)
    try:
        start = int(parts[0])
        end = int(parts[1]) if parts[1] else total - 1
    except (ValueError, IndexError):
        return None
    if start > end or start >= total:
        return "unsatisfiable"
    return start, min(end, total - 1)


def content_range(start: int, end: int, total: int) -> str:
    return f"bytes {start}-{end}/{total}"


# ── Wallet-style address ──────────────────────────────────────────────

_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_VERSION_V1 = 0x01


def _blake3(data: bytes) -> bytes:
    """BLAKE3 — required. Wallet addresses depend on byte-equivalence across
    every Hanzo runtime (TS @noble/hashes/blake3, Rust blake3 crate, Go
    lukechampine.com/blake3, C++ vendored reference impl). The `blake3` pip
    package is the only path here; do not fall back to anything else."""
    try:
        from blake3 import blake3 as _blake3_impl  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "hanzo_memory.algorithms requires the `blake3` package "
            "(pip install blake3). Wallet addresses are content-addressable; "
            "no other hash is acceptable."
        ) from exc
    return _blake3_impl(data).digest()


def encode_address(public_key: bytes, prefix: str = "hanzo") -> str:
    if len(public_key) != 32:
        raise ValueError("public key must be 32 bytes")
    h = _blake3(public_key)[:20]
    versioned = bytes([_VERSION_V1]) + h
    checksum = _blake3(versioned)[:4]
    return f"{prefix}:{_base58_encode(versioned + checksum)}"


def decode_address(address: str) -> dict:
    if ":" not in address:
        raise ValueError("address: missing prefix")
    prefix, body = address.split(":", 1)
    decoded = _base58_decode(body)
    if len(decoded) != 25:
        raise ValueError("address: wrong length")
    version = decoded[0]
    h = decoded[1:21]
    checksum = decoded[21:25]
    expected = _blake3(decoded[:21])[:4]
    if checksum != expected:
        raise ValueError("address: bad checksum")
    return {"prefix": prefix, "version": version, "hash": bytes(h)}


def _base58_encode(b: bytes) -> str:
    if not b:
        return ""
    zeros = 0
    for c in b:
        if c == 0:
            zeros += 1
        else:
            break
    n = int.from_bytes(b, "big")
    out = ""
    while n > 0:
        n, r = divmod(n, 58)
        out = _BASE58[r] + out
    return _BASE58[0] * zeros + out


def _base58_decode(s: str) -> bytes:
    if not s:
        return b""
    zeros = 0
    for c in s:
        if c == _BASE58[0]:
            zeros += 1
        else:
            break
    n = 0
    for c in s:
        if c not in _BASE58:
            raise ValueError(f"base58: invalid char {c}")
        n = n * 58 + _BASE58.index(c)
    out = n.to_bytes((n.bit_length() + 7) // 8, "big") if n > 0 else b""
    return b"\x00" * zeros + out


# ── Graph maintenance ─────────────────────────────────────────────────


@dataclass
class WeightedEdge:
    source: str
    target: str
    weight: float


def normalize_edges(edges: list[WeightedEdge]) -> list[WeightedEdge]:
    if not edges:
        return []
    lo = min(e.weight for e in edges)
    hi = max(e.weight for e in edges)
    span = hi - lo
    return [WeightedEdge(e.source, e.target, ((e.weight - lo) / span) if span > 0 else 1.0) for e in edges]


def snn_score(edges: list[WeightedEdge], k: int = 10) -> list[WeightedEdge]:
    adj: dict[str, list[WeightedEdge]] = {}
    for e in edges:
        adj.setdefault(e.source, []).append(e)
        adj.setdefault(e.target, []).append(WeightedEdge(e.target, e.source, e.weight))
    nbrs: dict[str, set[str]] = {}
    for node, lst in adj.items():
        lst.sort(key=lambda x: x.weight, reverse=True)
        nbrs[node] = {x.target for x in lst[:k]}
    out: list[WeightedEdge] = []
    for e in edges:
        a = nbrs.get(e.source, set())
        b = nbrs.get(e.target, set())
        inter = len(a & b)
        union = len(a | b)
        out.append(WeightedEdge(e.source, e.target, inter / union if union > 0 else 0.0))
    return out


def pfnet_infinity(edges: list[WeightedEdge]) -> list[WeightedEdge]:
    adj: dict[str, dict[str, float]] = {}
    for e in edges:
        adj.setdefault(e.source, {})[e.target] = max(adj.get(e.source, {}).get(e.target, 0), e.weight)
    keep: list[WeightedEdge] = []
    for e in edges:
        dominated = False
        for x, w_ux in adj.get(e.source, {}).items():
            if x == e.target:
                continue
            w_xv = adj.get(x, {}).get(e.target)
            if w_xv is None:
                continue
            if min(w_ux, w_xv) > e.weight:
                dominated = True
                break
        if not dominated:
            keep.append(e)
    return keep


def louvain(edges: list[WeightedEdge], passes: int = 10) -> dict[str, int]:
    nodes: set[str] = set()
    for e in edges:
        nodes.add(e.source)
        nodes.add(e.target)
    community = {n: i for i, n in enumerate(nodes)}
    adj: dict[str, list[tuple[str, float]]] = {}
    total = 0.0
    for e in edges:
        adj.setdefault(e.source, []).append((e.target, e.weight))
        adj.setdefault(e.target, []).append((e.source, e.weight))
        total += e.weight
    deg = {n: sum(w for _, w in adj.get(n, [])) for n in nodes}
    m = total

    for _ in range(passes):
        improved = False
        for n in nodes:
            cur = community[n]
            w_to: dict[int, float] = {}
            for nb, w in adj.get(n, []):
                c = community[nb]
                w_to[c] = w_to.get(c, 0) + w
            best = cur
            best_gain = 0.0
            kn = deg.get(n, 0)
            for c, wnc in w_to.items():
                if c == cur:
                    continue
                sigma_tot = sum(deg[o] for o, comm in community.items() if comm == c and o != n)
                gain = wnc - (kn * sigma_tot) / max(2 * m, 1e-9)
                if gain > best_gain:
                    best_gain = gain
                    best = c
            if best != cur:
                community[n] = best
                improved = True
        if not improved:
            break

    id_map: dict[int, int] = {}
    nxt = 0
    for c in community.values():
        if c not in id_map:
            id_map[c] = nxt
            nxt += 1
    return {n: id_map[c] for n, c in community.items()}


# ── Document type registry ────────────────────────────────────────────


@dataclass
class DocType:
    slug: str
    label: str
    chunking: str
    filename_patterns: list[re.Pattern] = field(default_factory=list)
    mime_types: list[str] = field(default_factory=list)
    content_match: Callable[[str], bool] | None = None
    revision_hints: list[str] = field(default_factory=list)


_DOCTYPES: dict[str, DocType] = {}


def register_doc_type(t: DocType) -> None:
    _DOCTYPES[t.slug] = t


def get_doc_type(slug: str) -> DocType | None:
    return _DOCTYPES.get(slug)


def list_doc_types() -> list[DocType]:
    return list(_DOCTYPES.values())


def detect_doc_type(filename: str | None = None, mime_type: str | None = None, body: str | None = None) -> DocType:
    best: DocType | None = None
    best_score = 0
    for t in _DOCTYPES.values():
        score = 0
        if filename:
            for p in t.filename_patterns:
                if p.search(filename):
                    score += 2
        if mime_type and mime_type in t.mime_types:
            score += 3
        if body and t.content_match and t.content_match(body):
            score += 1
        if score > best_score:
            best_score = score
            best = t
    return best or _DOCTYPES["note/plain"]


for _t in [
    DocType("note/plain", "Plain note", "paragraph", revision_hints=["Clarity", "Concision"]),
    DocType("meeting/notes", "Meeting notes", "semantic",
            filename_patterns=[re.compile("meeting", re.I), re.compile("standup", re.I), re.compile("retro", re.I)],
            content_match=lambda b: bool(re.search(r"\b(action item|decision|attendees)\b", b, re.I)),
            revision_hints=["Decisions", "Action Items", "Attendees", "Next Steps"]),
    DocType("research/paper", "Research paper", "semantic",
            filename_patterns=[re.compile("paper", re.I), re.compile(r"\.pdf$", re.I)],
            revision_hints=["Methodology", "Findings", "Citations"]),
    DocType("code/source", "Source code", "syntactic",
            filename_patterns=[re.compile(r"\.(rs|go|ts|tsx|js|py|java|c|cpp|h|rb|kt|swift|sql|sh)$", re.I)],
            revision_hints=["Purpose", "Inputs", "Outputs"]),
    DocType("code/markdown", "Markdown / docs", "semantic",
            filename_patterns=[re.compile(r"\.md$", re.I), re.compile("readme", re.I)],
            mime_types=["text/markdown"]),
    DocType("email/message", "Email", "paragraph",
            filename_patterns=[re.compile(r"\.eml$", re.I), re.compile(r"\.msg$", re.I)],
            mime_types=["message/rfc822"]),
    DocType("spreadsheet/table", "Spreadsheet", "fixed",
            filename_patterns=[re.compile(r"\.(xlsx|xls|ods|csv|tsv)$", re.I)]),
    DocType("media/audio", "Audio", "fixed", filename_patterns=[re.compile(r"\.(mp3|wav|flac|m4a|opus|ogg)$", re.I)]),
    DocType("media/video", "Video", "fixed", filename_patterns=[re.compile(r"\.(mp4|mkv|webm|mov)$", re.I)]),
    DocType("media/image", "Image", "fixed", filename_patterns=[re.compile(r"\.(png|jpe?g|webp|gif|tiff?)$", re.I)]),
    DocType("media/3d", "3D model", "fixed", filename_patterns=[re.compile(r"\.(glb|gltf|obj|fbx|stl|usdz)$", re.I)]),
    DocType("archive/zip", "Archive", "fixed", filename_patterns=[re.compile(r"\.(zip|tar|tar\.gz|tgz|7z)$", re.I)]),
]:
    register_doc_type(_t)


# ── Circuit breaker / retry ───────────────────────────────────────────


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_ms: int = 30_000) -> None:
        self.threshold = failure_threshold
        self.cooldown = cooldown_ms / 1000.0
        self.failures = 0
        self._opened_at = 0.0

    def state(self) -> str:
        import time
        if self.failures < self.threshold:
            return "closed"
        if time.time() - self._opened_at >= self.cooldown:
            return "half-open"
        return "open"

    def run(self, fn: Callable[[], object]) -> object:
        import time
        s = self.state()
        if s == "open":
            raise CircuitOpenError()
        try:
            r = fn()
            self.failures = 0
            self._opened_at = 0.0
            return r
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold and self._opened_at == 0:
                self._opened_at = time.time()
            raise


def retry(fn: Callable[[], object], attempts: int = 3, base_ms: int = 100, max_ms: int = 30_000,
          is_transient: Callable[[Exception], bool] | None = None,
          sleep_fn: Callable[[float], None] | None = None) -> object:
    import time
    import random
    sleep = sleep_fn or (lambda s: time.sleep(s))
    transient = is_transient or (lambda _e: True)
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last_err = e
            if i == attempts - 1 or not transient(e):
                break
            delay = min(max_ms, base_ms * (2 ** i)) * random.random() / 1000.0
            sleep(delay)
    assert last_err is not None
    raise last_err


# ── Inference: provider slug + capabilities ───────────────────────────

KNOWN_PROVIDERS = {"ollama", "openai", "openrouter", "llamacpp", "anthropic", "google", "azure", "groq", "together", "mock"}


def parse_slug(slug: str, default_provider: str = "ollama") -> dict:
    if ":" not in slug:
        return {"provider": default_provider, "model": slug}
    head, rest = slug.split(":", 1)
    if head in KNOWN_PROVIDERS:
        return {"provider": head, "model": rest}
    return {"provider": default_provider, "model": slug}


def format_slug(p: dict) -> str:
    return f"{p['provider']}:{p['model']}"


# ── Runtime config ────────────────────────────────────────────────────


class RuntimeConfig:
    def __init__(self, defaults: dict[str, str] | None = None, env: dict[str, str] | None = None) -> None:
        self.defaults = defaults or {}
        self.env = env if env is not None else dict(os.environ)
        self.overrides: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        if key in self.overrides:
            return self.overrides[key]
        if key in self.env:
            return self.env[key]
        return self.defaults.get(key)

    def source(self, key: str) -> str:
        if key in self.overrides:
            return "db_override"
        if key in self.env:
            return "env"
        if key in self.defaults:
            return "default"
        return "absent"

    def set(self, key: str, value: str) -> None:
        self.overrides[key] = value

    def clear(self, key: str) -> None:
        self.overrides.pop(key, None)


# ── Link-type rule classifier ─────────────────────────────────────────

LINK_TYPES = [
    "mentions", "founded", "invested_in", "advises", "works_at",
    "attended", "authored", "cites", "succeeded_by", "located_in", "related",
]

_LINK_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bfounded\b", re.I), "founded"),
    (re.compile(r"\binvested\s+in\b", re.I), "invested_in"),
    (re.compile(r"\badvis(?:or|es|ing)\b", re.I), "advises"),
    (re.compile(r"\bworks?\s+(?:at|for)\b", re.I), "works_at"),
    (re.compile(r"\battended\b", re.I), "attended"),
    (re.compile(r"\b(?:wrote|authored)\b", re.I), "authored"),
    (re.compile(r"\bcites?\b", re.I), "cites"),
    (re.compile(r"\bsucceeded\s+by\b", re.I), "succeeded_by"),
    (re.compile(r"\blocated\s+in\b", re.I), "located_in"),
]


def classify_link_rule(evidence: str) -> str:
    for pat, t in _LINK_RULES:
        if pat.search(evidence):
            return t
    return "mentions"


__all__ = [
    # Fusion
    "RRF_K_DEFAULT", "SearchHit", "rrf_fuse", "rsf_fuse", "QueryCharacteristics",
    "characterize", "select_rrf_k", "select_weights",
    # Rerank / dedup
    "cosine", "MmrInput", "mmr_rerank", "dedup_hits",
    # Script / FTS
    "detect_script", "has_cjk", "has_emoji", "cjk_bigrams", "emoji_trigrams",
    "parse_websearch", "to_fts5_match",
    # Embed
    "EmbeddingModel", "register_embedding_model", "get_embedding_model", "list_embedding_models",
    "prefix_for", "l2_normalize", "mrl_truncate", "coarse_dim",
    # Temporal
    "v7_floor", "v7_ceiling", "range_bounds",
    # Captions
    "CaptionSegment", "render_vtt", "render_srt", "render_rttm",
    # Tokenizer
    "estimate_tokens", "truncate_to_tokens",
    # Eval
    "QueryEval", "reciprocal_rank", "mean_reciprocal_rank", "recall_at_k", "precision_at_k", "ndcg_at_k",
    # Spatial / Range
    "haversine_km", "bbox_around", "in_box", "parse_range", "content_range",
    # Address
    "encode_address", "decode_address",
    # Graph
    "WeightedEdge", "normalize_edges", "snn_score", "pfnet_infinity", "louvain",
    # Doc types
    "DocType", "register_doc_type", "get_doc_type", "list_doc_types", "detect_doc_type",
    # Resilience
    "CircuitBreaker", "CircuitOpenError", "retry",
    # Inference
    "KNOWN_PROVIDERS", "parse_slug", "format_slug", "RuntimeConfig",
    # Link types
    "LINK_TYPES", "classify_link_rule",
]
