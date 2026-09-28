"""Rerank a keyword shortlist of docs pages for a question, and score the order against labels.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

import collections
import math
import re
import tempfile
import urllib.request
from pathlib import Path

from hanzo_kai import Kai, Noul, Score, RetryPolicy

INDEX = "https://docs.hanzo.ai/llms.txt"
CACHE = Path(tempfile.gettempdir()) / "kai-cookbook" / "docs-llms.txt"

# Each question with the one page that answers it.
QUERIES = [
    ("My key leaked. How do I revoke it and get a new one?", "/docs/api-keys"),
    ("Which package do I install for a Next.js app?", "/docs/sdks/typescript"),
    ("How do I check that a webhook request really came from you?", "/docs/webhooks"),
    ("Can I run the whole cloud on my own machines?", "/docs/network"),
    ("I am moving off Pinecone. What replaces my vector index?", "/docs/guides/migrate/pinecone"),
    ("What does a request cost per token?", "/docs/pricing"),
    ("We raised a seed round. Can we get free credits?", "/docs/startups"),
    ("Point LangGraph at your API", "/docs/guides/integrations/langgraph"),
    ("Where is the list of every error code and its HTTP status?", "/docs/errors"),
    ("Use Hanzo inside Excel and Word", "/docs/apps/office"),
    ("Earn money when people deploy my open-source template", "/docs/templates/kickbacks"),
    ("Run Hanzo Dev without the TUI in a CI job", "/docs/dev/usage/exec"),
]
LEVELS = ["unrelated", "on the topic, but does not answer it", "partly answers it", "answers it"]


def pages():
    """Every guide page in the docs index, path to 'title: description'; the per-operation API pages are left out."""
    if not CACHE.exists():
        CACHE.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(INDEX, CACHE)
    out, operations = {}, True
    for line in CACHE.read_text().splitlines():
        if line.startswith("## "):
            operations = line.startswith(("## API reference", "## CLI", "## MCP"))
        found = re.match(r"- \[([^\]]+)\]\((/docs[^)]*)\): (.+)", line)
        if found and not operations:
            out[found[2]] = f"{found[1]}: {found[3]}"
    return out


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def shortlist(query, docs, k=20):
    """The k pages BM25 ranks highest for the query: the incoming order."""
    bags = {path: collections.Counter(words(path + " " + text)) for path, text in docs.items()}
    df = collections.Counter(w for bag in bags.values() for w in bag)
    n, mean = len(bags), sum(sum(b.values()) for b in bags.values()) / len(bags)

    def bm25(bag):
        size = sum(bag.values())
        return sum(
            math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5)) * bag[w] * 2.2 / (bag[w] + 1.2 * (0.25 + 0.75 * size / mean))
            for w in set(words(query))
            if w in bag
        )

    return sorted(bags, key=lambda path: bm25(bags[path]), reverse=True)[:k]


def rank(order, gold):
    return order.index(gold) + 1 if gold in order else None


docs = pages()
ranks = {"incoming": [], "relevance nouls": [], "score questions": []}
with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    for query, gold in QUERIES:
        candidates = shortlist(query, docs)
        nouls = {
            f"c{i}": Noul(instructions={"passage": docs[path], "question": "Does `passage` help answer `query`?"})
            for i, path in enumerate(candidates)
        }
        scores = {
            f"c{i}": Score(instructions={"page": docs[path], "question": "How well does `page` answer `query`?"}, criteria=LEVELS)
            for i, path in enumerate(candidates)
        }
        by_noul = kai.decide({"query": query}, nouls).nouls
        by_score = kai.decide({"query": query}, scores).scores
        noul_order = sorted(candidates, key=lambda p: -by_noul[f"c{candidates.index(p)}"].noul)
        score_order = sorted(candidates, key=lambda p: -by_score[f"c{candidates.index(p)}"].score)
        ranks["incoming"].append(rank(candidates, gold))
        ranks["relevance nouls"].append(rank(noul_order, gold))
        ranks["score questions"].append(rank(score_order, gold))
        print(f"{query[:58]:58} incoming {ranks['incoming'][-1]}  nouls {ranks['relevance nouls'][-1]}  scores {ranks['score questions'][-1]}")
        print(f"{'':58} nouls' first: {noul_order[0]}")

print(f"\n{len(docs)} pages, a shortlist of 20 per question; rank of the page that answers (None: not shortlisted)")
print(f"{'order':16} {'first':>6} {'top 3':>6} {'MRR':>6}")
for name, found in ranks.items():
    first = sum(r == 1 for r in found)
    three = sum(r is not None and r <= 3 for r in found)
    mrr = sum(1 / r for r in found if r) / len(found)
    print(f"{name:16} {first:>6} {three:>6} {mrr:>6.3f}")
