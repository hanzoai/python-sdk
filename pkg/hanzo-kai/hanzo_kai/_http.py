"""Requests: resolved settings, headers, JSON bodies, and the retry loop around each call."""

import os
import json
import math
import time
import asyncio
import logging
import platform
from typing import Any
from dataclasses import field, dataclass
from collections.abc import Mapping, Callable, Sequence

import httpx
from pydantic import BaseModel

from hanzo_kai import constants
from hanzo_kai._log import logger, redact
from hanzo_kai._retry import RetryPolicy
from hanzo_kai._errors import KaiError, APITimeoutError, APIConnectionError, api_error
from hanzo_kai._answers import parse, endpoint
from hanzo_kai._version import __version__

AGENT = f"hanzo-kai/{__version__}"
RUNTIME = (
    f"{platform.python_implementation().lower()}/{platform.python_version()} httpx/{httpx.__version__} "
    f"{platform.system().lower()}/{platform.machine().lower()}"
)
RUNTIME_HEADER = "X-Kai-Runtime"
RETRY_HEADER = "X-Kai-Retry-Count"

type Timeout = float | httpx.Timeout


@dataclass(frozen=True)
class Config:
    """A client's settings, each resolved once from its argument, the environment or the default."""

    key: str = field(repr=False)
    base: str
    model: str
    timeout: Timeout
    headers: httpx.Headers = field(repr=False)
    retry: RetryPolicy


def config(
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: Timeout | None,
    headers: Mapping[str, str] | None,
    retry: RetryPolicy | None,
) -> Config:
    """Settings from arguments first, then HANZO_API_KEY, HANZO_BASE_URL and KAI_MODEL, then defaults.

    An environment value that is empty or all whitespace counts as unset.
    """
    return Config(
        key=key(api_key if api_key is not None else os.environ.get(constants.API_KEY_ENV, "")),
        base=url(base_url if base_url is not None else env(constants.BASE_URL_ENV) or constants.DEFAULT_BASE_URL),
        model=model if model is not None else env(constants.DEFAULT_MODEL_ENV) or constants.DEFAULT_MODEL,
        timeout=seconds(constants.DEFAULT_TIMEOUT if timeout is None else timeout),
        headers=httpx.Headers(headers),
        retry=RetryPolicy() if retry is None else retry,
    )


def env(name: str) -> str:
    return os.environ.get(name, "").strip()


def key(value: str) -> str:
    """An API key, stripped, refused when empty or when it could not travel in a header."""
    value = value.strip()
    if not value:
        raise KaiError(f"no API key: pass api_key or set {constants.API_KEY_ENV}")
    if not value.isascii() or not value.isprintable() or any(c.isspace() for c in value):
        raise KaiError("the API key must be printable ASCII without whitespace")
    return value


def url(value: str) -> str:
    """An http(s) API root without a trailing slash."""
    base = value.strip().rstrip("/")
    try:
        parsed = httpx.URL(base)
    except httpx.InvalidURL as error:
        raise KaiError(f"base URL {base!r} is not a URL: {error}") from error
    if parsed.scheme not in ("http", "https") or not parsed.host:
        raise KaiError(f"base URL {base!r} must be an http or https URL, such as {constants.DEFAULT_BASE_URL}")
    return base


def seconds(value: Timeout) -> Timeout:
    """A timeout: an `httpx.Timeout`, or a positive, finite number of seconds."""
    if isinstance(value, httpx.Timeout):
        return value
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value) or value <= 0:
        raise KaiError("timeout must be a positive, finite number of seconds or an httpx.Timeout")
    return float(value)


@dataclass(frozen=True)
class Call:
    """One request, as every attempt at it sends it."""

    method: str
    url: str
    headers: httpx.Headers
    content: bytes | None
    timeout: Timeout
    retry: RetryPolicy


def call(
    settings: Config,
    method: str,
    path: str,
    body: Any,
    timeout: Timeout | None,
    headers: Mapping[str, str] | None,
    retry: RetryPolicy | None,
) -> Call:
    """A request with the client's headers under the call's, and the headers only the client sets on top."""
    merged = httpx.Headers(settings.headers)
    merged.update(headers or {})
    merged.pop(RETRY_HEADER, None)
    merged.update(
        {
            "Authorization": f"Bearer {settings.key}",
            "Accept": "application/json",
            "User-Agent": AGENT,
            RUNTIME_HEADER: RUNTIME,
        }
    )
    content = None
    if body is not None:
        content = encode(body)
        merged["Content-Type"] = "application/json"
    return Call(
        method,
        settings.base + path,
        merged,
        content,
        settings.timeout if timeout is None else seconds(timeout),
        settings.retry if retry is None else retry,
    )


def encode(body: Any) -> bytes:
    """Compact UTF-8 JSON; NaN, infinities and types JSON has no form for are refused."""
    try:
        return json.dumps(body, ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=plain).encode()
    except (TypeError, ValueError) as error:
        raise KaiError(f"the request body is not JSON: {error}") from error


def plain(value: Any) -> Any:
    """A JSON form for the containers `json` leaves out: pydantic models, mappings and sequences."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return list(value)
    raise TypeError(f"{type(value).__name__} has no JSON form")


def send[T](http: httpx.Client, request: Call, read: Callable[[httpx.Response], T]) -> T:
    """Sends a call, retrying as its policy says, and reads the successful response."""
    started = time.monotonic()
    retries = 0
    while True:
        headers = numbered(request, retries)
        begun = time.monotonic()
        try:
            try:
                response = http.request(
                    request.method, request.url, content=request.content, headers=headers, timeout=request.timeout
                )
            except httpx.RequestError as error:
                raise failed(request, error) from error
            logged(request, response, begun)
            return read(checked(response))
        except Exception as error:
            delay = pause(request, error, retries, started)
            if delay is None:
                raise
        retries += 1
        time.sleep(delay)


async def send_async[T](http: httpx.AsyncClient, request: Call, read: Callable[[httpx.Response], T]) -> T:
    """`send` over an `httpx.AsyncClient`."""
    started = time.monotonic()
    retries = 0
    while True:
        headers = numbered(request, retries)
        begun = time.monotonic()
        try:
            try:
                response = await http.request(
                    request.method, request.url, content=request.content, headers=headers, timeout=request.timeout
                )
            except httpx.RequestError as error:
                raise failed(request, error) from error
            logged(request, response, begun)
            return read(checked(response))
        except Exception as error:
            delay = pause(request, error, retries, started)
            if delay is None:
                raise
        retries += 1
        await asyncio.sleep(delay)


def numbered(request: Call, retries: int) -> httpx.Headers:
    """The call's headers for one attempt: a retry says which one it is."""
    headers = request.headers.copy()
    if retries:
        headers[RETRY_HEADER] = str(retries)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s %s -> headers=%s body=%s", request.method, request.url, redact(headers), text(request.content))
    return headers


def failed(request: Call, error: httpx.RequestError) -> APIConnectionError:
    """The error for an attempt that got no response."""
    logger.info("%s %s <- %s", request.method, request.url, type(error).__name__)
    if isinstance(error, httpx.TimeoutException):
        return APITimeoutError(request.timeout)
    return APIConnectionError(f"{request.method} {request.url} failed: {type(error).__name__}: {error}")


def logged(request: Call, response: httpx.Response, started: float) -> None:
    logger.info(
        "%s %s <- %d in %.0f ms (request %s)",
        request.method,
        request.url,
        response.status_code,
        (time.monotonic() - started) * 1000,
        response.headers.get("x-request-id", "-"),
    )
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "%s %s <- headers=%s body=%s", request.method, request.url, redact(response.headers), text(response.content)
        )


def checked(response: httpx.Response) -> httpx.Response:
    """The response when it is a success, else the error its status maps to."""
    if response.is_success:
        return response
    body = parse(response)
    if body is None and response.content:
        body = response.text
    raise api_error(response.status_code, body, response.headers, endpoint(response))


def pause(request: Call, error: Exception, retries: int, started: float) -> float | None:
    """Seconds to wait before retrying after `error`, or None when the call gives up."""
    policy = request.retry
    if retries >= policy.max_retries or not policy._retries(error):
        return None
    delay = policy._delay(retries + 1, error)
    if policy.timeout is not None and time.monotonic() - started + delay >= policy.timeout:
        return None
    logger.info(
        "%s %s: retry %d of %d in %.2f s after %s",
        request.method,
        request.url,
        retries + 1,
        policy.max_retries,
        delay,
        error,
    )
    return delay


def text(content: bytes | None) -> str:
    return "" if content is None else content.decode("utf-8", errors="replace")
