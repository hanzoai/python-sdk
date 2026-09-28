from hanzo_kai import Kai, Noul

with Kai() as kai:
    d = kai.decide(
        state="Order 1182 arrived with a cracked screen. I want my money back, not a replacement.",
        questions={
            "refund": Noul(
                instructions="The customer wants a refund.",
                criteria={
                    "true": "they ask for their money back",
                    "false": "they ask for a repair, a replacement or nothing",
                },
                labels={"true": "refund", "false": "no refund"},
            ),
            "remedy": {
                "type": "choice",
                "instructions": "Which remedy does the customer ask for?",
                "criteria": ["refund", "replacement", "repair"],
            },
            "mood": {
                "type": "score",
                "instructions": "How upset is the customer?",
                "criteria": ["calm", "annoyed", "angry"],
            },
        },
    )

print(d.nouls["refund"].noul)
print(d.choices["remedy"].choice, d.choices["remedy"].probabilities)
print(d.scores["mood"].score, d.scores["mood"].probabilities)
