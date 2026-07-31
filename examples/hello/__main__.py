"""hello — who am I?

The smallest complete call: prove the key works and print the identity behind
it. ``GET /v1/ai/account`` (operationId ``ai_getAccount``).

This is also where you meet the envelope, because every ``/v1/ai/*`` route uses
it: ``status`` is the OUTCOME, not the HTTP code. A handled failure comes back
as HTTP 200 with ``status='error'`` and a human ``msg``, so the client does NOT
raise and code that only checks for an exception reports success on a failure.
Branch on ``status``. Every AI-plane example in this repo does.

    python -m examples.hello
"""

import json

from hanzoai.cloud import AccountApi

from examples.client import BASE_URL, client, run


def main() -> None:
    with client() as api:
        envelope = AccountApi(api).ai_get_account()

    if envelope.status != "ok":
        raise SystemExit(f"account read failed: {envelope.msg or 'no message'}")

    print(f"hello from {BASE_URL}")
    print(json.dumps(envelope.data, indent=2, default=str))


if __name__ == "__main__":
    run(main)
