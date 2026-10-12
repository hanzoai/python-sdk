"""The `search` tool: tokens, chunks, ranking, freshness, rendering, schema, dense cache, stdio."""

import json
import os
import shutil
import subprocess
import sys
import time

import pytest

from hanzo_search import DESCRIPTION, SCHEMA
from hanzo_search import index as X
from hanzo_search.dense import Dense

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRICE = '''"""Prices."""
import math

RATE = 0.2


def apply_discount(total, percent):
    """Take percent off total."""
    return total * (1 - percent / 100)


class Invoice:
    """An invoice."""

    currency = "usd"

    def subtotal(self, lines):
        return sum(q * p for q, p in lines)

    @property
    def taxRate(self):
        return RATE
'''

PARSE = '''def parse_header(line):
    key, _, value = line.partition(":")
    return key.strip().lower(), value.strip()


def read_body(stream):
    return stream.read()
'''

TEST = '''from shop.price import apply_discount


def test_apply_discount():
    assert apply_discount(100, 10) == 90
'''


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "shop").mkdir()
    (tmp_path / "shop" / "price.py").write_text(PRICE)
    (tmp_path / "shop" / "parse.py").write_text(PARSE)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_price.py").write_text(TEST)
    (tmp_path / "README.md").write_text("# Shop\n\nPrices and invoices for the shop.\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("apply_discount apply_discount")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("apply_discount()")
    (tmp_path / "blob.bin").write_bytes(b"apply_discount\0\0\0")
    return tmp_path


def top(ix, query):
    return [(h.chunk.path, h.chunk.name) for h in ix.search(query, 5)]


def test_tokens_split_identifiers_and_keep_them_whole():
    t = X.tokens("parse_header(HTTPServer.getValue) x 42")
    for want in ("parse_header", "parse", "header", "httpserver.getvalue", "httpserver", "http", "server", "getvalue", "get", "value"):
        assert want in t, want
    assert "x" not in t and "42" not in t


def test_python_chunks_follow_definitions():
    chunks = X.chunk("shop/price.py", PRICE)
    names = [(c.name, c.start, c.end) for c in chunks]
    assert ("apply_discount", 7, 9) in names
    assert ("Invoice.subtotal", 17, 18) in names
    assert ("Invoice.taxRate", 20, 22) in names  # the decorator starts the span
    assert any(n == "Invoice" and s == 12 for n, s, _ in names)  # the class header
    assert any(n == "" and s == 1 for n, s, _ in names)  # module code between definitions


def test_long_spans_and_other_files_are_overlapping_windows():
    body = "\n".join(f"line {i}" for i in range(1, 101))
    spans = [(c.start, c.end) for c in X.chunk("notes.txt", body)]
    assert spans == [(1, 40), (31, 70), (61, 100)]
    fn = "def big():\n" + "\n".join(f"    x{i} = {i}" for i in range(60)) + "\n"
    parts = [c for c in X.chunk("big.py", fn) if c.name == "big"]
    assert [(c.start, c.end) for c in parts] == [(1, 40), (31, 61)]
    assert all(c.end - c.start + 1 <= X.SPAN for c in parts)


def test_broken_python_still_indexes():
    chunks = X.chunk("bad.py", "def f(:\n    return 1\n")
    assert len(chunks) == 1 and chunks[0].start == 1


def test_walk_skips_vcs_vendor_and_binaries(repo):
    ix = X.Index(str(repo))
    ix.refresh()
    assert set(ix.files) == {"shop/price.py", "shop/parse.py", "tests/test_price.py", "README.md", "blob.bin"}
    assert ix.files["blob.bin"][2] == []


def test_bm25_ranks_the_named_definition_first(repo):
    ix = X.Index(str(repo))
    assert top(ix, "where is the header of a line parsed")[0] == ("shop/parse.py", "parse_header")
    assert top(ix, "subtotal of the invoice lines")[0] == ("shop/price.py", "Invoice.subtotal")


def test_a_traceback_names_its_span_and_the_code_under_test_comes_first(repo):
    ix = X.Index(str(repo))
    out = (
        "tests/test_price.py:5: in test_apply_discount\n    assert apply_discount(100, 10) == 90\n"
        "shop/price.py:9: in apply_discount\nE   AssertionError\n"
        "FAILED tests/test_price.py::test_apply_discount - AssertionError"
    )
    assert top(ix, out)[0] == ("shop/price.py", "apply_discount")
    ranked = [h.chunk for h in ix.rank(out)]
    first = max(i for i, c in enumerate(ranked) if not X.tested(c.path))
    assert all(X.tested(c.path) for c in ranked[first + 1 :]) and X.tested(ranked[-1].path)
    # a question that names no test file ranks tests by relevance alone
    assert top(ix, "test apply discount 100 10 90")[0] == ("tests/test_price.py", "test_apply_discount")


def test_freshness_create_modify_delete_and_replace(repo):
    ix = X.Index(str(repo))
    assert all(p != "shop/new.py" for p, _ in top(ix, "frobnicate widget"))
    (repo / "shop" / "new.py").write_text("def frobnicate_widget():\n    return 1\n")
    assert top(ix, "frobnicate widget")[0] == ("shop/new.py", "frobnicate_widget")

    # rewritten: same size, mtime put back; the ctime still moves
    p = repo / "shop" / "parse.py"
    st = p.stat()
    p.write_text(PARSE.replace("read_body", "zapx_body"))
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert top(ix, "zapx body")[0] == ("shop/parse.py", "zapx_body")
    assert all(c.name != "read_body" for c in ix.chunks.values())

    (repo / "shop" / "new.py").unlink()
    ix.search("x", 1)
    assert "shop/new.py" not in ix.files and all(c.path != "shop/new.py" for c in ix.chunks.values())

    # a whole directory swapped for another with the same names and new contents
    shutil.rmtree(repo / "shop")
    (repo / "shop").mkdir()
    (repo / "shop" / "price.py").write_text("def quux_total():\n    return 2\n")
    hits = top(ix, "quux total")
    assert hits[0] == ("shop/price.py", "quux_total")
    assert set(ix.files) == {"shop/price.py", "tests/test_price.py", "README.md", "blob.bin"}
    assert not any(t in ix.post for t in ("subtotal", "parse_header", "zapx_body"))
    assert sum(c.length for c in ix.chunks.values()) == ix.total


def test_unchanged_files_are_not_read_again(repo):
    ix = X.Index(str(repo))
    assert ix.refresh() == 5  # blob.bin is read once, found binary, and kept by its stat
    assert ix.refresh() == 0
    os.utime(repo / "README.md")  # touched, same bytes: read, not re-chunked
    before = set(ix.chunks)
    assert ix.refresh() == 1 and set(ix.chunks) == before


def test_render_caps_hits_lines_and_characters(tmp_path):
    for i in range(12):
        body = "\n".join(f"    v{j} = 'needle {i} {j}' + '{'w' * 400}'" for j in range(80))
        (tmp_path / f"m{i}.py").write_text(f"def needle_{i}():\n{body}\n")
    out = X.search("needle", str(tmp_path), k=50)
    assert len(out) <= 6000
    blocks = out.split("\n\n")
    assert all(len(b.splitlines()) <= X.SPAN + 1 for b in blocks)
    assert all(len(line) <= X.WIDTH + 1 for b in blocks for line in b.splitlines()[1:])
    head = blocks[0].splitlines()[0]
    path, _, rest = head.partition(":")
    assert path.startswith("m") and rest.split()[0].count("-") == 1
    assert len(X.search("needle", str(tmp_path), k=3).split("\n\n")) <= 3
    assert X.search("zzzqqq", str(tmp_path)) == "no match"
    assert X.search("  ", str(tmp_path)) == "empty query"
    assert X.search("x", str(tmp_path / "missing")).startswith("not a directory")


def test_schema_and_description_stay_small():
    tokens = len(json.dumps({"name": "search", "description": DESCRIPTION, "inputSchema": SCHEMA})) / 4
    assert tokens < 250, tokens


def test_fastmcp_registration_is_the_same_small_tool():
    from mcp.server.fastmcp import FastMCP

    from hanzo_search import register

    mcp = FastMCP("t")
    register(mcp)
    tool = mcp._tool_manager.get_tool("search")
    assert tool.description == DESCRIPTION
    assert set(tool.parameters["properties"]) == {"query", "root", "k"}
    assert tool.parameters["required"] == ["query"]
    assert len(json.dumps({"d": tool.description, "s": tool.parameters})) / 4 < 250


def test_dense_vectors_are_kept_by_content_across_trees(repo, tmp_path_factory):
    import numpy as np

    calls = []

    def embed(texts):
        calls.append(len(texts))
        out = np.zeros((len(texts), 8), np.float32)
        for i, t in enumerate(texts):
            out[i, hash(t) % 8] = 1.0
        return out

    db = str(tmp_path_factory.mktemp("cache") / "m.sqlite")
    ix = X.Index(str(repo), Dense(embed, db))
    ix.search("invoice", 3)
    first = sum(calls) - 1  # less the query
    assert first == len(ix.chunks)

    copy = tmp_path_factory.mktemp("copy") / "t"
    shutil.copytree(repo, copy)
    calls.clear()
    other = X.Index(str(copy), Dense(embed, db))  # a fresh process: memory empty, the file kept
    other.search("invoice", 3)
    assert calls == [1]  # the query alone

    (copy / "shop" / "parse.py").write_text(PARSE + "\n\ndef added():\n    return 3\n")
    calls.clear()
    other.search("invoice", 3)
    assert sum(calls) == 1 + 1  # the one new chunk, then the query


def rpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    if "id" not in msg:
        return None
    return json.loads(proc.stdout.readline())


def test_stdio_server_round_trip(repo, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "PYTHONPATH": PKG}
    t = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, "-m", "hanzo_search.server", "--root", str(repo)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=str(repo.parent), env=env,
    )
    try:
        init = rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}})
        assert time.perf_counter() - t < 1.0
        assert init["result"]["protocolVersion"] == "2025-06-18" and "tools" in init["result"]["capabilities"]
        rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        assert [x["name"] for x in tools] == ["search"]
        call = rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search", "arguments": {"query": "parse a header line", "k": 2}}})
        text = call["result"]["content"][0]["text"]
        assert call["result"]["isError"] is False and text.startswith("shop/parse.py:1-3 parse_header")
        bad = rpc(proc, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "search", "arguments": {}}})
        assert bad["result"]["isError"] is True
        assert rpc(proc, {"jsonrpc": "2.0", "id": 5, "method": "nope"})["error"]["code"] == -32601
        assert rpc(proc, {"jsonrpc": "2.0", "id": 6, "method": "ping"})["result"] == {}
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)
    assert proc.returncode == 0


def test_the_default_mode_carries_search_and_the_user_can_turn_it_off(monkeypatch, tmp_path):
    import asyncio

    from mcp.server.fastmcp import FastMCP

    from hanzo_mcp.tools import register_all_tools
    from hanzo_mcp.tools.common.mode_loader import ModeLoader
    from hanzo_mcp.tools.common.permissions import PermissionManager

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HANZO_MCP_ENABLED_TOOLS", raising=False)
    monkeypatch.delenv("HANZO_MCP_MODE", raising=False)
    ModeLoader.initialize_modes()

    def names():
        server = FastMCP("s")
        register_all_tools(server, PermissionManager())
        return [t.name for t in asyncio.run(server.list_tools())]

    assert names().count("search") == 1
    (tmp_path / ".hanzo" / "mcp").mkdir(parents=True)
    (tmp_path / ".hanzo" / "mcp" / "tool_states.json").write_text('{"search": false}')
    assert "search" not in names()
