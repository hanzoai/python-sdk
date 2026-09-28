"""Find emails, phone numbers and amounts with regexes; Kai says which one was asked for; code normalises it."""

import re
from decimal import Decimal

from hanzo_kai import Kai, Choice, RetryPolicy

PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "phone": r"\+\d{1,3}(?: ?\d{2,4}){2,4}|\(?\d{3}\)?[ .-]?\d{3}[ .-]\d{4}",
    "amount": r"[$€£]\s?\d[\d,]*(?:\.\d{2})?",
}
CURRENCY = {"$": "USD", "€": "EUR", "£": "GBP"}

# text, then each request: the kind of value, what is asked for, and the gold value (None: not in the text)
TEXTS = [
    (
        "Hi, Dana Reyes here. Call me back on (415) 555-0134; the front desk is 415-555-0100. "
        "My order came to $1,284.50 but my card was charged $1,824.50.",
        [
            ("phone", "the number to call the customer back on", "+14155550134"),
            ("amount", "the amount charged to the card", "USD 1824.50"),
            ("amount", "the order total", "USD 1284.50"),
        ],
    ),
    (
        "Forwarded by ops@contoso.example: the customer, J.Smith@Fabrikam.example, wants the €89.00 refund sent to her card.",
        [
            ("email", "the customer's email address", "j.smith@fabrikam.example"),
            ("amount", "the refund amount", "EUR 89.00"),
        ],
    ),
    (
        "Invoice 2231. Subtotal $450.00, tax $36.00, total $486.00. Questions go to billing@acme.example.",
        [("amount", "the amount to pay", "USD 486.00"), ("amount", "the tax", "USD 36.00")],
    ),
    (
        "Please change my phone number from +44 20 7946 0958 to +44 20 7946 0321.",
        [("phone", "the new phone number", "+442079460321")],
    ),
    (
        "I paid £25 for shipping on an order that promised free delivery. Email me at sam.okafor@example.net.",
        [("amount", "the shipping fee the customer paid", "GBP 25.00"), ("phone", "the customer's phone number", None)],
    ),
    (
        "You can reach me at maria.lopez@example.org. Our office line is 212 555 0199.",
        [
            ("phone", "the customer's mobile number", None),
            ("email", "the customer's email address", "maria.lopez@example.org"),
        ],
    ),
    (
        "The $500 deposit was refunded; the remaining balance of $1,250 is due at pickup.",
        [("amount", "the balance due", "USD 1250.00"), ("amount", "the deposit", "USD 500.00")],
    ),
    (
        "Replies to noreply@shop.example are not read. For help, write to help@shop.example.",
        [("email", "the address to write to for help", "help@shop.example")],
    ),
]

CHECK = Choice(
    instructions="How does `hypothesis` relate to `premise`?",
    criteria={
        "entailment": "the premise implies the hypothesis",
        "neutral": "the premise neither implies nor contradicts the hypothesis",
        "contradiction": "the premise contradicts the hypothesis",
    },
)


def normal(kind: str, span: str) -> str:
    """One canonical form per kind: lowercase email, E.164 phone, ISO currency and two decimals."""
    if kind == "email":
        return span.lower()
    if kind == "phone":
        digits = re.sub(r"\D", "", span)
        return "+" + digits if span.startswith("+") else "+1" + digits
    return f"{CURRENCY[span[0]]} {Decimal(span[1:].strip().replace(',', '')):.2f}"


def check(kai: Kai, text: str, want: str, spans: list[str]) -> tuple[str, float, str]:
    """One check per candidate: the best-supported span, its P(entailment), and whether to act on it."""
    support = {
        span: kai.decide(
            state={"premise": text, "hypothesis": f"{want[0].upper()}{want[1:]} is {span}."},
            questions={"check": CHECK},
        )
        .choices["check"]
        .probabilities["entailment"]
        for span in spans
    }
    span, p = max(support.items(), key=lambda item: item[1])
    return (span, p, "auto") if p >= 0.7 else ("none", p, "auto") if p < 0.3 else (span, p, "review")


def choose(kai: Kai, text: str, want: str, spans: list[str]) -> tuple[str, float, str]:
    """One choice over the candidates and none, kept for comparison: its pick, confidence and route."""
    options = {span: None for span in spans} | {"none": "the text does not state it"}
    ask = Choice(instructions=f"Which of these is {want}?", criteria=options)
    answer = kai.decide(state={"text": text}, questions={"pick": ask}).choices["pick"]
    return answer.choice, answer.confidence, "auto" if answer.confidence >= 0.5 else "review"


tally = {"check": [0, 0], "choice": [0, 0]}  # automatic answers right, automatic answers
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for text, requests in TEXTS:
        for kind, want, gold in requests:
            spans = list(dict.fromkeys(re.findall(PATTERNS[kind], text)))
            cells = []
            for name, ask in (("check", check), ("choice", choose)):
                span, p, route = ask(kai, text, want, spans) if spans else ("none", None, "auto")  # nothing to ask
                value = None if span == "none" else normal(kind, span)
                tally[name][0] += route == "auto" and value == gold
                tally[name][1] += route == "auto"
                shown = "no candidate" if p is None else f"{p:.2f}"
                cells.append(
                    f"{name:6} {span} {shown} {'review' if route == 'review' else 'ok' if value == gold else 'WRONG'}"
                )
            print(f"{want}, gold {gold or 'none'}\n    {cells[0]:44} {cells[1]}")

asked = sum(len(requests) for _, requests in TEXTS)
print()
for name, (right, auto) in tally.items():
    print(f"{name:7} {right} of {auto} automatic answers right; {asked - auto} of {asked} sent to review")
