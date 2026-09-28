"""Where Jev is ahead of Kai a7 on the frozen harness: accuracy, calibration, and MASSIVE by language."""

import json
import urllib.request

SCORES = ("https://raw.githubusercontent.com/hanzoai/benchmarks/"
          "c61361fedc5882b0d83b2f5d5a6a35c56ffeb3c3/decision/results/kai-a7/scores.json")

with urllib.request.urlopen(SCORES) as response:
    suites = json.load(response)["suites"]

print(f"{'':<26} {'accuracy':^13}  {'ECE':^13}  {'mean p_max':^13}")
print(f"{'suite':<26} {'Kai':>6} {'Jev':>6}  {'Kai':>6} {'Jev':>6}  {'Kai':>6} {'Jev':>6}")
for name, row in suites.items():
    if name.startswith("massive."):
        continue
    kai, jev = row["kai"], row["jev"]
    if jev["accuracy"] > kai["accuracy"] or jev["ece"] < kai["ece"]:
        print(f"{name:<26} {kai['accuracy']:>6.3f} {jev['accuracy']:>6.3f}  {kai['ece']:>6.3f} {jev['ece']:>6.3f}  "
              f"{kai['mean_confidence']:>6.3f} {jev['mean_confidence']:>6.3f}")

behind = sorted((row["kai"]["accuracy"] - row["jev"]["accuracy"], name[8:])
                for name, row in suites.items()
                if name.startswith("massive.") and row["jev"]["accuracy"] > row["kai"]["accuracy"])
print(f"\nMASSIVE, 100 utterances a language: Jev ahead in {len(behind)} of 51")
print(", ".join(f"{lang} {gap * 100:+.0f}" for gap, lang in behind))
