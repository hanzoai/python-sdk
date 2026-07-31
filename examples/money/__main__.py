"""money — what is in the wallet, and what spent it.

    GET /v1/billing/balance   billing_billingBalance   prepaid credit balance
    GET /v1/billing/usage     billing_billingUsage     per-request usage ledger

Neither call takes an org: both derive the tenant SERVER-side from the JWT
``owner`` claim, so a key can only ever read its own money. There is no org
argument to pass and no ``X-Org-Id`` header to set.

    python -m examples.money
"""

from datetime import datetime, timedelta, timezone

from hanzoai.cloud import BillingApi

from examples.client import client, run


def main() -> None:
    with client() as api:
        billing = BillingApi(api)

        print("balance:", billing.billing_billing_balance().to_str())

        # Unbounded, the ledger is every request the org ever made. Ask for a window.
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)
        usage = billing.billing_billing_usage(
            start=start.isoformat(),
            end=end.isoformat(),
        )
        print("usage (last 7d):", usage.to_str())


if __name__ == "__main__":
    run(main)
