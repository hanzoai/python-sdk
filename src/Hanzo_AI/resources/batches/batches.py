# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .cancel import (
    CancelResource,
    AsyncCancelResource,
    CancelResourceWithRawResponse,
    AsyncCancelResourceWithRawResponse,
    CancelResourceWithStreamingResponse,
    AsyncCancelResourceWithStreamingResponse,
)
from ...types import (
    batch_list_params,
    batch_create_params,
    batch_retrieve_params,
    batch_list_with_provider_params,
)
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import (
    maybe_transform,
    async_maybe_transform,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options

__all__ = ["BatchesResource", "AsyncBatchesResource"]


class BatchesResource(SyncAPIResource):
    @cached_property
    def cancel(self) -> CancelResource:
        return CancelResource(self._client)

    @cached_property
    def with_raw_response(self) -> BatchesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return BatchesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BatchesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return BatchesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create large batches of API requests for asynchronous processing.

        This is the
        equivalent of POST https://api.openai.com/v1/batch Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch

        Example Curl

        ```
        curl http://localhost:4000/v1/batches         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -d '{
                "input_file_id": "file-abc123",
                "endpoint": "/v1/chat/completions",
                "completion_window": "24h"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"provider": provider}, batch_create_params.BatchCreateParams),
            ),
            cast_to=object,
        )

    def retrieve(
        self,
        batch_id: str,
        *,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieves a batch.

        This is the equivalent of GET
        https://api.openai.com/v1/batches/{batch_id} Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/retrieve

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          batch_id: The ID of the batch to retrieve

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return self._get(
            f"/v1/batches/{batch_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"provider": provider}, batch_retrieve_params.BatchRetrieveParams),
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        after: Optional[str] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Lists This is the equivalent of GET https://api.openai.com/v1/batches/ Supports
        Identical Params as: https://platform.openai.com/docs/api-reference/batch/list

        Example Curl

        ```
        curl http://localhost:4000/v1/batches?limit=2     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "provider": provider,
                    },
                    batch_list_params.BatchListParams,
                ),
            ),
            cast_to=object,
        )

    def cancel_with_provider(
        self,
        batch_id: str,
        *,
        provider: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a batch.

        This is the equivalent of POST
        https://api.openai.com/v1/batches/{batch_id}/cancel

        Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/cancel

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123/cancel         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -X POST

        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return self._post(
            f"/{provider}/v1/batches/{batch_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create_with_provider(
        self,
        provider: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create large batches of API requests for asynchronous processing.

        This is the
        equivalent of POST https://api.openai.com/v1/batch Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch

        Example Curl

        ```
        curl http://localhost:4000/v1/batches         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -d '{
                "input_file_id": "file-abc123",
                "endpoint": "/v1/chat/completions",
                "completion_window": "24h"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        return self._post(
            f"/{provider}/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_with_provider(
        self,
        provider: str,
        *,
        after: Optional[str] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Lists This is the equivalent of GET https://api.openai.com/v1/batches/ Supports
        Identical Params as: https://platform.openai.com/docs/api-reference/batch/list

        Example Curl

        ```
        curl http://localhost:4000/v1/batches?limit=2     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        return self._get(
            f"/{provider}/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                    },
                    batch_list_with_provider_params.BatchListWithProviderParams,
                ),
            ),
            cast_to=object,
        )

    def retrieve_with_provider(
        self,
        batch_id: str,
        *,
        provider: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieves a batch.

        This is the equivalent of GET
        https://api.openai.com/v1/batches/{batch_id} Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/retrieve

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          batch_id: The ID of the batch to retrieve

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return self._get(
            f"/{provider}/v1/batches/{batch_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncBatchesResource(AsyncAPIResource):
    @cached_property
    def cancel(self) -> AsyncCancelResource:
        return AsyncCancelResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncBatchesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncBatchesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBatchesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncBatchesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create large batches of API requests for asynchronous processing.

        This is the
        equivalent of POST https://api.openai.com/v1/batch Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch

        Example Curl

        ```
        curl http://localhost:4000/v1/batches         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -d '{
                "input_file_id": "file-abc123",
                "endpoint": "/v1/chat/completions",
                "completion_window": "24h"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"provider": provider}, batch_create_params.BatchCreateParams),
            ),
            cast_to=object,
        )

    async def retrieve(
        self,
        batch_id: str,
        *,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieves a batch.

        This is the equivalent of GET
        https://api.openai.com/v1/batches/{batch_id} Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/retrieve

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          batch_id: The ID of the batch to retrieve

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return await self._get(
            f"/v1/batches/{batch_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"provider": provider}, batch_retrieve_params.BatchRetrieveParams),
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        after: Optional[str] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Lists This is the equivalent of GET https://api.openai.com/v1/batches/ Supports
        Identical Params as: https://platform.openai.com/docs/api-reference/batch/list

        Example Curl

        ```
        curl http://localhost:4000/v1/batches?limit=2     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "provider": provider,
                    },
                    batch_list_params.BatchListParams,
                ),
            ),
            cast_to=object,
        )

    async def cancel_with_provider(
        self,
        batch_id: str,
        *,
        provider: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a batch.

        This is the equivalent of POST
        https://api.openai.com/v1/batches/{batch_id}/cancel

        Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/cancel

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123/cancel         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -X POST

        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return await self._post(
            f"/{provider}/v1/batches/{batch_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create_with_provider(
        self,
        provider: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create large batches of API requests for asynchronous processing.

        This is the
        equivalent of POST https://api.openai.com/v1/batch Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch

        Example Curl

        ```
        curl http://localhost:4000/v1/batches         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -d '{
                "input_file_id": "file-abc123",
                "endpoint": "/v1/chat/completions",
                "completion_window": "24h"
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        return await self._post(
            f"/{provider}/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_with_provider(
        self,
        provider: str,
        *,
        after: Optional[str] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Lists This is the equivalent of GET https://api.openai.com/v1/batches/ Supports
        Identical Params as: https://platform.openai.com/docs/api-reference/batch/list

        Example Curl

        ```
        curl http://localhost:4000/v1/batches?limit=2     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        return await self._get(
            f"/{provider}/v1/batches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                    },
                    batch_list_with_provider_params.BatchListWithProviderParams,
                ),
            ),
            cast_to=object,
        )

    async def retrieve_with_provider(
        self,
        batch_id: str,
        *,
        provider: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retrieves a batch.

        This is the equivalent of GET
        https://api.openai.com/v1/batches/{batch_id} Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/retrieve

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123     -H "Authorization: Bearer sk-1234"     -H "Content-Type: application/json"
        ```

        Args:
          batch_id: The ID of the batch to retrieve

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not provider:
            raise ValueError(f"Expected a non-empty value for `provider` but received {provider!r}")
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return await self._get(
            f"/{provider}/v1/batches/{batch_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class BatchesResourceWithRawResponse:
    def __init__(self, batches: BatchesResource) -> None:
        self._batches = batches

        self.create = to_raw_response_wrapper(
            batches.create,
        )
        self.retrieve = to_raw_response_wrapper(
            batches.retrieve,
        )
        self.list = to_raw_response_wrapper(
            batches.list,
        )
        self.cancel_with_provider = to_raw_response_wrapper(
            batches.cancel_with_provider,
        )
        self.create_with_provider = to_raw_response_wrapper(
            batches.create_with_provider,
        )
        self.list_with_provider = to_raw_response_wrapper(
            batches.list_with_provider,
        )
        self.retrieve_with_provider = to_raw_response_wrapper(
            batches.retrieve_with_provider,
        )

    @cached_property
    def cancel(self) -> CancelResourceWithRawResponse:
        return CancelResourceWithRawResponse(self._batches.cancel)


class AsyncBatchesResourceWithRawResponse:
    def __init__(self, batches: AsyncBatchesResource) -> None:
        self._batches = batches

        self.create = async_to_raw_response_wrapper(
            batches.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            batches.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            batches.list,
        )
        self.cancel_with_provider = async_to_raw_response_wrapper(
            batches.cancel_with_provider,
        )
        self.create_with_provider = async_to_raw_response_wrapper(
            batches.create_with_provider,
        )
        self.list_with_provider = async_to_raw_response_wrapper(
            batches.list_with_provider,
        )
        self.retrieve_with_provider = async_to_raw_response_wrapper(
            batches.retrieve_with_provider,
        )

    @cached_property
    def cancel(self) -> AsyncCancelResourceWithRawResponse:
        return AsyncCancelResourceWithRawResponse(self._batches.cancel)


class BatchesResourceWithStreamingResponse:
    def __init__(self, batches: BatchesResource) -> None:
        self._batches = batches

        self.create = to_streamed_response_wrapper(
            batches.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            batches.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            batches.list,
        )
        self.cancel_with_provider = to_streamed_response_wrapper(
            batches.cancel_with_provider,
        )
        self.create_with_provider = to_streamed_response_wrapper(
            batches.create_with_provider,
        )
        self.list_with_provider = to_streamed_response_wrapper(
            batches.list_with_provider,
        )
        self.retrieve_with_provider = to_streamed_response_wrapper(
            batches.retrieve_with_provider,
        )

    @cached_property
    def cancel(self) -> CancelResourceWithStreamingResponse:
        return CancelResourceWithStreamingResponse(self._batches.cancel)


class AsyncBatchesResourceWithStreamingResponse:
    def __init__(self, batches: AsyncBatchesResource) -> None:
        self._batches = batches

        self.create = async_to_streamed_response_wrapper(
            batches.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            batches.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            batches.list,
        )
        self.cancel_with_provider = async_to_streamed_response_wrapper(
            batches.cancel_with_provider,
        )
        self.create_with_provider = async_to_streamed_response_wrapper(
            batches.create_with_provider,
        )
        self.list_with_provider = async_to_streamed_response_wrapper(
            batches.list_with_provider,
        )
        self.retrieve_with_provider = async_to_streamed_response_wrapper(
            batches.retrieve_with_provider,
        )

    @cached_property
    def cancel(self) -> AsyncCancelResourceWithStreamingResponse:
        return AsyncCancelResourceWithStreamingResponse(self._batches.cancel)
