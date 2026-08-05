"""hello — prove the key works.

``GET /v1/keys`` (operationId ``get_v1_keys``): the caller's own API keys.

This flow's whole job is to FAIL when the key is bad, so the route has to be one
that actually checks, and that is decided by probing api.hanzo.ai rather than by
reading the document. Three identity-shaped routes are disqualified for
answering 200 to a caller carrying no credential at all — ``/v1/ai/account``
(``type="anonymous-user"``), ``/v1/iam/whoami`` and ``/v1/iam/account`` (both
200 ``{"status":"error"}``) — and a ``hello`` built on any of them prints a
cheerful identity for a key that would be refused everywhere else, which is
worse than no check because it reads as proof.

``/v1/keys`` answers 403 ``{"code":"forbidden","error":"sign in to manage API
keys"}`` with no key and with a bogus one, while the nonsense sibling
``/v1/keys-zzq9`` answers 404 — so the 403 is this route refusing, not a
wildcard door swallowing the address.

This replaces ``bot_authMe`` (``GET /v1/bot/auth/me``), which no longer
resolves: cloud relays all of ``/v1/bot`` through one ``app.All("/v1/bot/*")``,
so the document carries ``/v1/bot/{wildcard1}`` and no operation at that
address. The old id existed only in a hand-authored spec and vanished with it —
which is the reason an example's operationId has to come from the served
document.

    python -m examples.hello
"""

from hanzoai.cloud import KeysApi

from examples.client import BASE_URL, client, run


def main() -> None:
    with client() as api:
        listing = KeysApi(api).get_v1_keys()

    keys = listing.keys or []
    print(f"hello from {BASE_URL}")
    print(f"  the key is accepted; this org has {len(keys)} API key(s)")
    for key in keys[:5]:
        # `key.key` is the secret itself and is never printed. The prefix is the
        # part that names one without disclosing it.
        print(f"  {key.prefix or '(no prefix)'} · {key.type or 'untyped'} · created {key.created_at or 'unknown'}")
    if len(keys) > 5:
        print(f"  … and {len(keys) - 5} more")


if __name__ == "__main__":
    run(main)
