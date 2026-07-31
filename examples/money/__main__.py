"""money — what is in the wallet, and what spent it.

    GET /v1/billing/balance   cloud_get_v1_billing_balance
    GET /v1/billing/usage     cloud_get_v1_billing_usage

Neither call takes an org: both derive the tenant SERVER-side from the token's
``owner`` claim, so a key can only ever read its own money. There is no org
argument to pass.

Both are declared with a ``default`` response and no ``content``, so the typed
methods return None even though the server sends JSON. That is a spec gap, not
an SDK one — 696 of 2425 operations currently model no response body — so this
example reads the raw payload through the generated ``*_without_preload_content``
variant rather than pretending a type it was not given. When the schemas land,
these become ordinary typed calls and nothing else about them changes.

    python -m examples.money
"""

import json

from hanzoai.cloud import BillingApi

from examples.client import client, run


def main() -> None:
    with client() as api:
        billing = BillingApi(api)
        for label, call in (
            ("balance", billing.cloud_get_v1_billing_balance_without_preload_content),
            ("usage", billing.cloud_get_v1_billing_usage_without_preload_content),
        ):
            response = call()
            body = response.read()
            # The raw variant does NOT raise on a 4xx — that check is part of the
            # typed deserialization this operation does not have. Without this,
            # a 401 body prints as though it were the balance.
            if response.status >= 400:
                raise SystemExit(f"HTTP {response.status}: {body.decode(errors='replace')}")
            print(f"{label}: {json.dumps(json.loads(body), indent=2)}")


if __name__ == "__main__":
    run(main)
