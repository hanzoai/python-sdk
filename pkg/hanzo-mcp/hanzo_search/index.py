"""An index of a source tree that ranks code spans for a query and follows the tree.

Every search stats the tree first: a file whose size, mtime, ctime or inode moved is read
again, re-chunked only when its bytes changed, and a file gone from the tree drops out.
Ranking fuses, by reciprocal rank, BM25 over code-aware tokens, the spans a traceback in
the query names by path and line, and (when a model is configured) dense similarity.
"""

from __future__ import annotations

import ast
import hashlib
import math
import os
import re
import threading
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from hanzo_search.dense import Dense

SKIP = {"node_modules", "__pycache__", "venv", "env", "build", "dist", "target", "site-packages"}
NOISE = (".lock", ".min.js", ".map", ".svg", ".pyc", ".pyo", ".so", ".o", ".a", ".dylib", ".dll", ".exe", ".whl", ".gz", ".zip", ".tar", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2", ".ttf", ".npy", ".npz", ".pkl", ".sqlite", ".db")
LIMIT = 1 << 20  # bytes: a larger file is not indexed
SPAN = 40  # lines a chunk holds at most
STRIDE = 30  # a window's step, so windows overlap by SPAN - STRIDE
WIDTH = 300  # characters a shown line keeps
K1, B = 1.2, 0.75
RRF = 60

WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
PART = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+")
PATH = re.compile(r"(?:[\w.-]+/)*[\w-]+\.\w+")
FRAME = re.compile(r"""(?:File "([^"]+)", line (\d+))|((?:[\w.-]+/)*[\w.-]+\.\w+):(\d+)""")


def tokens(text: str) -> list[str]:
    """Lowercased identifiers, each whole, then its dotted segments and their snake/camel parts."""
    out: list[str] = []
    for m in WORD.finditer(text):
        word = m.group()
        if "." in word:
            out.append(word.lower())
        for seg in word.split("."):
            low = seg.lower()
            if len(low) > 1:
                out.append(low)
            parts = PART.findall(seg)
            if len(parts) > 1:
                out.extend(p.lower() for p in parts if len(p) > 1)
    return out


@dataclass
class Chunk:
    path: str
    start: int  # 1-based, inclusive
    end: int
    name: str
    text: str
    tf: dict[str, int] = field(default_factory=dict)
    length: int = 0


def windows(start: int, end: int) -> list[tuple[int, int]]:
    """[start, end] as windows of at most SPAN lines, STRIDE apart, the last flush with end."""
    if end - start + 1 <= SPAN:
        return [(start, end)]
    out = []
    s = start
    while True:
        out.append((s, min(s + SPAN - 1, end)))
        if s + SPAN - 1 >= end:
            return out
        s += STRIDE


def outline(text: str) -> list[tuple[int, int, str]]:
    """Python spans: each function and method, each class's header, and the code between them."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tree = ast.parse(text)
    spans: list[tuple[int, int, str]] = []
    defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    def first(node: ast.AST) -> int:
        return min([node.lineno] + [d.lineno for d in node.decorator_list])  # type: ignore[attr-defined]

    def visit(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if not isinstance(node, defs):
                continue
            name = prefix + node.name
            inner = [n for n in node.body if isinstance(n, defs)] if isinstance(node, ast.ClassDef) else []
            if inner:
                spans.append((first(node), min(first(n) for n in inner) - 1, name))
                visit(node.body, name + ".")
            else:
                spans.append((first(node), node.end_lineno or node.lineno, name))

    visit(tree.body, "")
    return spans


def chunk(path: str, text: str) -> list[Chunk]:
    """A file's chunks: Python by its outline (code outside any def in gap windows), else windows."""
    lines = text.splitlines()
    n = len(lines)
    spans: list[tuple[int, int, str]] = []
    if path.endswith(".py"):
        try:
            spans = outline(text)
        except (SyntaxError, ValueError):
            spans = []
    covered = bytearray(n + 2)
    out: list[tuple[int, int, str]] = []
    for s, e, name in spans:
        for a, b in windows(s, e):
            out.append((a, b, name))
        for i in range(s, e + 1):
            covered[i] = 1
    i = 1
    while i <= n:
        if covered[i]:
            i += 1
            continue
        j = i
        while j + 1 <= n and not covered[j + 1]:
            j += 1
        out.extend((a, b, "") for a, b in windows(i, j))
        i = j + 1
    chunks = []
    for s, e, name in sorted(out):
        body = "\n".join(lines[s - 1 : e])
        if not body.strip():
            continue
        c = Chunk(path, s, e, name, body)
        toks = tokens(f"{path} {name}\n{body}")
        for t in toks:
            c.tf[t] = c.tf.get(t, 0) + 1
        c.length = len(toks)
        chunks.append(c)
    return chunks


def walk(root: str) -> dict[str, os.stat_result]:
    """Indexable files under root, by path relative to it."""
    out: dict[str, os.stat_result] = {}
    stack = [""]
    while stack:
        rel = stack.pop()
        try:
            it = os.scandir(os.path.join(root, rel) if rel else root)
        except OSError:
            continue
        with it:
            for e in it:
                name = e.name
                if name.startswith(".") or name in SKIP or name.endswith(".egg-info"):
                    continue
                path = f"{rel}/{name}" if rel else name
                try:
                    if e.is_dir(follow_symlinks=False):
                        stack.append(path)
                    elif e.is_file(follow_symlinks=False) and not name.endswith(NOISE):
                        st = e.stat(follow_symlinks=False)
                        if st.st_size <= LIMIT:
                            out[path] = st
                except OSError:
                    continue
    return out


def tested(path: str) -> bool:
    """A test file, by the names pytest and unittest collect."""
    parts = path.split("/")
    base = parts[-1]
    return base.startswith("test_") or base.endswith("_test.py") or base == "conftest.py" or any(p in ("test", "tests") for p in parts[:-1])


@dataclass
class Hit:
    chunk: Chunk
    score: float


class Index:
    """Chunks of one tree with BM25 postings, kept current by refresh()."""

    def __init__(self, root: str, dense: "Dense | None" = None):
        self.root = os.path.realpath(root)
        self.dense = dense
        self.files: dict[str, tuple[tuple[int, int, int, int], str, list[int]]] = {}
        self.chunks: dict[int, Chunk] = {}
        self.post: dict[str, dict[int, int]] = {}
        self.total = 0
        self.serial = 0
        self.lock = threading.Lock()

    def drop(self, path: str) -> None:
        for cid in self.files.pop(path)[2]:
            c = self.chunks.pop(cid)
            self.total -= c.length
            for t in c.tf:
                p = self.post[t]
                del p[cid]
                if not p:
                    del self.post[t]

    def add(self, path: str, key: tuple[int, int, int, int], digest: str, text: str) -> None:
        ids = []
        for c in chunk(path, text):
            cid = self.serial
            self.serial += 1
            self.chunks[cid] = c
            self.total += c.length
            for t, n in c.tf.items():
                self.post.setdefault(t, {})[cid] = n
            ids.append(cid)
        self.files[path] = (key, digest, ids)

    def refresh(self) -> int:
        """Bring the index to the tree as it is now; the number of files read again."""
        seen = walk(self.root)
        for path in [p for p in self.files if p not in seen]:
            self.drop(path)
        read = 0
        for path, st in seen.items():
            key = (st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino)
            old = self.files.get(path)
            if old and old[0] == key:
                continue
            try:
                data = open(os.path.join(self.root, path), "rb").read()
            except OSError:
                if old:
                    self.drop(path)
                continue
            read += 1
            if b"\0" in data[:8192]:  # binary: kept by its stat alone, so it is not read again
                if old:
                    self.drop(path)
                self.files[path] = (key, "", [])
                continue
            digest = hashlib.sha256(data).hexdigest()
            if old and old[1] == digest:
                self.files[path] = (key, digest, old[2])
                continue
            if old:
                self.drop(path)
            self.add(path, key, digest, data.decode("utf-8", "replace"))
        return read

    def bm25(self, query: str) -> list[int]:
        n = len(self.chunks)
        if not n:
            return []
        avg = self.total / n
        scores: dict[int, float] = {}
        for t in set(tokens(query)):
            p = self.post.get(t)
            if not p:
                continue
            idf = math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5))
            for cid, f in p.items():
                norm = K1 * (1 - B + B * self.chunks[cid].length / avg)
                scores[cid] = scores.get(cid, 0.0) + idf * f * (K1 + 1) / (f + norm)
        return sorted(scores, key=lambda c: -scores[c])

    def resolver(self) -> Callable[[str], str | None]:
        """A map from a path as a traceback or a message spells it to the one indexed file it names."""
        names: dict[str, list[str]] = {}
        for path in self.files:
            names.setdefault(path.rsplit("/", 1)[-1], []).append(path)

        def resolve(name: str) -> str | None:
            name = name.replace("\\", "/")
            if name.startswith("./"):
                name = name[2:]
            fits = [p for p in names.get(name.rsplit("/", 1)[-1], ()) if p == name or p.endswith("/" + name) or name.endswith("/" + p)]
            return fits[0] if len(fits) == 1 else None

        return resolve

    def frames(self, query: str) -> list[int]:
        """Chunks holding the lines a traceback in the query names, the deepest frame first."""
        resolve = self.resolver()
        order: list[int] = []
        for m in reversed(list(FRAME.finditer(query))):
            name, line = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
            path = resolve(name)
            if path is None:
                continue
            ln = int(line)
            for cid in self.files[path][2]:
                c = self.chunks[cid]
                if c.start <= ln <= c.end and cid not in order:
                    order.append(cid)
        return order

    def rank(self, query: str) -> list[Hit]:
        """Fused ranks; when the query names a test file it already holds, the code under test first."""
        lists = [self.bm25(query), self.frames(query)]
        if self.dense is not None:
            lists.append(self.dense.rank(self, query))
        fused: dict[int, float] = {}
        for ranked in lists:
            for r, cid in enumerate(ranked):
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF + r + 1)
        order = sorted(fused, key=lambda c: -fused[c])
        resolve = self.resolver()
        if any(tested(p) for p in filter(None, map(resolve, PATH.findall(query)))):
            order = [c for c in order if not tested(self.chunks[c].path)] + [c for c in order if tested(self.chunks[c].path)]
        return [Hit(self.chunks[c], fused[c]) for c in order]

    def search(self, query: str, k: int = 5) -> list[Hit]:
        with self.lock:
            self.refresh()
            return self.rank(query)[: max(1, k)]


def render(hits: list[Hit], cap: int = 6000) -> str:
    """Each hit as `path:start-end name` and its lines, all within cap characters."""
    blocks: list[str] = []
    used = 0
    for h in hits:
        c = h.chunk
        lines = [ln if len(ln) <= WIDTH else ln[:WIDTH] + "…" for ln in c.text.splitlines()[:SPAN]]
        block = f"{c.path}:{c.start}-{c.end}" + (f" {c.name}" if c.name else "") + "\n" + "\n".join(lines)
        room = cap - used - 2 * len(blocks)
        if room <= 0:
            break
        if len(block) > room:
            if blocks and room < 400:
                break
            block = block[:room]
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks) if blocks else "no match"


_open: dict[str, Index] = {}
_guard = threading.Lock()


def index(root: str) -> Index:
    """The process's index of root, made on first use."""
    real = os.path.realpath(root)
    with _guard:
        if real not in _open:
            from hanzo_search.dense import load

            _open[real] = Index(real, load())
        return _open[real]


def search(query: str, root: str = "", k: int = 5) -> str:
    """Rendered top-k spans of root (default: the working directory) for query."""
    if not query.strip():
        return "empty query"
    base = root or os.getcwd()
    if not os.path.isdir(base):
        return f"not a directory: {base}"
    return render(index(base).search(query, k))
