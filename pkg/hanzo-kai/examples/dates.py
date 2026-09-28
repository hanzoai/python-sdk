"""Find date expressions with code, have Kai check which one answers and what it counts from, resolve in code."""

import re
from datetime import date, timedelta

from hanzo_kai import Kai, Choice, RetryPolicy

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DAYS = "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
NUMBER = r"\d+|one|two|three|four|five|six|seven|eight|nine|ten"
FIXED = [r"\d{4}-\d{2}-\d{2}", rf"(?:{MONTHS}) \d{{1,2}}(?:, \d{{4}})?"]
RELATIVE = [
    rf"(?:in|within) (?:{NUMBER}) (?:days?|weeks?)",
    rf"(?:{NUMBER}) (?:days?|weeks?) (?:after|before|from)",
    r"today|tomorrow|yesterday",
    DAYS,
]

# sent, message, the date asked for, gold
MESSAGES = [
    (
        "2026-03-02",
        "Your invoice is dated February 27. Payment is due 30 days after the invoice date, and we ship on March 9.",
        "payment due date",
        "2026-03-29",
    ),
    (
        "2026-03-05",
        "The kickoff moved from March 10 to March 13. Please send your slides two days before the kickoff.",
        "deadline for the slides",
        "2026-03-11",
    ),
    (
        "2026-04-01",
        "Your trial ends in 14 days. After that you are billed monthly, starting May 1.",
        "last day of the trial",
        "2026-04-15",
    ),
    (
        "2026-04-10",
        "We received your return today. The refund reaches your card within 7 days.",
        "latest date for the refund",
        "2026-04-17",
    ),
    (
        "2026-06-03",
        "Your package shipped yesterday and should arrive by June 8.",
        "date the package shipped",
        "2026-06-02",
    ),
    (
        "2026-06-15",
        "The report covers May 1 to May 31. Send questions to finance by Friday.",
        "deadline for questions",
        "2026-06-19",
    ),
    (
        "2026-07-01",
        "Your appointment is confirmed for 2026-07-14 at 10:00. Please arrive 15 minutes early.",
        "appointment date",
        "2026-07-14",
    ),
    (
        "2026-07-20",
        "You bought the kettle on May 2, and the warranty runs 90 days from purchase.",
        "last day of the warranty",
        "2026-07-31",
    ),
    ("2026-08-03", "Thanks for your payment on July 28. Your receipt is attached.", "delivery date", None),
]

CHECK = Choice(
    instructions="How does `hypothesis` relate to `premise`?",
    criteria={
        "entailment": "the premise implies the hypothesis",
        "neutral": "the premise neither implies nor contradicts the hypothesis",
        "contradiction": "the premise contradicts the hypothesis",
    },
)


def spans(text: str, patterns: list[str]) -> list[str]:
    """Every expression in text that one of the patterns matches, in order of appearance."""
    return list(dict.fromkeys(m[0] for m in re.finditer(rf"\b(?:{'|'.join(patterns)})\b", text)))


def phrase(text: str, span: str) -> str:
    """The span with the rest of its clause when it counts from something: '30 days after the invoice date'."""
    if not span.endswith(("after", "before", "from")):
        return span
    return span + re.split(r"[.;:!?,](?:\s|$)", text[text.index(span) + len(span) :])[0]


def resolve(span: str, anchor: date) -> date:
    """The calendar date a span names; a relative span counts from anchor, a fixed one takes its year."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", span):
        return date.fromisoformat(span)
    if m := re.fullmatch(rf"({MONTHS}) (\d{{1,2}})(?:, (\d{{4}}))?", span):
        return date(int(m[3] or anchor.year), MONTHS.split("|").index(m[1]) + 1, int(m[2]))
    if span in ("today", "tomorrow", "yesterday"):
        return anchor + timedelta(days={"today": 0, "tomorrow": 1, "yesterday": -1}[span])
    if span in DAYS.split("|"):
        return anchor + timedelta(days=(DAYS.split("|").index(span) - anchor.weekday() - 1) % 7 + 1)
    m = re.fullmatch(rf"(?:in |within )?({NUMBER}) (day|week)s?(?: (after|before|from))?", span)
    count = int(m[1]) if m[1].isdigit() else NUMBER.split("|").index(m[1])
    step = timedelta(days=count * (7 if m[2] == "week" else 1))
    return anchor - step if m[3] == "before" else anchor + step


def best(kai: Kai, text: str, hypotheses: dict[str, str]) -> tuple[str, float]:
    """The key whose hypothesis the text supports most, with its P(entailment): one check per hypothesis."""
    support = {
        key: kai.decide(state={"premise": text, "hypothesis": hypothesis}, questions={"check": CHECK})
        .choices["check"]
        .probabilities["entailment"]
        for key, hypothesis in hypotheses.items()
    }
    return max(support.items(), key=lambda item: item[1])


def find(kai: Kai, sent: str, text: str, want: str) -> tuple[str | None, str, str]:
    """The date asked for, auto or review, and what Kai supported on the way."""
    fixed, relative = spans(text, FIXED), spans(text, RELATIVE)
    span, p = best(kai, text, {s: f"The {want} is {phrase(text, s)}." for s in fixed + relative})
    if p < 0.3:
        return None, "auto", f"none (best: {span} {p:.2f})"
    start, sure, why = date.fromisoformat(sent), p >= 0.7, f"{phrase(text, span)} {p:.2f}"
    if (
        named := phrase(text, span)[len(span) :].strip()
    ) and fixed:  # it counts from a named event: which date is that?
        point, q = best(kai, text, {s: f"{named[0].upper()}{named[1:]} is {s}." for s in fixed})
        start, sure, why = resolve(point, start), sure and q >= 0.7, f"{why}; {named} = {point} {q:.2f}"
    return resolve(span, start).isoformat(), "auto" if sure else "review", why


with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    right = automatic = 0
    for sent, text, want, gold in MESSAGES:
        found, route, why = find(kai, sent, text, want)
        automatic += route == "auto"
        right += route == "auto" and found == gold
        print(f"{want:27} {why:62} {found or '-':10} {route:6} {'ok' if found == gold else 'wrong'}")

print(f"\n{right} of {automatic} automatic answers right; {len(MESSAGES) - automatic} sent to review")
