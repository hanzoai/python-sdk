from hanzo_kai import Kai, Choice

VERDICTS = ["allow", "ask", "deny"]
ACTIONS = {"allow": "unlock the account", "ask": "queue for a person", "deny": "refuse"}
NEED = Choice(
    instructions="What does `message` need from IT?",
    criteria={
        "password": "reset a password or unlock an account",
        "access": "permission to a system, folder or app",
        "hardware": "a broken or missing laptop, monitor or phone",
        "network": "Wi-Fi, VPN or internet problems",
        "other": "anything else",
    },
)


def policy(account):
    """The desk's rules for an automatic unlock, decided without a model."""
    if account["admin"]:
        return "deny"
    if not account["verified"]:
        return "ask"
    return "allow"


def judged(need):
    """What Kai's answer supports: an unlock only for a clear password request."""
    return "allow" if need.choice == "password" and need.confidence >= 0.6 else "ask"


def join(*verdicts):
    """The strictest verdict, on allow < ask < deny."""
    return max(verdicts, key=VERDICTS.index)


tickets = [
    (
        {"user": "ana", "admin": False, "verified": True},
        "I got locked out after too many attempts, can you unlock my account?",
    ),
    (
        {"user": "ops", "admin": True, "verified": True},
        "I got locked out after too many attempts, can you unlock my account?",
    ),
    (
        {"user": "lee", "admin": False, "verified": False},
        "I got locked out after too many attempts, can you unlock my account?",
    ),
    (
        {"user": "ben", "admin": False, "verified": True},
        "Since the Wi-Fi password changed I cannot open the shared drive.",
    ),
]

with Kai() as kai:
    for account, text in tickets:
        rule = policy(account)
        if rule == "deny":
            print(f"{account['user']}: policy deny; Kai not asked -> {ACTIONS['deny']}")
            continue
        need = kai.decide(state={"message": text}, questions={"need": NEED}).choices["need"]
        verdict = join(rule, judged(need))
        print(
            f"{account['user']}: policy {rule}, Kai {judged(need)} ({need.choice}, confidence {need.confidence:.2f})"
            f" -> {verdict}: {ACTIONS[verdict]}"
        )
