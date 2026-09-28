from hanzo_kai import Kai, Choice

shared = (
    "The queue for staff who write to the service desk, by email, chat or phone, about a company laptop, "
    "desktop or phone issued in the last three years, including devices bought through a partner, devices "
    "shared between several people, and devices used both in the office and at home, and"
)
variants = {
    "short": {
        "queue_a": "Staff who need a password reset or an unlocked account.",
        "queue_b": "Staff whose Wi-Fi, VPN or internet is failing.",
    },
    "long, difference first": {
        "queue_a": "Staff who need a password reset or an unlocked account. " + shared,
        "queue_b": "Staff whose Wi-Fi, VPN or internet is failing. " + shared,
    },
    "long, difference last": {
        "queue_a": shared + " who need a password reset or an unlocked account.",
        "queue_b": shared + " whose Wi-Fi, VPN or internet is failing.",
    },
}

with Kai() as kai:
    for name, criteria in variants.items():
        d = kai.decide(
            state={"message": "The VPN drops every few minutes when I work from home."},
            questions={"queue": Choice(instructions="Which queue should take `message`?", criteria=criteria)},
        )
        p = d.choices["queue"].probabilities
        print(f"{name:23} queue_a {p['queue_a']:.4f}  queue_b {p['queue_b']:.4f}")
