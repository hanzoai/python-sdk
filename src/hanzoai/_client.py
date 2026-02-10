# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Mapping, cast
from typing_extensions import Self, Literal, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Body,
    Omit,
    Query,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import HanzoError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
    make_request_options,
)

if TYPE_CHECKING:
    from .resources import (
        add,
        key,
        chat,
        team,
        test,
        user,
        audio,
        azure,
        cache,
        files,
        model,
        spend,
        utils,
        active,
        budget,
        cohere,
        config,
        delete,
        gemini,
        health,
        images,
        models,
        openai,
        rerank,
        routes,
        batches,
        bedrock,
        engines,
        global_,
        threads,
        customer,
        langfuse,
        provider,
        settings,
        anthropic,
        responses,
        vertex_ai,
        assemblyai,
        assistants,
        embeddings,
        guardrails,
        completions,
        credentials,
        fine_tuning,
        model_group,
        moderations,
        organization,
        eu_assemblyai,
    )
    from .resources.add import AddResource, AsyncAddResource
    from .resources.test import TestResource, AsyncTestResource
    from .resources.user import UserResource, AsyncUserResource
    from .resources.azure import AzureResource, AsyncAzureResource
    from .resources.spend import SpendResource, AsyncSpendResource
    from .resources.utils import UtilsResource, AsyncUtilsResource
    from .resources.active import ActiveResource, AsyncActiveResource
    from .resources.budget import BudgetResource, AsyncBudgetResource
    from .resources.cohere import CohereResource, AsyncCohereResource
    from .resources.delete import DeleteResource, AsyncDeleteResource
    from .resources.gemini import GeminiResource, AsyncGeminiResource
    from .resources.health import HealthResource, AsyncHealthResource
    from .resources.models import ModelsResource, AsyncModelsResource
    from .resources.rerank import RerankResource, AsyncRerankResource
    from .resources.routes import RoutesResource, AsyncRoutesResource
    from .resources.bedrock import BedrockResource, AsyncBedrockResource
    from .resources.key.key import KeyResource, AsyncKeyResource
    from .resources.customer import CustomerResource, AsyncCustomerResource
    from .resources.langfuse import LangfuseResource, AsyncLangfuseResource
    from .resources.provider import ProviderResource, AsyncProviderResource
    from .resources.settings import SettingsResource, AsyncSettingsResource
    from .resources.anthropic import AnthropicResource, AsyncAnthropicResource
    from .resources.chat.chat import ChatResource, AsyncChatResource
    from .resources.team.team import TeamResource, AsyncTeamResource
    from .resources.vertex_ai import VertexAIResource, AsyncVertexAIResource
    from .resources.assemblyai import AssemblyaiResource, AsyncAssemblyaiResource
    from .resources.assistants import AssistantsResource, AsyncAssistantsResource
    from .resources.embeddings import EmbeddingsResource, AsyncEmbeddingsResource
    from .resources.guardrails import GuardrailsResource, AsyncGuardrailsResource
    from .resources.audio.audio import AudioResource, AsyncAudioResource
    from .resources.cache.cache import CacheResource, AsyncCacheResource
    from .resources.completions import CompletionsResource, AsyncCompletionsResource
    from .resources.credentials import CredentialsResource, AsyncCredentialsResource
    from .resources.files.files import FilesResource, AsyncFilesResource
    from .resources.model.model import ModelResource, AsyncModelResource
    from .resources.model_group import ModelGroupResource, AsyncModelGroupResource
    from .resources.moderations import ModerationsResource, AsyncModerationsResource
    from .resources.config.config import ConfigResource, AsyncConfigResource
    from .resources.eu_assemblyai import EuAssemblyaiResource, AsyncEuAssemblyaiResource
    from .resources.images.images import ImagesResource, AsyncImagesResource
    from .resources.openai.openai import OpenAIResource, AsyncOpenAIResource
    from .resources.batches.batches import BatchesResource, AsyncBatchesResource
    from .resources.engines.engines import EnginesResource, AsyncEnginesResource
    from .resources.global_.global_ import GlobalResource, AsyncGlobalResource
    from .resources.threads.threads import ThreadsResource, AsyncThreadsResource
    from .resources.responses.responses import ResponsesResource, AsyncResponsesResource
    from .resources.fine_tuning.fine_tuning import FineTuningResource, AsyncFineTuningResource
    from .resources.organization.organization import OrganizationResource, AsyncOrganizationResource

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
    # client options
    api_key: str

    _environment: Literal["production", "sandbox"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "sandbox"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
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

    @cached_property
    def models(self) -> ModelsResource:
        from .resources.models import ModelsResource

        return ModelsResource(self)

    @cached_property
    def openai(self) -> OpenAIResource:
        from .resources.openai import OpenAIResource

        return OpenAIResource(self)

    @cached_property
    def engines(self) -> EnginesResource:
        from .resources.engines import EnginesResource

        return EnginesResource(self)

    @cached_property
    def chat(self) -> ChatResource:
        from .resources.chat import ChatResource

        return ChatResource(self)

    @cached_property
    def completions(self) -> CompletionsResource:
        from .resources.completions import CompletionsResource

        return CompletionsResource(self)

    @cached_property
    def embeddings(self) -> EmbeddingsResource:
        from .resources.embeddings import EmbeddingsResource

        return EmbeddingsResource(self)

    @cached_property
    def images(self) -> ImagesResource:
        from .resources.images import ImagesResource

        return ImagesResource(self)

    @cached_property
    def audio(self) -> AudioResource:
        from .resources.audio import AudioResource

        return AudioResource(self)

    @cached_property
    def assistants(self) -> AssistantsResource:
        from .resources.assistants import AssistantsResource

        return AssistantsResource(self)

    @cached_property
    def threads(self) -> ThreadsResource:
        from .resources.threads import ThreadsResource

        return ThreadsResource(self)

    @cached_property
    def moderations(self) -> ModerationsResource:
        from .resources.moderations import ModerationsResource

        return ModerationsResource(self)

    @cached_property
    def utils(self) -> UtilsResource:
        from .resources.utils import UtilsResource

        return UtilsResource(self)

    @cached_property
    def model(self) -> ModelResource:
        from .resources.model import ModelResource

        return ModelResource(self)

    @cached_property
    def model_group(self) -> ModelGroupResource:
        from .resources.model_group import ModelGroupResource

        return ModelGroupResource(self)

    @cached_property
    def routes(self) -> RoutesResource:
        from .resources.routes import RoutesResource

        return RoutesResource(self)

    @cached_property
    def responses(self) -> ResponsesResource:
        from .resources.responses import ResponsesResource

        return ResponsesResource(self)

    @cached_property
    def batches(self) -> BatchesResource:
        from .resources.batches import BatchesResource

        return BatchesResource(self)

    @cached_property
    def rerank(self) -> RerankResource:
        from .resources.rerank import RerankResource

        return RerankResource(self)

    @cached_property
    def fine_tuning(self) -> FineTuningResource:
        from .resources.fine_tuning import FineTuningResource

        return FineTuningResource(self)

    @cached_property
    def credentials(self) -> CredentialsResource:
        from .resources.credentials import CredentialsResource

        return CredentialsResource(self)

    @cached_property
    def vertex_ai(self) -> VertexAIResource:
        from .resources.vertex_ai import VertexAIResource

        return VertexAIResource(self)

    @cached_property
    def gemini(self) -> GeminiResource:
        from .resources.gemini import GeminiResource

        return GeminiResource(self)

    @cached_property
    def cohere(self) -> CohereResource:
        from .resources.cohere import CohereResource

        return CohereResource(self)

    @cached_property
    def anthropic(self) -> AnthropicResource:
        from .resources.anthropic import AnthropicResource

        return AnthropicResource(self)

    @cached_property
    def bedrock(self) -> BedrockResource:
        from .resources.bedrock import BedrockResource

        return BedrockResource(self)

    @cached_property
    def eu_assemblyai(self) -> EuAssemblyaiResource:
        from .resources.eu_assemblyai import EuAssemblyaiResource

        return EuAssemblyaiResource(self)

    @cached_property
    def assemblyai(self) -> AssemblyaiResource:
        from .resources.assemblyai import AssemblyaiResource

        return AssemblyaiResource(self)

    @cached_property
    def azure(self) -> AzureResource:
        from .resources.azure import AzureResource

        return AzureResource(self)

    @cached_property
    def langfuse(self) -> LangfuseResource:
        from .resources.langfuse import LangfuseResource

        return LangfuseResource(self)

    @cached_property
    def config(self) -> ConfigResource:
        from .resources.config import ConfigResource

        return ConfigResource(self)

    @cached_property
    def test(self) -> TestResource:
        from .resources.test import TestResource

        return TestResource(self)

    @cached_property
    def health(self) -> HealthResource:
        from .resources.health import HealthResource

        return HealthResource(self)

    @cached_property
    def active(self) -> ActiveResource:
        from .resources.active import ActiveResource

        return ActiveResource(self)

    @cached_property
    def settings(self) -> SettingsResource:
        from .resources.settings import SettingsResource

        return SettingsResource(self)

    @cached_property
    def key(self) -> KeyResource:
        from .resources.key import KeyResource

        return KeyResource(self)

    @cached_property
    def user(self) -> UserResource:
        from .resources.user import UserResource

        return UserResource(self)

    @cached_property
    def team(self) -> TeamResource:
        from .resources.team import TeamResource

        return TeamResource(self)

    @cached_property
    def organization(self) -> OrganizationResource:
        from .resources.organization import OrganizationResource

        return OrganizationResource(self)

    @cached_property
    def customer(self) -> CustomerResource:
        from .resources.customer import CustomerResource

        return CustomerResource(self)

    @cached_property
    def spend(self) -> SpendResource:
        from .resources.spend import SpendResource

        return SpendResource(self)

    @cached_property
    def global_(self) -> GlobalResource:
        from .resources.global_ import GlobalResource

        return GlobalResource(self)

    @cached_property
    def provider(self) -> ProviderResource:
        from .resources.provider import ProviderResource

        return ProviderResource(self)

    @cached_property
    def cache(self) -> CacheResource:
        from .resources.cache import CacheResource

        return CacheResource(self)

    @cached_property
    def guardrails(self) -> GuardrailsResource:
        from .resources.guardrails import GuardrailsResource

        return GuardrailsResource(self)

    @cached_property
    def add(self) -> AddResource:
        from .resources.add import AddResource

        return AddResource(self)

    @cached_property
    def delete(self) -> DeleteResource:
        from .resources.delete import DeleteResource

        return DeleteResource(self)

    @cached_property
    def files(self) -> FilesResource:
        from .resources.files import FilesResource

        return FilesResource(self)

    @cached_property
    def budget(self) -> BudgetResource:
        from .resources.budget import BudgetResource

        return BudgetResource(self)

    @cached_property
    def with_raw_response(self) -> HanzoWithRawResponse:
        return HanzoWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HanzoWithStreamedResponse:
        return HanzoWithStreamedResponse(self)

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
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
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
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
    # client options
    api_key: str

    _environment: Literal["production", "sandbox"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "sandbox"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
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

    @cached_property
    def models(self) -> AsyncModelsResource:
        from .resources.models import AsyncModelsResource

        return AsyncModelsResource(self)

    @cached_property
    def openai(self) -> AsyncOpenAIResource:
        from .resources.openai import AsyncOpenAIResource

        return AsyncOpenAIResource(self)

    @cached_property
    def engines(self) -> AsyncEnginesResource:
        from .resources.engines import AsyncEnginesResource

        return AsyncEnginesResource(self)

    @cached_property
    def chat(self) -> AsyncChatResource:
        from .resources.chat import AsyncChatResource

        return AsyncChatResource(self)

    @cached_property
    def completions(self) -> AsyncCompletionsResource:
        from .resources.completions import AsyncCompletionsResource

        return AsyncCompletionsResource(self)

    @cached_property
    def embeddings(self) -> AsyncEmbeddingsResource:
        from .resources.embeddings import AsyncEmbeddingsResource

        return AsyncEmbeddingsResource(self)

    @cached_property
    def images(self) -> AsyncImagesResource:
        from .resources.images import AsyncImagesResource

        return AsyncImagesResource(self)

    @cached_property
    def audio(self) -> AsyncAudioResource:
        from .resources.audio import AsyncAudioResource

        return AsyncAudioResource(self)

    @cached_property
    def assistants(self) -> AsyncAssistantsResource:
        from .resources.assistants import AsyncAssistantsResource

        return AsyncAssistantsResource(self)

    @cached_property
    def threads(self) -> AsyncThreadsResource:
        from .resources.threads import AsyncThreadsResource

        return AsyncThreadsResource(self)

    @cached_property
    def moderations(self) -> AsyncModerationsResource:
        from .resources.moderations import AsyncModerationsResource

        return AsyncModerationsResource(self)

    @cached_property
    def utils(self) -> AsyncUtilsResource:
        from .resources.utils import AsyncUtilsResource

        return AsyncUtilsResource(self)

    @cached_property
    def model(self) -> AsyncModelResource:
        from .resources.model import AsyncModelResource

        return AsyncModelResource(self)

    @cached_property
    def model_group(self) -> AsyncModelGroupResource:
        from .resources.model_group import AsyncModelGroupResource

        return AsyncModelGroupResource(self)

    @cached_property
    def routes(self) -> AsyncRoutesResource:
        from .resources.routes import AsyncRoutesResource

        return AsyncRoutesResource(self)

    @cached_property
    def responses(self) -> AsyncResponsesResource:
        from .resources.responses import AsyncResponsesResource

        return AsyncResponsesResource(self)

    @cached_property
    def batches(self) -> AsyncBatchesResource:
        from .resources.batches import AsyncBatchesResource

        return AsyncBatchesResource(self)

    @cached_property
    def rerank(self) -> AsyncRerankResource:
        from .resources.rerank import AsyncRerankResource

        return AsyncRerankResource(self)

    @cached_property
    def fine_tuning(self) -> AsyncFineTuningResource:
        from .resources.fine_tuning import AsyncFineTuningResource

        return AsyncFineTuningResource(self)

    @cached_property
    def credentials(self) -> AsyncCredentialsResource:
        from .resources.credentials import AsyncCredentialsResource

        return AsyncCredentialsResource(self)

    @cached_property
    def vertex_ai(self) -> AsyncVertexAIResource:
        from .resources.vertex_ai import AsyncVertexAIResource

        return AsyncVertexAIResource(self)

    @cached_property
    def gemini(self) -> AsyncGeminiResource:
        from .resources.gemini import AsyncGeminiResource

        return AsyncGeminiResource(self)

    @cached_property
    def cohere(self) -> AsyncCohereResource:
        from .resources.cohere import AsyncCohereResource

        return AsyncCohereResource(self)

    @cached_property
    def anthropic(self) -> AsyncAnthropicResource:
        from .resources.anthropic import AsyncAnthropicResource

        return AsyncAnthropicResource(self)

    @cached_property
    def bedrock(self) -> AsyncBedrockResource:
        from .resources.bedrock import AsyncBedrockResource

        return AsyncBedrockResource(self)

    @cached_property
    def eu_assemblyai(self) -> AsyncEuAssemblyaiResource:
        from .resources.eu_assemblyai import AsyncEuAssemblyaiResource

        return AsyncEuAssemblyaiResource(self)

    @cached_property
    def assemblyai(self) -> AsyncAssemblyaiResource:
        from .resources.assemblyai import AsyncAssemblyaiResource

        return AsyncAssemblyaiResource(self)

    @cached_property
    def azure(self) -> AsyncAzureResource:
        from .resources.azure import AsyncAzureResource

        return AsyncAzureResource(self)

    @cached_property
    def langfuse(self) -> AsyncLangfuseResource:
        from .resources.langfuse import AsyncLangfuseResource

        return AsyncLangfuseResource(self)

    @cached_property
    def config(self) -> AsyncConfigResource:
        from .resources.config import AsyncConfigResource

        return AsyncConfigResource(self)

    @cached_property
    def test(self) -> AsyncTestResource:
        from .resources.test import AsyncTestResource

        return AsyncTestResource(self)

    @cached_property
    def health(self) -> AsyncHealthResource:
        from .resources.health import AsyncHealthResource

        return AsyncHealthResource(self)

    @cached_property
    def active(self) -> AsyncActiveResource:
        from .resources.active import AsyncActiveResource

        return AsyncActiveResource(self)

    @cached_property
    def settings(self) -> AsyncSettingsResource:
        from .resources.settings import AsyncSettingsResource

        return AsyncSettingsResource(self)

    @cached_property
    def key(self) -> AsyncKeyResource:
        from .resources.key import AsyncKeyResource

        return AsyncKeyResource(self)

    @cached_property
    def user(self) -> AsyncUserResource:
        from .resources.user import AsyncUserResource

        return AsyncUserResource(self)

    @cached_property
    def team(self) -> AsyncTeamResource:
        from .resources.team import AsyncTeamResource

        return AsyncTeamResource(self)

    @cached_property
    def organization(self) -> AsyncOrganizationResource:
        from .resources.organization import AsyncOrganizationResource

        return AsyncOrganizationResource(self)

    @cached_property
    def customer(self) -> AsyncCustomerResource:
        from .resources.customer import AsyncCustomerResource

        return AsyncCustomerResource(self)

    @cached_property
    def spend(self) -> AsyncSpendResource:
        from .resources.spend import AsyncSpendResource

        return AsyncSpendResource(self)

    @cached_property
    def global_(self) -> AsyncGlobalResource:
        from .resources.global_ import AsyncGlobalResource

        return AsyncGlobalResource(self)

    @cached_property
    def provider(self) -> AsyncProviderResource:
        from .resources.provider import AsyncProviderResource

        return AsyncProviderResource(self)

    @cached_property
    def cache(self) -> AsyncCacheResource:
        from .resources.cache import AsyncCacheResource

        return AsyncCacheResource(self)

    @cached_property
    def guardrails(self) -> AsyncGuardrailsResource:
        from .resources.guardrails import AsyncGuardrailsResource

        return AsyncGuardrailsResource(self)

    @cached_property
    def add(self) -> AsyncAddResource:
        from .resources.add import AsyncAddResource

        return AsyncAddResource(self)

    @cached_property
    def delete(self) -> AsyncDeleteResource:
        from .resources.delete import AsyncDeleteResource

        return AsyncDeleteResource(self)

    @cached_property
    def files(self) -> AsyncFilesResource:
        from .resources.files import AsyncFilesResource

        return AsyncFilesResource(self)

    @cached_property
    def budget(self) -> AsyncBudgetResource:
        from .resources.budget import AsyncBudgetResource

        return AsyncBudgetResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncHanzoWithRawResponse:
        return AsyncHanzoWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHanzoWithStreamedResponse:
        return AsyncHanzoWithStreamedResponse(self)

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
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
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
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
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
    _client: Hanzo

    def __init__(self, client: Hanzo) -> None:
        self._client = client

        self.get_home = to_raw_response_wrapper(
            client.get_home,
        )

    @cached_property
    def models(self) -> models.ModelsResourceWithRawResponse:
        from .resources.models import ModelsResourceWithRawResponse

        return ModelsResourceWithRawResponse(self._client.models)

    @cached_property
    def openai(self) -> openai.OpenAIResourceWithRawResponse:
        from .resources.openai import OpenAIResourceWithRawResponse

        return OpenAIResourceWithRawResponse(self._client.openai)

    @cached_property
    def engines(self) -> engines.EnginesResourceWithRawResponse:
        from .resources.engines import EnginesResourceWithRawResponse

        return EnginesResourceWithRawResponse(self._client.engines)

    @cached_property
    def chat(self) -> chat.ChatResourceWithRawResponse:
        from .resources.chat import ChatResourceWithRawResponse

        return ChatResourceWithRawResponse(self._client.chat)

    @cached_property
    def completions(self) -> completions.CompletionsResourceWithRawResponse:
        from .resources.completions import CompletionsResourceWithRawResponse

        return CompletionsResourceWithRawResponse(self._client.completions)

    @cached_property
    def embeddings(self) -> embeddings.EmbeddingsResourceWithRawResponse:
        from .resources.embeddings import EmbeddingsResourceWithRawResponse

        return EmbeddingsResourceWithRawResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.ImagesResourceWithRawResponse:
        from .resources.images import ImagesResourceWithRawResponse

        return ImagesResourceWithRawResponse(self._client.images)

    @cached_property
    def audio(self) -> audio.AudioResourceWithRawResponse:
        from .resources.audio import AudioResourceWithRawResponse

        return AudioResourceWithRawResponse(self._client.audio)

    @cached_property
    def assistants(self) -> assistants.AssistantsResourceWithRawResponse:
        from .resources.assistants import AssistantsResourceWithRawResponse

        return AssistantsResourceWithRawResponse(self._client.assistants)

    @cached_property
    def threads(self) -> threads.ThreadsResourceWithRawResponse:
        from .resources.threads import ThreadsResourceWithRawResponse

        return ThreadsResourceWithRawResponse(self._client.threads)

    @cached_property
    def moderations(self) -> moderations.ModerationsResourceWithRawResponse:
        from .resources.moderations import ModerationsResourceWithRawResponse

        return ModerationsResourceWithRawResponse(self._client.moderations)

    @cached_property
    def utils(self) -> utils.UtilsResourceWithRawResponse:
        from .resources.utils import UtilsResourceWithRawResponse

        return UtilsResourceWithRawResponse(self._client.utils)

    @cached_property
    def model(self) -> model.ModelResourceWithRawResponse:
        from .resources.model import ModelResourceWithRawResponse

        return ModelResourceWithRawResponse(self._client.model)

    @cached_property
    def model_group(self) -> model_group.ModelGroupResourceWithRawResponse:
        from .resources.model_group import ModelGroupResourceWithRawResponse

        return ModelGroupResourceWithRawResponse(self._client.model_group)

    @cached_property
    def routes(self) -> routes.RoutesResourceWithRawResponse:
        from .resources.routes import RoutesResourceWithRawResponse

        return RoutesResourceWithRawResponse(self._client.routes)

    @cached_property
    def responses(self) -> responses.ResponsesResourceWithRawResponse:
        from .resources.responses import ResponsesResourceWithRawResponse

        return ResponsesResourceWithRawResponse(self._client.responses)

    @cached_property
    def batches(self) -> batches.BatchesResourceWithRawResponse:
        from .resources.batches import BatchesResourceWithRawResponse

        return BatchesResourceWithRawResponse(self._client.batches)

    @cached_property
    def rerank(self) -> rerank.RerankResourceWithRawResponse:
        from .resources.rerank import RerankResourceWithRawResponse

        return RerankResourceWithRawResponse(self._client.rerank)

    @cached_property
    def fine_tuning(self) -> fine_tuning.FineTuningResourceWithRawResponse:
        from .resources.fine_tuning import FineTuningResourceWithRawResponse

        return FineTuningResourceWithRawResponse(self._client.fine_tuning)

    @cached_property
    def credentials(self) -> credentials.CredentialsResourceWithRawResponse:
        from .resources.credentials import CredentialsResourceWithRawResponse

        return CredentialsResourceWithRawResponse(self._client.credentials)

    @cached_property
    def vertex_ai(self) -> vertex_ai.VertexAIResourceWithRawResponse:
        from .resources.vertex_ai import VertexAIResourceWithRawResponse

        return VertexAIResourceWithRawResponse(self._client.vertex_ai)

    @cached_property
    def gemini(self) -> gemini.GeminiResourceWithRawResponse:
        from .resources.gemini import GeminiResourceWithRawResponse

        return GeminiResourceWithRawResponse(self._client.gemini)

    @cached_property
    def cohere(self) -> cohere.CohereResourceWithRawResponse:
        from .resources.cohere import CohereResourceWithRawResponse

        return CohereResourceWithRawResponse(self._client.cohere)

    @cached_property
    def anthropic(self) -> anthropic.AnthropicResourceWithRawResponse:
        from .resources.anthropic import AnthropicResourceWithRawResponse

        return AnthropicResourceWithRawResponse(self._client.anthropic)

    @cached_property
    def bedrock(self) -> bedrock.BedrockResourceWithRawResponse:
        from .resources.bedrock import BedrockResourceWithRawResponse

        return BedrockResourceWithRawResponse(self._client.bedrock)

    @cached_property
    def eu_assemblyai(self) -> eu_assemblyai.EuAssemblyaiResourceWithRawResponse:
        from .resources.eu_assemblyai import EuAssemblyaiResourceWithRawResponse

        return EuAssemblyaiResourceWithRawResponse(self._client.eu_assemblyai)

    @cached_property
    def assemblyai(self) -> assemblyai.AssemblyaiResourceWithRawResponse:
        from .resources.assemblyai import AssemblyaiResourceWithRawResponse

        return AssemblyaiResourceWithRawResponse(self._client.assemblyai)

    @cached_property
    def azure(self) -> azure.AzureResourceWithRawResponse:
        from .resources.azure import AzureResourceWithRawResponse

        return AzureResourceWithRawResponse(self._client.azure)

    @cached_property
    def langfuse(self) -> langfuse.LangfuseResourceWithRawResponse:
        from .resources.langfuse import LangfuseResourceWithRawResponse

        return LangfuseResourceWithRawResponse(self._client.langfuse)

    @cached_property
    def config(self) -> config.ConfigResourceWithRawResponse:
        from .resources.config import ConfigResourceWithRawResponse

        return ConfigResourceWithRawResponse(self._client.config)

    @cached_property
    def test(self) -> test.TestResourceWithRawResponse:
        from .resources.test import TestResourceWithRawResponse

        return TestResourceWithRawResponse(self._client.test)

    @cached_property
    def health(self) -> health.HealthResourceWithRawResponse:
        from .resources.health import HealthResourceWithRawResponse

        return HealthResourceWithRawResponse(self._client.health)

    @cached_property
    def active(self) -> active.ActiveResourceWithRawResponse:
        from .resources.active import ActiveResourceWithRawResponse

        return ActiveResourceWithRawResponse(self._client.active)

    @cached_property
    def settings(self) -> settings.SettingsResourceWithRawResponse:
        from .resources.settings import SettingsResourceWithRawResponse

        return SettingsResourceWithRawResponse(self._client.settings)

    @cached_property
    def key(self) -> key.KeyResourceWithRawResponse:
        from .resources.key import KeyResourceWithRawResponse

        return KeyResourceWithRawResponse(self._client.key)

    @cached_property
    def user(self) -> user.UserResourceWithRawResponse:
        from .resources.user import UserResourceWithRawResponse

        return UserResourceWithRawResponse(self._client.user)

    @cached_property
    def team(self) -> team.TeamResourceWithRawResponse:
        from .resources.team import TeamResourceWithRawResponse

        return TeamResourceWithRawResponse(self._client.team)

    @cached_property
    def organization(self) -> organization.OrganizationResourceWithRawResponse:
        from .resources.organization import OrganizationResourceWithRawResponse

        return OrganizationResourceWithRawResponse(self._client.organization)

    @cached_property
    def customer(self) -> customer.CustomerResourceWithRawResponse:
        from .resources.customer import CustomerResourceWithRawResponse

        return CustomerResourceWithRawResponse(self._client.customer)

    @cached_property
    def spend(self) -> spend.SpendResourceWithRawResponse:
        from .resources.spend import SpendResourceWithRawResponse

        return SpendResourceWithRawResponse(self._client.spend)

    @cached_property
    def global_(self) -> global_.GlobalResourceWithRawResponse:
        from .resources.global_ import GlobalResourceWithRawResponse

        return GlobalResourceWithRawResponse(self._client.global_)

    @cached_property
    def provider(self) -> provider.ProviderResourceWithRawResponse:
        from .resources.provider import ProviderResourceWithRawResponse

        return ProviderResourceWithRawResponse(self._client.provider)

    @cached_property
    def cache(self) -> cache.CacheResourceWithRawResponse:
        from .resources.cache import CacheResourceWithRawResponse

        return CacheResourceWithRawResponse(self._client.cache)

    @cached_property
    def guardrails(self) -> guardrails.GuardrailsResourceWithRawResponse:
        from .resources.guardrails import GuardrailsResourceWithRawResponse

        return GuardrailsResourceWithRawResponse(self._client.guardrails)

    @cached_property
    def add(self) -> add.AddResourceWithRawResponse:
        from .resources.add import AddResourceWithRawResponse

        return AddResourceWithRawResponse(self._client.add)

    @cached_property
    def delete(self) -> delete.DeleteResourceWithRawResponse:
        from .resources.delete import DeleteResourceWithRawResponse

        return DeleteResourceWithRawResponse(self._client.delete)

    @cached_property
    def files(self) -> files.FilesResourceWithRawResponse:
        from .resources.files import FilesResourceWithRawResponse

        return FilesResourceWithRawResponse(self._client.files)

    @cached_property
    def budget(self) -> budget.BudgetResourceWithRawResponse:
        from .resources.budget import BudgetResourceWithRawResponse

        return BudgetResourceWithRawResponse(self._client.budget)


class AsyncHanzoWithRawResponse:
    _client: AsyncHanzo

    def __init__(self, client: AsyncHanzo) -> None:
        self._client = client

        self.get_home = async_to_raw_response_wrapper(
            client.get_home,
        )

    @cached_property
    def models(self) -> models.AsyncModelsResourceWithRawResponse:
        from .resources.models import AsyncModelsResourceWithRawResponse

        return AsyncModelsResourceWithRawResponse(self._client.models)

    @cached_property
    def openai(self) -> openai.AsyncOpenAIResourceWithRawResponse:
        from .resources.openai import AsyncOpenAIResourceWithRawResponse

        return AsyncOpenAIResourceWithRawResponse(self._client.openai)

    @cached_property
    def engines(self) -> engines.AsyncEnginesResourceWithRawResponse:
        from .resources.engines import AsyncEnginesResourceWithRawResponse

        return AsyncEnginesResourceWithRawResponse(self._client.engines)

    @cached_property
    def chat(self) -> chat.AsyncChatResourceWithRawResponse:
        from .resources.chat import AsyncChatResourceWithRawResponse

        return AsyncChatResourceWithRawResponse(self._client.chat)

    @cached_property
    def completions(self) -> completions.AsyncCompletionsResourceWithRawResponse:
        from .resources.completions import AsyncCompletionsResourceWithRawResponse

        return AsyncCompletionsResourceWithRawResponse(self._client.completions)

    @cached_property
    def embeddings(self) -> embeddings.AsyncEmbeddingsResourceWithRawResponse:
        from .resources.embeddings import AsyncEmbeddingsResourceWithRawResponse

        return AsyncEmbeddingsResourceWithRawResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.AsyncImagesResourceWithRawResponse:
        from .resources.images import AsyncImagesResourceWithRawResponse

        return AsyncImagesResourceWithRawResponse(self._client.images)

    @cached_property
    def audio(self) -> audio.AsyncAudioResourceWithRawResponse:
        from .resources.audio import AsyncAudioResourceWithRawResponse

        return AsyncAudioResourceWithRawResponse(self._client.audio)

    @cached_property
    def assistants(self) -> assistants.AsyncAssistantsResourceWithRawResponse:
        from .resources.assistants import AsyncAssistantsResourceWithRawResponse

        return AsyncAssistantsResourceWithRawResponse(self._client.assistants)

    @cached_property
    def threads(self) -> threads.AsyncThreadsResourceWithRawResponse:
        from .resources.threads import AsyncThreadsResourceWithRawResponse

        return AsyncThreadsResourceWithRawResponse(self._client.threads)

    @cached_property
    def moderations(self) -> moderations.AsyncModerationsResourceWithRawResponse:
        from .resources.moderations import AsyncModerationsResourceWithRawResponse

        return AsyncModerationsResourceWithRawResponse(self._client.moderations)

    @cached_property
    def utils(self) -> utils.AsyncUtilsResourceWithRawResponse:
        from .resources.utils import AsyncUtilsResourceWithRawResponse

        return AsyncUtilsResourceWithRawResponse(self._client.utils)

    @cached_property
    def model(self) -> model.AsyncModelResourceWithRawResponse:
        from .resources.model import AsyncModelResourceWithRawResponse

        return AsyncModelResourceWithRawResponse(self._client.model)

    @cached_property
    def model_group(self) -> model_group.AsyncModelGroupResourceWithRawResponse:
        from .resources.model_group import AsyncModelGroupResourceWithRawResponse

        return AsyncModelGroupResourceWithRawResponse(self._client.model_group)

    @cached_property
    def routes(self) -> routes.AsyncRoutesResourceWithRawResponse:
        from .resources.routes import AsyncRoutesResourceWithRawResponse

        return AsyncRoutesResourceWithRawResponse(self._client.routes)

    @cached_property
    def responses(self) -> responses.AsyncResponsesResourceWithRawResponse:
        from .resources.responses import AsyncResponsesResourceWithRawResponse

        return AsyncResponsesResourceWithRawResponse(self._client.responses)

    @cached_property
    def batches(self) -> batches.AsyncBatchesResourceWithRawResponse:
        from .resources.batches import AsyncBatchesResourceWithRawResponse

        return AsyncBatchesResourceWithRawResponse(self._client.batches)

    @cached_property
    def rerank(self) -> rerank.AsyncRerankResourceWithRawResponse:
        from .resources.rerank import AsyncRerankResourceWithRawResponse

        return AsyncRerankResourceWithRawResponse(self._client.rerank)

    @cached_property
    def fine_tuning(self) -> fine_tuning.AsyncFineTuningResourceWithRawResponse:
        from .resources.fine_tuning import AsyncFineTuningResourceWithRawResponse

        return AsyncFineTuningResourceWithRawResponse(self._client.fine_tuning)

    @cached_property
    def credentials(self) -> credentials.AsyncCredentialsResourceWithRawResponse:
        from .resources.credentials import AsyncCredentialsResourceWithRawResponse

        return AsyncCredentialsResourceWithRawResponse(self._client.credentials)

    @cached_property
    def vertex_ai(self) -> vertex_ai.AsyncVertexAIResourceWithRawResponse:
        from .resources.vertex_ai import AsyncVertexAIResourceWithRawResponse

        return AsyncVertexAIResourceWithRawResponse(self._client.vertex_ai)

    @cached_property
    def gemini(self) -> gemini.AsyncGeminiResourceWithRawResponse:
        from .resources.gemini import AsyncGeminiResourceWithRawResponse

        return AsyncGeminiResourceWithRawResponse(self._client.gemini)

    @cached_property
    def cohere(self) -> cohere.AsyncCohereResourceWithRawResponse:
        from .resources.cohere import AsyncCohereResourceWithRawResponse

        return AsyncCohereResourceWithRawResponse(self._client.cohere)

    @cached_property
    def anthropic(self) -> anthropic.AsyncAnthropicResourceWithRawResponse:
        from .resources.anthropic import AsyncAnthropicResourceWithRawResponse

        return AsyncAnthropicResourceWithRawResponse(self._client.anthropic)

    @cached_property
    def bedrock(self) -> bedrock.AsyncBedrockResourceWithRawResponse:
        from .resources.bedrock import AsyncBedrockResourceWithRawResponse

        return AsyncBedrockResourceWithRawResponse(self._client.bedrock)

    @cached_property
    def eu_assemblyai(self) -> eu_assemblyai.AsyncEuAssemblyaiResourceWithRawResponse:
        from .resources.eu_assemblyai import AsyncEuAssemblyaiResourceWithRawResponse

        return AsyncEuAssemblyaiResourceWithRawResponse(self._client.eu_assemblyai)

    @cached_property
    def assemblyai(self) -> assemblyai.AsyncAssemblyaiResourceWithRawResponse:
        from .resources.assemblyai import AsyncAssemblyaiResourceWithRawResponse

        return AsyncAssemblyaiResourceWithRawResponse(self._client.assemblyai)

    @cached_property
    def azure(self) -> azure.AsyncAzureResourceWithRawResponse:
        from .resources.azure import AsyncAzureResourceWithRawResponse

        return AsyncAzureResourceWithRawResponse(self._client.azure)

    @cached_property
    def langfuse(self) -> langfuse.AsyncLangfuseResourceWithRawResponse:
        from .resources.langfuse import AsyncLangfuseResourceWithRawResponse

        return AsyncLangfuseResourceWithRawResponse(self._client.langfuse)

    @cached_property
    def config(self) -> config.AsyncConfigResourceWithRawResponse:
        from .resources.config import AsyncConfigResourceWithRawResponse

        return AsyncConfigResourceWithRawResponse(self._client.config)

    @cached_property
    def test(self) -> test.AsyncTestResourceWithRawResponse:
        from .resources.test import AsyncTestResourceWithRawResponse

        return AsyncTestResourceWithRawResponse(self._client.test)

    @cached_property
    def health(self) -> health.AsyncHealthResourceWithRawResponse:
        from .resources.health import AsyncHealthResourceWithRawResponse

        return AsyncHealthResourceWithRawResponse(self._client.health)

    @cached_property
    def active(self) -> active.AsyncActiveResourceWithRawResponse:
        from .resources.active import AsyncActiveResourceWithRawResponse

        return AsyncActiveResourceWithRawResponse(self._client.active)

    @cached_property
    def settings(self) -> settings.AsyncSettingsResourceWithRawResponse:
        from .resources.settings import AsyncSettingsResourceWithRawResponse

        return AsyncSettingsResourceWithRawResponse(self._client.settings)

    @cached_property
    def key(self) -> key.AsyncKeyResourceWithRawResponse:
        from .resources.key import AsyncKeyResourceWithRawResponse

        return AsyncKeyResourceWithRawResponse(self._client.key)

    @cached_property
    def user(self) -> user.AsyncUserResourceWithRawResponse:
        from .resources.user import AsyncUserResourceWithRawResponse

        return AsyncUserResourceWithRawResponse(self._client.user)

    @cached_property
    def team(self) -> team.AsyncTeamResourceWithRawResponse:
        from .resources.team import AsyncTeamResourceWithRawResponse

        return AsyncTeamResourceWithRawResponse(self._client.team)

    @cached_property
    def organization(self) -> organization.AsyncOrganizationResourceWithRawResponse:
        from .resources.organization import AsyncOrganizationResourceWithRawResponse

        return AsyncOrganizationResourceWithRawResponse(self._client.organization)

    @cached_property
    def customer(self) -> customer.AsyncCustomerResourceWithRawResponse:
        from .resources.customer import AsyncCustomerResourceWithRawResponse

        return AsyncCustomerResourceWithRawResponse(self._client.customer)

    @cached_property
    def spend(self) -> spend.AsyncSpendResourceWithRawResponse:
        from .resources.spend import AsyncSpendResourceWithRawResponse

        return AsyncSpendResourceWithRawResponse(self._client.spend)

    @cached_property
    def global_(self) -> global_.AsyncGlobalResourceWithRawResponse:
        from .resources.global_ import AsyncGlobalResourceWithRawResponse

        return AsyncGlobalResourceWithRawResponse(self._client.global_)

    @cached_property
    def provider(self) -> provider.AsyncProviderResourceWithRawResponse:
        from .resources.provider import AsyncProviderResourceWithRawResponse

        return AsyncProviderResourceWithRawResponse(self._client.provider)

    @cached_property
    def cache(self) -> cache.AsyncCacheResourceWithRawResponse:
        from .resources.cache import AsyncCacheResourceWithRawResponse

        return AsyncCacheResourceWithRawResponse(self._client.cache)

    @cached_property
    def guardrails(self) -> guardrails.AsyncGuardrailsResourceWithRawResponse:
        from .resources.guardrails import AsyncGuardrailsResourceWithRawResponse

        return AsyncGuardrailsResourceWithRawResponse(self._client.guardrails)

    @cached_property
    def add(self) -> add.AsyncAddResourceWithRawResponse:
        from .resources.add import AsyncAddResourceWithRawResponse

        return AsyncAddResourceWithRawResponse(self._client.add)

    @cached_property
    def delete(self) -> delete.AsyncDeleteResourceWithRawResponse:
        from .resources.delete import AsyncDeleteResourceWithRawResponse

        return AsyncDeleteResourceWithRawResponse(self._client.delete)

    @cached_property
    def files(self) -> files.AsyncFilesResourceWithRawResponse:
        from .resources.files import AsyncFilesResourceWithRawResponse

        return AsyncFilesResourceWithRawResponse(self._client.files)

    @cached_property
    def budget(self) -> budget.AsyncBudgetResourceWithRawResponse:
        from .resources.budget import AsyncBudgetResourceWithRawResponse

        return AsyncBudgetResourceWithRawResponse(self._client.budget)


class HanzoWithStreamedResponse:
    _client: Hanzo

    def __init__(self, client: Hanzo) -> None:
        self._client = client

        self.get_home = to_streamed_response_wrapper(
            client.get_home,
        )

    @cached_property
    def models(self) -> models.ModelsResourceWithStreamingResponse:
        from .resources.models import ModelsResourceWithStreamingResponse

        return ModelsResourceWithStreamingResponse(self._client.models)

    @cached_property
    def openai(self) -> openai.OpenAIResourceWithStreamingResponse:
        from .resources.openai import OpenAIResourceWithStreamingResponse

        return OpenAIResourceWithStreamingResponse(self._client.openai)

    @cached_property
    def engines(self) -> engines.EnginesResourceWithStreamingResponse:
        from .resources.engines import EnginesResourceWithStreamingResponse

        return EnginesResourceWithStreamingResponse(self._client.engines)

    @cached_property
    def chat(self) -> chat.ChatResourceWithStreamingResponse:
        from .resources.chat import ChatResourceWithStreamingResponse

        return ChatResourceWithStreamingResponse(self._client.chat)

    @cached_property
    def completions(self) -> completions.CompletionsResourceWithStreamingResponse:
        from .resources.completions import CompletionsResourceWithStreamingResponse

        return CompletionsResourceWithStreamingResponse(self._client.completions)

    @cached_property
    def embeddings(self) -> embeddings.EmbeddingsResourceWithStreamingResponse:
        from .resources.embeddings import EmbeddingsResourceWithStreamingResponse

        return EmbeddingsResourceWithStreamingResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.ImagesResourceWithStreamingResponse:
        from .resources.images import ImagesResourceWithStreamingResponse

        return ImagesResourceWithStreamingResponse(self._client.images)

    @cached_property
    def audio(self) -> audio.AudioResourceWithStreamingResponse:
        from .resources.audio import AudioResourceWithStreamingResponse

        return AudioResourceWithStreamingResponse(self._client.audio)

    @cached_property
    def assistants(self) -> assistants.AssistantsResourceWithStreamingResponse:
        from .resources.assistants import AssistantsResourceWithStreamingResponse

        return AssistantsResourceWithStreamingResponse(self._client.assistants)

    @cached_property
    def threads(self) -> threads.ThreadsResourceWithStreamingResponse:
        from .resources.threads import ThreadsResourceWithStreamingResponse

        return ThreadsResourceWithStreamingResponse(self._client.threads)

    @cached_property
    def moderations(self) -> moderations.ModerationsResourceWithStreamingResponse:
        from .resources.moderations import ModerationsResourceWithStreamingResponse

        return ModerationsResourceWithStreamingResponse(self._client.moderations)

    @cached_property
    def utils(self) -> utils.UtilsResourceWithStreamingResponse:
        from .resources.utils import UtilsResourceWithStreamingResponse

        return UtilsResourceWithStreamingResponse(self._client.utils)

    @cached_property
    def model(self) -> model.ModelResourceWithStreamingResponse:
        from .resources.model import ModelResourceWithStreamingResponse

        return ModelResourceWithStreamingResponse(self._client.model)

    @cached_property
    def model_group(self) -> model_group.ModelGroupResourceWithStreamingResponse:
        from .resources.model_group import ModelGroupResourceWithStreamingResponse

        return ModelGroupResourceWithStreamingResponse(self._client.model_group)

    @cached_property
    def routes(self) -> routes.RoutesResourceWithStreamingResponse:
        from .resources.routes import RoutesResourceWithStreamingResponse

        return RoutesResourceWithStreamingResponse(self._client.routes)

    @cached_property
    def responses(self) -> responses.ResponsesResourceWithStreamingResponse:
        from .resources.responses import ResponsesResourceWithStreamingResponse

        return ResponsesResourceWithStreamingResponse(self._client.responses)

    @cached_property
    def batches(self) -> batches.BatchesResourceWithStreamingResponse:
        from .resources.batches import BatchesResourceWithStreamingResponse

        return BatchesResourceWithStreamingResponse(self._client.batches)

    @cached_property
    def rerank(self) -> rerank.RerankResourceWithStreamingResponse:
        from .resources.rerank import RerankResourceWithStreamingResponse

        return RerankResourceWithStreamingResponse(self._client.rerank)

    @cached_property
    def fine_tuning(self) -> fine_tuning.FineTuningResourceWithStreamingResponse:
        from .resources.fine_tuning import FineTuningResourceWithStreamingResponse

        return FineTuningResourceWithStreamingResponse(self._client.fine_tuning)

    @cached_property
    def credentials(self) -> credentials.CredentialsResourceWithStreamingResponse:
        from .resources.credentials import CredentialsResourceWithStreamingResponse

        return CredentialsResourceWithStreamingResponse(self._client.credentials)

    @cached_property
    def vertex_ai(self) -> vertex_ai.VertexAIResourceWithStreamingResponse:
        from .resources.vertex_ai import VertexAIResourceWithStreamingResponse

        return VertexAIResourceWithStreamingResponse(self._client.vertex_ai)

    @cached_property
    def gemini(self) -> gemini.GeminiResourceWithStreamingResponse:
        from .resources.gemini import GeminiResourceWithStreamingResponse

        return GeminiResourceWithStreamingResponse(self._client.gemini)

    @cached_property
    def cohere(self) -> cohere.CohereResourceWithStreamingResponse:
        from .resources.cohere import CohereResourceWithStreamingResponse

        return CohereResourceWithStreamingResponse(self._client.cohere)

    @cached_property
    def anthropic(self) -> anthropic.AnthropicResourceWithStreamingResponse:
        from .resources.anthropic import AnthropicResourceWithStreamingResponse

        return AnthropicResourceWithStreamingResponse(self._client.anthropic)

    @cached_property
    def bedrock(self) -> bedrock.BedrockResourceWithStreamingResponse:
        from .resources.bedrock import BedrockResourceWithStreamingResponse

        return BedrockResourceWithStreamingResponse(self._client.bedrock)

    @cached_property
    def eu_assemblyai(self) -> eu_assemblyai.EuAssemblyaiResourceWithStreamingResponse:
        from .resources.eu_assemblyai import EuAssemblyaiResourceWithStreamingResponse

        return EuAssemblyaiResourceWithStreamingResponse(self._client.eu_assemblyai)

    @cached_property
    def assemblyai(self) -> assemblyai.AssemblyaiResourceWithStreamingResponse:
        from .resources.assemblyai import AssemblyaiResourceWithStreamingResponse

        return AssemblyaiResourceWithStreamingResponse(self._client.assemblyai)

    @cached_property
    def azure(self) -> azure.AzureResourceWithStreamingResponse:
        from .resources.azure import AzureResourceWithStreamingResponse

        return AzureResourceWithStreamingResponse(self._client.azure)

    @cached_property
    def langfuse(self) -> langfuse.LangfuseResourceWithStreamingResponse:
        from .resources.langfuse import LangfuseResourceWithStreamingResponse

        return LangfuseResourceWithStreamingResponse(self._client.langfuse)

    @cached_property
    def config(self) -> config.ConfigResourceWithStreamingResponse:
        from .resources.config import ConfigResourceWithStreamingResponse

        return ConfigResourceWithStreamingResponse(self._client.config)

    @cached_property
    def test(self) -> test.TestResourceWithStreamingResponse:
        from .resources.test import TestResourceWithStreamingResponse

        return TestResourceWithStreamingResponse(self._client.test)

    @cached_property
    def health(self) -> health.HealthResourceWithStreamingResponse:
        from .resources.health import HealthResourceWithStreamingResponse

        return HealthResourceWithStreamingResponse(self._client.health)

    @cached_property
    def active(self) -> active.ActiveResourceWithStreamingResponse:
        from .resources.active import ActiveResourceWithStreamingResponse

        return ActiveResourceWithStreamingResponse(self._client.active)

    @cached_property
    def settings(self) -> settings.SettingsResourceWithStreamingResponse:
        from .resources.settings import SettingsResourceWithStreamingResponse

        return SettingsResourceWithStreamingResponse(self._client.settings)

    @cached_property
    def key(self) -> key.KeyResourceWithStreamingResponse:
        from .resources.key import KeyResourceWithStreamingResponse

        return KeyResourceWithStreamingResponse(self._client.key)

    @cached_property
    def user(self) -> user.UserResourceWithStreamingResponse:
        from .resources.user import UserResourceWithStreamingResponse

        return UserResourceWithStreamingResponse(self._client.user)

    @cached_property
    def team(self) -> team.TeamResourceWithStreamingResponse:
        from .resources.team import TeamResourceWithStreamingResponse

        return TeamResourceWithStreamingResponse(self._client.team)

    @cached_property
    def organization(self) -> organization.OrganizationResourceWithStreamingResponse:
        from .resources.organization import OrganizationResourceWithStreamingResponse

        return OrganizationResourceWithStreamingResponse(self._client.organization)

    @cached_property
    def customer(self) -> customer.CustomerResourceWithStreamingResponse:
        from .resources.customer import CustomerResourceWithStreamingResponse

        return CustomerResourceWithStreamingResponse(self._client.customer)

    @cached_property
    def spend(self) -> spend.SpendResourceWithStreamingResponse:
        from .resources.spend import SpendResourceWithStreamingResponse

        return SpendResourceWithStreamingResponse(self._client.spend)

    @cached_property
    def global_(self) -> global_.GlobalResourceWithStreamingResponse:
        from .resources.global_ import GlobalResourceWithStreamingResponse

        return GlobalResourceWithStreamingResponse(self._client.global_)

    @cached_property
    def provider(self) -> provider.ProviderResourceWithStreamingResponse:
        from .resources.provider import ProviderResourceWithStreamingResponse

        return ProviderResourceWithStreamingResponse(self._client.provider)

    @cached_property
    def cache(self) -> cache.CacheResourceWithStreamingResponse:
        from .resources.cache import CacheResourceWithStreamingResponse

        return CacheResourceWithStreamingResponse(self._client.cache)

    @cached_property
    def guardrails(self) -> guardrails.GuardrailsResourceWithStreamingResponse:
        from .resources.guardrails import GuardrailsResourceWithStreamingResponse

        return GuardrailsResourceWithStreamingResponse(self._client.guardrails)

    @cached_property
    def add(self) -> add.AddResourceWithStreamingResponse:
        from .resources.add import AddResourceWithStreamingResponse

        return AddResourceWithStreamingResponse(self._client.add)

    @cached_property
    def delete(self) -> delete.DeleteResourceWithStreamingResponse:
        from .resources.delete import DeleteResourceWithStreamingResponse

        return DeleteResourceWithStreamingResponse(self._client.delete)

    @cached_property
    def files(self) -> files.FilesResourceWithStreamingResponse:
        from .resources.files import FilesResourceWithStreamingResponse

        return FilesResourceWithStreamingResponse(self._client.files)

    @cached_property
    def budget(self) -> budget.BudgetResourceWithStreamingResponse:
        from .resources.budget import BudgetResourceWithStreamingResponse

        return BudgetResourceWithStreamingResponse(self._client.budget)


class AsyncHanzoWithStreamedResponse:
    _client: AsyncHanzo

    def __init__(self, client: AsyncHanzo) -> None:
        self._client = client

        self.get_home = async_to_streamed_response_wrapper(
            client.get_home,
        )

    @cached_property
    def models(self) -> models.AsyncModelsResourceWithStreamingResponse:
        from .resources.models import AsyncModelsResourceWithStreamingResponse

        return AsyncModelsResourceWithStreamingResponse(self._client.models)

    @cached_property
    def openai(self) -> openai.AsyncOpenAIResourceWithStreamingResponse:
        from .resources.openai import AsyncOpenAIResourceWithStreamingResponse

        return AsyncOpenAIResourceWithStreamingResponse(self._client.openai)

    @cached_property
    def engines(self) -> engines.AsyncEnginesResourceWithStreamingResponse:
        from .resources.engines import AsyncEnginesResourceWithStreamingResponse

        return AsyncEnginesResourceWithStreamingResponse(self._client.engines)

    @cached_property
    def chat(self) -> chat.AsyncChatResourceWithStreamingResponse:
        from .resources.chat import AsyncChatResourceWithStreamingResponse

        return AsyncChatResourceWithStreamingResponse(self._client.chat)

    @cached_property
    def completions(self) -> completions.AsyncCompletionsResourceWithStreamingResponse:
        from .resources.completions import AsyncCompletionsResourceWithStreamingResponse

        return AsyncCompletionsResourceWithStreamingResponse(self._client.completions)

    @cached_property
    def embeddings(self) -> embeddings.AsyncEmbeddingsResourceWithStreamingResponse:
        from .resources.embeddings import AsyncEmbeddingsResourceWithStreamingResponse

        return AsyncEmbeddingsResourceWithStreamingResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.AsyncImagesResourceWithStreamingResponse:
        from .resources.images import AsyncImagesResourceWithStreamingResponse

        return AsyncImagesResourceWithStreamingResponse(self._client.images)

    @cached_property
    def audio(self) -> audio.AsyncAudioResourceWithStreamingResponse:
        from .resources.audio import AsyncAudioResourceWithStreamingResponse

        return AsyncAudioResourceWithStreamingResponse(self._client.audio)

    @cached_property
    def assistants(self) -> assistants.AsyncAssistantsResourceWithStreamingResponse:
        from .resources.assistants import AsyncAssistantsResourceWithStreamingResponse

        return AsyncAssistantsResourceWithStreamingResponse(self._client.assistants)

    @cached_property
    def threads(self) -> threads.AsyncThreadsResourceWithStreamingResponse:
        from .resources.threads import AsyncThreadsResourceWithStreamingResponse

        return AsyncThreadsResourceWithStreamingResponse(self._client.threads)

    @cached_property
    def moderations(self) -> moderations.AsyncModerationsResourceWithStreamingResponse:
        from .resources.moderations import AsyncModerationsResourceWithStreamingResponse

        return AsyncModerationsResourceWithStreamingResponse(self._client.moderations)

    @cached_property
    def utils(self) -> utils.AsyncUtilsResourceWithStreamingResponse:
        from .resources.utils import AsyncUtilsResourceWithStreamingResponse

        return AsyncUtilsResourceWithStreamingResponse(self._client.utils)

    @cached_property
    def model(self) -> model.AsyncModelResourceWithStreamingResponse:
        from .resources.model import AsyncModelResourceWithStreamingResponse

        return AsyncModelResourceWithStreamingResponse(self._client.model)

    @cached_property
    def model_group(self) -> model_group.AsyncModelGroupResourceWithStreamingResponse:
        from .resources.model_group import AsyncModelGroupResourceWithStreamingResponse

        return AsyncModelGroupResourceWithStreamingResponse(self._client.model_group)

    @cached_property
    def routes(self) -> routes.AsyncRoutesResourceWithStreamingResponse:
        from .resources.routes import AsyncRoutesResourceWithStreamingResponse

        return AsyncRoutesResourceWithStreamingResponse(self._client.routes)

    @cached_property
    def responses(self) -> responses.AsyncResponsesResourceWithStreamingResponse:
        from .resources.responses import AsyncResponsesResourceWithStreamingResponse

        return AsyncResponsesResourceWithStreamingResponse(self._client.responses)

    @cached_property
    def batches(self) -> batches.AsyncBatchesResourceWithStreamingResponse:
        from .resources.batches import AsyncBatchesResourceWithStreamingResponse

        return AsyncBatchesResourceWithStreamingResponse(self._client.batches)

    @cached_property
    def rerank(self) -> rerank.AsyncRerankResourceWithStreamingResponse:
        from .resources.rerank import AsyncRerankResourceWithStreamingResponse

        return AsyncRerankResourceWithStreamingResponse(self._client.rerank)

    @cached_property
    def fine_tuning(self) -> fine_tuning.AsyncFineTuningResourceWithStreamingResponse:
        from .resources.fine_tuning import AsyncFineTuningResourceWithStreamingResponse

        return AsyncFineTuningResourceWithStreamingResponse(self._client.fine_tuning)

    @cached_property
    def credentials(self) -> credentials.AsyncCredentialsResourceWithStreamingResponse:
        from .resources.credentials import AsyncCredentialsResourceWithStreamingResponse

        return AsyncCredentialsResourceWithStreamingResponse(self._client.credentials)

    @cached_property
    def vertex_ai(self) -> vertex_ai.AsyncVertexAIResourceWithStreamingResponse:
        from .resources.vertex_ai import AsyncVertexAIResourceWithStreamingResponse

        return AsyncVertexAIResourceWithStreamingResponse(self._client.vertex_ai)

    @cached_property
    def gemini(self) -> gemini.AsyncGeminiResourceWithStreamingResponse:
        from .resources.gemini import AsyncGeminiResourceWithStreamingResponse

        return AsyncGeminiResourceWithStreamingResponse(self._client.gemini)

    @cached_property
    def cohere(self) -> cohere.AsyncCohereResourceWithStreamingResponse:
        from .resources.cohere import AsyncCohereResourceWithStreamingResponse

        return AsyncCohereResourceWithStreamingResponse(self._client.cohere)

    @cached_property
    def anthropic(self) -> anthropic.AsyncAnthropicResourceWithStreamingResponse:
        from .resources.anthropic import AsyncAnthropicResourceWithStreamingResponse

        return AsyncAnthropicResourceWithStreamingResponse(self._client.anthropic)

    @cached_property
    def bedrock(self) -> bedrock.AsyncBedrockResourceWithStreamingResponse:
        from .resources.bedrock import AsyncBedrockResourceWithStreamingResponse

        return AsyncBedrockResourceWithStreamingResponse(self._client.bedrock)

    @cached_property
    def eu_assemblyai(self) -> eu_assemblyai.AsyncEuAssemblyaiResourceWithStreamingResponse:
        from .resources.eu_assemblyai import AsyncEuAssemblyaiResourceWithStreamingResponse

        return AsyncEuAssemblyaiResourceWithStreamingResponse(self._client.eu_assemblyai)

    @cached_property
    def assemblyai(self) -> assemblyai.AsyncAssemblyaiResourceWithStreamingResponse:
        from .resources.assemblyai import AsyncAssemblyaiResourceWithStreamingResponse

        return AsyncAssemblyaiResourceWithStreamingResponse(self._client.assemblyai)

    @cached_property
    def azure(self) -> azure.AsyncAzureResourceWithStreamingResponse:
        from .resources.azure import AsyncAzureResourceWithStreamingResponse

        return AsyncAzureResourceWithStreamingResponse(self._client.azure)

    @cached_property
    def langfuse(self) -> langfuse.AsyncLangfuseResourceWithStreamingResponse:
        from .resources.langfuse import AsyncLangfuseResourceWithStreamingResponse

        return AsyncLangfuseResourceWithStreamingResponse(self._client.langfuse)

    @cached_property
    def config(self) -> config.AsyncConfigResourceWithStreamingResponse:
        from .resources.config import AsyncConfigResourceWithStreamingResponse

        return AsyncConfigResourceWithStreamingResponse(self._client.config)

    @cached_property
    def test(self) -> test.AsyncTestResourceWithStreamingResponse:
        from .resources.test import AsyncTestResourceWithStreamingResponse

        return AsyncTestResourceWithStreamingResponse(self._client.test)

    @cached_property
    def health(self) -> health.AsyncHealthResourceWithStreamingResponse:
        from .resources.health import AsyncHealthResourceWithStreamingResponse

        return AsyncHealthResourceWithStreamingResponse(self._client.health)

    @cached_property
    def active(self) -> active.AsyncActiveResourceWithStreamingResponse:
        from .resources.active import AsyncActiveResourceWithStreamingResponse

        return AsyncActiveResourceWithStreamingResponse(self._client.active)

    @cached_property
    def settings(self) -> settings.AsyncSettingsResourceWithStreamingResponse:
        from .resources.settings import AsyncSettingsResourceWithStreamingResponse

        return AsyncSettingsResourceWithStreamingResponse(self._client.settings)

    @cached_property
    def key(self) -> key.AsyncKeyResourceWithStreamingResponse:
        from .resources.key import AsyncKeyResourceWithStreamingResponse

        return AsyncKeyResourceWithStreamingResponse(self._client.key)

    @cached_property
    def user(self) -> user.AsyncUserResourceWithStreamingResponse:
        from .resources.user import AsyncUserResourceWithStreamingResponse

        return AsyncUserResourceWithStreamingResponse(self._client.user)

    @cached_property
    def team(self) -> team.AsyncTeamResourceWithStreamingResponse:
        from .resources.team import AsyncTeamResourceWithStreamingResponse

        return AsyncTeamResourceWithStreamingResponse(self._client.team)

    @cached_property
    def organization(self) -> organization.AsyncOrganizationResourceWithStreamingResponse:
        from .resources.organization import AsyncOrganizationResourceWithStreamingResponse

        return AsyncOrganizationResourceWithStreamingResponse(self._client.organization)

    @cached_property
    def customer(self) -> customer.AsyncCustomerResourceWithStreamingResponse:
        from .resources.customer import AsyncCustomerResourceWithStreamingResponse

        return AsyncCustomerResourceWithStreamingResponse(self._client.customer)

    @cached_property
    def spend(self) -> spend.AsyncSpendResourceWithStreamingResponse:
        from .resources.spend import AsyncSpendResourceWithStreamingResponse

        return AsyncSpendResourceWithStreamingResponse(self._client.spend)

    @cached_property
    def global_(self) -> global_.AsyncGlobalResourceWithStreamingResponse:
        from .resources.global_ import AsyncGlobalResourceWithStreamingResponse

        return AsyncGlobalResourceWithStreamingResponse(self._client.global_)

    @cached_property
    def provider(self) -> provider.AsyncProviderResourceWithStreamingResponse:
        from .resources.provider import AsyncProviderResourceWithStreamingResponse

        return AsyncProviderResourceWithStreamingResponse(self._client.provider)

    @cached_property
    def cache(self) -> cache.AsyncCacheResourceWithStreamingResponse:
        from .resources.cache import AsyncCacheResourceWithStreamingResponse

        return AsyncCacheResourceWithStreamingResponse(self._client.cache)

    @cached_property
    def guardrails(self) -> guardrails.AsyncGuardrailsResourceWithStreamingResponse:
        from .resources.guardrails import AsyncGuardrailsResourceWithStreamingResponse

        return AsyncGuardrailsResourceWithStreamingResponse(self._client.guardrails)

    @cached_property
    def add(self) -> add.AsyncAddResourceWithStreamingResponse:
        from .resources.add import AsyncAddResourceWithStreamingResponse

        return AsyncAddResourceWithStreamingResponse(self._client.add)

    @cached_property
    def delete(self) -> delete.AsyncDeleteResourceWithStreamingResponse:
        from .resources.delete import AsyncDeleteResourceWithStreamingResponse

        return AsyncDeleteResourceWithStreamingResponse(self._client.delete)

    @cached_property
    def files(self) -> files.AsyncFilesResourceWithStreamingResponse:
        from .resources.files import AsyncFilesResourceWithStreamingResponse

        return AsyncFilesResourceWithStreamingResponse(self._client.files)

    @cached_property
    def budget(self) -> budget.AsyncBudgetResourceWithStreamingResponse:
        from .resources.budget import AsyncBudgetResourceWithStreamingResponse

        return AsyncBudgetResourceWithStreamingResponse(self._client.budget)


Client = Hanzo

AsyncClient = AsyncHanzo
