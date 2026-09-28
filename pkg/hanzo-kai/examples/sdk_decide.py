from hanzo_kai import Choice, Kai, Noul, Score

with Kai() as kai:
    d = kai.decide(
        state={"ticket": "I was charged twice for my March invoice. Please refund the duplicate.", "plan": "pro"},
        questions={
            "team": Choice(
                instructions="Which team should handle `ticket`?",
                criteria={
                    "billing": "charges, invoices, refunds",
                    "tech": "bugs and outages",
                    "sales": "plans and upgrades",
                },
            ),
            "refund": Noul(
                instructions="The customer asks for money back.",
                criteria={"true": "the ticket asks for a refund", "false": "the ticket asks for something else"},
            ),
            "urgency": Score(
                instructions="How soon does `ticket` need an answer?",
                criteria=["this month", "this week", "today"],
            ),
        },
    )

team, refund, urgency = d.choices["team"], d.nouls["refund"], d.scores["urgency"]
print(team.choice, team.confidence, team.probabilities)
print(refund.noul, refund.answer_confidence)
print(urgency.score, urgency.confidence, urgency.probabilities, urgency.legend[2])
print(d.model, d.usage.input_tokens, d.usage.output_tokens, d.routing["checkpoint"])
print(d.raw_http_response.status_code, d.request_id)
