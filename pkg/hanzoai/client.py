"""The client, and the one call that scopes it to a tenant.

    from hanzoai import Client
    from hanzoai.cloud import Configuration, MemoryApi

    hanzo = Client(Configuration(access_token="sk-..."))      # the operator
    memory = MemoryApi(hanzo.as_("user_42"))                  # one customer

`Client` is the generated :class:`~hanzoai.cloud.api_client.ApiClient` plus two
behaviours the generator has no way to know about — token scoping and the held
result — so every one of the generated API classes takes it unchanged.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from hanzoai.grant import ISSUER, Grant
from hanzoai.result import Held, Approval
from hanzoai.cloud.api_client import ApiClient
from hanzoai.cloud.exceptions import ApiException
from hanzoai.cloud.configuration import Configuration

__all__ = ["Client"]


class Client(ApiClient):
    """An API client, optionally bound to one subject.

    Construct it with an operator credential and call :meth:`as_` per customer.
    The returned client mints a subject-bound token from IAM, sends it on every
    call, and re-mints once on a 401 before giving up — so a rotated or expired
    token costs a round trip, not an error the caller has to handle.

    :param issuer: where IAM answers, when it is not the public issuer.
    :param grant: the mint this client sends for. `None` on an operator client.
        A client that has one writes the live token into its configuration on
        the way into every request, so it needs a configuration of its own —
        which is what :meth:`as_` hands it.
    """

    def __init__(
        self,
        configuration: Optional[Configuration] = None,
        header_name: Optional[str] = None,
        header_value: Optional[str] = None,
        cookie: Optional[str] = None,
        *,
        issuer: str = ISSUER,
        grant: Optional[Grant] = None,
    ) -> None:
        super().__init__(configuration, header_name, header_value, cookie)
        self.issuer = issuer
        self.grant = grant

    def as_(self, subject: str) -> "Client":
        """Returns a client scoped to `subject` — a subject id or an externalId.

        Spelled with the trailing underscore PEP 8 prescribes for a name that
        collides with a keyword, so the platform's one word for this survives
        into Python instead of growing a synonym here.

        The credential is the scope: no operation on the returned client takes a
        user id, so there is none to pass wrongly and none to forget.
        """
        key = self.configuration.access_token
        if not key:
            raise ApiException(
                status=0,
                reason="no operator credential to scope: set Configuration.access_token",
            )
        configuration = copy.deepcopy(self.configuration)
        # The operator key never rides a scoped client. The minted token replaces
        # it on the way into every request.
        configuration.access_token = None
        return Client(
            configuration,
            issuer=self.issuer,
            grant=Grant(key, subject, self.issuer, self.rest_client),
        )

    # Where the token joins the request. The generated serializer reads
    # `configuration.access_token` through `auth_settings()`, so refreshing it
    # here puts the live token on every operation without touching one of them.
    def param_serialize(self, *args: Any, **kwargs: Any) -> Any:
        if self.grant is not None:
            self.configuration.access_token = self.grant.token()
        return super().param_serialize(*args, **kwargs)

    def call_api(
        self,
        method: str,
        url: str,
        header_params: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        post_params: Optional[Any] = None,
        _request_timeout: Optional[Any] = None,
    ) -> Any:
        response = super().call_api(method, url, header_params, body, post_params, _request_timeout)
        if response.status == 401 and self.grant is not None:
            self.grant.invalidate()
            header_params = dict(header_params or {})
            header_params["Authorization"] = "Bearer {0}".format(self.grant.token())
            response = super().call_api(method, url, header_params, body, post_params, _request_timeout)
        return response

    def response_deserialize(self, response_data: Any, response_types_map: Optional[Any] = None) -> Any:
        """A held call raises rather than returning — it produced no value.

        The hold arrives as 202 with ``status: "held"``. No operation declares a
        schema for that, so the generated deserializer answers it with `None`
        and the call reads as one that succeeded and returned nothing. The
        dozen operations whose 202 means "accepted, working on it" carry their
        own schema and pass straight through.

        Wrap a call in :func:`hanzoai.result` to handle the hold as a value.
        """
        if response_data.status == 202:
            body = response_data.data
            if isinstance(body, (bytes, bytearray)):
                body = body.decode("utf-8", "replace")
            approval = Approval.held(body)
            if approval is not None:
                raise Held(approval, body=body)
        return super().response_deserialize(response_data, response_types_map)
