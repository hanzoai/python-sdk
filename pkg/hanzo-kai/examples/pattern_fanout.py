"""Speculative fan-out: one call asks every question a branch could need; code reads only its branch's answers."""

from hanzo_kai import Choice, Kai, Noul, RetryPolicy

QUESTIONS = {
    "phishing": Noul(
        instructions="This email is a phishing or scam attempt to steal money, credentials or personal data.",
        criteria={"true": "phishing, scam or fraud", "false": "a legitimate email, even if promotional"},
    ),
    "spam": Noul(
        instructions="This email is unsolicited spam or bulk marketing.",
        criteria={"true": "spam or bulk marketing sent to many people", "false": "a message written to us personally"},
    ),
    # speculative: read only when both checks pass
    "topic": Choice(
        instructions="What is the topic of this email?",
        criteria={
            "world": "world news and international politics",
            "sports": "sports",
            "business": "business and economy",
            "sci_tech": "science and technology",
        },
    ),
}

INBOX = [
    {"subject": "LAST CHANCE: 80% off designer watches",
     "body": "Luxury replicas shipped worldwide. Click now, offer ends at midnight! Unsubscribe here."},
    {"subject": "Your mailbox is full",
     "body": "Your newsroom mailbox has exceeded its quota. Sign in within 24 hours at http://mail-quota-reset.example "
             "to keep receiving mail, or your account will be closed."},
    {"subject": "Tip: striker transfer",
     "body": "Sources at the club say their top striker has agreed terms with a Spanish side; the fee is around "
             "40 million euros and the medical is on Thursday."},
    {"subject": "Tip: supermarket merger",
     "body": "Two regional supermarket chains are in late talks to merge; the combined group would have 900 stores "
             "and the deal could be announced before quarterly results."},
    {"subject": "Tip: satellite launch slip",
     "body": "The weather satellite launch has slipped three weeks because of a faulty valve found during the final "
             "engine test, according to two engineers on the team."},
    {"subject": "Tip: border talks",
     "body": "Negotiators from both governments will meet in Geneva next week to discuss reopening the border "
             "crossing closed since the spring."},
]


def route(d):
    """Where an email goes, and the answers that decided it."""
    if d.nouls["phishing"].noul >= 0.5:
        return "quarantine", ["phishing"]
    if d.nouls["spam"].noul >= 0.5:
        return "delete", ["phishing", "spam"]
    topic = d.choices["topic"]
    if topic.confidence < 0.5:
        return "duty editor", ["phishing", "spam", "topic"]
    return f"{topic.choice} desk", ["phishing", "spam", "topic"]


with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    print(f"{'subject':<30} {'phishing':>8} {'spam':>6}  {'topic':<16} {'route':<14} read")
    tokens = 0
    for email in INBOX:
        d = kai.decide(state=email, questions=QUESTIONS)
        where, read = route(d)
        topic = d.choices["topic"]
        tokens += d.usage.input_tokens
        print(f"{email['subject'][:30]:<30} {d.nouls['phishing'].noul:>8.4f} {d.nouls['spam'].noul:>6.4f}  "
              f"{topic.choice + f' ({topic.confidence:.2f})':<16} {where:<14} {', '.join(read)}")
    print(f"\n{len(INBOX)} calls, {tokens} input tokens")

    guards = {name: QUESTIONS[name] for name in ("phishing", "spam")}
    for asked in (QUESTIONS, guards):
        d = kai.decide(state=INBOX[2], questions=asked)
        print(f"third email, {len(asked)} questions: phishing {d.nouls['phishing'].noul:.4f}, "
              f"spam {d.nouls['spam'].noul:.4f}, {d.usage.input_tokens} input tokens")
