"""One choice over 300, then 1,000 described labels: every label gets a probability, and a narrower re-ask keeps the order."""

from hanzo_kai import Choice, Kai, RetryPolicy

AREAS = {
    "billing": ["invoice", "payment method", "refund", "subscription", "tax id",
                "credit balance", "receipt", "usage report", "price plan", "discount code"],
    "identity": ["password", "single sign-on", "two-factor code", "api key", "user role",
                 "team invite", "session", "audit log", "service account", "login alert"],
    "storage": ["bucket", "file upload", "backup", "snapshot", "retention rule",
                "public link", "folder", "quota", "encryption key", "object version"],
    "compute": ["virtual machine", "container", "gpu node", "autoscaling rule", "cron job",
                "machine image", "ssh key", "instance size", "startup script", "spot instance"],
    "network": ["domain", "dns record", "tls certificate", "load balancer", "firewall rule",
                "private network", "static ip", "cdn cache", "rate limit", "webhook url"],
    "database": ["postgres cluster", "read replica", "connection pool", "schema migration", "slow query",
                 "index", "point-in-time restore", "user grant", "extension", "failover"],
    "messaging": ["email template", "sms sender", "push notification", "queue", "topic",
                  "delivery log", "bounce list", "unsubscribe link", "sender domain", "message retry"],
    "analytics": ["dashboard", "chart", "event stream", "funnel", "cohort",
                  "data export", "saved query", "alert rule", "metric", "scheduled report"],
    "support": ["ticket", "live chat", "help article", "satisfaction survey", "escalation",
                "sla", "canned reply", "agent seat", "call recording", "support hours"],
    "compliance": ["data processing agreement", "gdpr request", "soc 2 report", "data residency", "access review",
                   "retention policy", "legal hold", "subprocessor list", "pen test report", "privacy policy"],
}
ACTIONS = {
    "setup": "set up a new {o}",
    "remove": "remove the {o}",
    "change": "change the settings of the {o}",
    "export": "export or download the {o}",
    "error": "an error when using the {o}",
    "access": "cannot access the {o}: permission denied",
    "cost": "a question about the cost of the {o}",
    "recover": "recover the {o} after it was deleted by mistake",
    "limit": "raise the limit on the {o}",
    "move": "move the {o} to another account",
}
TICKETS = [
    ("The download button for our March invoice shows 'Something went wrong' every time we click it.", "billing.invoice.error"),
    ("I deleted our assets-prod bucket by mistake an hour ago. Is there any way to get it back?", "storage.bucket.recover"),
    ("How much more would we pay per month if we added two GPU nodes?", "compute.gpu-node.cost"),
]
ASK = "Which support category does this ticket belong to?"


def taxonomy(areas: list[str]) -> dict[str, str]:
    """Every object of each area crossed with every action, as label: description."""
    return {
        f"{area}.{obj.replace(' ', '-')}.{action}": f"{text.format(o=obj)}, in {area}"
        for area in areas
        for obj in AREAS[area]
        for action, text in ACTIONS.items()
    }


with Kai(retry=RetryPolicy(max_retries=10), timeout=120) as kai:
    for areas in (["billing", "identity", "storage"], list(AREAS)):
        labels = taxonomy(areas)
        for ticket, expected in TICKETS:
            if expected not in labels:
                continue
            d = kai.decide(state={"ticket": ticket}, questions={"category": Choice(instructions=ASK, criteria=labels)})
            a = d.choices["category"]
            order = sorted(a.probabilities, key=a.probabilities.__getitem__, reverse=True)
            print(
                f"{len(labels)} labels, {len(a.probabilities)} probabilities, input_tokens {d.usage.input_tokens}\n"
                f"  answer   {a.choice} p={a.answer_confidence} confidence={a.confidence}\n"
                f"  expected {expected} p={a.probabilities[expected]} rank {order.index(expected) + 1}"
            )
            if len(labels) == 1000:
                top = {label: labels[label] for label in order[:20]}
                again = kai.decide(state={"ticket": ticket}, questions={"category": Choice(instructions=ASK, criteria=top)})
                b = again.choices["category"]
                print(f"  top 20 re-asked: {b.choice} p={b.answer_confidence}")
