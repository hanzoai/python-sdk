"""Act on a yes/no answer only near 0 or 1; send the middle band to review, with the probability on the record."""

import gzip
import json
import random
import pathlib
import tempfile
import urllib.request

from hanzo_kai import Kai, RetryPolicy, UnprocessableEntityError

HARNESS = "https://raw.githubusercontent.com/hanzoai/benchmarks/039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz"
SUITE, NAME = "app.phishing", "is_phishing"


def harness(suite: str) -> list:
    """The pinned harness's cases for one suite, each [state, questions, gold]."""
    path = pathlib.Path(tempfile.gettempdir()) / "hanzo-kai-cookbook" / "states.json.gz"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(HARNESS, path)
    with gzip.open(path) as file:
        return json.load(file)[suite]


def ask(kai: Kai, email: str, questions: dict) -> float:
    """P(phishing) for an email; one the API refuses as longer than Kai reads is halved until it fits."""
    while True:
        try:
            return kai.decide(state={"email": email}, questions=questions).nouls[NAME].noul
        except UnprocessableEntityError as error:
            if error.code != "state_too_long":
                raise
            email = email[: len(email) // 2]


def route(p: float, low: float, high: float) -> str:
    """Where an email goes: automatic at either end of the band, a person in between."""
    return "phishing" if p >= high else "legitimate" if p <= low else "review"


cases = harness(SUITE)
records = []
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for index in sorted(random.Random(7).sample(range(len(cases)), 80)):
        state, questions, gold = cases[index]
        p = ask(kai, state["email"], questions)  # the harness's own question
        records.append({"case": index, "p": p, "route": route(p, 0.1, 0.9), "gold": gold[NAME]["idx"] == 1})

print(f"{len(records)} emails, {sum(r['gold'] for r in records)} phishing by gold\n")
print("P(phishing)    emails  phishing by gold")
for low, high in [(0, 0.05), (0.05, 0.2), (0.2, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 1.01)]:
    band = [r for r in records if low <= r["p"] < high]
    print(f"[{low:.2f}, {min(high, 1):.2f}{')' if high < 1 else ']'}  {len(band):6}  {sum(r['gold'] for r in band):16}")

print("\nreview band    automated  right among automated")
for low, high in [(0.5, 0.5), (0.2, 0.8), (0.1, 0.9), (0.05, 0.95), (0.01, 0.99)]:
    auto = [r for r in records if route(r["p"], low, high) != "review"]
    right = sum((route(r["p"], low, high) == "phishing") == r["gold"] for r in auto)
    band = "none" if low == high else f"({low}, {high})"
    print(f"{band:13} {len(auto):4}/{len(records)}  {right:4}/{len(auto)} = {right / len(auto):.3f}")

print("\nrecords at (0.1, 0.9) that are wrong or held for review:")
for r in records:
    if r["route"] == "review" or (r["route"] == "phishing") != r["gold"]:
        print({**r, "p": round(r["p"], 4)})
