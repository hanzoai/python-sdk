"""Report a fine label when Kai is sure of it, its parent group when only the group is clear, else review."""

import gzip
import json
import random
import pathlib
import tempfile
import urllib.request
from collections import Counter

from hanzo_kai import Kai, RetryPolicy

HARNESS = "https://raw.githubusercontent.com/hanzoai/benchmarks/039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz"

# Banking77's 77 intents in nine groups of our own, each group's labels separated by semicolons
GROUPS = {
    "card": (
        "activate my card; card about to expire; card arrival; card delivery estimate; card linking; "
        "disposable card limits; get disposable virtual card; get physical card; getting spare card; "
        "getting virtual card; order physical card; visa or mastercard"
    ),
    "broken card": (
        "card acceptance; card not working; card swallowed; contactless not working; "
        "declined card payment; virtual card not working"
    ),
    "security": (
        "change pin; compromised card; lost or stolen card; lost or stolen phone; passcode forgotten; pin blocked"
    ),
    "payment": (
        "Refund not showing up; apple pay or google pay; card payment fee charged; "
        "card payment not recognised; direct debit payment not recognised; extra charge on statement; "
        "pending card payment; request refund; reverted card payment?; transaction charged twice"
    ),
    "cash": (
        "atm support; cash withdrawal charge; cash withdrawal not recognised; declined cash withdrawal; "
        "pending cash withdrawal; wrong amount of cash received; wrong exchange rate for cash withdrawal"
    ),
    "transfer": (
        "balance not updated after bank transfer; beneficiary not allowed; cancel transfer; "
        "declined transfer; failed transfer; pending transfer; receiving money; transfer fee charged; "
        "transfer into account; transfer not received by recipient; transfer timing"
    ),
    "top up": (
        "automatic top up; balance not updated after cheque or cash deposit; pending top up; "
        "top up by bank transfer charge; top up by card charge; top up by cash or cheque; top up failed; "
        "top up limits; top up reverted; topping up by card; verify top up"
    ),
    "currency": (
        "card payment wrong exchange rate; exchange charge; exchange rate; exchange via app; "
        "fiat currency support; supported cards and currencies"
    ),
    "account": (
        "age limit; country support; edit personal details; terminate account; unable to verify identity; "
        "verify my identity; verify source of funds; why verify identity"
    ),
}
PARENT = {label: group for group, labels in GROUPS.items() for label in labels.split("; ")}


def harness(suite: str) -> list:
    """The pinned harness's cases for one suite, each [state, questions, gold]."""
    path = pathlib.Path(tempfile.gettempdir()) / "hanzo-kai-cookbook" / "states.json.gz"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(HARNESS, path)
    with gzip.open(path) as file:
        return json.load(file)[suite]


def place(answer, fine: float, coarse: float = 0.8) -> tuple[str, str | None]:
    """The level Kai can answer at, and the answer: a label, its group, or nothing for review."""
    if answer.confidence >= fine:
        return "label", answer.choice
    mass = Counter()
    for label, p in answer.probabilities.items():
        mass[PARENT[label]] += p
    group, p = mass.most_common(1)[0]
    return ("group", group) if p >= coarse else ("review", None)


cases = harness("jev.banking77_full")
if set(cases[0][1]["intent"]["criteria"]) != set(PARENT):
    raise SystemExit("GROUPS must cover every Banking77 label exactly once")
by_label = {}
for case in cases:
    by_label.setdefault(case[2]["intent"]["idx"], []).append(case)
rng = random.Random(7)
drawn = [case for idx in sorted(by_label) for case in rng.sample(by_label[idx], 6)]

rows = []
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for state, questions, gold in drawn:
        answer = kai.decide(state=state, questions=questions).choices["intent"]  # the harness's own question
        rows.append((state["message"], answer, list(questions["intent"]["criteria"])[gold["intent"]["idx"]]))

print(f"{len(rows)} messages, {len(by_label)} gold labels, {len(PARENT)} labels in {len(GROUPS)} groups\n")
print("label at    label: n  right   group: n  right   review    (group when its probability is at least 0.8)")
for fine in (0.0, 0.9, 0.99, 0.999, 0.9999):
    levels, right = Counter(), Counter()
    for _, answer, truth in rows:
        level, value = place(answer, fine)
        levels[level] += 1
        right[level] += value == (truth if level == "label" else PARENT[truth])
    print(
        f"{fine:8.4f}  {levels['label']:8} {right['label']:6}  {levels['group']:8} {right['group']:6}  {levels['review']:7}"
    )
grouped = sum(PARENT[answer.choice] == PARENT[truth] for _, answer, truth in rows)
print(f"the group of the top label, always: {grouped}/{len(rows)} right")

print(f"\n{'wrong label':40} {'gold':32} kai, confidence, same group")
for message, answer, truth in rows:
    if answer.choice != truth:
        same = "yes" if PARENT[answer.choice] == PARENT[truth] else "no"
        print(f"{message[:40]:40} {truth:32} {answer.choice}, {answer.confidence:.4f}, {same}")
