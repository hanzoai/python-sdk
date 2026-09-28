"""Turn support conversations into numbers with Kai's answers, then fit a small regressor to labels."""

import gzip
import json
import pathlib
import tempfile
import urllib.request

import numpy as np
from hanzo_kai import Kai, Noul, Score, RetryPolicy

HARNESS = "https://raw.githubusercontent.com/hanzoai/benchmarks/039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz"

FEATURES = {
    "upset": Noul(
        instructions="The customer is upset.",
        criteria={"true": "they sound angry, frustrated or anxious", "false": "they sound calm or satisfied"},
    ),
    "leave": Noul(
        instructions="The customer threatens to leave.",
        criteria={
            "true": "they mention cancelling, switching, a chargeback, a dispute or a bad review",
            "false": "no such threat",
        },
    ),
    "again": Noul(
        instructions="The problem has happened before.",
        criteria={
            "true": "they say it keeps happening, or was reported before and is still not fixed",
            "false": "this is the first report",
        },
    ),
    "money": Noul(
        instructions="The customer has lost money.",
        criteria={
            "true": "a wrong, duplicate or unexpected charge, or a refund that has not arrived",
            "false": "no money is at stake",
        },
    ),
    "effort": Score(
        instructions="How much effort has the customer spent on this problem?",
        criteria=["almost none", "one message", "several messages or attempts", "repeated contacts over days"],
    ),
    "tone": Score(
        instructions="How does the customer's last message sound?",
        criteria=["pleased", "neutral", "annoyed", "furious"],
    ),
}


def harness(suite: str) -> list:
    """The pinned harness's cases for one suite, each [state, questions, gold]."""
    path = pathlib.Path(tempfile.gettempdir()) / "hanzo-kai-cookbook" / "states.json.gz"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(HARNESS, path)
    with gzip.open(path) as file:
        return json.load(file)[suite]


def value(answers, name: str) -> float:
    """A noul's P(yes) or a score's expected level."""
    return answers.nouls[name].noul if name in answers.nouls else answers.scores[name].score


def ridge(x: np.ndarray, y: np.ndarray, train: np.ndarray, penalty: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Predictions for every row from a ridge fit on the training rows, and the standardized weights."""
    mean, scale = x[train].mean(0), x[train].std(0) + 1e-9
    z = (x - mean) / scale
    weights = np.linalg.solve(
        z[train].T @ z[train] + penalty * np.eye(x.shape[1]), z[train].T @ (y[train] - y[train].mean())
    )
    return y[train].mean() + z @ weights, weights


cases = [case for case in harness("typed_decisions") if case[2]["_wf"] == "customer_service"]
x, direct, y = [], [], []
with Kai(retry=RetryPolicy(max_retries=10)) as kai:
    for state, questions, gold in cases:
        answers = kai.decide(state=state, questions=FEATURES | {"churn": questions["churn_risk"]})
        x.append([value(answers, name) for name in FEATURES])
        direct.append(answers.scores["churn"].score)
        y.append(gold["churn_risk"]["gold_score"])  # raters' mean level, 0 to 3
x, direct, y = np.array(x), np.array(direct)[:, None], np.array(y)

order = np.random.default_rng(7).permutation(len(y))
train, test = order[:60], order[60:]
print(f"{len(y)} conversations: {len(train)} to fit, {len(test)} to test; churn risk 0 to 3, mean {y.mean():.2f}\n")
print(f"{'predictor':34} test RMSE  correlation")
fits = {
    "mean of the training labels": np.full(len(y), y[train].mean()),
    "Kai's churn score, as answered": direct[:, 0],
    "Kai's churn score, refit": ridge(direct, y, train)[0],
    "six Kai features": ridge(x, y, train)[0],
    "six features and the churn score": ridge(np.hstack([x, direct]), y, train)[0],
}
for name, prediction in fits.items():
    error = np.sqrt(np.mean((prediction[test] - y[test]) ** 2))
    r = f"{np.corrcoef(prediction[test], y[test])[0, 1]:.2f}" if np.ptp(prediction[test]) else "-"
    print(f"{name:34} {error:9.3f}  {r:>11}")

print("\nweights of the six-feature fit, per standard deviation of each feature:")
print("  ".join(f"{name} {w:+.3f}" for name, w in zip(FEATURES, ridge(x, y, train)[1], strict=True)))
