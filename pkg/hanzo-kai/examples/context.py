from hanzo_kai import Kai, Choice, UnprocessableEntityError

latest = "I lost my card on the train this morning. Please block it."
events = [
    "signed in from the mobile app",
    "downloaded the August statement",
    "changed the mailing address",
    "sent EUR 40.00 to a saved contact",
    "enabled notifications",
    "viewed the savings goal",
]
intent = Choice(
    instructions="What does `latest` ask for?",
    criteria={
        "activate_card": "turn on a new card",
        "lost_card": "report a lost or stolen card",
        "refund": "money back for a payment",
        "transfer": "send or receive money",
        "other": "anything else",
    },
)

with Kai() as kai:
    for lines in (0, 10, 40, 160):
        history = [f"2026-09-{1 + i % 28:02d} {events[i % len(events)]}" for i in range(lines)]
        for first in ("latest", "history"):
            state = {"latest": latest, "history": history}
            if first == "history":
                state = {"history": history, "latest": latest}
            try:
                a = kai.decide(state=state, questions={"intent": intent}).choices["intent"]
            except UnprocessableEntityError as error:
                print(f"{lines:3} lines, {first:7} first: refused, {error.status}: {error.message}")
                continue
            print(f"{lines:3} lines, {first:7} first: {a.choice:9} p(lost_card)={a.probabilities['lost_card']:.4f}")
