"""Confidence gate: act on an answer above a threshold measured on labelled cases; send the rest to a person."""

import gzip
import json
import urllib.request

from hanzo_kai import Kai, Noul, RetryPolicy

HARNESS = ("https://raw.githubusercontent.com/hanzoai/benchmarks/"
           "039fbfe5fa5dcb1483407594d829fa822d78974a/decision/results/states.json.gz")
QUESTION = {
    "true_positive": Noul(
        instructions="This alert reflects genuinely malicious or unauthorised activity.",
        criteria={
            "true": "The underlying behaviour is malicious or unauthorised.",
            "false": "Benign activity, a misconfiguration, or a known false positive.",
        },
    )
}
TARGET = 0.95

with urllib.request.urlopen(HARNESS) as response:
    suites = json.loads(gzip.decompress(response.read()))
alerts = [case for case in suites["typed_decisions"] if case[2]["_wf"] == "security_incidents"]
sample, unseen = alerts[:40], alerts[40]

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    answers = []
    for state, _, gold in sample:
        d = kai.decide(state=state, questions=QUESTION)
        answers.append((d.nouls["true_positive"].noul, gold["true_positive"]["idx"] == 1))
    calibration = d.routing["calibration"]

    print(f"{len(answers)} alerts, {sum(truth for _, truth in answers)} of them true positives, {calibration}\n")
    print("threshold  acted  right  accuracy  to analyst")
    threshold = None
    for line in (0.5, 0.6, 0.7, 0.8, 0.9):
        acted = [(p >= 0.5) == truth for p, truth in answers if max(p, 1 - p) >= line]
        accuracy = sum(acted) / len(acted) if acted else float("nan")
        print(f"{line:>9}  {len(acted):>5}  {sum(acted):>5}  {accuracy:>8.3f}  {len(answers) - len(acted):>10}")
        if threshold is None and acted and accuracy >= TARGET:
            threshold = line
    print(f"\nlowest threshold with accuracy >= {TARGET}: {threshold}")

    def triage(alert):
        """incident, close or analyst for one alert, under the threshold and calibration measured above."""
        d = kai.decide(state=alert, questions=QUESTION)
        p = d.nouls["true_positive"].noul
        if threshold is None or d.routing["calibration"] != calibration or max(p, 1 - p) < threshold:
            return "analyst", p
        return ("incident" if p >= 0.5 else "close"), p

    verdict, p = triage(unseen[0])
    label = "true positive" if unseen[2]["true_positive"]["idx"] == 1 else "false positive"
    print(f"alert 41, outside the sample: P(true) {p:.4f} -> {verdict}; the harness labels it a {label}")
