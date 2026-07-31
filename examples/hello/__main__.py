"""hello — who am I?

The smallest complete call: prove the key works and print the identity behind
it. ``GET /v1/bot/auth/me`` (operationId ``bot_authMe``).

This flow's whole job is to FAIL when the key is bad, so the route has to be one
that actually checks. Not every identity-shaped route does: ``/v1/ai/account``
answers 200 with ``type="anonymous-user"`` to a request carrying no
Authorization header at all, so a ``hello`` built on it prints a cheerful
identity for a key that would 401 everywhere else — worse than no check, because
it reads as proof. ``/v1/bot/auth/me`` answers 403
``{"error":"no validated principal"}``. Verified against api.hanzo.ai, not
assumed from the spec.

    python -m examples.hello
"""

from hanzoai.cloud import AuthApi

from examples.client import BASE_URL, client, run


def main() -> None:
    with client() as api:
        me = AuthApi(api).bot_auth_me()

    print(f"hello from {BASE_URL}")
    print(f"  {me.display_name or me.handle or '(unnamed)'} <{me.email or 'no email'}>")
    print(f"  id {me.id} · role {me.role}")


if __name__ == "__main__":
    run(main)
