"""The one place an example learns where the API is and who it is.

Every flow imports this and nothing else builds a client, so there is a single
answer to "which base URL?" and "which env var?" across all six.

Run any flow from the repo root::

    python -m examples.models     # no credential — GET /v1/models is public
    python -m examples.hello      # needs HANZO_API_KEY
"""

from __future__ import annotations

import os
import sys

from hanzoai.cloud import ApiClient, Configuration
from hanzoai.cloud.exceptions import ApiException

#: Default host. ``HANZO_BASE_URL`` overrides it (staging, a local cloud, a tunnel).
BASE_URL = os.environ.get("HANZO_BASE_URL", "https://api.hanzo.ai")

#: ``zen4`` is the flagship the spec documents as its own example value.
MODEL = os.environ.get("HANZO_MODEL", "zen4")


def api_key() -> str:
    """Fail loudly and early when the key is absent or of the wrong shape.

    Without this the SDK sends an unauthenticated request and the flow dies on a
    403 several frames deep, which reads like an API bug rather than an unset
    shell variable.

    A ``pk-`` is rejected here for the same reason. It is the PUBLISHABLE shape:
    cloud resolves it to an org so a browser beacon can be attributed, but the
    identity boundary refuses it outright, so it never becomes a principal. Every
    route below wants one — ``/v1/tools`` says so in as many words, "a validated
    principal is required" — so a ``pk-`` collects the same 403 as no key at all,
    and that 403 reads like a revoked key rather than the wrong shape of key.
    """
    key = os.environ.get("HANZO_API_KEY")
    if not key:
        raise SystemExit("HANZO_API_KEY is not set — export an sk- cloud key or an IAM access token")
    if key.startswith("pk-"):
        raise SystemExit("HANZO_API_KEY is a pk- (publishable) key, which authenticates nobody — use an sk-")
    return key


def client() -> ApiClient:
    """An ApiClient carrying the credential the generated code knows how to send.

    ``access_token`` is the whole configuration. The document declares one
    security scheme — ``bearer``, HTTP bearer — and applies it to every operation
    except the four marked ``security: []``, so the generator wrote a populated
    ``Configuration.auth_settings()`` and an ``auth_settings=['bearer']`` into
    2498 call sites. ``ApiClient._apply_auth_params`` reads that and sets
    ``Authorization: Bearer <token>`` on the way out.

    This used to pass ``header_name``/``header_value`` on the ApiClient, because
    the document declared no scheme at all: ``auth_settings()`` returned ``{}``,
    ``access_token`` was read by nothing, and a client built the obvious way sent
    no ``Authorization`` header. That is fixed at the source — in the document —
    which is where every other language got the same fix.

    The header goes only where the document says it belongs. A flow that calls a
    ``security: []`` operation through this client sends no credential on that
    call, which is the correct behaviour and not a hole: those four operations
    are public.
    """
    return ApiClient(Configuration(host=BASE_URL, access_token=api_key()))


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
