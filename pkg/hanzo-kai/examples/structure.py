from hanzo_kai import Kai, Choice

messages = [
    ("password", "I got locked out after too many attempts, can you unlock my account?"),
    ("network", "The VPN drops every few minutes when I work from home."),
    ("access", "I need edit rights on the finance shared drive for the audit."),
    ("hardware", "My laptop screen cracked when it fell off the desk."),
]
question = "What does `message` need from IT?"
plain = {
    "password": "reset a password or unlock an account",
    "access": "permission to a system, folder or app",
    "hardware": "a broken or missing laptop, monitor or phone",
    "network": "Wi-Fi, VPN or internet problems",
    "other": "anything else",
}
objects = {
    "password": {"covers": "forgotten passwords, locked accounts", "not": "Wi-Fi keys"},
    "access": {"covers": "new permissions to a system, folder or app", "not": "a login that used to work"},
    "hardware": {"covers": "broken or missing laptops, monitors, phones", "not": "software"},
    "network": {"covers": "Wi-Fi, VPN, internet", "not": "account logins"},
    "other": "anything else",
}
questions = {
    "plain": Choice(instructions=question, criteria=plain),
    "objects": Choice(instructions=question, criteria=objects),
    "note": Choice(
        instructions={"question": question, "note": "judge the underlying problem, not the words used"}, criteria=plain
    ),
}

with Kai() as kai:
    print("a person says  " + "".join(f"{name:>16}" for name in questions))
    for label, text in messages:
        d = kai.decide(state={"message": text}, questions=questions)
        print(f"{label:13}  " + "".join(f"{a.choice:>11} {a.answer_confidence:.2f}" for a in d.choices.values()))
