"""Tests for hanzo-tools-vector.

Import/registration checks plus offline tests of the cloud-backed VectorTool
wiring (/v1/code/search, /v1/code/index, /v1/embeddings) and the mock-kill.
"""

import re
import asyncio
import importlib
from pathlib import Path

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import vector

        assert vector is not None

    def test_import_tools(self):
        from hanzo_tools.vector import TOOLS

        assert len(TOOLS) > 0


class FakeCloud:
    def __init__(self, get_result=None, post_result=None, configured=True):
        self.get_result = get_result if get_result is not None else {}
        self.post_result = post_result if post_result is not None else {}
        self.calls = []
        self._configured = configured

    def configured(self):
        return self._configured

    async def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        if isinstance(self.get_result, Exception):
            raise self.get_result
        return self.get_result

    async def post(self, path, json_body=None):
        self.calls.append(("POST", path, json_body))
        if isinstance(self.post_result, Exception):
            raise self.post_result
        return self.post_result


def _run(coro):
    return asyncio.run(coro)


class TestCloudVectorTool:
    def test_actions_present(self):
        from hanzo_tools.vector import VectorTool

        t = VectorTool()
        for a in ("search", "index", "embed"):
            assert a in t._handlers

    def test_search_maps_to_code_search_hybrid_default(self):
        from hanzo_tools.vector import VectorTool

        t = VectorTool()
        t._cloud = FakeCloud(get_result={"results": [{"file": "a.go"}]})
        env = _run(t.call(None, action="search", query="qdrant", collection="c"))
        assert env["ok"] is True
        method, path, params = t._cloud.calls[0]
        assert method == "GET" and path == "/v1/code/search"
        assert params["q"] == "qdrant"
        assert params["type"] == "hybrid"  # robust default
        assert params["repo"] == "c"
        assert env["data"]["count"] == 1

    def test_embed_maps_to_embeddings(self):
        from hanzo_tools.vector import VectorTool

        t = VectorTool()
        t._cloud = FakeCloud(
            post_result={
                "model": "zen-embedding",
                "data": [{"embedding": [0.1, 0.2, 0.3]}],
                "usage": {"total_tokens": 2},
            }
        )
        env = _run(t.call(None, action="embed", input="hello"))
        assert env["ok"] is True
        method, path, body = t._cloud.calls[0]
        assert method == "POST" and path == "/v1/embeddings"
        assert body == {"model": "zen-embedding", "input": "hello"}
        assert env["data"]["dimensions"] == 3 and env["data"]["count"] == 1

    def test_index_collects_dir(self, tmp_path):
        from hanzo_tools.vector import VectorTool

        (tmp_path / "a.py").write_text("print(1)")
        (tmp_path / "README.md").write_text("# hi")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("x")

        t = VectorTool()
        t._cloud = FakeCloud(post_result={"indexed": 2})
        env = _run(t.call(None, action="index", collection="c", path=str(tmp_path)))
        assert env["ok"] is True
        method, path, body = t._cloud.calls[0]
        assert method == "POST" and path == "/v1/code/index"
        assert body["repo"] == "c"
        names = {f["path"] for f in body["files"]}
        assert names == {"a.py", "README.md"}  # .git skipped

    def test_not_configured_fails_closed(self):
        from hanzo_tools.vector import VectorTool

        t = VectorTool()
        t._cloud = FakeCloud(configured=False)
        env = _run(t.call(None, action="search", query="x"))
        assert env["ok"] is False
        assert env["error"]["code"] == "INVALID_PARAMS"


class TestNoFake:
    """The random-vector local store is deleted, not flag-guarded.

    Regression guard: an importable local store means an embedder-less path
    exists again, and the only vectors it can produce are noise.
    """

    @pytest.mark.parametrize(
        "gone",
        [
            "infinity_store",
            "mock_infinity",
            "vector_search",
            "vector_index",
            "index_tool",
            "git_ingester",
            "project_manager",
        ],
    )
    def test_local_store_modules_are_gone(self, gone):
        with pytest.raises(ImportError):
            importlib.import_module(f"hanzo_tools.vector.{gone}")

    def test_no_random_in_package(self):
        """No module in the package may import `random` — vectors come from the service."""
        pkg = Path(importlib.import_module("hanzo_tools.vector").__file__).parent
        offenders = [
            p.name
            for p in pkg.glob("*.py")
            if re.search(r"^\s*(import random|from random import)", p.read_text(), re.M)
        ]
        assert offenders == []
