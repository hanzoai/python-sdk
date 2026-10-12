"""The optional dense stage: a local embedding model, on only when HANZO_SEARCH_MODEL names one.

The model is read in the Qwen3-Embedding form (last-token pooled, unit length, a query under
an instruction), on the CPU, offline. Each chunk is embedded once: its vector is kept under the
SHA-256 of its text in HANZO_SEARCH_CACHE (default ~/.cache/hanzo/search), one SQLite file per
model, so another process, or another checkout of the same files, embeds nothing again.
Needs torch and transformers, which the base install does not carry.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from hanzo_search.index import Chunk, Index

PREFIX = "Instruct: Given a failing test's output or a question about code, retrieve the code it concerns\nQuery:"
LENGTH = 512  # tokens read of a chunk or a query (a query keeps its end)
BATCH = 16


def text(c: "Chunk") -> str:
    return f"{c.path} {c.name}\n{c.text}"


def cache() -> str:
    return os.environ.get("HANZO_SEARCH_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "hanzo", "search")


class Dense:
    """Chunk vectors by text hash (memory, then the SQLite file, then embed), ranked by cosine."""

    def __init__(self, embed: Callable[[list[str]], Any], db: str):
        os.makedirs(os.path.dirname(db), exist_ok=True)
        self.embed = embed
        self.db = sqlite3.connect(db, check_same_thread=False)
        self.db.execute("create table if not exists v (k blob primary key, x blob)")
        self.lock = threading.Lock()
        self.held: dict[bytes, Any] = {}
        self.matrix: dict[int, tuple[tuple[bytes, ...], Any]] = {}
        self.embedded = 0

    def vectors(self, ix: "Index") -> tuple[list[int], Any]:
        import numpy as np

        ids = sorted(ix.chunks)
        keys = [hashlib.sha256(text(ix.chunks[c]).encode()).digest() for c in ids]
        want = list({k for k in keys if k not in self.held})
        for i in range(0, len(want), 500):
            part = want[i : i + 500]
            for k, x in self.db.execute("select k, x from v where k in (%s)" % ",".join("?" * len(part)), part):
                self.held[k] = np.frombuffer(x, dtype=np.float16).astype(np.float32)
        todo = [k for k in want if k not in self.held]
        if todo:
            byk = {k: c for c, k in zip(ids, keys)}
            new = self.embed([text(ix.chunks[byk[k]]) for k in todo])
            self.embedded += len(todo)
            self.db.executemany("insert or replace into v values (?, ?)", [(k, v.astype(np.float16).tobytes()) for k, v in zip(todo, new)])
            self.db.commit()
            for k, v in zip(todo, new):
                self.held[k] = np.asarray(v, dtype=np.float16).astype(np.float32)
        tag = tuple(keys)
        m = self.matrix.get(id(ix))
        if m is None or m[0] != tag:
            m = (tag, np.stack([self.held[k] for k in keys]) if keys else np.zeros((0, 1), np.float32))
            self.matrix[id(ix)] = m
        return ids, m[1]

    def rank(self, ix: "Index", query: str) -> list[int]:
        with self.lock:
            ids, m = self.vectors(ix)
            if not ids:
                return []
            s = m @ self.embed([PREFIX + query])[0]
        return [ids[i] for i in (-s).argsort()]


def model(path: str, device: str = "cpu") -> tuple[Callable[[list[str]], Any], str]:
    """An embed function over a local model directory, and the model's identity."""
    try:
        import torch
        from transformers import AutoModel, AutoTokenizer
    except ImportError as e:
        raise RuntimeError(f"HANZO_SEARCH_MODEL is set but {e.name} is not installed") from e
    tok = AutoTokenizer.from_pretrained(path, padding_side="left", truncation_side="left", local_files_only=True)
    dtype = torch.float32 if device == "cpu" else torch.bfloat16
    net = AutoModel.from_pretrained(path, dtype=dtype, local_files_only=True).to(device).eval()

    def embed(texts: list[str]) -> Any:
        import numpy as np

        out = []
        for i in range(0, len(texts), BATCH):
            b = tok(texts[i : i + BATCH], padding=True, truncation=True, max_length=LENGTH, return_tensors="pt").to(device)
            with torch.inference_mode():
                h = net(**b).last_hidden_state[:, -1].float()
            out.append(torch.nn.functional.normalize(h, dim=-1).cpu().numpy())
        return np.concatenate(out)

    ident = hashlib.sha256(open(os.path.join(path, "config.json"), "rb").read())
    for name in sorted(os.listdir(path)):
        if name.endswith(".safetensors"):
            ident.update(f"{name}:{os.path.getsize(os.path.join(path, name))}".encode())
    return embed, ident.hexdigest()[:16]


_dense: Dense | None = None
_guard = threading.Lock()


def load() -> Dense | None:
    """The process's dense stage, None unless HANZO_SEARCH_MODEL names a model directory."""
    global _dense
    path = os.environ.get("HANZO_SEARCH_MODEL")
    if not path:
        return None
    with _guard:
        if _dense is None:
            embed, ident = model(path)
            _dense = Dense(embed, os.path.join(cache(), ident + ".sqlite"))
        return _dense
