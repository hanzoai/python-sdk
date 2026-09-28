"""Answers asked independently can break a rule between them: keep the most probable joint answer that holds every rule."""

import itertools
import math

from hanzo_kai import Choice, Kai, RetryPolicy

QUESTIONS = {
    "decision": Choice(
        instructions="How should this access request be handled?",
        criteria={
            "grant": "routine access the requester's role needs",
            "ask": "a manager should approve it first",
            "deny": "it should not be granted",
        },
    ),
    "production": Choice(
        instructions="Does the request give access to production systems or customer data?",
        criteria={"yes": "production systems or customer data", "no": "internal tools or documents only"},
    ),
    "reason": Choice(
        instructions="Does the request state a business reason?",
        criteria={"yes": "it says why the access is needed", "no": "it gives no reason"},
    ),
}
REQUESTS = [
    "Please add me to the #design Slack channel so I can follow the rebrand.",
    "Need read access to the production orders database to debug ticket 4411.",
    "Give me admin on the billing Stripe account.",
    "Add Jane to the analytics dashboard viewers; she joins the growth team Monday.",
]
RULES = [  # (if, then not): when the first answer holds, the second may not
    ({"production": "yes"}, {"decision": "grant"}),
    ({"reason": "no"}, {"decision": "grant"}),
]


def holds(x: dict[str, str], part: dict[str, str]) -> bool:
    return all(x[name] == label for name, label in part.items())


def words(part: dict[str, str]) -> str:
    return " and ".join(f"{name}={label}" for name, label in part.items())


def broken(x: dict[str, str]) -> list[str]:
    """The rules a joint answer breaks, in words."""
    return [f"{words(a)} rules out {words(b)}" for a, b in RULES if holds(x, a) and holds(x, b)]


def project(p: dict[str, dict[str, float]]) -> dict[str, str]:
    """The joint answer of highest probability, one label per question, that breaks no rule."""
    names = list(p)
    joint = (dict(zip(names, labels)) for labels in itertools.product(*(p[n] for n in names)))
    return max((x for x in joint if not broken(x)), key=lambda x: sum(math.log(max(p[n][x[n]], 1e-12)) for n in names))


with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for request in REQUESTS:
        d = kai.decide(state={"request": request}, questions=QUESTIONS)
        p = {name: answer.probabilities for name, answer in d.choices.items()}
        top = {name: answer.choice for name, answer in d.choices.items()}
        print(request)
        print("  answers   " + ", ".join(f"{n}={top[n]} ({p[n][top[n]]})" for n in top))
        if not broken(top):
            print("  keeps every rule")
            continue
        fixed = project(p)
        print(f"  breaks    {'; '.join(broken(top))}")
        print("  projected " + ", ".join(f"{n}={fixed[n]}" for n in fixed))
