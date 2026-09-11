"""The client: one credential, one endpoint, six capabilities.

    from hanzoai import Client

    c = Client()                          # id and secret from the environment
    left = c.budget.left()
    a = c.search.find("q3 incident postmortems")

It is also the generated client, so a caller who needs an operation the six do
not cover keeps the same credential::

    from hanzoai.cloud import IamApi

    IamApi(c.as_("usr_7")).get_iam_keys(...)

Two things the generator cannot know about live here: where the credential
comes from, and how a call is scoped to one subject. Everything else about a
capability lives in that capability's own module.
"""

from __future__ import annotations

import os
import json
import time
from typing import Any, Dict, Optional
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode

from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError, ResponseError

from hanzoai import wire
from hanzoai.kb import Kb
from hanzoai.audit import Audit
from hanzoai.grant import Grant
from hanzoai.graph import Graph
from hanzoai.token import BASE, ISSUER, Token
from hanzoai.answer import Held, held, value
from hanzoai.budget import Budget
from hanzoai.policy import Policy
from hanzoai.search import Search
from hanzoai.cloud.api_client import ApiClient
from hanzoai.cloud.configuration import Configuration

__all__ = ["Client"]

#: The longest Retry-After a call sleeps through, in seconds. api.hanzo.ai
#: answers an exhausted quota with the time until it resets, which is hours; a
#: longer wait comes back to the caller at once instead.
WAIT = 60


class _Retry(Retry):
    """urllib3's retries, ended at once by a server that asks for more than `WAIT`.

    urllib3 sleeps for whatever Retry-After says, on each of its retries. Here a
    longer wait ends the retries and the answer reaches the caller as it arrived:
    a generated operation raises `ApiException`, whose `headers` carry
    Retry-After, and a reply from :meth:`Client.send` faults with `retry_after`.
    """

    def increment(
        self,
        method: Optional[str] = None,
        url: Optional[str] = None,
        response: Any = None,
        error: Optional[Exception] = None,
        _pool: Any = None,
        _stacktrace: Any = None,
    ) -> Retry:
        if (
            response is not None
            and response.status in self.RETRY_AFTER_STATUS_CODES
            and _wait(response.headers.get("Retry-After", "")) > WAIT
        ):
            raise MaxRetryError(_pool, url, ResponseError("Retry-After is longer than {0}s".format(WAIT)))
        return super().increment(method, url, response, error, _pool, _stacktrace)


class Client(ApiClient):
    """An API client that holds an IAM credential and answers the six.

    Every option falls back to an environment variable, so the zero-argument
    constructor is the normal case:

    ==========  =======================  =========================
    option      environment              default
    ==========  =======================  =========================
    id          ``HANZO_CLIENT_ID``      —
    secret      ``HANZO_CLIENT_SECRET``  —
    base        ``HANZO_BASE_URL``       ``https://api.hanzo.ai``
    issuer      ``HANZO_ISSUER_URL``     ``https://hanzo.id``
    resource    ``HANZO_RESOURCE``       = base
    ==========  =======================  =========================

    :param credential: what to send for. Left unset the client mints from
        `id` and `secret`; :meth:`as_` passes the subject-bound mint it made.
        Nothing else sets it — the SDK does not take a bearer.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        secret: Optional[str] = None,
        *,
        base: Optional[str] = None,
        issuer: Optional[str] = None,
        resource: Optional[str] = None,
        credential: Optional[Any] = None,
    ) -> None:
        self.base = (base or os.environ.get("HANZO_BASE_URL") or BASE).rstrip("/")
        self.issuer = (issuer or os.environ.get("HANZO_ISSUER_URL") or ISSUER).rstrip("/")
        self.resource = resource or os.environ.get("HANZO_RESOURCE") or self.base
        # urllib3 takes a Retry where the generated hint names an int.
        retries: Any = _Retry(3, raise_on_status=False)
        super().__init__(Configuration(host=self.base, retries=retries))

        if credential is None:
            # Construction never fails on a missing credential; the first call
            # does, and says which variable is unset (:meth:`hanzoai.Token.token`).
            id = id or os.environ.get("HANZO_CLIENT_ID") or ""
            secret = secret or os.environ.get("HANZO_CLIENT_SECRET") or ""
            credential = Token(id, secret, issuer=self.issuer, resource=self.resource, transport=self.rest_client)
        self.credential = credential

        self.budget = Budget(self)
        self.policy = Policy(self)
        self.audit = Audit(self)
        self.search = Search(self)
        self.kb = Kb(self)
        self.graph = Graph(self)

    def as_(self, subject: str) -> "Client":
        """A client that acts as `subject` — a subject id, or an externalId.

        The operator credential leaves with the scope: two credentials on one
        request are two answers to who is calling. No method on the returned
        client takes a user id, so there is none to pass wrongly and none to
        forget.

        Spelled with the trailing underscore PEP 8 prescribes for a name that
        collides with a keyword. The word is still ``as``.
        """
        return Client(
            base=self.base,
            issuer=self.issuer,
            resource=self.resource,
            credential=Grant(self.credential, subject, issuer=self.issuer, transport=self.rest_client),
        )

    # ---- the wire under the six ------------------------------------------

    def send(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Any = None,
        media: str = "application/json",
    ) -> wire.Reply:
        """One call, with the credential on it and the request id off it.

        A `query` entry that is `None` or empty is dropped, and so is a `body`
        member nobody set — a request carries what the caller determined, and a
        JSON null is not that. A `datetime` is stamped RFC 3339. A 401 re-mints
        once and replays, so a rotated token costs a round trip rather than an
        error the caller has to handle.
        """
        headers = {"Accept": "application/json", "Authorization": "Bearer " + self.credential.token()}
        if body is not None:
            headers["Content-Type"] = media
        response = self.call_api(method, self.base + path + _query(query), headers, _body(body))
        response.read()
        return _reply(response)

    def read(self, method: str, path: str, **call: Any) -> Any:
        """A call no gate refuses: the decoded body, or the reason there is none."""
        return value(self.send(method, path, **call))

    # ---- where the credential joins a generated operation ------------------

    def param_serialize(self, *args: Any, **kwargs: Any) -> Any:
        """The generated serializer reads the credential off the configuration.

        Refreshing it here puts the live token on every one of the generated
        operations without touching a single one of them.
        """
        self.configuration.access_token = self.credential.token()
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
        if response.status == 401:
            self.credential.invalidate()
            header_params = dict(header_params or {})
            header_params["Authorization"] = "Bearer " + self.credential.token()
            response = super().call_api(method, url, header_params, body, post_params, _request_timeout)
        return response

    def response_deserialize(self, response_data: Any, response_types_map: Optional[Any] = None) -> Any:
        """A generated operation the platform held raises rather than returning nothing.

        The hold arrives as 202 carrying ``status: "held"``. No operation
        declares a schema for that, so the generated deserializer answers it
        with `None` and a queued call reads as one that succeeded and returned
        nothing. The six capabilities answer the same hold as
        :class:`hanzoai.Held`, which is the arm this raises.
        """
        reply = _reply(response_data)
        if held(reply):
            raise Held.read(reply.body, reply.request)
        return super().response_deserialize(response_data, response_types_map)


def _query(params: Optional[Dict[str, Any]]) -> str:
    """The query string. What survives is decided once, in :func:`hanzoai.wire.query`."""
    asked = wire.query(params)
    return "?" + urlencode(asked) if asked else ""


def _body(body: Any) -> Any:
    """The body cloud reads: the members somebody set, and no nulls.

    A member the caller left unset is a member the caller did not narrow by.
    Sending it as an explicit null makes three languages send three different
    requests for one call, and asks cloud to read a value where there is none.
    Anything that is not a JSON object — an upload's bytes — passes through.
    """
    if not isinstance(body, dict):
        return body
    return {k: v for k, v in body.items() if v is not None}


def _reply(response: Any) -> wire.Reply:
    """The decoded answer, and the id that names this call in the trail."""
    raw = response.data
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    body: Any = raw
    if isinstance(raw, str) and raw:
        try:
            body = json.loads(raw)
        except ValueError:
            body = raw
    return wire.Reply(
        status=response.status,
        body=body if raw else None,
        request=response.getheader("x-request-id", "") or "",
        retry_after=_wait(response.getheader("retry-after", "") or ""),
    )


def _wait(header: str) -> float:
    """Retry-After in seconds, in either form RFC 9110 allows; 0 for none, or one unreadable."""
    if header.strip().isdigit():
        return float(header)
    try:
        return max(parsedate_to_datetime(header).timestamp() - time.time(), 0.0)
    except (TypeError, ValueError):
        return 0.0
