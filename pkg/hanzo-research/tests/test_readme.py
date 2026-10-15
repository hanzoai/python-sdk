"""The README's worked example runs as written, against the fake, and the docs page shows the same code."""

from __future__ import annotations

import os
import re

from conftest import HANZO

HERE = os.path.dirname(__file__)
README = os.path.join(HERE, "..", "README.md")
DOCS = os.path.join(HERE, "..", "..", "..", "docs", "content", "docs", "research.mdx")


def example(path: str) -> str:
    text = open(path, encoding="utf-8").read()
    return re.search(r"## Worked example.*?```python\n(.*?)```", text, re.S).group(1)


def test_the_worked_example_files_reads_back(server, monkeypatch, capsys):
    monkeypatch.setenv("HANZO_API_KEY", HANZO)
    monkeypatch.setenv("RESEARCH_BASE", server.url)
    exec(compile(example(README), "README.md", "exec"), {"__name__": "example"})  # noqa: S102
    out = capsys.readouterr().out.split()
    assert out[0] == "complete" and float(out[1]) > 0
    paths = [(q["method"], q["path"]) for q in server.fake.requests]
    assert paths == [
        ("POST", "/v1/research/benchmarks"),
        ("POST", "/v1/research/runs"),
        ("POST", "/v1/research/grants"),
        ("GET", "/v1/research/runs"),
    ]
    run = server.fake.requests[1]["body"]["runs"][0]
    assert run["commit"] == out[2] and "Provenance: harness " in run["notes"] and run["by"]


def test_the_docs_page_shows_the_same_example():
    assert example(DOCS) == example(README)
