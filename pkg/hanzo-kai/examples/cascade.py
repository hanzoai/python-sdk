"""Extract invoice fields with one Zen model, check each field with Kai, and send failed invoices to a second."""

import os
import re
import json
import time
import statistics
from decimal import Decimal, InvalidOperation

import httpx
from hanzo_kai import Kai, Choice, RetryPolicy

BASE = os.environ.get("HANZO_BASE_URL", "https://api.hanzo.ai")
FIRST, SECOND = "zen5.8-spark", "zen6"
LINES = (0.0, 0.3, 0.5, 0.7, 0.9)  # the P(entailment) every field of an invoice must reach to skip the second model
FIELDS = {
    "vendor": "the company that issued the invoice",
    "number": "the invoice number",
    "total": "the amount still to pay",
    "currency": "the currency of that amount",
    "due": "the date that amount is due",
}
FORMAT = "Write total as digits with two decimals, currency as an ISO 4217 code and due as YYYY-MM-DD."

# each invoice, then its gold fields in the order of FIELDS (None: the invoice does not say)
DOCS = [
    (
        "INVOICE A-1043\nBrightline Supply Co., 12 Dock Road\nBill to: Meridian Labs\n"
        "Subtotal 1,200.00 USD. Shipping 45.00 USD. Total 1,245.00 USD. Please pay by 2026-04-01.",
        ("Brightline Supply Co.", "A-1043", "1245.00", "USD", "2026-04-01"),
    ),
    (
        "Meridian Labs received invoice no. 7781 from Oakridge Freight on 2026-03-10. Amount €3,400.00; "
        "paid on account €400.00; balance €3,000.00, payable by 2026-04-09.",
        ("Oakridge Freight", "7781", "3000.00", "EUR", "2026-04-09"),
    ),
    (
        "From: Northwind Traders <ar@northwind.example>\nRe: INV-2026-118 overdue\nOur invoice INV-2026-118 for "
        "$12,480.00 was due on 2026-02-28. A late fee of $150.00 now applies, so please pay $12,630.00 by 2026-03-15.",
        ("Northwind Traders", "INV-2026-118", "12630.00", "USD", "2026-03-15"),
    ),
    (
        "Rechnung Nr. 2026-0457 / Invoice no. 2026-0457\nKlarwerk GmbH, Berlin\n"
        "Gesamtbetrag / Total: 2.150,00 EUR\nZahlbar bis / Due: 15.05.2026",
        ("Klarwerk GmbH", "2026-0457", "2150.00", "EUR", "2026-05-15"),
    ),
    (
        "Pine & Pixel Studio, invoice 88 for the website redesign. Fee: 6,000 CAD. Terms: due on receipt.",
        ("Pine & Pixel Studio", "88", "6000.00", "CAD", None),
    ),
    (
        "Invoice #0093 from Lumen Electric to Grayson Property Group. Labour $1,120.00, parts $385.50, "
        "total $1,505.50. Payment due 2026-07-01 (net 30).",
        ("Lumen Electric", "0093", "1505.50", "USD", "2026-07-01"),
    ),
    (
        "Statement from Coastal Linen Services: invoices 4410 ($230.00) and 4411 ($310.00) are open. "
        "This notice concerns invoice 4411 only, due 2026-08-20.",
        ("Coastal Linen Services", "4411", "310.00", "USD", "2026-08-20"),
    ),
    (
        "Tokyo Office Supply K.K. Invoice T-5521. Total ¥84,000 (tax included). Payment due by 2026-09-30.",
        ("Tokyo Office Supply K.K.", "T-5521", "84000.00", "JPY", "2026-09-30"),
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


def post(path: str, body: dict | None = None) -> dict:
    """GET (no body) or POST a JSON body to the Hanzo API, trying again after a rate limit or a failed reply."""
    headers = {"Authorization": f"Bearer {os.environ['HANZO_API_KEY']}"}
    method = "GET" if body is None else "POST"
    for _ in range(10):
        response = httpx.request(method, BASE + path, json=body, headers=headers, timeout=300)
        if response.status_code == 429 or response.status_code >= 500:
            time.sleep(float(response.headers.get("retry-after", "2")))
            continue
        response.raise_for_status()
        if body is None or "choices" in response.json():  # a reply without choices is an upstream failure
            return response.json()
        time.sleep(2)
    raise RuntimeError(f"{path} failed ten times: {response.text[:200]}")


def extract(model: str, document: str) -> tuple[dict, tuple[int, int]]:
    """The fields as a Zen model reads them from the invoice, and the reply's input and output tokens."""
    keys = "; ".join(f'"{name}": {what}' for name, what in FIELDS.items())
    system = f"Reply with one JSON object with exactly these keys: {keys}. {FORMAT} Use null for anything not stated."
    messages = [{"role": "system", "content": system}, {"role": "user", "content": document}]
    reply = post("/v1/chat/completions", {"model": model, "messages": messages, "temperature": 0})
    text = re.sub(r"<think>.*?</think>", "", reply["choices"][0]["message"]["content"], flags=re.S)
    tokens = (reply["usage"]["prompt_tokens"], reply["usage"]["completion_tokens"])
    return json.loads(text[text.index("{") : text.rindex("}") + 1]), tokens


def claim(name: str, value) -> str:
    """The statement Kai checks for one extracted field."""
    what = FIELDS[name]
    return f"The invoice does not state {what}." if value is None else f"{what[0].upper()}{what[1:]} is {value}."


def cost(model: str, tokens: tuple[int, int]) -> float:
    """US dollars for input and output tokens at a model's catalogue price per million."""
    return (tokens[0] * price[model]["input"] + tokens[1] * price[model]["output"]) / 1e6


def same(name: str, value, gold) -> bool:
    """Whether an extracted value equals the gold one, up to case and number format."""
    if value is None or gold is None:
        return value is gold
    if name != "total":
        return str(value).strip().casefold() == gold.casefold()
    try:
        return Decimal(str(value).replace(",", "")) == Decimal(gold)
    except InvalidOperation:
        return False


price = {row["id"]: row["pricing"] for row in post("/v1/models")["data"] if "pricing" in row}
rows, checked = [], 0  # one row per invoice; the input tokens Kai read
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for document, values in DOCS:
        draft, drafting = extract(FIRST, document)
        support = {}
        for name in FIELDS:
            state = {"premise": document, "hypothesis": claim(name, draft.get(name))}
            check = kai.decide(state=state, questions={"check": CHECK})
            checked += check.usage.input_tokens
            support[name] = check.choices["check"].probabilities["entailment"]
        redo, redoing = extract(SECOND, document)
        gold = dict(zip(FIELDS, values, strict=True))
        rows.append((gold, draft, support, redo, drafting, redoing))

wrong = [
    (n, name)
    for n, (gold, draft, _, redo, _, _) in enumerate(rows)
    for name in FIELDS
    if not (same(name, draft.get(name), gold[name]) and same(name, redo.get(name), gold[name]))
]
print(f"fields either model got wrong, with Kai's P(entailment) for {FIRST}'s value: {len(wrong) or 'none'}")
for n, name in wrong:
    gold, draft, support, redo, _, _ = rows[n]
    print(f"invoice {n} {name:8} {FIRST} {draft.get(name)!s:14} P {support[name]:.2f}  ", end="")
    print(f"{SECOND} {redo.get(name)!s:14} gold {gold[name]}")
good = [
    p for gold, draft, support, *_ in rows for name, p in support.items() if same(name, draft.get(name), gold[name])
]
print(
    f"\nP(entailment) of {FIRST}'s {len(good)} right fields: lowest {min(good):.2f}, median {statistics.median(good):.2f}"
)

fields, checking = len(rows) * len(FIELDS), checked * price["kai"]["input"] / 1e6
print(
    f"\nKai read {checked} input tokens for {fields} checks: {checking:.6f} USD at {price['kai']['input']} per million"
)
print(f"an invoice goes to {SECOND} when any of its fields is under the line")
print("line          invoices sent  fields right  Zen input  Zen output  cost, USD")
for line in [*LINES, None]:  # None: the second model alone
    goes = [line is None or min(row[2].values()) < line for row in rows]
    right = sum(
        same(name, (redo if go else draft).get(name), gold[name])
        for (gold, draft, _, redo, _, _), go in zip(rows, goes, strict=True)
        for name in FIELDS
    )
    used = [
        (drafting if line is not None else (0, 0), redoing if go else (0, 0))
        for (*_, drafting, redoing), go in zip(rows, goes, strict=True)
    ]
    tokens = [sum(a[i] + b[i] for a, b in used) for i in (0, 1)]
    spent = sum(cost(FIRST, a) + cost(SECOND, b) for a, b in used) + (checking if line is not None else 0)
    label = f"{SECOND} alone" if line is None else f"{line}"
    print(f"{label:<13} {sum(goes):13} {right:9}/{fields}  {tokens[0]:9}  {tokens[1]:10}  {spent:.6f}")
