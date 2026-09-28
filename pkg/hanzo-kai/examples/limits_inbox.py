"""A label set no suite measured: four finance-inbox messages, two choices each."""

from hanzo_kai import Choice, Kai, RetryPolicy

KIND = Choice(
    instructions="What is this message?",
    criteria={
        "invoice": "a bill asking us to pay for goods or services",
        "reminder": "a follow-up about a bill that is already overdue",
        "receipt": "a confirmation that a payment was received",
        "other": "anything else",
    },
)
BANK = Choice(
    instructions="Does the message give payment details?",
    criteria={"new": "asks us to pay into a new or different bank account", "same": "gives no new bank details"},
)
MESSAGES = [
    ("invoice", "new", "Please find attached invoice INV-2291 for the September migration work: 14,200 EUR, due in "
     "30 days. We have changed banks, so please pay this and future invoices to IBAN DE44 5001 0517 5407 3249 31."),
    ("reminder", "same", "Invoice 88-1043 for 3,480 USD was due on 31 August and is still unpaid. Without payment "
     "within 7 days we will add a 5% late fee and pass the account to our collections partner."),
    ("receipt", "same", "Thank you: we received your payment of 612.50 GBP for order 55710 on 26 September. "
     "Nothing more is needed."),
    ("invoice", "same", "Attached is invoice 7731 for the October office cleaning, 890 EUR, payable by 15 November "
     "to the usual account."),
]

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    for kind, bank, message in MESSAGES:
        d = kai.decide(state=message, questions={"kind": KIND, "bank": BANK})
        k, b = d.choices["kind"], d.choices["bank"]
        print(f"kind: want {kind:<8} got {k.choice:<8} {k.probabilities[k.choice]:.4f}   "
              f"bank: want {bank:<4} got {b.choice:<4} {b.probabilities[b.choice]:.4f}")
