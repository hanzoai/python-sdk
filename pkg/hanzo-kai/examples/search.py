"""Find the line of a docs page that answers a question, and whether the page answers it at all.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

import collections
import math
import re
import tempfile
import urllib.request
from pathlib import Path

from hanzo_kai import Kai, Choice, Noul, RetryPolicy

PAGE = (
    "https://raw.githubusercontent.com/hanzo-docs/docs/23a4eecc7544e46f9c2a74f278f58e640d4b0732"
    "/apps/docs/content/docs/credits.mdx"
)
CACHE = Path(tempfile.gettempdir()) / "kai-cookbook" / "credits.mdx"

# Each question with the page lines that answer it; an empty set when the page does not.
QUERIES = [
    ("Do I pay anything in a month when I send no requests?", {3}),
    ("Which address tells me what a unit costs before I spend it?", {6}),
    ("Is my balance a number someone keeps by hand?", {12}),
    ("How is an allowance different from my balance?", {15, 16, 18, 19}),
    ("Is there a monthly spending cliff?", {21}),
    ("Will the error tell me I am out of credit rather than that my key is bad?", {25}),
    ("Is listing my projects free?", {29}),
    ("What kinds of calls cost money?", {30}),
    ("How do I add a teammate to my org?", set()),
    ("Which regions can I run a sandbox in?", set()),
    ("How many requests per minute may one key send?", set()),
]


def lines(mdx):
    """The page's prose as lines: one per sentence, table row, heading or list item; code dropped."""
    body = re.sub(r"^---\n.*?\n---\n|```.*?```|</?Callout>", "", mdx, flags=re.S)
    out = []
    for block in re.split(r"\n\s*\n", body.strip()):
        rows = block.strip().splitlines()
        if rows[0].startswith("|"):
            out += [" ".join(cell.strip() for cell in row.strip("|").split("|")) for row in rows[2:]]
        elif rows[0].startswith("#"):
            out.append(rows[0].lstrip("# "))
        else:
            for item in re.split(r"\n(?=- |\d+\. )", block.strip()):
                out += re.split(r"(?<=\.)\s+(?=[A-Z])", " ".join(re.sub(r"^(- |\d+\. )", "", item).split()))
    plain = [re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line).replace("**", "").strip() for line in out]
    return {f"L{n:02d}": line for n, line in enumerate(filter(None, plain), 1)}


if not CACHE.exists():
    CACHE.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(PAGE, CACHE)
page = lines(CACHE.read_text())
document = "\n".join(f"{key} {line}" for key, line in page.items())
answered = Noul(
    instructions="`document` answers `query`.",
    criteria={"true": "a line of the document gives the answer", "false": "the document does not cover it"},
)
pick = Choice(instructions="Which line of `document` answers `query`?", criteria=page)
per_line = {key: Noul(instructions={"line": line, "question": "Does `line` help answer `query`?"}) for key, line in page.items()}


def keywords(query, page):
    """Each line's BM25 score for the query: plain keyword search over the page."""
    bags = {key: collections.Counter(re.findall(r"[a-z0-9]+", line.lower())) for key, line in page.items()}
    df = collections.Counter(w for bag in bags.values() for w in bag)
    n, mean = len(bags), sum(sum(b.values()) for b in bags.values()) / len(bags)
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    return {
        key: sum(math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5)) * bag[w] * 2.2 / (bag[w] + 1.2 * (0.25 + 0.75 * sum(bag.values()) / mean))
                 for w in terms if w in bag)
        for key, bag in bags.items()
    }


def rank(scores, gold):
    """The best rank any gold line reaches when lines are sorted by score."""
    order = sorted(scores, key=scores.get, reverse=True)
    return min(order.index(f"L{n:02d}") + 1 for n in gold)


hits = {"line nouls": [0, 0], "keywords": [0, 0], "one choice": [0, 0]}
with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    print(f"{len(page)} lines. For each question: the line nouls' best line, the keyword best line, the choice's best line.")
    for query, gold in QUERIES:
        nouls = kai.decide({"query": query}, per_line)
        whole = kai.decide({"query": query, "document": document}, {"line": pick, "answered": answered})
        by_noul = {key: a.noul for key, a in nouls.nouls.items()}
        by_words = keywords(query, page)
        by_choice = whole.choices["line"].probabilities
        best_noul, best_words, best_choice = (max(s, key=s.get) for s in (by_noul, by_words, by_choice))
        print(f"\n{query}")
        print(f"  gold {sorted(f'L{n:02d}' for n in gold) or 'none'}   the page answers it: p={whole.nouls['answered'].noul:.3f}")
        print(f"  line nouls: {best_noul} p={by_noul[best_noul]:.3f}   keywords: {best_words}   one choice: {best_choice} p={by_choice[best_choice]:.3f}")
        if gold:
            for name, scores in (("line nouls", by_noul), ("keywords", by_words), ("one choice", by_choice)):
                r = rank(scores, gold)
                hits[name][0] += r == 1
                hits[name][1] += r <= 3
        print(f"  nouls' line: {page[best_noul][:100]}")

answerable = sum(1 for _, gold in QUERIES if gold)
print()
for name, (first, three) in hits.items():
    print(f"{name:11} answer line first: {first} of {answerable}   in the top three: {three} of {answerable}")
