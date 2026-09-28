"""The request rules, each tested once: what the server accepts and what it refuses, in its own words."""

from hanzo_kai import APIError, Choice, Kai, RetryPolicy, Score

STATE = "Refund my duplicate charge."
TEAM = Choice(instructions="Which team should take this?", criteria={"billing": "charges", "design": "themes"})
CASES = {
    "no instructions": {"want": Choice(criteria={"refund": "money back for a charge", "other": "something else"})},
    "100 questions": {f"q{i}": TEAM for i in range(100)},
    "101 questions": {f"q{i}": TEAM for i in range(101)},
    "a choice with one label": {"team": Choice(instructions="Which team?", criteria={"billing": "charges"})},
    "a choice with 1,000 labels": {"team": Choice(instructions="Which team?", criteria=[f"t{i}" for i in range(1000)])},
    "a score with 20 levels": {"urgency": Score(instructions="How urgent?", criteria=[f"level {i}" for i in range(20)])},
    "a null score level": {"urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["later", None, "now"]}},
}

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    for name, questions in CASES.items():
        try:
            d = kai.decide(state=STATE, questions=questions)
            widest = max(len(answer.probabilities) for answer in d.answers.values())
            print(f"{name:<27} accepted: {len(d.answers)} answers, the widest over {widest} options")
        except APIError as error:
            print(f"{name:<27} {error.status} {error.message}")
