from hanzo_kai import Kai, Choice

requests = [
    "Our checkout page throws a TypeError when the cart is empty. Find the bug in this function and fix it.",
    "Write a short, friendly note telling our customers that the office is closed on Monday.",
    "What is the probability of rolling at least one six in four throws of a fair die?",
    "Compare what three recent studies found about remote work and productivity.",
    "hey, how is your day going?",
]
instructions = "What kind of work does `request` ask for?"
wordings = {
    "A": Choice(
        instructions=instructions,
        criteria={
            "code": "write, fix or explain software",
            "math": "calculate, prove or solve a problem",
            "writing": "draft, edit or translate prose",
            "research": "find and compare sources on a topic",
            "chat": "small talk or a quick fact",
        },
    ),
    "B": Choice(
        instructions=instructions,
        criteria={
            "code": "programs, bugs, errors and APIs",
            "math": "numbers, equations, probability and proofs",
            "writing": "emails, notes, posts and other prose",
            "research": "studies, sources and comparisons",
            "chat": "greetings and small talk",
        },
    ),
}

with Kai() as kai:
    for text in requests:
        d = kai.decide(state={"request": text}, questions=wordings)
        cells = [f"{name}: {a.choice:8} {a.answer_confidence:.2f}" for name, a in d.choices.items()]
        print(" | ".join(cells), "|", text[:40])
