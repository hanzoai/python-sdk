"""A question over a state answers the same each time, alone or beside others, so a local cache keyed by state_hash and question is exact."""

import hashlib
import json

from hanzo_kai import Choice, Kai, RetryPolicy

STATE = {"ticket": "Our card was declined when we tried to renew the annual plan."}
TEAM = Choice(
    instructions="Which team should handle this ticket?",
    criteria={"billing": "charges, invoices, refunds", "technical": "errors, outages, slowness", "account": "sign-in and access"},
)
TODAY = Choice(
    instructions="Does this ticket need an answer today?",
    criteria={"yes": "it blocks work or money", "no": "it can wait"},
)


def state_hash(state) -> str:
    """The response's state_hash, computed locally: a string as itself, anything else as json.dumps writes it."""
    text = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def definition(question: Choice) -> str:
    return json.dumps(question.model_dump(), sort_keys=True)


class Memo:
    """Answers kept by state_hash and question; an answer from another checkpoint or calibration clears them."""

    def __init__(self, kai: Kai):
        self.kai, self.kept, self.checkpoint, self.calls = kai, {}, None, 0

    def decide(self, state, questions: dict[str, Choice]) -> dict[str, dict[str, float]]:
        h = state_hash(state)
        missing = {n: q for n, q in questions.items() if (h, definition(q)) not in self.kept}
        if missing:
            d = self.kai.decide(state=state, questions=missing)
            self.calls += 1
            now = (d.routing["sha256"], d.routing["calibration"])
            if self.checkpoint not in (None, now):
                self.kept, self.checkpoint = {}, now
                return self.decide(state, questions)
            self.checkpoint = now
            self.kept.update({(h, definition(q)): d.choices[n].probabilities for n, q in missing.items()})
        return {n: self.kept[(h, definition(q))] for n, q in questions.items()}


with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    first = kai.decide(state=STATE, questions={"team": TEAM})
    again = kai.decide(state=STATE, questions={"team": TEAM})
    pair = kai.decide(state=STATE, questions={"team": TEAM, "today": TODAY})
    renamed = kai.decide(state=STATE, questions={"queue": TEAM})
    print("state_hash, local   ", state_hash(STATE))
    print("state_hash, returned", first.state_hash)
    for label, d, name in (("alone", first, "team"), ("alone, again", again, "team"), ("beside today", pair, "team"), ("named queue", renamed, "queue")):
        print(f"team, {label:<13}{d.choices[name].probabilities}  input_tokens {d.usage.input_tokens}")

    memo = Memo(kai)
    for questions in ({"team": TEAM}, {"team": TEAM, "today": TODAY}, {"team": TEAM, "today": TODAY}):
        answers = memo.decide(STATE, questions)
        print(f"memo, asked for {', '.join(answers)}: calls to Kai so far {memo.calls}")
