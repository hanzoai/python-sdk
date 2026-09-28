from hanzo_kai import Kai, Noul, Score, Choice

state = {
    "message": "My new card arrived yesterday but the app will not activate it. It says the code is invalid, and I fly on Friday."
}
questions = {
    "intent": Choice(
        instructions="What does `message` ask for?",
        criteria={
            "activate_card": "turn on a new card",
            "lost_card": "report a lost or stolen card",
            "refund": "money back for a payment",
            "transfer": "send or receive money",
            "other": "anything else",
        },
    ),
    "urgency": Score(
        instructions="How soon does `message` need an answer?",
        criteria=["routine: no deadline", "soon: a deadline this week", "urgent: blocked now or losing money"],
    ),
    "app_error": Noul(
        instructions="`message` reports an error in the app.",
        criteria={"true": "the app shows an error, crashes or refuses an action", "false": "the app works as expected"},
    ),
}

with Kai() as kai:
    together = kai.decide(state=state, questions=questions)
    apart = {name: kai.decide(state=state, questions={name: q}) for name, q in questions.items()}

for name in questions:
    same = together.answers[name] == apart[name].answers[name]
    print(f"{name:9} same answer together and apart: {same}   input_tokens apart: {apart[name].usage.input_tokens}")
print("input_tokens together:", together.usage.input_tokens)
print("input_tokens apart, summed:", sum(d.usage.input_tokens for d in apart.values()))
