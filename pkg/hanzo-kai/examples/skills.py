"""Pick at most one skill from the Hanzo skills catalog for an agent's turn: shortlist, then re-check.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

import collections
import math
import re
import tempfile
import urllib.request
from pathlib import Path

from hanzo_kai import Kai, Choice, Noul, RetryPolicy

INDEX = "https://hanzoskills.com/llms.txt"
CACHE = Path(tempfile.gettempdir()) / "kai-cookbook" / "skills-llms.txt"

# Each agent turn with the skills a person would load for it; empty when no skill fits.
TURNS = [
    ("The payment API throws 500s in prod. Set up error tracking so we see stack traces.", {"hanzo-sentry"}),
    ("Store our Stripe live key so only the billing service can read it.", {"hanzo-kms"}),
    ("Add similarity search over our product embeddings.", {"hanzo-vector", "hanzo-vector-go", "hanzo-datastore"}),
    ("Write a browser check that the signup page loads and the form submits.", {"webapp-testing"}),
    ("Move our Rails backend onto Go and the Hanzo stack.", {"app-port", "hanzo-base"}),
    ("Keep wallet balances in a double-entry ledger.", {"hanzo-ledger", "hanzo-treasury"}),
    ("Make an animated GIF for the release announcement in Slack.", {"slack-gif-creator"}),
    ("Send the contractor agreement out for electronic signature.", {"hanzo-sign"}),
    ("Build an MCP server that exposes our ticket database to agents.", {"mcp-builder", "hanzo-mcp"}),
    ("thanks, that fixed it", set()),
    ("What time is it in Tokyo right now?", set()),
    ("good morning!", set()),
]


def catalog():
    """The Hanzo skills and the core skills from the published index: name to description."""
    if not CACHE.exists():
        CACHE.parent.mkdir(exist_ok=True)
        request = urllib.request.Request(INDEX, headers={"User-Agent": "kai-cookbook"})
        CACHE.write_bytes(urllib.request.urlopen(request).read())
    out, section = {}, ""
    for line in CACHE.read_text().splitlines():
        if line.startswith("#"):
            section = line.lstrip("#").strip()
        found = re.match(r"- \[([^\]]+)\]\(https://hanzoskills\.com/[^)]+\): (.+)", line)
        if found and section in ("hanzo", "core"):
            out[found[1]] = found[2]
    return out


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def lexical(turn, skills, k=5):
    """The k skills BM25 ranks highest for the turn, over name and description."""
    bags = {name: collections.Counter(words(name.replace("-", " ") + " " + text)) for name, text in skills.items()}
    df = collections.Counter(w for bag in bags.values() for w in bag)
    n, mean = len(bags), sum(sum(b.values()) for b in bags.values()) / len(bags)

    def bm25(bag):
        size = sum(bag.values())
        return sum(
            math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5)) * bag[w] * 2.2 / (bag[w] + 1.2 * (0.25 + 0.75 * size / mean))
            for w in set(words(turn))
            if w in bag
        )

    return sorted(bags, key=lambda name: bm25(bags[name]), reverse=True)[:k]


def pick(shortlist, relevance, threshold):
    """The shortlisted skill the re-check rates highest, or None when none clears the threshold."""
    best = max(shortlist, key=relevance.get)
    return best if relevance[best] >= threshold else None


skills = catalog()
choose = Choice(instructions="Which skill does this task need?", criteria={name: text[:200] for name, text in skills.items()})
rows = []
with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    for turn, gold in TURNS:
        ranked = kai.decide({"task": turn}, {"skill": choose}).choices["skill"].probabilities
        by_kai = sorted(ranked, key=ranked.get, reverse=True)
        by_words = lexical(turn, skills)
        both = list(dict.fromkeys(by_kai[:5] + by_words))
        check = {
            f"s{i}": Noul(instructions={"passage": f"{name}: {skills[name]}", "question": "Does `passage` help answer `query`?"})
            for i, name in enumerate(both)
        }
        answers = kai.decide({"query": turn}, check).nouls
        relevance = {name: answers[f"s{i}"].noul for i, name in enumerate(both)}
        rows.append((gold, by_kai, by_words, relevance))
        where = min((by_kai.index(g) + 1 for g in gold), default="-")
        print(f"{turn[:64]:64} gold: {', '.join(sorted(gold)) or 'none'}")
        print(f"    Kai's choice over {len(skills)}: gold ranked {where}; first {by_kai[0]}")
        print(f"    BM25 top 5: {', '.join(by_words)}")
        print("    re-check, highest: " + ", ".join(f"{n} {p:.2f}" for n, p in sorted(relevance.items(), key=lambda kv: -kv[1])[:3]))

fits = [r for r in rows if r[0]]
print(f"\ngold in the top 5, of {len(fits)} turns a skill fits: Kai's choice {sum(bool(r[0] & set(r[1][:5])) for r in fits)}, BM25 {sum(bool(r[0] & set(r[2])) for r in fits)}")
print(f"right, of {len(rows)} turns (no skill is right when none fits):")
print(f"    Kai's choice alone, first skill: {sum(r[1][0] in r[0] for r in rows)}")
print(f"    BM25 alone, first skill: {sum(r[2][0] in r[0] for r in rows)}")
for name, column in (("Kai's top 5, re-checked", 1), ("BM25 top 5, re-checked", 2)):
    right = [sum((pick(r[column][:5], r[3], t) in r[0]) if r[0] else pick(r[column][:5], r[3], t) is None for r in rows) for t in (0.4, 0.5)]
    print(f"    {name}: {right[0]} keeping p >= 0.4, {right[1]} keeping p >= 0.5")
