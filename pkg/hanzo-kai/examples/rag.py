"""Keep or drop retrieved passages before they reach the answering model, on the public RAG relevance suite.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

import gzip
import json
import random
import tempfile
import urllib.request
from pathlib import Path

from hanzo_kai import Kai, Noul, RetryPolicy

HARNESS = "https://raw.githubusercontent.com/hanzoai/benchmarks/039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/"
CACHE = Path(tempfile.gettempdir()) / "kai-cookbook"

STATEMENT = Noul(
    instructions="`passage` helps answer `query`.",
    criteria={"true": "the passage gives facts the answer needs", "false": "the passage is off topic or leaves the question open"},
)


def harness(name):
    """A pinned harness file, downloaded once."""
    path = CACHE / name.replace("/", "-")
    if not path.exists():
        CACHE.mkdir(exist_ok=True)
        urllib.request.urlretrieve(HARNESS + name, path)
    return json.load(gzip.open(path))


suite = harness("states.json.gz")["app.rag_relevance"]
jev = harness("jev/preds.json.gz")["suites"]["app.rag_relevance"]["p"]
picked = random.Random(7).sample(range(len(suite)), 100)

rows = []
with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    for case in picked:
        state, questions, gold = suite[case]
        decision = kai.decide(state, {**questions, "statement": STATEMENT})
        rows.append(
            {
                "relevant": gold["relevant"]["idx"] == 1,
                "Kai, harness question": decision.nouls["relevant"].noul,
                "Kai, statement": decision.nouls["statement"].noul,
                "Jev, recorded": jev[f"{case}/relevant"][1],
            }
        )

relevant = sum(row["relevant"] for row in rows)
print(f"{len(rows)} passages, {relevant} of them relevant")
print(f"{'who':24} {'keep if p >=':>12} {'accuracy':>9} {'kept':>6} {'precision':>10} {'recall':>7}")
for who in ("Kai, harness question", "Kai, statement", "Jev, recorded"):
    for threshold in (0.3, 0.5, 0.7):
        keep = [row[who] >= threshold for row in rows]
        right = sum(k == row["relevant"] for k, row in zip(keep, rows))
        good = sum(k and row["relevant"] for k, row in zip(keep, rows))
        print(
            f"{who:24} {threshold:>12.1f} {right / len(rows):>9.2f} {sum(keep) / len(rows):>6.2f}"
            f" {good / max(1, sum(keep)):>10.2f} {good / relevant:>7.2f}"
        )
