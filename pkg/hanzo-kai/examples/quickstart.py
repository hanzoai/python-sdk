from hanzo_kai import Kai, Score, Choice

with Kai() as kai:
    d = kai.decide(
        state={
            "message": "My new card arrived yesterday but the app will not activate it. It says the code is invalid, and I fly on Friday."
        },
        questions={
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
        },
    )

intent, urgency = d.choices["intent"], d.scores["urgency"]
print(intent.choice, intent.confidence)
print(urgency.score, urgency.confidence, urgency.probabilities)
print(d.usage.input_tokens, d.routing["checkpoint"])
