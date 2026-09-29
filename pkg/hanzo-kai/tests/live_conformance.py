"""Runs every conformance fixture against the live API and prints, rule by rule, which cases hold.

    HANZO_API_KEY=sk-... python tests/live_conformance.py [base_url]

Cases marked `"live": false` need a fault the API cannot be asked for and are listed as skipped.
A rate-limited attempt waits out its `Retry-After` and tries again, up to ten times, so a failure
names the contract and not the pace.
Exits 1 when any case fails. pytest does not collect this file; `test_conformance.py` runs the
same fixtures against the fake service.
"""

import sys
import time
import datetime
import platform
import functools

import hanzo_kai
from hanzo_kai import Kai, Noul, RetryPolicy
from conformance import run, load, client


@functools.cache
def version(base: str) -> str:
    """The served checkpoint's versioned id: `kai-` and the first 12 hex digits of its weights' SHA-256."""
    with Kai(base_url=base) as kai:
        d = kai.decide("ping", {"q": Noul(instructions="The message is a greeting.")})
    return "kai-" + d.routing["sha256"][:12]


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "https://api.hanzo.ai"
    now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    print(f"# hanzo-kai {hanzo_kai.__version__} conformance against {base}, python {platform.python_version()}, {now}")
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    rule = None
    for case in load():
        if case.rule != rule:
            rule = case.rule
            print(f"\n{rule}")
        if not case.live:
            counts["SKIP"] += 1
            print(f"  SKIP {case.name}: needs a fault the live API cannot be asked for")
            continue
        sdk, attempts = client(case, base_url=base, retry=RetryPolicy(max_retries=10))
        started = time.monotonic()
        with sdk:
            failures = run(case, sdk, attempts, lambda: version(base))
        verdict = "FAIL" if failures else "PASS"
        counts[verdict] += 1
        took = f"{time.monotonic() - started:.1f} s"
        print(f"  {verdict} {case.name} ({took})" + "".join(f"\n       {failure}" for failure in failures))
    print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
