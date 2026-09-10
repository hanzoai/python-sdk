"""Acting as one subject.

A caller holds one identity. Every call it makes on behalf of a customer has to
be bound to that customer and nothing else. IAM does the binding: it reads the
act grant off the caller's own token and issues a short-lived token for the
subject named in the request, so the credential carries the scope and no method
has to take a user id.

The mint answers on IAM's own host — `api.hanzo.ai` 404s it — and the path
carries the `iam` segment. The subject rides as the `id` query; there is no
body, because the grant is already on the token.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional
from urllib.parse import urlencode

from hanzoai.token import TTL, EARLY, ISSUER
from hanzoai.answer import error

__all__ = ["Grant"]

#: IAM's canonical act mint. The platform API does not serve it.
PATH = "/v1/iam/tokens/issue"


class Grant:
    """A subject-bound token, minted from the caller's own token and held to expiry.

    Not thread-safe by design: the worst a race costs is a duplicate mint.

    :param operator: the credential IAM reads the act grant off — a
        :class:`hanzoai.Token`, or anything else that answers `token()` and
        `invalidate()`.
    :param subject: a subject id, or the ``externalId`` the operator filed the
        member under.
    :param issuer: where IAM answers.
    :param transport: anything shaped like
        :class:`hanzoai.cloud.rest.RESTClientObject`.
    """

    def __init__(
        self,
        operator: Any,
        subject: str,
        issuer: str = ISSUER,
        transport: Optional[Any] = None,
    ) -> None:
        self.operator = operator
        self.subject = subject
        self.issuer = issuer.rstrip("/")
        self._transport = transport
        self._held: Optional[str] = None
        self._until = 0.0

    @property
    def url(self) -> str:
        """The mint, subject and all."""
        return "{0}{1}?{2}".format(self.issuer, PATH, urlencode({"id": self.subject}))

    def token(self) -> str:
        """The live subject token, minting one when what is held nears expiry."""
        if self._held is not None and self._until - time.monotonic() > EARLY:
            return self._held
        return self._mint()

    def invalidate(self) -> None:
        """Drops the held token so the next read mints a fresh one.

        The operator's token is dropped too: a subject token IAM refused may
        have been refused because the token it was minted from is stale.
        """
        self._held = None
        self._until = 0.0
        self.operator.invalidate()

    def _mint(self) -> str:
        response = self.transport.request(
            "POST",
            self.url,
            headers={
                "Authorization": "Bearer " + self.operator.token(),
                "Accept": "application/json",
            },
        )
        response.read()
        body = response.data.decode("utf-8", "replace") if response.data else ""
        if not 200 <= response.status <= 299:
            raise error(
                response.status,
                "{0} refused an act grant for {1}".format(self.issuer, self.subject),
                body,
            )

        # IAM answers camelCase here. The oauth mint next door answers RFC 6749
        # snake_case; they are different endpoints and each keeps its own wire.
        payload = json.loads(body) if body else {}
        token = payload.get("accessToken") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise error(
                response.status,
                "IAM issued no token for {0}".format(self.subject),
                body,
            )

        seconds = payload.get("expiresIn")
        self._held = token
        self._until = time.monotonic() + (float(seconds) if isinstance(seconds, (int, float)) else TTL)
        return token

    @property
    def transport(self) -> Any:
        if self._transport is None:
            from hanzoai.cloud.rest import RESTClientObject
            from hanzoai.cloud.configuration import Configuration

            self._transport = RESTClientObject(Configuration(host=self.issuer))
        return self._transport
