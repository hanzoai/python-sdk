"""The clients: `Kai` and `AsyncKai` over `/v1/decisions`, on the settings and HTTP client every client holds."""

from __future__ import annotations

from types import TracebackType
from typing import Self, overload
from functools import cached_property
from collections.abc import Mapping

import httpx
from pydantic import BaseModel

from hanzo_kai import _http
from hanzo_kai._retry import RetryPolicy
from hanzo_kai._answers import Model, Decision, read, models
from hanzo_kai._questions import JSONValue, Questions, JSONContent, encode

DECISIONS = "/v1/decisions"
MODELS = "/v1/models"


def request(
    settings: _http.Config,
    path: str,
    state: JSONContent,
    questions: Questions,
    model: str | None,
    extra_body: Mapping[str, JSONValue] | None,
    timeout: float | httpx.Timeout | None,
    extra_headers: Mapping[str, str] | None,
    retry: RetryPolicy | None,
) -> _http.Call:
    """The call for one decision: `{model, state, questions}`, with `extra_body` merged over it."""
    body: dict[str, object] = {
        "model": settings.model if model is None else model,
        "state": state,
        "questions": encode(questions),
    }
    body.update(extra_body or {})
    return _http.call(settings, "POST", path, body, timeout, extra_headers, retry)


class Sync:
    """What a synchronous client holds: its settings, and an `httpx.Client` it closes when it closes."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        headers: Mapping[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        http_client: httpx.Client | None = None,
        base_url: str | None = None,
    ) -> None:
        if transport is not None and http_client is not None:
            raise ValueError("pass transport or http_client, not both")
        if timeout is None and http_client is not None:
            timeout = http_client.timeout
        self._config = _http.config(api_key, base_url, model, timeout, headers, retry)
        self._http = (
            http_client if http_client is not None else httpx.Client(transport=transport, timeout=self._config.timeout)
        )

    def close(self) -> None:
        """Closes the HTTP client, a supplied one included."""
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None
    ) -> None:
        self.close()


class Async:
    """What an asyncio client holds: its settings, and an `httpx.AsyncClient` it closes when it closes."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        headers: Mapping[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
    ) -> None:
        if transport is not None and http_client is not None:
            raise ValueError("pass transport or http_client, not both")
        if timeout is None and http_client is not None:
            timeout = http_client.timeout
        self._config = _http.config(api_key, base_url, model, timeout, headers, retry)
        self._http = (
            http_client
            if http_client is not None
            else httpx.AsyncClient(transport=transport, timeout=self._config.timeout)
        )

    async def aclose(self) -> None:
        """Closes the HTTP client, a supplied one included."""
        await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None
    ) -> None:
        await self.aclose()


class Kai(Sync):
    """A client for Kai decisions on the Hanzo API.

    Arguments win over the environment; an empty environment value counts as unset.

    Args:
        api_key: A Hanzo `sk-` key or an IAM access token; else `HANZO_API_KEY`.
        model: Model each decision asks for unless the call names one; else `KAI_MODEL`, else `kai`.
        retry: How calls retry; see `RetryPolicy`. `RetryPolicy(max_retries=0)` turns retrying off.
        timeout: Seconds, or an `httpx.Timeout`, each attempt may take; else the `http_client`'s, else 60.
        headers: Headers sent with every request. They cannot replace `Authorization`, `Accept`,
            `User-Agent` or `X-Kai-Runtime`.
        transport: An `httpx` transport to send through, such as `httpx.MockTransport` in tests.
        http_client: An `httpx.Client` to send through; not together with `transport`.
        base_url: API root; else `HANZO_BASE_URL`, else `https://api.hanzo.ai`.

    The client closes its HTTP client, a supplied one included, when it closes.

    Raises:
        KaiError: No API key, or a key, base URL or timeout that cannot work.
        ValueError: Both `transport` and `http_client` are given.

    Examples:
        ```python
        from hanzo_kai import Choice, Kai

        with Kai() as kai:
            d = kai.decide(
                state={"ticket": "I was charged twice for my March invoice."},
                questions={
                    "team": Choice(
                        instructions="Which team handles this?", criteria={"billing": "charges", "tech": "bugs"}
                    )
                },
            )
        print(d.choices["team"].choice)
        ```
    """

    @cached_property
    def models(self) -> Models:
        """The models that answer decisions."""
        return Models(self._config, self._http)

    @overload
    def decide(
        self,
        state: JSONContent,
        questions: Questions,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_body: Mapping[str, JSONValue] | None = None,
        response_model: None = None,
    ) -> Decision: ...

    @overload
    def decide[T: BaseModel](
        self,
        state: JSONContent,
        questions: Questions,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_body: Mapping[str, JSONValue] | None = None,
        response_model: type[T],
    ) -> T: ...

    def decide[T: BaseModel](
        self,
        state: JSONContent,
        questions: Questions,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_body: Mapping[str, JSONValue] | None = None,
        response_model: type[T] | None = None,
    ) -> Decision | T:
        """Ask Kai named questions about one state: `POST /v1/decisions`.

        Args:
            state: What the questions are about: text, a JSON object or an array.
            questions: At least one question, keyed by the name its answer comes back under.
            model: The model for this call; else the client's.
            retry: The retry policy for this call; else the client's.
            timeout: The per-attempt timeout for this call; else the client's.
            extra_headers: Headers for this call, over the client's.
            extra_body: Top-level body fields merged over `model`, `state` and `questions`,
                such as `session_id`, `user` or `trace`; a key given here replaces the same key.
            response_model: A pydantic model to read the body into instead of `Decision`.

        Returns:
            A `Decision`, or an instance of `response_model`.

        Raises:
            KaiError: No questions, a score question whose criteria is not a list, a choice
                question whose criteria is neither a mapping nor a list, or a body that is not JSON.
            APIError: The API refused the request; the subclass names the status.
            APIConnectionError: No response came back after the retries.
            APIResponseValidationError: The response does not fit the model it is read into.
        """
        call = request(self._config, DECISIONS, state, questions, model, extra_body, timeout, extra_headers, retry)
        if response_model is None:
            return _http.send(self._http, call, lambda response: read(response, Decision))
        return _http.send(self._http, call, lambda response: read(response, response_model))


class AsyncKai(Async):
    """`Kai` for asyncio: the same arguments, with `await` and `async with`.

    Examples:
        ```python
        from hanzo_kai import AsyncKai, Noul

        async with AsyncKai() as kai:
            d = await kai.decide(
                state="Refund my duplicate charge.",
                questions={"refund": Noul(instructions="Does the customer ask for a refund?")},
            )
        print(d.nouls["refund"].noul)
        ```
    """

    @cached_property
    def models(self) -> AsyncModels:
        """The models that answer decisions."""
        return AsyncModels(self._config, self._http)

    @overload
    async def decide(
        self,
        state: JSONContent,
        questions: Questions,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_body: Mapping[str, JSONValue] | None = None,
        response_model: None = None,
    ) -> Decision: ...

    @overload
    async def decide[T: BaseModel](
        self,
        state: JSONContent,
        questions: Questions,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_body: Mapping[str, JSONValue] | None = None,
        response_model: type[T],
    ) -> T: ...

    async def decide[T: BaseModel](
        self,
        state: JSONContent,
        questions: Questions,
        *,
        model: str | None = None,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_body: Mapping[str, JSONValue] | None = None,
        response_model: type[T] | None = None,
    ) -> Decision | T:
        """Ask Kai named questions about one state: `POST /v1/decisions`. See `Kai.decide`."""
        call = request(self._config, DECISIONS, state, questions, model, extra_body, timeout, extra_headers, retry)
        if response_model is None:
            return await _http.send_async(self._http, call, lambda response: read(response, Decision))
        return await _http.send_async(self._http, call, lambda response: read(response, response_model))


class Models:
    """The models resource of `Kai`: `kai.models.list()`."""

    def __init__(self, settings: _http.Config, http: httpx.Client) -> None:
        self._config = settings
        self._http = http

    def list(
        self,
        *,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> list[Model]:
        """The models that answer decisions: `GET /v1/models`, keeping those whose outputs include `decision`."""
        return _http.send(
            self._http, _http.call(self._config, "GET", MODELS, None, timeout, extra_headers, retry), models
        )


class AsyncModels:
    """The models resource of `AsyncKai`: `await kai.models.list()`."""

    def __init__(self, settings: _http.Config, http: httpx.AsyncClient) -> None:
        self._config = settings
        self._http = http

    async def list(
        self,
        *,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> list[Model]:
        """The models that answer decisions: `GET /v1/models`, keeping those whose outputs include `decision`."""
        return await _http.send_async(
            self._http, _http.call(self._config, "GET", MODELS, None, timeout, extra_headers, retry), models
        )
