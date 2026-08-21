"""Minting the token that lets one operator credential act as one subject.

An operator holds a single key. Every call it makes on behalf of a customer has
to be bound to that customer and nothing else. IAM does the binding: it reads
the grant off the key and issues a short-lived token for the subject named in
the request, so the credential carries the scope and no method has to take a
user id.

The mint answers on IAM's own host — `api.hanzo.ai` 404s it — and the path
carries the `iam` segment. The subject rides as the `id` query; there is no
body, because the grant is already on the key.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional
from urllib.parse import urlencode

from hanzoai.cloud.exceptions import ApiException

__all__ = ["Grant", "ISSUER"]

#: Where IAM answers. Override for a private estate.
ISSUER = "https://hanzo.id"

#: IAM's canonical mint. The platform API does not serve it.
PATH = "/v1/iam/tokens/issue"

#: Re-mint this many seconds early so a request never rides an about-to-die token.
SKEW = 30.0

#: Lifetime assumed when IAM states none.
TTL = 300.0


class Grant:
    """A cached, subject-bound token minted from an operator credential.

    Holds the token until it nears expiry and drops it on request, so a 401
    costs one extra mint rather than a failed call. Not thread-safe by design:
    the worst a race costs is a duplicate mint.

    :param key: the operator credential IAM reads the grant off.
    :param subject: a subject id, or the ``externalId`` the operator filed the
        member under.
    :param issuer: where IAM answers.
    :param transport: anything shaped like
        :class:`hanzoai.cloud.rest.RESTClientObject` — the client passes its own
        so the mint reuses one connection pool and the SDK's TLS settings.
    """

    def __init__(
        self,
        key: str,
        subject: str,
        issuer: str = ISSUER,
        transport: Optional[Any] = None,
    ) -> None:
        self.key = key
        self.subject = subject
        self.issuer = issuer.rstrip("/")
        self._transport = transport
        self._token: Optional[str] = None
        self._expires = 0.0

    @property
    def url(self) -> str:
        """The mint, subject and all."""
        return "{0}{1}?{2}".format(self.issuer, PATH, urlencode({"id": self.subject}))

    def token(self) -> str:
        """The live token, minting one if the cached token is gone or near expiry."""
        if self._token is not None and self._expires - time.monotonic() > SKEW:
            return self._token
        return self._mint()

    def invalidate(self) -> None:
        """Drops the cached token so the next read mints a fresh one."""
        self._token = None
        self._expires = 0.0

    def _mint(self) -> str:
        response = self.transport.request(
            "POST",
            self.url,
            headers={
                "Authorization": "Bearer {0}".format(self.key),
                "Accept": "application/json",
            },
        )
        response.read()
        body = response.data.decode("utf-8", "replace") if response.data else ""
        if not 200 <= response.status <= 299:
            raise ApiException.from_response(http_resp=response, body=body, data=None)

        # IAM answers camelCase.
        payload = json.loads(body) if body else {}
        token = payload.get("accessToken") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise ApiException(
                status=response.status,
                reason="IAM issued no token for {0}".format(self.subject),
                body=body,
            )

        expires_in = payload.get("expiresIn")
        seconds = float(expires_in) if isinstance(expires_in, (int, float)) else TTL
        self._token = token
        self._expires = time.monotonic() + seconds
        return token

    @property
    def transport(self) -> Any:
        if self._transport is None:
            from hanzoai.cloud.rest import RESTClientObject
            from hanzoai.cloud.configuration import Configuration

            self._transport = RESTClientObject(Configuration(host=self.issuer))
        return self._transport
