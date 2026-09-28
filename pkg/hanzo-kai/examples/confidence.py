from hanzo_kai import Kai, Choice

need = Choice(
    instructions="What does `message` need from IT?",
    criteria={
        "password": "reset a password or unlock an account",
        "access": "permission to a system, folder or app",
        "hardware": "a broken or missing laptop, monitor or phone",
        "network": "Wi-Fi, VPN or internet problems",
        "other": "anything else",
    },
)
messages = [
    "I got locked out after too many attempts, can you unlock my account?",
    "Since the Wi-Fi password changed I cannot open the shared drive.",
]
THRESHOLD = 0.6  # the desk acts on answers at or above this confidence

with Kai() as kai:
    for text in messages:
        a = kai.decide(state={"message": text}, questions={"need": need}).choices["need"]
        top = sorted(a.probabilities.items(), key=lambda kv: -kv[1])[:3]
        action = f"route to {a.choice}" if a.confidence >= THRESHOLD else "ask a person"
        print(text)
        print(f"  top three {[(label, round(p, 4)) for label, p in top]}")
        print(f"  answer_confidence {a.answer_confidence:.4f}  confidence {a.confidence:.4f}  -> {action}")
