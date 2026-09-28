from hanzo_kai import Choice, ChoiceAnswer, Decision, Kai, Noul, NoulAnswer


class Triage(Decision):
    team: ChoiceAnswer
    refund: NoulAnswer


with Kai() as kai:
    t = kai.decide(
        state={"ticket": "I was charged twice for my March invoice. Please refund the duplicate."},
        questions={
            "team": Choice(
                instructions="Which team should handle `ticket`?",
                criteria={"billing": "charges, invoices, refunds", "tech": "bugs and outages"},
            ),
            "refund": Noul(
                instructions="The customer asks for money back.",
                criteria={"true": "the ticket asks for a refund", "false": "the ticket asks for something else"},
            ),
        },
        response_model=Triage,
        extra_body={"session_id": "ticket-4411", "user": "agent-7"},
    )

print(type(t).__name__, t.team.choice, t.refund.noul)
print(t.team == t.answers["team"], sorted(t.answers))
