"""Dependent questions over /v1/decisions: ask the parent, pick the child question by its answer, and pass that answer on as a fact."""

from hanzo_kai import Choice, Kai, RetryPolicy

TEAM = Choice(
    instructions="Which team should handle this ticket?",
    criteria={
        "billing": "charges, invoices, payments and refunds",
        "technical": "errors, outages, slowness and integrations",
        "account": "sign-in, users and permissions",
    },
)
ISSUE = {
    "billing": Choice(
        instructions="What is the billing issue?",
        criteria={
            "double_charge": "the customer was charged twice",
            "declined": "a payment or renewal was declined",
            "invoice_copy": "the customer needs a copy or a corrected invoice",
            "refund": "the customer wants money back",
            "plan_change": "the customer wants a different plan",
        },
    ),
    "technical": Choice(
        instructions="What is the technical issue?",
        criteria={
            "bug": "a feature behaves wrongly",
            "outage": "the service is down",
            "slow": "something is slow or times out",
            "integration": "a connection to another system fails",
            "howto": "the customer asks how to do something",
        },
    ),
    "account": Choice(
        instructions="What is the account issue?",
        criteria={
            "login": "the customer cannot sign in",
            "invite": "adding or removing users",
            "role": "changing what a user may do",
            "sso": "single sign-on setup",
            "delete": "closing the account",
        },
    ),
}
THRESHOLD = 0.5
TICKETS = [
    "I was charged twice for the March invoice.",
    "Our card was declined when we tried to renew the annual plan.",
    "The export to CSV times out after 30 seconds.",
    "Please send a copy of last month's invoice with our VAT number on it.",
    "New hires can't log in with Okta since this morning.",
]


def fact(question: Choice, label: str) -> dict:
    """A parent's answer as the native scheduler states it to a child: type, question, and the chosen option's text."""
    return {"type": "choice", "question": question.instructions, "answer": f"{label}: {question.criteria[label]}"}


with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for ticket in TICKETS:
        state = {"ticket": ticket}
        team = kai.decide(state=state, questions={"team": TEAM}).choices["team"]
        print(f"{ticket}\n  team   {team.choice} p={team.answer_confidence}")
        if team.answer_confidence < THRESHOLD:
            print("  stop: the team is under its threshold; a person routes this one")
            continue
        child = {"issue": ISSUE[team.choice]}
        told = kai.decide(state={"facts": {"team": fact(TEAM, team.choice)}, **state}, questions=child).choices["issue"]
        blind = kai.decide(state=state, questions=child).choices["issue"]
        print(f"  issue  {told.choice} p={told.answer_confidence} with the fact; {blind.choice} p={blind.answer_confidence} without")
