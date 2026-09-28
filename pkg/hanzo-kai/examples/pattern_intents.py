"""Intent routing: one choice picks the handler; code, a Zen model or a person does the work."""

import datetime
import os

import httpx

from hanzo_kai import Choice, Kai, RetryPolicy

INTENT = Choice(
    instructions="What is the employee asking for in `message`?",
    criteria={
        "pto_balance": "how many vacation days are left",
        "pto_request": "book days off",
        "payday": "when the salary is paid",
        "insurance": "health, dental or vision cover and benefits",
        "direct_deposit": "change the bank account the salary goes to",
        "other": "anything else",
    },
)
FLOOR = 0.5
BASE = os.environ.get("HANZO_BASE_URL", "https://api.hanzo.ai")
POLICY = ("Dental: two cleanings a year at no cost; fillings at 80%; orthodontics for children under 18 at 50%, "
          "up to $1,500 per child for life. Vision: one eye exam a year and $150 toward glasses or contacts every "
          "two years. Health: up to 20 physiotherapy sessions a year with a doctor's referral.")
BALANCES = {"e-1042": 7}


def balance(employee, message):
    return f"code: {BALANCES[employee]} vacation days left"


def payday(employee, message):
    """The last weekday of this month, or of next month once it has passed."""
    today = datetime.date.today()
    for months in (1, 2):
        end = (today.replace(day=1) + datetime.timedelta(days=32 * months)).replace(day=1) - datetime.timedelta(days=1)
        while end.weekday() > 4:
            end -= datetime.timedelta(days=1)
        if end >= today:
            return f"code: next payday is {end:%A %d %B %Y}"


def benefits(employee, message):
    reply = httpx.post(
        f"{BASE}/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['HANZO_API_KEY']}"},
        json={
            "model": "zen6",
            "messages": [
                {"role": "system", "content": "Answer from this policy only, in at most two sentences. " + POLICY},
                {"role": "user", "content": message},
            ],
        },
        timeout=120,
    )
    reply.raise_for_status()
    return "zen6: " + reply.json()["choices"][0]["message"]["content"].strip()


def person(team):
    return lambda employee, message: f"person: queued for {team}"


HANDLERS = {
    "pto_balance": balance,
    "payday": payday,
    "insurance": benefits,
    "pto_request": person("the employee's manager"),
    "direct_deposit": person("payroll, who confirm the new account by phone"),
    "other": person("the help desk"),
}

MESSAGES = [
    "How many days of holiday do I still have this year?",
    "I'd like to take the 23rd to the 27th of December off.",
    "When is the next payday?",
    "Does our dental plan cover braces for my son?",
    "I switched banks, please send my pay to my new account from next month.",
    "The printer on the third floor is jammed again.",
]

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    for message in MESSAGES:
        intent = kai.decide(state={"message": message}, questions={"intent": INTENT}).choices["intent"]
        handler = HANDLERS[intent.choice] if intent.confidence >= FLOOR else person("the help desk")
        print(f"{message}\n  {intent.choice} ({intent.confidence:.2f}) -> {handler('e-1042', message)}\n")
