# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["PubSubResource", "AsyncPubSubResource"]


class PubSubResource(SyncAPIResource):
    """Pub/Sub messaging service."""

    @cached_property
    def with_raw_response(self) -> PubSubResourceWithRawResponse:
        return PubSubResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PubSubResourceWithStreamingResponse:
        return PubSubResourceWithStreamingResponse(self)

    def list_topics(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all topics."""
        return self._get(
            "/pubsub/topics",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create_topic(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new topic."""
        return self._post(
            "/pubsub/topics",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete_topic(
        self,
        topic_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a topic."""
        return self._delete(
            f"/pubsub/topics/{topic_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def publish(
        self,
        topic_id: str,
        *,
        message: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Publish a message to a topic."""
        return self._post(
            f"/pubsub/topics/{topic_id}/publish",
            body={"message": message},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_subscriptions(
        self,
        topic_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List subscriptions for a topic."""
        return self._get(
            f"/pubsub/topics/{topic_id}/subscriptions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create_subscription(
        self,
        topic_id: str,
        *,
        name: str,
        endpoint: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a subscription."""
        return self._post(
            f"/pubsub/topics/{topic_id}/subscriptions",
            body={"name": name, "endpoint": endpoint},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete_subscription(
        self,
        topic_id: str,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a subscription."""
        return self._delete(
            f"/pubsub/topics/{topic_id}/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def pull(
        self,
        topic_id: str,
        subscription_id: str,
        *,
        max_messages: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Pull messages from a subscription."""
        return self._get(
            f"/pubsub/topics/{topic_id}/subscriptions/{subscription_id}/pull",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"max_messages": max_messages},
            ),
            cast_to=object,
        )

    def ack(
        self,
        topic_id: str,
        subscription_id: str,
        *,
        ack_ids: List[str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Acknowledge messages."""
        return self._post(
            f"/pubsub/topics/{topic_id}/subscriptions/{subscription_id}/ack",
            body={"ack_ids": ack_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncPubSubResource(AsyncAPIResource):
    """Pub/Sub messaging service (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncPubSubResourceWithRawResponse:
        return AsyncPubSubResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPubSubResourceWithStreamingResponse:
        return AsyncPubSubResourceWithStreamingResponse(self)

    async def list_topics(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/pubsub/topics",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create_topic(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/pubsub/topics",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete_topic(
        self,
        topic_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/pubsub/topics/{topic_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def publish(
        self,
        topic_id: str,
        *,
        message: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/pubsub/topics/{topic_id}/publish",
            body={"message": message},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_subscriptions(
        self,
        topic_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/pubsub/topics/{topic_id}/subscriptions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create_subscription(
        self,
        topic_id: str,
        *,
        name: str,
        endpoint: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/pubsub/topics/{topic_id}/subscriptions",
            body={"name": name, "endpoint": endpoint},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete_subscription(
        self,
        topic_id: str,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/pubsub/topics/{topic_id}/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def pull(
        self,
        topic_id: str,
        subscription_id: str,
        *,
        max_messages: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/pubsub/topics/{topic_id}/subscriptions/{subscription_id}/pull",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"max_messages": max_messages},
            ),
            cast_to=object,
        )

    async def ack(
        self,
        topic_id: str,
        subscription_id: str,
        *,
        ack_ids: List[str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/pubsub/topics/{topic_id}/subscriptions/{subscription_id}/ack",
            body={"ack_ids": ack_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class PubSubResourceWithRawResponse:
    def __init__(self, pubsub: PubSubResource) -> None:
        self._pubsub = pubsub
        self.list_topics = to_raw_response_wrapper(pubsub.list_topics)
        self.create_topic = to_raw_response_wrapper(pubsub.create_topic)
        self.delete_topic = to_raw_response_wrapper(pubsub.delete_topic)
        self.publish = to_raw_response_wrapper(pubsub.publish)
        self.list_subscriptions = to_raw_response_wrapper(pubsub.list_subscriptions)
        self.create_subscription = to_raw_response_wrapper(pubsub.create_subscription)
        self.delete_subscription = to_raw_response_wrapper(pubsub.delete_subscription)
        self.pull = to_raw_response_wrapper(pubsub.pull)
        self.ack = to_raw_response_wrapper(pubsub.ack)


class AsyncPubSubResourceWithRawResponse:
    def __init__(self, pubsub: AsyncPubSubResource) -> None:
        self._pubsub = pubsub
        self.list_topics = async_to_raw_response_wrapper(pubsub.list_topics)
        self.create_topic = async_to_raw_response_wrapper(pubsub.create_topic)
        self.delete_topic = async_to_raw_response_wrapper(pubsub.delete_topic)
        self.publish = async_to_raw_response_wrapper(pubsub.publish)
        self.list_subscriptions = async_to_raw_response_wrapper(pubsub.list_subscriptions)
        self.create_subscription = async_to_raw_response_wrapper(pubsub.create_subscription)
        self.delete_subscription = async_to_raw_response_wrapper(pubsub.delete_subscription)
        self.pull = async_to_raw_response_wrapper(pubsub.pull)
        self.ack = async_to_raw_response_wrapper(pubsub.ack)


class PubSubResourceWithStreamingResponse:
    def __init__(self, pubsub: PubSubResource) -> None:
        self._pubsub = pubsub
        self.list_topics = to_streamed_response_wrapper(pubsub.list_topics)
        self.create_topic = to_streamed_response_wrapper(pubsub.create_topic)
        self.delete_topic = to_streamed_response_wrapper(pubsub.delete_topic)
        self.publish = to_streamed_response_wrapper(pubsub.publish)
        self.list_subscriptions = to_streamed_response_wrapper(pubsub.list_subscriptions)
        self.create_subscription = to_streamed_response_wrapper(pubsub.create_subscription)
        self.delete_subscription = to_streamed_response_wrapper(pubsub.delete_subscription)
        self.pull = to_streamed_response_wrapper(pubsub.pull)
        self.ack = to_streamed_response_wrapper(pubsub.ack)


class AsyncPubSubResourceWithStreamingResponse:
    def __init__(self, pubsub: AsyncPubSubResource) -> None:
        self._pubsub = pubsub
        self.list_topics = async_to_streamed_response_wrapper(pubsub.list_topics)
        self.create_topic = async_to_streamed_response_wrapper(pubsub.create_topic)
        self.delete_topic = async_to_streamed_response_wrapper(pubsub.delete_topic)
        self.publish = async_to_streamed_response_wrapper(pubsub.publish)
        self.list_subscriptions = async_to_streamed_response_wrapper(pubsub.list_subscriptions)
        self.create_subscription = async_to_streamed_response_wrapper(pubsub.create_subscription)
        self.delete_subscription = async_to_streamed_response_wrapper(pubsub.delete_subscription)
        self.pull = async_to_streamed_response_wrapper(pubsub.pull)
        self.ack = async_to_streamed_response_wrapper(pubsub.ack)
