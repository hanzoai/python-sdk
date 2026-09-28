"""A state has to fit beside each question in what the checkpoint reads: a7 reads 1,024 tokens a question."""

from hanzo_kai import Choice, Kai, RetryPolicy, UnprocessableEntityError

LOG = "\n".join(f"2026-09-27T10:{i // 60:02d}:{i % 60:02d}Z GET /v1/models 200 {12 + i % 7}ms" for i in range(200))
ASK = "Please refund the duplicate charge on my March invoice."
WANT = Choice(
    instructions="What does the customer want?",
    criteria={"refund": "money back for a charge", "other": "something else, such as help or a fix"},
)

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    for name, state in (("log, then request", LOG + "\n\n" + ASK), ("request alone", ASK)):
        try:
            d = kai.decide(state=state, questions={"want": WANT})
            print(f"{name:<18} {len(state):>6,} characters: answered, P(refund) "
                  f"{d.choices['want'].probabilities['refund']:.4f}, {d.usage.input_tokens:,} input tokens")
        except UnprocessableEntityError as error:
            print(f"{name:<18} {len(state):>6,} characters: {error.status} {error.code} {error.message}")
