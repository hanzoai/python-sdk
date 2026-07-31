"""The one place an example learns where the API is and who it is.

Every flow imports this and nothing else builds a client, so there is a single
answer to "which base URL?" and "which env var?" across all six.

Run any flow from the repo root::

    python -m examples.hello
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
    """Fail loudly and early when the key is absent.

    Without this the SDK sends an unauthenticated request and the flow dies on a
    401 several frames deep, which reads like an API bug rather than an unset
    shell variable.
    """
    key = os.environ.get("HANZO_API_KEY")
    if not key:
        raise SystemExit("HANZO_API_KEY is not set — export an IAM JWT or an hk- cloud key")
    return key


def client() -> ApiClient:
    """An ApiClient bound to the configured host and bearer key.

    ``access_token`` becomes ``Authorization: Bearer <key>``, which is the only
    scheme the spec declares.
    """
    return ApiClient(Configuration(host=BASE_URL, access_token=api_key()))


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
