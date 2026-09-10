"""The access token the client presents, minted from its own IAM credential.

A caller holds a clientId and a clientSecret. It exchanges them for a
short-lived access token and sends that. It never takes a bearer from a config
value: a credential the SDK is handed is a credential nobody rotates, and it
says nothing about who is calling — which is the one question every gate in the
estate exists to answer.

    POST {issuer}/v1/iam/oauth/token
    Authorization: Basic base64(id:secret)
    Content-Type: application/x-www-form-urlencoded

    grant_type=client_credentials&resource={resource}

`resource` is RFC 8707: it names the server the token is for, so a token minted
for api.hanzo.ai is useless anywhere else. IAM verifies the exchange (HIP-0111)
and every resource server verifies the result against the published JWKS.
"""

from __future__ import annotations

import json
import time
from base64 import b64encode
from typing import Any, Optional

from hanzoai.answer import Fault

__all__ = ["Token", "ISSUER", "BASE", "PATH", "EARLY", "TTL"]

#: Where IAM answers. Override for a private estate.
ISSUER = "https://hanzo.id"

#: The one endpoint. Every capability path is `/v1/...` below it.
BASE = "https://api.hanzo.ai"

#: IAM's client_credentials exchange.
PATH = "/v1/iam/oauth/token"

#: How long before expiry a held token stops being offered. A token that dies
#: in flight is a 401 the caller cannot tell from a revoked identity, so it is
#: replaced while it still works.
EARLY = 60.0

#: Lifetime assumed when IAM states none.
TTL = 300.0


class Token:
    """A live access token, minted on demand and held until it nears expiry.

    Not thread-safe by design: the worst a race costs is a duplicate mint.

    :param id: the IAM clientId.
    :param secret: the IAM clientSecret.
    :param issuer: where IAM answers.
    :param resource: the RFC 8707 audience the token is minted for.
    :param transport: anything shaped like
        :class:`hanzoai.cloud.rest.RESTClientObject`. Left unset it builds its
        own against `issuer`, which is a different host from the API and so a
        different pool either way.
    """

    def __init__(
        self,
        id: str,
        secret: str,
        issuer: str = ISSUER,
        resource: str = BASE,
        transport: Optional[Any] = None,
    ) -> None:
        self.id = id
        self.secret = secret
        self.issuer = issuer.rstrip("/")
        self.resource = resource
        self._transport = transport
        self._held: Optional[str] = None
        self._until = 0.0

    @property
    def url(self) -> str:
        """The mint."""
        return self.issuer + PATH

    def token(self) -> str:
        """The live token, minting one when what is held is gone or nearly so.

        A client built with no credential raises here rather than at
        construction: there is nothing to exchange, so nothing is sent to IAM
        and nothing is sent unsigned to the gateway — an unsigned call comes
        back a bare 403, which reads as a refusal of the caller rather than the
        absence of one.
        """
        if not self.id or not self.secret:
            raise Fault(
                0,
                reason="no IAM client credentials: pass id and secret, or set HANZO_CLIENT_ID and HANZO_CLIENT_SECRET",
            )
        if self._held is not None and self._until - time.monotonic() > EARLY:
            return self._held
        return self._mint()

    def invalidate(self) -> None:
        """Drops the held token so the next read mints a fresh one."""
        self._held = None
        self._until = 0.0

    def _mint(self) -> str:
        basic = b64encode("{0}:{1}".format(self.id, self.secret).encode()).decode()
        form = [("grant_type", "client_credentials")]
        if self.resource:
            form.append(("resource", self.resource))

        response = self.transport.request(
            "POST",
            self.url,
            headers={
                "Authorization": "Basic " + basic,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            post_params=form,
        )
        response.read()
        body = response.data.decode("utf-8", "replace") if response.data else ""
        payload = _json(body)

        token = payload.get("access_token")
        if not 200 <= response.status <= 299 or not isinstance(token, str) or not token:
            # Say which identity was refused. A 401 here reads the same whether
            # the id is wrong, the secret is stale, or the app may not use this
            # grant, and the reader is holding none of those.
            raise Fault(
                response.status,
                reason="{0} refused client {1}: {2} {3}".format(
                    self.issuer,
                    self.id,
                    payload.get("error", ""),
                    payload.get("error_description", ""),
                ).rstrip(),
            )

        seconds = payload.get("expires_in")
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


def _json(body: str) -> Any:
    try:
        return json.loads(body) if body else {}
    except ValueError:
        return {}
