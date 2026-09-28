"""Check each claim against the sentence it cites: supported, contradicted, or not in the source."""

from hanzo_kai import Kai, Choice, RetryPolicy

DOC = [
    "Unused items can be returned within 30 days of delivery.",
    "Refunds go back to the original payment method within 5 business days of the return arriving.",
    "Shipping costs are refunded only when the item arrived damaged or was not what was ordered.",
    "Sale items can be exchanged but not refunded.",
    "Gift cards cannot be returned or exchanged.",
    "Returns from outside the country are sent at the customer's expense.",
]

# claim, the sentence it cites, gold against that sentence, gold against the whole document
CLAIMS = [
    ("You have 30 days after delivery to return an unused item.", 0, "supported", "supported"),
    ("Unused items can be returned within 60 days.", 0, "contradicted", "contradicted"),
    ("Refunds are paid to the original payment method.", 1, "supported", "supported"),
    ("Shipping costs are always refunded.", 2, "contradicted", "contradicted"),
    ("An item that arrived damaged gets its shipping cost refunded.", 2, "supported", "supported"),
    ("A sale item can be refunded.", 3, "contradicted", "contradicted"),
    ("Gift cards are final: they cannot be returned.", 4, "supported", "supported"),
    ("The store pays for returns sent from abroad.", 5, "contradicted", "contradicted"),
    ("Sale items can be swapped for another item.", 0, "absent", "supported"),
    ("Refunds are made within 5 business days of the return arriving.", 4, "absent", "supported"),
    ("Returns can be dropped off at any store.", 0, "absent", "absent"),
    ("Refunds include a 10% restocking fee.", 1, "absent", "absent"),
]
WIDTH = max(len(claim) for claim, *_ in CLAIMS)

# a citation check is natural-language inference: the source is the premise, the claim the hypothesis
CHECK = Choice(
    instructions="How does `hypothesis` relate to `premise`?",
    criteria={
        "entailment": "the premise implies the hypothesis",
        "neutral": "the premise neither implies nor contradicts the hypothesis",
        "contradiction": "the premise contradicts the hypothesis",
    },
)
VERDICT = {"entailment": "supported", "neutral": "absent", "contradiction": "contradicted"}


def check(kai: Kai, source: str, claim: str) -> tuple[str, float]:
    """Kai's verdict on one claim against one source, with its confidence."""
    answer = kai.decide(state={"premise": source, "hypothesis": claim}, questions={"check": CHECK}).choices["check"]
    return VERDICT[answer.choice], answer.confidence


with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    cited = whole = widened = 0
    print(f"{'claim':{WIDTH}} cites  {'gold':13} {'kai':13} conf")
    for claim, cite, gold, truth in CLAIMS:
        verdict, confidence = check(kai, DOC[cite], claim)
        cited += verdict == gold
        line = f"{claim:{WIDTH}} {cite:5}  {gold:13} {verdict:13} {confidence:.2f}"
        if verdict == "absent":  # the cited sentence misses the claim: look in the whole document
            widened += 1
            verdict, confidence = check(kai, " ".join(DOC), claim)
            whole += verdict == truth
            line += f"  document: {verdict} {confidence:.2f} (gold {truth})"
        print(line)

print(f"\nagainst the cited sentence: {cited}/{len(CLAIMS)} as labelled")
print(f"against the whole document: {whole}/{widened} as labelled")
