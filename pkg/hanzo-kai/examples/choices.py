"""Give a moderation choice a third outcome, uncertain, set by confidence rather than by a label."""

import gzip
import json
import random
import pathlib
import tempfile
import urllib.request

from hanzo_kai import Kai, Noul, Choice, RetryPolicy

HARNESS = "https://raw.githubusercontent.com/hanzoai/benchmarks/039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz"
ASK = "Is `post` toxic: rude, disrespectful or likely to make someone leave the discussion?"  # the harness's words
YESNO = {"yes": "it is toxic", "no": "it is not toxic"}
QUESTIONS = {
    "moderate": Choice(instructions=ASK, criteria=YESNO),
    "unsure": Choice(instructions=ASK, criteria=YESNO | {"unsure": "it could be read either way"}),
    "noul": Noul(instructions=ASK),
    "labels": Choice(
        instructions="How should a moderator label `post`?",
        criteria={
            "acceptable": "polite, neutral or merely blunt",
            "toxic": "rude, disrespectful or likely to make someone leave the discussion",
        },
    ),
}


def harness(suite: str) -> list:
    """The pinned harness's cases for one suite, each [state, questions, gold]."""
    path = pathlib.Path(tempfile.gettempdir()) / "hanzo-kai-cookbook" / "states.json.gz"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(HARNESS, path)
    with gzip.open(path) as file:
        return json.load(file)[suite]


def outcome(yes: float, confidence: float, threshold: float) -> str:
    """remove or keep when the confidence clears the threshold, else uncertain."""
    if confidence < threshold:
        return "uncertain"
    return "remove" if yes >= 0.5 else "keep"


def share(part: int, whole: int) -> str:
    """part/whole with the rate, or a dash when whole is 0."""
    return f"{part:3}/{whole:<3}= {part / whole:.3f}" if whole else f"{part:3}/{whole:<3}  -"


rows = []
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for state, _, gold in random.Random(7).sample(harness("app.moderation_toxicity"), 80):
        answers = kai.decide(state=state, questions=QUESTIONS)
        rows.append((answers, gold["toxic"]["idx"] == 1))

print(f"{len(rows)} posts, {sum(toxic for _, toxic in rows)} toxic by gold\n")
print("the same question, three ways             agrees with gold")
ways = {
    "noul, P(yes) at 0.5": lambda a: a.nouls["noul"].noul >= 0.5,
    "choice yes/no": lambda a: a.choices["moderate"].choice == "yes",
    "choice acceptable/toxic": lambda a: a.choices["labels"].choice == "toxic",
}
for name, says in ways.items():
    print(f"{name:41} {share(sum(says(a) == toxic for a, toxic in rows), len(rows))}")

choice = [(a.choices["moderate"].probabilities["yes"], a.choices["moderate"].confidence, toxic) for a, toxic in rows]
noul = [(a.nouls["noul"].noul, abs(2 * a.nouls["noul"].noul - 1), toxic) for a, toxic in rows]
print("\nuncertain below a confidence   choice yes/no           noul, confidence |2p - 1|")
print("confidence at least        automated  agrees         automated  agrees")
for threshold in (0.0, 0.2, 0.4, 0.6, 0.8):
    cells = []
    for triples in (choice, noul):
        routes = [(outcome(yes, confidence, threshold), toxic) for yes, confidence, toxic in triples]
        acted = [(route == "remove") == toxic for route, toxic in routes if route != "uncertain"]
        cells.append(f"{len(acted):5}/{len(rows)}  {share(sum(acted), len(acted))}")
    print(f"{threshold:19.1f}  {cells[0]}  {cells[1]}")

picked = [(a.choices["unsure"].choice, toxic) for a, toxic in rows if a.choices["unsure"].choice != "unsure"]
agree = sum((label == "yes") == toxic for label, toxic in picked)
print(
    f"\n`unsure` as a third label: chosen {len(rows) - len(picked)} times; the rest agree with gold {share(agree, len(picked))}"
)
