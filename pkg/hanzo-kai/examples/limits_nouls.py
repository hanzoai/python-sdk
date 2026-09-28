"""One yes/no question asked four ways about four messages; each cell is the probability Kai gives to yes."""

from hanzo_kai import Choice, Kai, Noul, RetryPolicy

MESSAGES = [
    ("I was charged twice for my March invoice. Please refund the duplicate.", "yes"),
    ("How do I change the color theme of the dashboard?", "no"),
    ("Can I get my money back for the annual plan? I no longer need it.", "yes"),
    ("The app crashes every time I upload a photo from my phone.", "no"),
]
WAYS = {
    "noul, a question": Noul(instructions="Does the customer ask for a refund?"),
    "noul, a statement with criteria": Noul(
        instructions="The customer asks for a refund.",
        criteria={"true": "the customer wants money back", "false": "the customer wants something else"},
    ),
    "choice, yes or no": Choice(
        instructions="Does the customer ask for a refund?",
        criteria={"yes": "the customer wants money back", "no": "the customer wants something else"},
    ),
    "choice, named outcomes": Choice(
        instructions="What does the customer want?",
        criteria={"refund": "money back for a charge", "other": "something else, such as help or a fix"},
    ),
}


def yes(answer):
    if answer.type == "noul":
        return answer.noul
    return answer.probabilities.get("yes", answer.probabilities.get("refund"))


with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    rows = {way: [] for way in WAYS}
    for message, _ in MESSAGES:
        d = kai.decide(state=message, questions=WAYS)
        for way in WAYS:
            rows[way].append(yes(d.answers[way]))

print(f"{'':<32}" + "".join(f"{f'message {i + 1}':>11}" for i in range(len(MESSAGES))))
print(f"{'right answer':<32}" + "".join(f"{want:>11}" for _, want in MESSAGES))
for way, cells in rows.items():
    print(f"{way:<32}" + "".join(f"{p:>11.4f}" for p in cells))
