"""Rebuild the structure of a README that lost its markdown: which lines join, and what each block is.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

import tempfile
import textwrap
import urllib.request
from pathlib import Path

from hanzo_kai import Kai, Choice, RetryPolicy

README = "https://raw.githubusercontent.com/hanzoai/base/4506925bff6d89aafbf7433bc0abec0d6131865e/README.md"
CACHE = Path(tempfile.gettempdir()) / "kai-cookbook" / "base-README.md"
WIDTH = 64
JOIN = {
    "same": "`next` continues the block `line` is in: the same sentence, paragraph, list item or code",
    "new": "`next` starts a new heading, paragraph, list item or code block",
}
KINDS = {
    "heading": "a section title: a few words, no sentence",
    "paragraph": "prose: one or more full sentences",
    "list": "one item of a bulleted list",
    "code": "source code, shell commands or program output",
}


def blocks(markdown):
    """The README as (kind, text) blocks; tables and HTML are dropped."""
    out, rows, i = [], markdown.splitlines(), 0
    while i < len(rows):
        row = rows[i]
        if row.startswith("```"):
            end = rows.index("```", i + 1) if "```" in rows[i + 1 :] else len(rows)
            out.append(("code", "\n".join(rows[i + 1 : end])))
            i = end + 1
            continue
        if row.startswith("#"):
            out.append(("heading", row.lstrip("# ")))
        elif row.startswith("- "):
            item = [row[2:]]
            while i + 1 < len(rows) and rows[i + 1].startswith("  "):
                i += 1
                item.append(rows[i].strip())
            out.append(("list", " ".join(item)))
        elif row.strip() and not row.startswith(("<", "|")):
            text = [row]
            while i + 1 < len(rows) and rows[i + 1].strip() and not rows[i + 1].startswith(("```", "#", "- ", "|")):
                i += 1
                text.append(rows[i])
            out.append(("paragraph", " ".join(t.strip() for t in text)))
        i += 1
    return out


if not CACHE.exists():
    CACHE.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(README, CACHE)
original = blocks(CACHE.read_text())
# Flattened: no markers, no blank lines, prose wrapped at WIDTH, each line tagged with its block.
flat = [(k, line.strip()) for k, (kind, text) in enumerate(original)
        for line in (text.splitlines() if kind == "code" else textwrap.wrap(text, WIDTH)) if line.strip()]
pairs = list(zip(flat, flat[1:]))
truth = [a[0] == b[0] for a, b in pairs]

with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    joins = []
    for start in range(0, len(pairs), 50):
        questions = {
            f"b{i}": Choice(
                instructions={"line": a[1], "next": b[1], "question": "Does `next` continue the block that `line` is in?"},
                criteria=JOIN,
            )
            for i, (a, b) in enumerate(pairs[start : start + 50], start)
        }
        d = kai.decide({"source": f"a README whose markdown markers and blank lines were lost, wrapped at {WIDTH} characters"}, questions)
        joins += [d.choices[f"b{i}"].choice == "same" for i in range(start, start + len(questions))]
    kinds = kai.decide(
        {"source": "blocks of a README whose markdown markers were lost"},
        {f"k{i}": Choice(instructions={"block": text[:300], "question": "What kind of block is `block`?"}, criteria=KINDS)
         for i, (kind, text) in enumerate(original)},
    )

width = [len(a[1]) >= WIDTH - 12 for a, _ in pairs]
breaks = len(truth) - sum(truth)
print(f"{len(original)} blocks flattened to {len(flat)} lines: {len(pairs)} boundaries, {sum(truth)} inside a block, {breaks} between blocks")
print(f"{'':38} {'right':>6} {'breaks found':>13} {'false breaks':>13}")
for name, guess in (("Kai, one choice per boundary", joins), ("code: a line near full width joins", width)):
    found = sum(not g and not t for g, t in zip(guess, truth))
    false = sum(not g and t for g, t in zip(guess, truth))
    print(f"{name:38} {sum(g == t for g, t in zip(guess, truth)):>6} {f'{found} of {breaks}':>13} {false:>13}")

said = [kinds.choices[f"k{i}"].choice for i in range(len(original))]
print(f"\nwhat each block is: Kai right on {sum(s == k for s, (k, _) in zip(said, original))} of {len(original)}")
for kind in KINDS:
    got = [s for s, (k, _) in zip(said, original) if k == kind]
    print(f"    {kind:10} {len(got):>3} blocks, Kai said: " + ", ".join(f"{n} {got.count(n)}" for n in KINDS if got.count(n)))
