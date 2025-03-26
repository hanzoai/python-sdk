# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Optional
from typing_extensions import Literal

import httpx

from .cancel import (
    CancelResource,
    AsyncCancelResource,
    CancelResourceWithRawResponse,
    AsyncCancelResourceWithRawResponse,
    CancelResourceWithStreamingResponse,
    AsyncCancelResourceWithStreamingResponse,
)
from ...._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ...._utils import (
    maybe_transform,
    async_maybe_transform,
)
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.fine_tuning import job_list_params, job_create_params, job_retrieve_params

__all__ = ["JobsResource", "AsyncJobsResource"]


class JobsResource(SyncAPIResource):
    @cached_property
    def cancel(self) -> CancelResource:
        return CancelResource(self._client)

    @cached_property
    def with_raw_response(self) -> JobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return JobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> JobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return JobsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        custom_llm_provider: Literal["openai", "azure", "vertex_ai"],
        model: str,
        training_file: str,
        hyperparameters: Optional[job_create_params.Hyperparameters] | NotGiven = NOT_GIVEN,
        integrations: Optional[List[str]] | NotGiven = NOT_GIVEN,
        seed: Optional[int] | NotGiven = NOT_GIVEN,
        suffix: Optional[str] | NotGiven = NOT_GIVEN,
        validation_file: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Creates a fine-tuning job which begins the process of creating a new model from
        a given dataset. This is the equivalent of POST
        https://api.openai.com/v1/fine_tuning/jobs

        Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/fine-tuning/create

        Example Curl:

        ```
        curl http://localhost:4000/v1/fine_tuning/jobs       -H "Content-Type: application/json"       -H "Authorization: Bearer sk-1234"       -d '{
            "model": "gpt-3.5-turbo",
            "training_file": "file-abc123",
            "hyperparameters": {
              "n_epochs": 4
            }
          }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/fine_tuning/jobs",
            body=maybe_transform(
                {
                    "custom_llm_provider": custom_llm_provider,
                    "model": model,
                    "training_file": training_file,
                    "hyperparameters": hyperparameters,
                    "integrations": integrations,
                    "seed": seed,
                    "suffix": suffix,
                    "validation_file": validation_file,
                },
                job_create_params.JobCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def retrieve(
        self,
        fine_tuning_job_id: str,
        *,
        custom_llm_provider: Literal["openai", "azure"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieves a fine-tuning job.

        This is the equivalent of GET
        https://api.openai.com/v1/fine_tuning/jobs/{fine_tuning_job_id}

        Supported Query Params:

        - `custom_llm_provider`: Name of the LLM provider
        - `fine_tuning_job_id`: The ID of the fine-tuning job to retrieve.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not fine_tuning_job_id:
            raise ValueError(f"Expected a non-empty value for `fine_tuning_job_id` but received {fine_tuning_job_id!r}")
        return self._get(
            f"/v1/fine_tuning/jobs/{fine_tuning_job_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"custom_llm_provider": custom_llm_provider}, job_retrieve_params.JobRetrieveParams
                ),
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        custom_llm_provider: Literal["openai", "azure"],
        after: Optional[str] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Lists fine-tuning jobs for the organization.

        This is the equivalent of GET
        https://api.openai.com/v1/fine_tuning/jobs

        Supported Query Params:

        - `custom_llm_provider`: Name of the LLM provider
        - `after`: Identifier for the last job from the previous pagination request.
        - `limit`: Number of fine-tuning jobs to retrieve (default is 20).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/v1/fine_tuning/jobs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "custom_llm_provider": custom_llm_provider,
                        "after": after,
                        "limit": limit,
                    },
                    job_list_params.JobListParams,
                ),
            ),
            cast_to=object,
        )


class AsyncJobsResource(AsyncAPIResource):
    @cached_property
    def cancel(self) -> AsyncCancelResource:
        return AsyncCancelResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncJobsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        custom_llm_provider: Literal["openai", "azure", "vertex_ai"],
        model: str,
        training_file: str,
        hyperparameters: Optional[job_create_params.Hyperparameters] | NotGiven = NOT_GIVEN,
        integrations: Optional[List[str]] | NotGiven = NOT_GIVEN,
        seed: Optional[int] | NotGiven = NOT_GIVEN,
        suffix: Optional[str] | NotGiven = NOT_GIVEN,
        validation_file: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Creates a fine-tuning job which begins the process of creating a new model from
        a given dataset. This is the equivalent of POST
        https://api.openai.com/v1/fine_tuning/jobs

        Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/fine-tuning/create

        Example Curl:

        ```
        curl http://localhost:4000/v1/fine_tuning/jobs       -H "Content-Type: application/json"       -H "Authorization: Bearer sk-1234"       -d '{
            "model": "gpt-3.5-turbo",
            "training_file": "file-abc123",
            "hyperparameters": {
              "n_epochs": 4
            }
          }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/fine_tuning/jobs",
            body=await async_maybe_transform(
                {
                    "custom_llm_provider": custom_llm_provider,
                    "model": model,
                    "training_file": training_file,
                    "hyperparameters": hyperparameters,
                    "integrations": integrations,
                    "seed": seed,
                    "suffix": suffix,
                    "validation_file": validation_file,
                },
                job_create_params.JobCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def retrieve(
        self,
        fine_tuning_job_id: str,
        *,
        custom_llm_provider: Literal["openai", "azure"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieves a fine-tuning job.

        This is the equivalent of GET
        https://api.openai.com/v1/fine_tuning/jobs/{fine_tuning_job_id}

        Supported Query Params:

        - `custom_llm_provider`: Name of the LLM provider
        - `fine_tuning_job_id`: The ID of the fine-tuning job to retrieve.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not fine_tuning_job_id:
            raise ValueError(f"Expected a non-empty value for `fine_tuning_job_id` but received {fine_tuning_job_id!r}")
        return await self._get(
            f"/v1/fine_tuning/jobs/{fine_tuning_job_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"custom_llm_provider": custom_llm_provider}, job_retrieve_params.JobRetrieveParams
                ),
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        custom_llm_provider: Literal["openai", "azure"],
        after: Optional[str] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Lists fine-tuning jobs for the organization.

        This is the equivalent of GET
        https://api.openai.com/v1/fine_tuning/jobs

        Supported Query Params:

        - `custom_llm_provider`: Name of the LLM provider
        - `after`: Identifier for the last job from the previous pagination request.
        - `limit`: Number of fine-tuning jobs to retrieve (default is 20).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/v1/fine_tuning/jobs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "custom_llm_provider": custom_llm_provider,
                        "after": after,
                        "limit": limit,
                    },
                    job_list_params.JobListParams,
                ),
            ),
            cast_to=object,
        )


class JobsResourceWithRawResponse:
    def __init__(self, jobs: JobsResource) -> None:
        self._jobs = jobs

        self.create = to_raw_response_wrapper(
            jobs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            jobs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            jobs.list,
        )

    @cached_property
    def cancel(self) -> CancelResourceWithRawResponse:
        return CancelResourceWithRawResponse(self._jobs.cancel)


class AsyncJobsResourceWithRawResponse:
    def __init__(self, jobs: AsyncJobsResource) -> None:
        self._jobs = jobs

        self.create = async_to_raw_response_wrapper(
            jobs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            jobs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            jobs.list,
        )

    @cached_property
    def cancel(self) -> AsyncCancelResourceWithRawResponse:
        return AsyncCancelResourceWithRawResponse(self._jobs.cancel)


class JobsResourceWithStreamingResponse:
    def __init__(self, jobs: JobsResource) -> None:
        self._jobs = jobs

        self.create = to_streamed_response_wrapper(
            jobs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            jobs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            jobs.list,
        )

    @cached_property
    def cancel(self) -> CancelResourceWithStreamingResponse:
        return CancelResourceWithStreamingResponse(self._jobs.cancel)


class AsyncJobsResourceWithStreamingResponse:
    def __init__(self, jobs: AsyncJobsResource) -> None:
        self._jobs = jobs

        self.create = async_to_streamed_response_wrapper(
            jobs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            jobs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            jobs.list,
        )

    @cached_property
    def cancel(self) -> AsyncCancelResourceWithStreamingResponse:
        return AsyncCancelResourceWithStreamingResponse(self._jobs.cancel)
