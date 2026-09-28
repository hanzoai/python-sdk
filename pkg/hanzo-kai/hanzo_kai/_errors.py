"""The errors this package raises, and how a failed response becomes one."""

import json
import math
import time
from typing import Any
from email.utils import parsedate_to_datetime
from collections.abc import Mapping

import httpx

LIMIT = 200
"""Characters of a text or unrecognized error body kept in the message."""


class KaiError(Exception):
    """Base of every error this package raises."""


class APIError(KaiError):
    """The API answered with a status that is not a success.

    `message` is the server's own sentence; `code` is the code the body names, when it names one.
    """

    def __init__(
        self,
        status: int,
        body: Any = None,
        headers: httpx.Headers | Mapping[str, str] | None = None,
        message: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        super().__init__(status, body, headers, message, endpoint)
        self.status = status
        """HTTP status of the response."""
        self.body = body
        """The decoded JSON body, its text when it is not JSON, or None when it is empty."""
        self.headers = httpx.Headers(headers)
        """Headers of the response."""
        self.endpoint = endpoint
        """Method and URL of the request."""
        said, self.code = sentence(body)
        self.message: str = message or said or fallback(status, body)
        """What the server said went wrong."""
        self.request_id: str | None = self.headers.get("x-request-id")
        """The response's `x-request-id`, to quote when reporting a problem."""
        self.retry_after: float | None = wait(self.headers)
        """Seconds the server asked the client to wait, from `retry-after-ms` or `Retry-After`."""

    def __str__(self) -> str:
        text = f"{self.status} {self.message}"
        return f"{text} (request {self.request_id})" if self.request_id else text

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"


class BadRequestError(APIError):
    """400: the request is malformed; the message names what to change."""


class AuthenticationError(APIError):
    """401: the API key is missing, unknown or revoked."""


class PaymentRequiredError(APIError):
    """402: the account has no plan or no balance."""


class PermissionDeniedError(APIError):
    """403: the key may not make this call; a publishable `pk-` key never may."""


class NotFoundError(APIError):
    """404: nothing is served at this path."""


class UnprocessableEntityError(APIError):
    """422: the request is well formed but past a model limit, such as options over the window."""


class RateLimitError(APIError):
    """429: too many requests; `retry_after` says how long to wait."""


class InternalServerError(APIError):
    """5xx: the server or a service behind it failed."""


class APIResponseValidationError(APIError):
    """A success response whose body does not fit the type it is read into.

    `field_path` names the first field that is missing or malformed, such as `answers.team.choice`.
    """

    def __init__(
        self,
        status: int,
        body: Any,
        headers: httpx.Headers | Mapping[str, str] | None,
        field_path: str,
        endpoint: str | None = None,
    ) -> None:
        self.field_path = field_path
        """Dotted path to the first field that does not fit."""
        where = f"at {field_path!r}" if field_path else "(not a JSON object)"
        super().__init__(status, body, headers, f"the response does not fit its schema {where}", endpoint)
        self.args = (status, body, headers, field_path, endpoint)


class APIConnectionError(KaiError, ConnectionError):
    """The request got no response: the connection failed, dropped or never opened."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
        """What failed."""

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message!r})"


class APITimeoutError(APIConnectionError, TimeoutError):
    """An attempt ran past its timeout."""

    def __init__(self, timeout: float | httpx.Timeout) -> None:
        self.timeout = timeout
        """The timeout the attempt ran under, in seconds or as an `httpx.Timeout`."""
        limit = f"{timeout:g} s" if isinstance(timeout, float | int) else repr(timeout)
        super().__init__(f"the request timed out after {limit}")
        self.args = (timeout,)


STATUS: dict[int, type[APIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def api_error(status: int, body: Any, headers: httpx.Headers, endpoint: str | None) -> APIError:
    """The error class a status maps to, built from the response."""
    kind = STATUS.get(status) or (InternalServerError if status >= 500 else APIError)
    return kind(status, body, headers, endpoint=endpoint)


def sentence(body: Any) -> tuple[str | None, int | str | None]:
    """The message and code of an error body, in any of the shapes the API sends.

    `/v1/decisions` sends `{"error": {"code", "message"}}`; `/v1/systemone` sends FastAPI's
    `{"detail": "<message>"}` or `{"detail": [{"loc", "msg", "type"}]}`, whose first `type` is the
    code; the gateway sends `{"error": {"message", "type", "code"}}` or `{"status": "error", "msg"}`.
    """
    if isinstance(body, str):
        text = body.strip()
        return (text if len(text) <= LIMIT else text[:LIMIT] + "…") or None, None
    if not isinstance(body, dict):
        return None, None
    error, detail = body.get("error"), body.get("detail")
    if isinstance(error, dict):
        message, code = error.get("message"), error.get("code")
        if isinstance(code, bool) or not isinstance(code, int | str):
            code = None
        return (message if isinstance(message, str) and message else None), code
    if isinstance(detail, list):
        return fields(detail)
    for said in (error, detail, body.get("msg"), body.get("message")):
        if isinstance(said, str) and said:
            return said, None
    return None, None


def fields(detail: list[Any]) -> tuple[str | None, str | None]:
    """FastAPI's validation entries as one message, `where: what` each, and the first entry's type."""
    parts: list[str] = []
    code = None
    for entry in detail:
        if not isinstance(entry, dict) or not isinstance(entry.get("msg"), str):
            continue
        loc = entry.get("loc")
        where = ".".join(str(part) for part in loc if part != "body") if isinstance(loc, list) else ""
        parts.append(f"{where}: {entry['msg']}" if where else entry["msg"])
        if code is None and isinstance(entry.get("type"), str):
            code = entry["type"]
    return "; ".join(parts) or None, code


def fallback(status: int, body: Any) -> str:
    """A message for a body that holds no sentence."""
    if body is None or body == "":
        return httpx.codes.get_reason_phrase(status) or f"HTTP {status}"
    text = json.dumps(body, ensure_ascii=False)
    return text if len(text) <= LIMIT else text[:LIMIT] + "…"


def wait(headers: httpx.Headers) -> float | None:
    """Seconds the server asks a client to wait, from `retry-after-ms` or `Retry-After`."""
    raw = headers.get("retry-after-ms")
    if raw is not None and (ms := seconds(raw)) is not None:
        return ms / 1000
    raw = headers.get("retry-after")
    if raw is None:
        return None
    if (value := seconds(raw)) is not None:
        return value
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return None
    return max(0.0, when.timestamp() - time.time())


def seconds(raw: str) -> float | None:
    """A non-negative, finite number, or None."""
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if math.isfinite(value) and value >= 0 else None
