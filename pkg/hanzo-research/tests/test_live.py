"""Reads of api.hanzo.ai that need no credential: `pytest -m integration`."""

from __future__ import annotations

import pytest
from hanzo_research import Run, Arena, Research

pytestmark = pytest.mark.integration


def test_the_public_runs_of_hanzo():
    r = Research(api_key="", repo=".")
    page = r.runs(org="hanzo")
    assert page.total == len(page.data) > 0
    assert all(isinstance(x, Run) and x.visibility == "public" and x.canonical for x in page.data)
    c = page.completion
    assert c.complete + c.partial + c.inconsistent + c.unknown == page.total
    first = page.data[0]
    assert r.get_run(first.id, org="hanzo").id == first.id


def test_the_arena_reads():
    a = Arena(api_key="")
    assert any(e.id == "gpqa_diamond" for e in a.catalog())
    assert a.leaderboard().benchmark == "gpqa_diamond"
    assert all(c.source for c in a.claims(benchmark="gpqa_diamond"))
