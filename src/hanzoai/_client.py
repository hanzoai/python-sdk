# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Dict, Union, Mapping, cast
from typing_extensions import Self, Literal, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    NOT_GIVEN,
    Body,
    Omit,
    Query,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
)
from ._utils import (
    is_given,
    get_async_library,
)
from ._version import __version__
from ._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .resources import (
    add,
    test,
    user,
    azure,
    spend,
    utils,
    active,
    budget,
    cohere,
    delete,
    gemini,
    health,
    models,
    rerank,
    routes,
    bedrock,
    customer,
    langfuse,
    provider,
    settings,
    anthropic,
    vertex_ai,
    assemblyai,
    assistants,
    embeddings,
    guardrails,
    completions,
    credentials,
    model_group,
    moderations,
    eu_assemblyai,
)
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import HanzoError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
    make_request_options,
)
from .resources.key import key
from .resources.chat import chat
from .resources.team import team
from .resources.audio import audio
from .resources.cache import cache
from .resources.files import files
from .resources.model import model
from .resources.config import config
from .resources.images import images
from .resources.openai import openai
from .resources.batches import batches
from .resources.engines import engines
from .resources.global_ import global_
from .resources.threads import threads
from .resources.responses import responses
from .resources.fine_tuning import fine_tuning
from .resources.organization import organization

__all__ = [
    "ENVIRONMENTS",
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Hanzo",
    "AsyncHanzo",
    "Client",
    "AsyncClient",
]

ENVIRONMENTS: Dict[str, str] = {
    "production": "https://api.hanzo.ai",
    "sandbox": "https://api.sandbox.hanzo.ai",
}


class Hanzo(SyncAPIClient):
    models: models.ModelsResource
    openai: openai.OpenAIResource
    engines: engines.EnginesResource
    chat: chat.ChatResource
    completions: completions.CompletionsResource
    embeddings: embeddings.EmbeddingsResource
    images: images.ImagesResource
    audio: audio.AudioResource
    assistants: assistants.AssistantsResource
    threads: threads.ThreadsResource
    moderations: moderations.ModerationsResource
    utils: utils.UtilsResource
    model: model.ModelResource
    model_group: model_group.ModelGroupResource
    routes: routes.RoutesResource
    responses: responses.ResponsesResource
    batches: batches.BatchesResource
    rerank: rerank.RerankResource
    fine_tuning: fine_tuning.FineTuningResource
    credentials: credentials.CredentialsResource
    vertex_ai: vertex_ai.VertexAIResource
    gemini: gemini.GeminiResource
    cohere: cohere.CohereResource
    anthropic: anthropic.AnthropicResource
    bedrock: bedrock.BedrockResource
    eu_assemblyai: eu_assemblyai.EuAssemblyaiResource
    assemblyai: assemblyai.AssemblyaiResource
    azure: azure.AzureResource
    langfuse: langfuse.LangfuseResource
    config: config.ConfigResource
    test: test.TestResource
    health: health.HealthResource
    active: active.ActiveResource
    settings: settings.SettingsResource
    key: key.KeyResource
    user: user.UserResource
    team: team.TeamResource
    organization: organization.OrganizationResource
    customer: customer.CustomerResource
    spend: spend.SpendResource
    global_: global_.GlobalResource
    provider: provider.ProviderResource
    cache: cache.CacheResource
    guardrails: guardrails.GuardrailsResource
    add: add.AddResource
    delete: delete.DeleteResource
    files: files.FilesResource
    budget: budget.BudgetResource
    with_raw_response: HanzoWithRawResponse
    with_streaming_response: HanzoWithStreamedResponse

    # client options
    api_key: str

    _environment: Literal["production", "sandbox"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "sandbox"] | NotGiven = NOT_GIVEN,
        base_url: str | httpx.URL | None | NotGiven = NOT_GIVEN,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Hanzo client instance.

        This automatically infers the `api_key` argument from the `HANZO_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("HANZO_API_KEY")
        if api_key is None:
            raise HanzoError(
                "The api_key client option must be set either by passing api_key to the client or by setting the HANZO_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("HANZO_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `HANZO_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.models = models.ModelsResource(self)
        self.openai = openai.OpenAIResource(self)
        self.engines = engines.EnginesResource(self)
        self.chat = chat.ChatResource(self)
        self.completions = completions.CompletionsResource(self)
        self.embeddings = embeddings.EmbeddingsResource(self)
        self.images = images.ImagesResource(self)
        self.audio = audio.AudioResource(self)
        self.assistants = assistants.AssistantsResource(self)
        self.threads = threads.ThreadsResource(self)
        self.moderations = moderations.ModerationsResource(self)
        self.utils = utils.UtilsResource(self)
        self.model = model.ModelResource(self)
        self.model_group = model_group.ModelGroupResource(self)
        self.routes = routes.RoutesResource(self)
        self.responses = responses.ResponsesResource(self)
        self.batches = batches.BatchesResource(self)
        self.rerank = rerank.RerankResource(self)
        self.fine_tuning = fine_tuning.FineTuningResource(self)
        self.credentials = credentials.CredentialsResource(self)
        self.vertex_ai = vertex_ai.VertexAIResource(self)
        self.gemini = gemini.GeminiResource(self)
        self.cohere = cohere.CohereResource(self)
        self.anthropic = anthropic.AnthropicResource(self)
        self.bedrock = bedrock.BedrockResource(self)
        self.eu_assemblyai = eu_assemblyai.EuAssemblyaiResource(self)
        self.assemblyai = assemblyai.AssemblyaiResource(self)
        self.azure = azure.AzureResource(self)
        self.langfuse = langfuse.LangfuseResource(self)
        self.config = config.ConfigResource(self)
        self.test = test.TestResource(self)
        self.health = health.HealthResource(self)
        self.active = active.ActiveResource(self)
        self.settings = settings.SettingsResource(self)
        self.key = key.KeyResource(self)
        self.user = user.UserResource(self)
        self.team = team.TeamResource(self)
        self.organization = organization.OrganizationResource(self)
        self.customer = customer.CustomerResource(self)
        self.spend = spend.SpendResource(self)
        self.global_ = global_.GlobalResource(self)
        self.provider = provider.ProviderResource(self)
        self.cache = cache.CacheResource(self)
        self.guardrails = guardrails.GuardrailsResource(self)
        self.add = add.AddResource(self)
        self.delete = delete.DeleteResource(self)
        self.files = files.FilesResource(self)
        self.budget = budget.BudgetResource(self)
        self.with_raw_response = HanzoWithRawResponse(self)
        self.with_streaming_response = HanzoWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Ocp-Apim-Subscription-Key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "sandbox"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    def get_home(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Home"""
        return self.get(
            "/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncHanzo(AsyncAPIClient):
    models: models.AsyncModelsResource
    openai: openai.AsyncOpenAIResource
    engines: engines.AsyncEnginesResource
    chat: chat.AsyncChatResource
    completions: completions.AsyncCompletionsResource
    embeddings: embeddings.AsyncEmbeddingsResource
    images: images.AsyncImagesResource
    audio: audio.AsyncAudioResource
    assistants: assistants.AsyncAssistantsResource
    threads: threads.AsyncThreadsResource
    moderations: moderations.AsyncModerationsResource
    utils: utils.AsyncUtilsResource
    model: model.AsyncModelResource
    model_group: model_group.AsyncModelGroupResource
    routes: routes.AsyncRoutesResource
    responses: responses.AsyncResponsesResource
    batches: batches.AsyncBatchesResource
    rerank: rerank.AsyncRerankResource
    fine_tuning: fine_tuning.AsyncFineTuningResource
    credentials: credentials.AsyncCredentialsResource
    vertex_ai: vertex_ai.AsyncVertexAIResource
    gemini: gemini.AsyncGeminiResource
    cohere: cohere.AsyncCohereResource
    anthropic: anthropic.AsyncAnthropicResource
    bedrock: bedrock.AsyncBedrockResource
    eu_assemblyai: eu_assemblyai.AsyncEuAssemblyaiResource
    assemblyai: assemblyai.AsyncAssemblyaiResource
    azure: azure.AsyncAzureResource
    langfuse: langfuse.AsyncLangfuseResource
    config: config.AsyncConfigResource
    test: test.AsyncTestResource
    health: health.AsyncHealthResource
    active: active.AsyncActiveResource
    settings: settings.AsyncSettingsResource
    key: key.AsyncKeyResource
    user: user.AsyncUserResource
    team: team.AsyncTeamResource
    organization: organization.AsyncOrganizationResource
    customer: customer.AsyncCustomerResource
    spend: spend.AsyncSpendResource
    global_: global_.AsyncGlobalResource
    provider: provider.AsyncProviderResource
    cache: cache.AsyncCacheResource
    guardrails: guardrails.AsyncGuardrailsResource
    add: add.AsyncAddResource
    delete: delete.AsyncDeleteResource
    files: files.AsyncFilesResource
    budget: budget.AsyncBudgetResource
    with_raw_response: AsyncHanzoWithRawResponse
    with_streaming_response: AsyncHanzoWithStreamedResponse

    # client options
    api_key: str

    _environment: Literal["production", "sandbox"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "sandbox"] | NotGiven = NOT_GIVEN,
        base_url: str | httpx.URL | None | NotGiven = NOT_GIVEN,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncHanzo client instance.

        This automatically infers the `api_key` argument from the `HANZO_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("HANZO_API_KEY")
        if api_key is None:
            raise HanzoError(
                "The api_key client option must be set either by passing api_key to the client or by setting the HANZO_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("HANZO_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `HANZO_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.models = models.AsyncModelsResource(self)
        self.openai = openai.AsyncOpenAIResource(self)
        self.engines = engines.AsyncEnginesResource(self)
        self.chat = chat.AsyncChatResource(self)
        self.completions = completions.AsyncCompletionsResource(self)
        self.embeddings = embeddings.AsyncEmbeddingsResource(self)
        self.images = images.AsyncImagesResource(self)
        self.audio = audio.AsyncAudioResource(self)
        self.assistants = assistants.AsyncAssistantsResource(self)
        self.threads = threads.AsyncThreadsResource(self)
        self.moderations = moderations.AsyncModerationsResource(self)
        self.utils = utils.AsyncUtilsResource(self)
        self.model = model.AsyncModelResource(self)
        self.model_group = model_group.AsyncModelGroupResource(self)
        self.routes = routes.AsyncRoutesResource(self)
        self.responses = responses.AsyncResponsesResource(self)
        self.batches = batches.AsyncBatchesResource(self)
        self.rerank = rerank.AsyncRerankResource(self)
        self.fine_tuning = fine_tuning.AsyncFineTuningResource(self)
        self.credentials = credentials.AsyncCredentialsResource(self)
        self.vertex_ai = vertex_ai.AsyncVertexAIResource(self)
        self.gemini = gemini.AsyncGeminiResource(self)
        self.cohere = cohere.AsyncCohereResource(self)
        self.anthropic = anthropic.AsyncAnthropicResource(self)
        self.bedrock = bedrock.AsyncBedrockResource(self)
        self.eu_assemblyai = eu_assemblyai.AsyncEuAssemblyaiResource(self)
        self.assemblyai = assemblyai.AsyncAssemblyaiResource(self)
        self.azure = azure.AsyncAzureResource(self)
        self.langfuse = langfuse.AsyncLangfuseResource(self)
        self.config = config.AsyncConfigResource(self)
        self.test = test.AsyncTestResource(self)
        self.health = health.AsyncHealthResource(self)
        self.active = active.AsyncActiveResource(self)
        self.settings = settings.AsyncSettingsResource(self)
        self.key = key.AsyncKeyResource(self)
        self.user = user.AsyncUserResource(self)
        self.team = team.AsyncTeamResource(self)
        self.organization = organization.AsyncOrganizationResource(self)
        self.customer = customer.AsyncCustomerResource(self)
        self.spend = spend.AsyncSpendResource(self)
        self.global_ = global_.AsyncGlobalResource(self)
        self.provider = provider.AsyncProviderResource(self)
        self.cache = cache.AsyncCacheResource(self)
        self.guardrails = guardrails.AsyncGuardrailsResource(self)
        self.add = add.AsyncAddResource(self)
        self.delete = delete.AsyncDeleteResource(self)
        self.files = files.AsyncFilesResource(self)
        self.budget = budget.AsyncBudgetResource(self)
        self.with_raw_response = AsyncHanzoWithRawResponse(self)
        self.with_streaming_response = AsyncHanzoWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Ocp-Apim-Subscription-Key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "sandbox"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    async def get_home(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Home"""
        return await self.get(
            "/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class HanzoWithRawResponse:
    def __init__(self, client: Hanzo) -> None:
        self.models = models.ModelsResourceWithRawResponse(client.models)
        self.openai = openai.OpenAIResourceWithRawResponse(client.openai)
        self.engines = engines.EnginesResourceWithRawResponse(client.engines)
        self.chat = chat.ChatResourceWithRawResponse(client.chat)
        self.completions = completions.CompletionsResourceWithRawResponse(client.completions)
        self.embeddings = embeddings.EmbeddingsResourceWithRawResponse(client.embeddings)
        self.images = images.ImagesResourceWithRawResponse(client.images)
        self.audio = audio.AudioResourceWithRawResponse(client.audio)
        self.assistants = assistants.AssistantsResourceWithRawResponse(client.assistants)
        self.threads = threads.ThreadsResourceWithRawResponse(client.threads)
        self.moderations = moderations.ModerationsResourceWithRawResponse(client.moderations)
        self.utils = utils.UtilsResourceWithRawResponse(client.utils)
        self.model = model.ModelResourceWithRawResponse(client.model)
        self.model_group = model_group.ModelGroupResourceWithRawResponse(client.model_group)
        self.routes = routes.RoutesResourceWithRawResponse(client.routes)
        self.responses = responses.ResponsesResourceWithRawResponse(client.responses)
        self.batches = batches.BatchesResourceWithRawResponse(client.batches)
        self.rerank = rerank.RerankResourceWithRawResponse(client.rerank)
        self.fine_tuning = fine_tuning.FineTuningResourceWithRawResponse(client.fine_tuning)
        self.credentials = credentials.CredentialsResourceWithRawResponse(client.credentials)
        self.vertex_ai = vertex_ai.VertexAIResourceWithRawResponse(client.vertex_ai)
        self.gemini = gemini.GeminiResourceWithRawResponse(client.gemini)
        self.cohere = cohere.CohereResourceWithRawResponse(client.cohere)
        self.anthropic = anthropic.AnthropicResourceWithRawResponse(client.anthropic)
        self.bedrock = bedrock.BedrockResourceWithRawResponse(client.bedrock)
        self.eu_assemblyai = eu_assemblyai.EuAssemblyaiResourceWithRawResponse(client.eu_assemblyai)
        self.assemblyai = assemblyai.AssemblyaiResourceWithRawResponse(client.assemblyai)
        self.azure = azure.AzureResourceWithRawResponse(client.azure)
        self.langfuse = langfuse.LangfuseResourceWithRawResponse(client.langfuse)
        self.config = config.ConfigResourceWithRawResponse(client.config)
        self.test = test.TestResourceWithRawResponse(client.test)
        self.health = health.HealthResourceWithRawResponse(client.health)
        self.active = active.ActiveResourceWithRawResponse(client.active)
        self.settings = settings.SettingsResourceWithRawResponse(client.settings)
        self.key = key.KeyResourceWithRawResponse(client.key)
        self.user = user.UserResourceWithRawResponse(client.user)
        self.team = team.TeamResourceWithRawResponse(client.team)
        self.organization = organization.OrganizationResourceWithRawResponse(client.organization)
        self.customer = customer.CustomerResourceWithRawResponse(client.customer)
        self.spend = spend.SpendResourceWithRawResponse(client.spend)
        self.global_ = global_.GlobalResourceWithRawResponse(client.global_)
        self.provider = provider.ProviderResourceWithRawResponse(client.provider)
        self.cache = cache.CacheResourceWithRawResponse(client.cache)
        self.guardrails = guardrails.GuardrailsResourceWithRawResponse(client.guardrails)
        self.add = add.AddResourceWithRawResponse(client.add)
        self.delete = delete.DeleteResourceWithRawResponse(client.delete)
        self.files = files.FilesResourceWithRawResponse(client.files)
        self.budget = budget.BudgetResourceWithRawResponse(client.budget)

        self.get_home = to_raw_response_wrapper(
            client.get_home,
        )


class AsyncHanzoWithRawResponse:
    def __init__(self, client: AsyncHanzo) -> None:
        self.models = models.AsyncModelsResourceWithRawResponse(client.models)
        self.openai = openai.AsyncOpenAIResourceWithRawResponse(client.openai)
        self.engines = engines.AsyncEnginesResourceWithRawResponse(client.engines)
        self.chat = chat.AsyncChatResourceWithRawResponse(client.chat)
        self.completions = completions.AsyncCompletionsResourceWithRawResponse(client.completions)
        self.embeddings = embeddings.AsyncEmbeddingsResourceWithRawResponse(client.embeddings)
        self.images = images.AsyncImagesResourceWithRawResponse(client.images)
        self.audio = audio.AsyncAudioResourceWithRawResponse(client.audio)
        self.assistants = assistants.AsyncAssistantsResourceWithRawResponse(client.assistants)
        self.threads = threads.AsyncThreadsResourceWithRawResponse(client.threads)
        self.moderations = moderations.AsyncModerationsResourceWithRawResponse(client.moderations)
        self.utils = utils.AsyncUtilsResourceWithRawResponse(client.utils)
        self.model = model.AsyncModelResourceWithRawResponse(client.model)
        self.model_group = model_group.AsyncModelGroupResourceWithRawResponse(client.model_group)
        self.routes = routes.AsyncRoutesResourceWithRawResponse(client.routes)
        self.responses = responses.AsyncResponsesResourceWithRawResponse(client.responses)
        self.batches = batches.AsyncBatchesResourceWithRawResponse(client.batches)
        self.rerank = rerank.AsyncRerankResourceWithRawResponse(client.rerank)
        self.fine_tuning = fine_tuning.AsyncFineTuningResourceWithRawResponse(client.fine_tuning)
        self.credentials = credentials.AsyncCredentialsResourceWithRawResponse(client.credentials)
        self.vertex_ai = vertex_ai.AsyncVertexAIResourceWithRawResponse(client.vertex_ai)
        self.gemini = gemini.AsyncGeminiResourceWithRawResponse(client.gemini)
        self.cohere = cohere.AsyncCohereResourceWithRawResponse(client.cohere)
        self.anthropic = anthropic.AsyncAnthropicResourceWithRawResponse(client.anthropic)
        self.bedrock = bedrock.AsyncBedrockResourceWithRawResponse(client.bedrock)
        self.eu_assemblyai = eu_assemblyai.AsyncEuAssemblyaiResourceWithRawResponse(client.eu_assemblyai)
        self.assemblyai = assemblyai.AsyncAssemblyaiResourceWithRawResponse(client.assemblyai)
        self.azure = azure.AsyncAzureResourceWithRawResponse(client.azure)
        self.langfuse = langfuse.AsyncLangfuseResourceWithRawResponse(client.langfuse)
        self.config = config.AsyncConfigResourceWithRawResponse(client.config)
        self.test = test.AsyncTestResourceWithRawResponse(client.test)
        self.health = health.AsyncHealthResourceWithRawResponse(client.health)
        self.active = active.AsyncActiveResourceWithRawResponse(client.active)
        self.settings = settings.AsyncSettingsResourceWithRawResponse(client.settings)
        self.key = key.AsyncKeyResourceWithRawResponse(client.key)
        self.user = user.AsyncUserResourceWithRawResponse(client.user)
        self.team = team.AsyncTeamResourceWithRawResponse(client.team)
        self.organization = organization.AsyncOrganizationResourceWithRawResponse(client.organization)
        self.customer = customer.AsyncCustomerResourceWithRawResponse(client.customer)
        self.spend = spend.AsyncSpendResourceWithRawResponse(client.spend)
        self.global_ = global_.AsyncGlobalResourceWithRawResponse(client.global_)
        self.provider = provider.AsyncProviderResourceWithRawResponse(client.provider)
        self.cache = cache.AsyncCacheResourceWithRawResponse(client.cache)
        self.guardrails = guardrails.AsyncGuardrailsResourceWithRawResponse(client.guardrails)
        self.add = add.AsyncAddResourceWithRawResponse(client.add)
        self.delete = delete.AsyncDeleteResourceWithRawResponse(client.delete)
        self.files = files.AsyncFilesResourceWithRawResponse(client.files)
        self.budget = budget.AsyncBudgetResourceWithRawResponse(client.budget)

        self.get_home = async_to_raw_response_wrapper(
            client.get_home,
        )


class HanzoWithStreamedResponse:
    def __init__(self, client: Hanzo) -> None:
        self.models = models.ModelsResourceWithStreamingResponse(client.models)
        self.openai = openai.OpenAIResourceWithStreamingResponse(client.openai)
        self.engines = engines.EnginesResourceWithStreamingResponse(client.engines)
        self.chat = chat.ChatResourceWithStreamingResponse(client.chat)
        self.completions = completions.CompletionsResourceWithStreamingResponse(client.completions)
        self.embeddings = embeddings.EmbeddingsResourceWithStreamingResponse(client.embeddings)
        self.images = images.ImagesResourceWithStreamingResponse(client.images)
        self.audio = audio.AudioResourceWithStreamingResponse(client.audio)
        self.assistants = assistants.AssistantsResourceWithStreamingResponse(client.assistants)
        self.threads = threads.ThreadsResourceWithStreamingResponse(client.threads)
        self.moderations = moderations.ModerationsResourceWithStreamingResponse(client.moderations)
        self.utils = utils.UtilsResourceWithStreamingResponse(client.utils)
        self.model = model.ModelResourceWithStreamingResponse(client.model)
        self.model_group = model_group.ModelGroupResourceWithStreamingResponse(client.model_group)
        self.routes = routes.RoutesResourceWithStreamingResponse(client.routes)
        self.responses = responses.ResponsesResourceWithStreamingResponse(client.responses)
        self.batches = batches.BatchesResourceWithStreamingResponse(client.batches)
        self.rerank = rerank.RerankResourceWithStreamingResponse(client.rerank)
        self.fine_tuning = fine_tuning.FineTuningResourceWithStreamingResponse(client.fine_tuning)
        self.credentials = credentials.CredentialsResourceWithStreamingResponse(client.credentials)
        self.vertex_ai = vertex_ai.VertexAIResourceWithStreamingResponse(client.vertex_ai)
        self.gemini = gemini.GeminiResourceWithStreamingResponse(client.gemini)
        self.cohere = cohere.CohereResourceWithStreamingResponse(client.cohere)
        self.anthropic = anthropic.AnthropicResourceWithStreamingResponse(client.anthropic)
        self.bedrock = bedrock.BedrockResourceWithStreamingResponse(client.bedrock)
        self.eu_assemblyai = eu_assemblyai.EuAssemblyaiResourceWithStreamingResponse(client.eu_assemblyai)
        self.assemblyai = assemblyai.AssemblyaiResourceWithStreamingResponse(client.assemblyai)
        self.azure = azure.AzureResourceWithStreamingResponse(client.azure)
        self.langfuse = langfuse.LangfuseResourceWithStreamingResponse(client.langfuse)
        self.config = config.ConfigResourceWithStreamingResponse(client.config)
        self.test = test.TestResourceWithStreamingResponse(client.test)
        self.health = health.HealthResourceWithStreamingResponse(client.health)
        self.active = active.ActiveResourceWithStreamingResponse(client.active)
        self.settings = settings.SettingsResourceWithStreamingResponse(client.settings)
        self.key = key.KeyResourceWithStreamingResponse(client.key)
        self.user = user.UserResourceWithStreamingResponse(client.user)
        self.team = team.TeamResourceWithStreamingResponse(client.team)
        self.organization = organization.OrganizationResourceWithStreamingResponse(client.organization)
        self.customer = customer.CustomerResourceWithStreamingResponse(client.customer)
        self.spend = spend.SpendResourceWithStreamingResponse(client.spend)
        self.global_ = global_.GlobalResourceWithStreamingResponse(client.global_)
        self.provider = provider.ProviderResourceWithStreamingResponse(client.provider)
        self.cache = cache.CacheResourceWithStreamingResponse(client.cache)
        self.guardrails = guardrails.GuardrailsResourceWithStreamingResponse(client.guardrails)
        self.add = add.AddResourceWithStreamingResponse(client.add)
        self.delete = delete.DeleteResourceWithStreamingResponse(client.delete)
        self.files = files.FilesResourceWithStreamingResponse(client.files)
        self.budget = budget.BudgetResourceWithStreamingResponse(client.budget)

        self.get_home = to_streamed_response_wrapper(
            client.get_home,
        )


class AsyncHanzoWithStreamedResponse:
    def __init__(self, client: AsyncHanzo) -> None:
        self.models = models.AsyncModelsResourceWithStreamingResponse(client.models)
        self.openai = openai.AsyncOpenAIResourceWithStreamingResponse(client.openai)
        self.engines = engines.AsyncEnginesResourceWithStreamingResponse(client.engines)
        self.chat = chat.AsyncChatResourceWithStreamingResponse(client.chat)
        self.completions = completions.AsyncCompletionsResourceWithStreamingResponse(client.completions)
        self.embeddings = embeddings.AsyncEmbeddingsResourceWithStreamingResponse(client.embeddings)
        self.images = images.AsyncImagesResourceWithStreamingResponse(client.images)
        self.audio = audio.AsyncAudioResourceWithStreamingResponse(client.audio)
        self.assistants = assistants.AsyncAssistantsResourceWithStreamingResponse(client.assistants)
        self.threads = threads.AsyncThreadsResourceWithStreamingResponse(client.threads)
        self.moderations = moderations.AsyncModerationsResourceWithStreamingResponse(client.moderations)
        self.utils = utils.AsyncUtilsResourceWithStreamingResponse(client.utils)
        self.model = model.AsyncModelResourceWithStreamingResponse(client.model)
        self.model_group = model_group.AsyncModelGroupResourceWithStreamingResponse(client.model_group)
        self.routes = routes.AsyncRoutesResourceWithStreamingResponse(client.routes)
        self.responses = responses.AsyncResponsesResourceWithStreamingResponse(client.responses)
        self.batches = batches.AsyncBatchesResourceWithStreamingResponse(client.batches)
        self.rerank = rerank.AsyncRerankResourceWithStreamingResponse(client.rerank)
        self.fine_tuning = fine_tuning.AsyncFineTuningResourceWithStreamingResponse(client.fine_tuning)
        self.credentials = credentials.AsyncCredentialsResourceWithStreamingResponse(client.credentials)
        self.vertex_ai = vertex_ai.AsyncVertexAIResourceWithStreamingResponse(client.vertex_ai)
        self.gemini = gemini.AsyncGeminiResourceWithStreamingResponse(client.gemini)
        self.cohere = cohere.AsyncCohereResourceWithStreamingResponse(client.cohere)
        self.anthropic = anthropic.AsyncAnthropicResourceWithStreamingResponse(client.anthropic)
        self.bedrock = bedrock.AsyncBedrockResourceWithStreamingResponse(client.bedrock)
        self.eu_assemblyai = eu_assemblyai.AsyncEuAssemblyaiResourceWithStreamingResponse(client.eu_assemblyai)
        self.assemblyai = assemblyai.AsyncAssemblyaiResourceWithStreamingResponse(client.assemblyai)
        self.azure = azure.AsyncAzureResourceWithStreamingResponse(client.azure)
        self.langfuse = langfuse.AsyncLangfuseResourceWithStreamingResponse(client.langfuse)
        self.config = config.AsyncConfigResourceWithStreamingResponse(client.config)
        self.test = test.AsyncTestResourceWithStreamingResponse(client.test)
        self.health = health.AsyncHealthResourceWithStreamingResponse(client.health)
        self.active = active.AsyncActiveResourceWithStreamingResponse(client.active)
        self.settings = settings.AsyncSettingsResourceWithStreamingResponse(client.settings)
        self.key = key.AsyncKeyResourceWithStreamingResponse(client.key)
        self.user = user.AsyncUserResourceWithStreamingResponse(client.user)
        self.team = team.AsyncTeamResourceWithStreamingResponse(client.team)
        self.organization = organization.AsyncOrganizationResourceWithStreamingResponse(client.organization)
        self.customer = customer.AsyncCustomerResourceWithStreamingResponse(client.customer)
        self.spend = spend.AsyncSpendResourceWithStreamingResponse(client.spend)
        self.global_ = global_.AsyncGlobalResourceWithStreamingResponse(client.global_)
        self.provider = provider.AsyncProviderResourceWithStreamingResponse(client.provider)
        self.cache = cache.AsyncCacheResourceWithStreamingResponse(client.cache)
        self.guardrails = guardrails.AsyncGuardrailsResourceWithStreamingResponse(client.guardrails)
        self.add = add.AsyncAddResourceWithStreamingResponse(client.add)
        self.delete = delete.AsyncDeleteResourceWithStreamingResponse(client.delete)
        self.files = files.AsyncFilesResourceWithStreamingResponse(client.files)
        self.budget = budget.AsyncBudgetResourceWithStreamingResponse(client.budget)

        self.get_home = async_to_streamed_response_wrapper(
            client.get_home,
        )


Client = Hanzo

AsyncClient = AsyncHanzo
