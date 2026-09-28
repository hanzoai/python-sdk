"""Jev compatibility: the call shapes of TypeSafe's SDK over Kai's Jev-compatible path, `POST /v1/systemone`.

A program written against TypeSafe's SDK moves to Kai by changing one import:

    from hanzo_kai.jev import Choice, Noul, Score, Client as TypeSafeClient

The path answers in Jev's shape (`model`, `answers`, `usage`) and serves one model, `kai`; it
refuses every Jev model id. Errors arrive in FastAPI's shape and raise the same classes as
`hanzo_kai`. New code uses `hanzo_kai.Kai` and `/v1/decisions`, which answer with Kai's own fields.
"""

from __future__ import annotations

from typing import overload
from functools import cached_property
from collections.abc import Mapping

import httpx
from pydantic import BaseModel

from hanzo_kai import _http
from hanzo_kai._retry import RetryPolicy
from hanzo_kai._client import MODELS, Sync, Async, request
from hanzo_kai._errors import (
    APIError,
    KaiError,
    NotFoundError,
    RateLimitError,
    APITimeoutError,
    BadRequestError,
    APIConnectionError,
    AuthenticationError,
    InternalServerError,
    PaymentRequiredError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)
from hanzo_kai._answers import (
    Usage,
    Answer,
    Response,
    NoulAnswer,
    ScoreAnswer,
    ChoiceAnswer,
    ModelMetadata,
    ListModelsResponse,
    read,
    catalog,
)
from hanzo_kai._questions import (
    Noul,
    Score,
    Choice,
    Question,
    JSONValue,
    NoulModel,
    Questions,
    ScoreModel,
    ChoiceModel,
    JSONContent,
    NoulCriteria,
    QuestionModel,
)

SYSTEMONE = "/v1/systemone"

__all__ = [
    "APIConnectionError",
    "APIError",
    "APIResponseValidationError",
    "APITimeoutError",
    "Answer",
    "AsyncClient",
    "AsyncModels",
    "AuthenticationError",
    "BadRequestError",
    "Choice",
    "ChoiceAnswer",
    "ChoiceModel",
    "Client",
    "InternalServerError",
    "JSONContent",
    "JSONValue",
    "KaiError",
    "ListModelsResponse",
    "ModelMetadata",
    "Models",
    "NotFoundError",
    "Noul",
    "NoulAnswer",
    "NoulCriteria",
    "NoulModel",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "Question",
    "QuestionModel",
    "Questions",
    "RateLimitError",
    "Response",
    "RetryPolicy",
    "Score",
    "ScoreAnswer",
    "ScoreModel",
    "UnprocessableEntityError",
    "Usage",
]


class Client(Sync):
    """A client for Kai over `/v1/systemone`, with the same arguments and settings as `hanzo_kai.Kai`.

    Examples:
        ```python
        from hanzo_kai.jev import Choice, Client

        with Client() as client:
            response = client.system_one(
                state={"ticket": "I was charged twice for my March invoice."},
                questions={
                    "team": Choice(instructions="Which team handles this?", criteria={"billing": None, "tech": None})
                },
            )
        print(response.choices["team"].choice)
        ```
    """

    @cached_property
    def models(self) -> Models:
        """The models `/v1/systemone` serves."""
        return Models(self._config, self._http)

    @overload
    def system_one(
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
    ) -> Response: ...

    @overload
    def system_one[T: BaseModel](
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

    def system_one[T: BaseModel](
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
    ) -> Response | T:
        """Ask Kai named questions about one state: `POST /v1/systemone`, answered in Jev's shape.

        The arguments are those of `hanzo_kai.Kai.decide`; the result is a `Response`, or an
        instance of `response_model`.
        """
        call = request(self._config, SYSTEMONE, state, questions, model, extra_body, timeout, extra_headers, retry)
        if response_model is None:
            return _http.send(self._http, call, lambda response: read(response, Response))
        return _http.send(self._http, call, lambda response: read(response, response_model))


class AsyncClient(Async):
    """`Client` for asyncio: the same arguments, with `await` and `async with`."""

    @cached_property
    def models(self) -> AsyncModels:
        """The models `/v1/systemone` serves."""
        return AsyncModels(self._config, self._http)

    @overload
    async def system_one(
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
    ) -> Response: ...

    @overload
    async def system_one[T: BaseModel](
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

    async def system_one[T: BaseModel](
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
    ) -> Response | T:
        """Ask Kai named questions about one state: `POST /v1/systemone`. See `Client.system_one`."""
        call = request(self._config, SYSTEMONE, state, questions, model, extra_body, timeout, extra_headers, retry)
        if response_model is None:
            return await _http.send_async(self._http, call, lambda response: read(response, Response))
        return await _http.send_async(self._http, call, lambda response: read(response, response_model))


class Models:
    """The models resource of `Client`: `client.models.list()`."""

    def __init__(self, settings: _http.Config, http: httpx.Client) -> None:
        self._config = settings
        self._http = http

    def list(
        self,
        *,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ListModelsResponse:
        """The `models` key of `GET /v1/models`: each model's name, description and release date."""
        return _http.send(
            self._http, _http.call(self._config, "GET", MODELS, None, timeout, extra_headers, retry), catalog
        )


class AsyncModels:
    """The models resource of `AsyncClient`: `await client.models.list()`."""

    def __init__(self, settings: _http.Config, http: httpx.AsyncClient) -> None:
        self._config = settings
        self._http = http

    async def list(
        self,
        *,
        retry: RetryPolicy | None = None,
        timeout: float | httpx.Timeout | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ListModelsResponse:
        """The `models` key of `GET /v1/models`: each model's name, description and release date."""
        return await _http.send_async(
            self._http, _http.call(self._config, "GET", MODELS, None, timeout, extra_headers, retry), catalog
        )
