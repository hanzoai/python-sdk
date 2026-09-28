"""How much of an option Kai reads: two options that differ only after a long shared opening, then one over 512 tokens."""

from hanzo_kai import Choice, Kai, RetryPolicy, UnprocessableEntityError

OPENING = ("Send the ticket to this queue when, after reading the whole message, any earlier replies in the thread "
           "and the notes other agents left on it, and after checking the customer's plan, region and account "
           "history, the main thing the customer needs from us is help from the team that looks after ")
LATE = Choice(instructions="Which queue should take this ticket?",
              criteria={"q1": OPENING + "charges, invoices and refunds.", "q2": OPENING + "themes, colors and layout."})
EARLY = Choice(instructions="Which queue should take this ticket?",
               criteria={"q1": "Charges, invoices and refunds. " + OPENING, "q2": "Themes, colors and layout. " + OPENING})
LONG = Choice(instructions="Which queue should take this ticket?",
              criteria={"q1": "charges, invoices and refunds " * 150, "q2": "themes, colors and layout"})
TICKETS = [("q1", "I was charged twice for my March invoice."),
           ("q2", "How do I change the color theme of the dashboard?")]

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    for want, ticket in TICKETS:
        late = kai.decide(state=ticket, questions={"queue": LATE}).choices["queue"].probabilities
        early = kai.decide(state=ticket, questions={"queue": EARLY}).choices["queue"].probabilities
        print(f"{ticket:<50} want {want}   difference last: P(q1) {late['q1']:.4f}   first: P(q1) {early['q1']:.4f}")
    try:
        answer = kai.decide(state=TICKETS[0][1], questions={"queue": LONG}).choices["queue"]
        print(f"an option of {len(LONG.criteria['q1']):,} characters: answered, P(q1) {answer.probabilities['q1']:.4f}")
    except UnprocessableEntityError as error:
        print(f"an option of {len(LONG.criteria['q1']):,} characters: {error.status} {error.code} {error.message}")
