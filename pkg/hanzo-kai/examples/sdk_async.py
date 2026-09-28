import asyncio

from hanzo_kai import AsyncKai, Choice

TICKETS = [
    "I was charged twice for my March invoice.",
    "The dashboard shows a blank page since this morning.",
    "Can I move my team to the annual plan?",
]
TEAM = Choice(
    instructions="Which team should handle `ticket`?",
    criteria={"billing": "charges, invoices, refunds", "tech": "bugs and outages", "sales": "plans and upgrades"},
)


async def main() -> None:
    async with AsyncKai() as kai:
        decisions = await asyncio.gather(*(kai.decide({"ticket": ticket}, {"team": TEAM}) for ticket in TICKETS))
    for ticket, d in zip(TICKETS, decisions, strict=True):
        print(d.choices["team"].choice, d.choices["team"].confidence, ticket)


asyncio.run(main())
