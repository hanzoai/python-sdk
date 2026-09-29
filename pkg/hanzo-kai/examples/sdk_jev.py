from hanzo_kai.jev import APIError, Choice, Noul, Score, Client as TypeSafeClient

QUESTIONS = {
    "team": Choice(instructions="Which team should handle this?", criteria={"billing": None, "tech": None}),
    "refund": Noul(
        instructions="The customer asks for money back.",
        criteria={"true": "the ticket asks for a refund", "false": "the ticket asks for something else"},
    ),
    "urgency": Score(instructions="How soon does it need an answer?", criteria=["this month", "this week", "today"]),
}

with TypeSafeClient() as client:
    for model in ("kai", "jev-latest"):
        try:
            result = client.system_one("I was charged twice for my March invoice. Please refund the duplicate.", QUESTIONS, model=model)
            print(model, "->", result.model, result.choices["team"].choice, result.nouls["refund"].noul, result.usage)
        except APIError as error:
            print(model, "->", type(error).__name__, error.status, error.message)
    print(client.models.list())
