"""The one place an example learns where the API is and who it is.

Every flow imports this and nothing else builds a client, so there is a single
answer to "which base URL?" and "which env var?" across all six.

Run any flow from the repo root::

    python -m examples.models     # no credential — GET /v1/models is public
    python -m examples.hello      # needs HANZO_CLIENT_ID and HANZO_CLIENT_SECRET
"""

from __future__ import annotations

import os
import sys

from hanzoai import Client
from hanzoai.cloud import ApiClient, Configuration
from hanzoai.cloud.exceptions import ApiException

#: Default host. ``HANZO_BASE_URL`` overrides it (staging, a local cloud, a tunnel).
BASE_URL = os.environ.get("HANZO_BASE_URL", "https://api.hanzo.ai")

#: ``zen4`` is the flagship the spec documents as its own example value.
MODEL = os.environ.get("HANZO_MODEL", "zen4")


def client() -> Client:
    """A client holding this caller's IAM credential.

    ``Client`` exchanges ``HANZO_CLIENT_ID`` and ``HANZO_CLIENT_SECRET`` for a
    short-lived access token and presents that. It takes no bearer, because a
    credential handed to an SDK is a credential nobody rotates and one that says
    nothing about who is calling.

    It is an ``ApiClient``, so every generated operation takes it unchanged, and
    it answers the six capabilities besides. ``Configuration.auth_settings()``
    is where the token joins a generated request: the document declares one
    security scheme, ``bearer``, and applies it to every operation except the
    handful marked ``security: []``, so the credential goes where the document
    says it belongs and nowhere else.
    """
    return Client(base=BASE_URL)


def public() -> ApiClient:
    """An ApiClient with no credential, for the operations that need none.

    Four of the document's 2479 operations carry ``security: []`` — ``GET
    /v1/models``, ``GET /v1/models/providers``, ``GET /v1/commands``, ``GET
    /v1/openapi.json``. They are the public face of the API, and they answer 200
    to a caller who has nothing. ``examples.models`` runs on this.
    """
    return ApiClient(Configuration(host=BASE_URL))


def run(main) -> None:
    """Invoke a flow and report an API failure the way a caller can act on.

    ApiException stringifies to the status line alone; the server's explanation
    is in ``.body``, which is the part worth printing.
    """
    try:
        main()
    except ApiException as e:
        print(f"HTTP {e.status}: {e.body}", file=sys.stderr)
        raise SystemExit(1) from e
