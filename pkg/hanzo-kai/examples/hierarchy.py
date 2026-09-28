"""Classify down a label tree: pick the likely scenarios, then an intent inside each, and keep the best path."""

import gzip
import json
import random
import pathlib
import tempfile
import urllib.request

from hanzo_kai import Kai, Choice, RetryPolicy

HARNESS = "https://raw.githubusercontent.com/hanzoai/benchmarks/039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz"
WIDTH = 2  # scenarios kept after the first level


def harness(suite: str) -> list:
    """The pinned harness's cases for one suite, each [state, questions, gold]."""
    path = pathlib.Path(tempfile.gettempdir()) / "hanzo-kai-cookbook" / "states.json.gz"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(HARNESS, path)
    with gzip.open(path) as file:
        return json.load(file)[suite]


def top(intent: str) -> str:
    """The scenario an intent sits under: MASSIVE names an intent scenario_action."""
    return intent.split("_")[0]


cases = harness("massive.en")
DESCRIBE = {}  # every intent any case offers, with the harness's description
for _, questions, _ in cases:
    DESCRIBE.update(questions["intent"]["criteria"])
TREE = {}  # scenario -> its intents
for intent in sorted(DESCRIBE):
    TREE.setdefault(top(intent), []).append(intent)

ASK = "What is the user asking for in `utterance`?"
SCENARIO = Choice(
    instructions="Which part of a voice assistant is `utterance` for?",
    criteria={scenario: ", ".join(DESCRIBE[i] for i in intents) for scenario, intents in TREE.items()},
)
INTENT = {
    s: Choice(instructions=ASK, criteria={i: DESCRIBE[i] for i in intents})
    for s, intents in TREE.items()
    if len(intents) > 1
}
FLAT = Choice(instructions=ASK, criteria=DESCRIBE)


def classify(kai: Kai, state: dict) -> tuple[str, str, list[str], int]:
    """The flat answer, the tree's answer, the scenarios kept, and how many second-level questions it took."""
    first = kai.decide(state=state, questions={"scenario": SCENARIO, "flat": FLAT}).choices
    beam = sorted(first["scenario"].probabilities.items(), key=lambda kv: -kv[1])[:WIDTH]
    asks = {scenario: INTENT[scenario] for scenario, _ in beam if scenario in INTENT}
    second = kai.decide(state=state, questions=asks).choices if asks else {}
    paths = [
        (p * (second[scenario].probabilities[intent] if scenario in second else 1.0), intent)
        for scenario, p in beam
        for intent in TREE[scenario]
    ]
    return first["flat"].choice, max(paths)[1], [scenario for scenario, _ in beam], len(asks)


score = {"flat": [0, 0], "tree": [0, 0]}
kept = asked = 0
misses = []
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for state, questions, gold in random.Random(7).sample(cases, 50):
        truth = list(questions["intent"]["criteria"])[gold["intent"]["idx"]]
        flat, tree, beam, n = classify(kai, state)
        asked += n
        kept += top(truth) in beam
        for name, answer in (("flat", flat), ("tree", tree)):
            score[name][0] += top(answer) == top(truth)
            score[name][1] += answer == truth
        if flat != truth or tree != truth:
            misses.append(f"{state['utterance'][:40]:40} {truth:20} {flat:20} {tree}")

print(f"{len(DESCRIBE)} intents under {len(TREE)} scenarios; 50 utterances\n")
print(f"{'':30} scenario  intent")
print(f"{f'flat: one choice of {len(DESCRIBE)}':30} {score['flat'][0]:5}/50  {score['flat'][1]:3}/50")
print(f"{f'tree: beam of {WIDTH} scenarios':30} {score['tree'][0]:5}/50  {score['tree'][1]:3}/50")
print(f"\ngold scenario inside the beam: {kept}/50; second-level questions asked: {asked}\n")
print(f"{'utterance':40} {'gold':20} {'flat':20} tree")
print("\n".join(misses))
