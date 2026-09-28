from hanzo_kai import Kai, Noul, Choice

messages = [
    (True, "My new card came yesterday but the app will not let me activate it. It keeps saying the code is invalid."),
    (True, "The app crashes every time I open the statements tab."),
    (True, "I tried to send money three times and the app just shows a spinning wheel and then an error."),
    (True, "Since the last update I cannot log in to the app, it says something went wrong."),
    (False, "How long does a transfer to a German bank account usually take?"),
    (False, "I lost my card on the train this morning, please block it."),
    (False, "Can I raise my daily ATM withdrawal limit?"),
    (False, "Thanks, the refund arrived today. Great service!"),
]
broken = "the app shows an error, crashes or refuses an action"
working = "the app works, or the message is about something else"
forms = {
    "question": Noul(instructions="Is the app broken?"),
    "statement": Noul(
        instructions="`message` reports that the app is not working.", criteria={"true": broken, "false": working}
    ),
    "yes/no": Choice(
        instructions="Does `message` report that the app is not working?", criteria={"yes": broken, "no": working}
    ),
    "five-way": Choice(
        instructions="What does `message` report?",
        criteria={
            "app_error": broken,
            "card": "a card is lost, stolen, blocked or needs activating",
            "transfer": "sending or receiving money",
            "limits": "limits, fees or account settings",
            "other": "thanks, feedback or anything else",
        },
    ),
}


def failing(answer):
    """P(the app is not working) as each form reports it."""
    if answer.type == "noul":
        return answer.noul
    return answer.probabilities.get("yes", answer.probabilities.get("app_error"))


right = dict.fromkeys(forms, 0)
with Kai() as kai:
    print("truth  " + "  ".join(f"{name:>9}" for name in forms))
    for truth, text in messages:
        d = kai.decide(state={"message": text}, questions=forms)
        row = []
        for name in forms:
            p = failing(d.answers[name])
            right[name] += (p > 0.5) == truth
            row.append(f"{p:9.2f}")
        print(f"{str(truth):5}  " + "  ".join(row))
print("right  " + "  ".join(f"{right[name]:>7}/8" for name in forms))
