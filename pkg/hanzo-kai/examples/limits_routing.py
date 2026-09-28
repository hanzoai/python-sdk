"""The routing suite's 1.000 covers the three labels its cases use; requests for the other three, asked the same way."""

import collections
import gzip
import json
import urllib.request

from hanzo_kai import Choice, Kai, RetryPolicy

HARNESS = ("https://raw.githubusercontent.com/hanzoai/benchmarks/"
           "039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz")
DOMAIN = Choice(
    instructions="What domain does `request` belong to?",
    criteria={
        "code": "software engineering, programming, refactoring, architecture, debugging",
        "math_or_logic": "mathematics, logic puzzles, proofs, complex calculation",
        "writing": "creative writing, essays, emails, blog posts, copywriting",
        "factual_lookup": "facts, definitions, trivia, history",
        "data_analysis": "statistics, SQL, data manipulation, metrics",
        "chitchat": "casual conversation, greetings, small talk",
    },
)
REQUESTS = [
    ("code", "Write a Python function that merges two sorted lists in linear time."),
    ("math_or_logic", "What is the probability of rolling at least one six in four throws of a die?"),
    ("factual_lookup", "Which river flows through Budapest?"),
    ("writing", "Draft a two-line thank-you note to a colleague who covered my shift."),
    ("data_analysis", "Write a SQL query for the median order value per month."),
    ("chitchat", "Good morning! How was your weekend?"),
]

with urllib.request.urlopen(HARNESS) as response:
    cases = json.loads(gzip.decompress(response.read()))["app.model_routing_domain"]
counts = collections.Counter(list(q["domain"]["criteria"])[g["domain"]["idx"]] for _, q, g in cases)
print(f"harness routing suite, {len(cases)} cases, by right answer: {dict(counts)}\n")

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    for want, request in REQUESTS:
        answer = kai.decide(state={"request": request}, questions={"domain": DOMAIN}).choices["domain"]
        mark = "right" if answer.choice == want else "wrong"
        print(f"{want:<15} -> {answer.choice:<15} {answer.probabilities[answer.choice]:.4f}  {mark}")
