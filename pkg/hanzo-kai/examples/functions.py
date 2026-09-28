"""Turn a request into a call to an ordinary typed function, and ask back when the call is not settled.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

import inspect
import re
import typing
from typing import Literal

from hanzo_kai import Kai, Choice, RetryPolicy

Service = Literal["api", "console", "iam", "kms", "docs"]
Env = Literal["staging", "production"]
Replicas = Literal[1, 2, 3, 5, 10]


def deploy(service: Service, env: Env) -> str:
    """deploy a service"""
    return f"deploy({service!r}, {env!r})"


def rollback(service: Service, env: Env) -> str:
    """roll back a release"""
    return f"rollback({service!r}, {env!r})"


def scale(service: Service, replicas: Replicas) -> str:
    """scale replicas"""
    return f"scale({service!r}, {replicas})"


def logs(service: Service, env: Env) -> str:
    """read logs"""
    return f"logs({service!r}, {env!r})"


FUNCTIONS = {f.__name__: f for f in (deploy, rollback, scale, logs)}
VALUES = {name: typing.get_args(hint) for f in FUNCTIONS.values() for name, hint in inspect.get_annotations(f).items() if name != "return"}
PROMPTS = {
    "service": "Which service is the user asking about in `utterance`?",
    "env": "Which environment is the user asking about in `utterance`?",
    "replicas": "How many replicas is the user asking for in `utterance`?",
}
QUESTIONS = {
    "function": Choice(
        instructions="What is the user asking for in `utterance`?",
        criteria={name: f.__doc__ for name, f in FUNCTIONS.items()} | {"none": "something else"},
    ),
    **{name: Choice(instructions=PROMPTS[name], criteria=[str(v) for v in values]) for name, values in VALUES.items()},
}
WORDS = {"prod": "production", "one": 1, "single": 1, "two": 2, "three": 3, "five": 5, "ten": 10}

# Request, the function a person would pick, and the call: "ask" when an argument is open, "none" when no operation.
REQUESTS = [
    ("ship the latest iam build to staging", "deploy", "deploy('iam', 'staging')"),
    ("prod console broke after today's release, put the previous one back", "rollback", "rollback('console', 'production')"),
    ("we need five copies of the api", "scale", "scale('api', 5)"),
    ("show me the kms logs from staging", "logs", "logs('kms', 'staging')"),
    ("push docs to production", "deploy", "deploy('docs', 'production')"),
    ("undo the last api release on staging", "rollback", "rollback('api', 'staging')"),
    ("scale iam down to a single replica", "scale", "scale('iam', 1)"),
    ("tail the production api logs", "logs", "logs('api', 'production')"),
    ("give the console ten replicas", "scale", "scale('console', 10)"),
    ("the login service on prod needs its previous release back", "rollback", "rollback('iam', 'production')"),
    ("roll it back", "rollback", "ask"),
    ("deploy to staging", "deploy", "ask"),
    ("what's the weather in Kyoto?", "none", "none"),
]


def literal(text, values):
    """The one value the text names outright, or None."""
    said = {WORDS.get(w, int(w) if w.isdigit() else w) for w in re.findall(r"[a-z0-9]+", text.lower())}
    found = [v for v in values if v in said]
    return found[0] if len(found) == 1 else None


def plan(decision, request, arguments):
    """The call to make, or what to ask: arguments come from Kai's answers or from the words of the request."""
    function = decision.choices["function"]
    if function.confidence < 0.5:
        return "ask"
    if function.choice == "none":
        return "none"
    args = {}
    for name in inspect.signature(FUNCTIONS[function.choice]).parameters:
        if arguments == "kai":
            answer = decision.choices[name]
            value = type(VALUES[name][0])(answer.choice) if answer.confidence >= 0.5 else None
        else:
            value = literal(request, VALUES[name])
        if value is None:
            return "ask"
        args[name] = value
    return FUNCTIONS[function.choice](**args)


tally, named = {"kai": [0, 0, 0], "words": [0, 0, 0]}, 0
with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    for request, function, gold in REQUESTS:
        decision = kai.decide({"utterance": request}, QUESTIONS)
        f = decision.choices["function"]
        named += f.choice == function
        said = ", ".join(f"{n} {decision.choices[n].choice} {decision.choices[n].confidence:.2f}" for n in VALUES)
        print(f"{request}\n    function {f.choice} {f.confidence:.2f} (gold {function}); {said}")
        for arguments in ("kai", "words"):
            got = plan(decision, request, arguments)
            outcome = 0 if got == gold else 2 if got == "ask" else 1
            tally[arguments][outcome] += 1
            print(f"    arguments from {arguments:5}: {got:34} {('right', 'WRONG', 'asked back')[outcome]}, gold {gold}")

print(f"\nfunction named right: {named} of {len(REQUESTS)}")
for arguments, (right, wrong, asked) in tally.items():
    print(f"arguments from {arguments:5}: {right} right, {wrong} wrong, {asked} asked back, of {len(REQUESTS)}")
