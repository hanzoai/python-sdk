"""Twelve questions about one support ticket: asked in one call, then in twelve calls of one.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

from hanzo_kai import Kai, Choice, Noul, Score, RetryPolicy

TICKET = {
    "subject": "Deploys to production failing since 09:10 UTC",
    "body": (
        "Every deploy of our api to production has failed since 09:10 UTC with 'image pull backoff'. "
        "Staging deploys still work. We launch on Friday and the whole team is blocked. "
        "If this is on your side, we expect the build minutes refunded."
    ),
    "plan": "team",
}

QUESTIONS = {
    "team": Choice(
        instructions="Which team should handle `body`?",
        criteria={
            "billing": "charges, invoices and refunds",
            "platform": "deploys, builds and clusters",
            "account": "logins, keys and members",
            "sales": "plans, pricing and upgrades",
        },
    ),
    "intent": Choice(
        instructions="What does the sender want?",
        criteria={
            "fix": "something broken made to work",
            "howto": "to learn how to do something",
            "feature": "a capability that does not exist yet",
            "cancel": "to stop using the service",
        },
    ),
    "environment": Choice(
        instructions="Which environment is failing?",
        criteria={"production": "production only", "staging": "staging only", "both": "production and staging"},
    ),
    "language": Choice(instructions="Which language is `body` written in?", criteria=["english", "spanish", "german", "french"]),
    "refund": Noul(
        instructions="The sender asks for money back.",
        criteria={"true": "a refund or credit is requested", "false": "no refund or credit is requested"},
    ),
    "outage": Noul(
        instructions="The sender reports something that does not work.",
        criteria={"true": "a service or feature is failing", "false": "everything works"},
    ),
    "blocked": Noul(
        instructions="The sender's work is blocked.",
        criteria={"true": "they cannot proceed until this is fixed", "false": "they can keep working"},
    ),
    "human": Noul(
        instructions="A person should reply, not a template.",
        criteria={"true": "the case needs judgment or an apology", "false": "a standard answer covers it"},
    ),
    "urgency": Score(instructions="How urgent is `body`?", criteria=["can wait", "this week", "today", "now"]),
    "sentiment": Score(instructions="How does the sender feel?", criteria=["angry", "frustrated", "neutral", "pleased"]),
    "churn": Score(instructions="How likely is the sender to leave?", criteria=["unlikely", "possible", "likely"]),
    "severity": Score(
        instructions="How severe is the problem?",
        criteria=["cosmetic", "degraded", "broken for some users", "broken for everyone"],
    ),
}


def top(answer):
    """An answer's most probable label or level, and its probability."""
    if answer.type == "noul":
        return ("true" if answer.noul >= 0.5 else "false"), max(answer.noul, 1 - answer.noul)
    best = max(answer.probabilities, key=answer.probabilities.get)
    label = answer.legend[best] if answer.type == "score" else best
    return label, answer.probabilities[best]


def distribution(answer):
    """Every probability an answer carries, in order."""
    if answer.type == "noul":
        return [answer.noul]
    return list(answer.probabilities.values())


with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    batched = kai.decide(TICKET, QUESTIONS)
    single = {name: kai.decide(TICKET, {name: question}) for name, question in QUESTIONS.items()}

print(f"{'question':12} {'one call':>28} {'one call each':>28}")
gap = 0.0
for name in QUESTIONS:
    (a, p), (b, q) = top(batched.answers[name]), top(single[name].answers[name])
    print(f"{name:12} {a:>22} {p:.3f} {b:>22} {q:.3f}")
    pairs = zip(distribution(batched.answers[name]), distribution(single[name].answers[name]))
    gap = max([gap, *(abs(x - y) for x, y in pairs)])

once = batched.usage.input_tokens
each = sum(d.usage.input_tokens for d in single.values())
print()
print(f"calls                          1  against  {len(single)}")
print(f"billed input tokens    {once:>9}  against  {each}")
print(f"largest probability gap between the two ways: {gap:.6f}")
