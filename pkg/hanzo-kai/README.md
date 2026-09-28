# hanzo-kai

Python client for Kai decisions on the Hanzo API. Send a state and named questions; get typed,
calibrated answers back: a label for a choice, a probability for a yes/no noul, an expected level
for a score.

## Install

```bash
pip install hanzo-kai    # or: uv add hanzo-kai
```

Python 3.12 or later. Set `HANZO_API_KEY` to a Hanzo `sk-` key.

## Quickstart

```python
from hanzo_kai import Choice, Kai, Noul, Score

teams = {"billing": "charges, invoices, refunds", "tech": "bugs and outages"}
billing = {"true": "it concerns charges, invoices or refunds", "false": "it concerns something else"}
questions = {
    "team": Choice(instructions="Which team should handle this?", criteria=teams),
    "billing": Noul(instructions="Is this about billing?", criteria=billing),
    "urgency": Score(instructions="How urgent is this?", criteria=["can wait", "this week", "today"]),
}
with Kai() as kai:  # reads HANZO_API_KEY
    d = kai.decide({"ticket": "I was charged twice for my March invoice. Please refund the duplicate."}, questions)

print(d.choices["team"].choice, d.choices["team"].probabilities)
print(d.nouls["billing"].noul)
print(d.scores["urgency"].score, d.scores["urgency"].probabilities)
```

`AsyncKai` takes the same arguments, with `await` and `async with`. `kai.models.list()` lists the
models that answer decisions.

Settings come from arguments, then `HANZO_API_KEY`, `HANZO_BASE_URL` (default
`https://api.hanzo.ai`), `KAI_MODEL` (default `kai`) and `KAI_LOG_LEVEL` (default `warn`).

## Moving from Jev

`hanzo_kai.jev` keeps TypeSafe's call shapes on Kai's Jev-compatible path, `POST /v1/systemone`, answering in Jev's shape:
`from hanzo_kai.jev import Choice, Noul, Score, Client as TypeSafeClient` ports a TypeSafe program in one line.

## Docs

- Kai: https://docs.hanzo.ai/docs/kai
- Moving from TypeSafe's Jev: https://docs.hanzo.ai/docs/guides/migrate/jev
