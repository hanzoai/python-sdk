# Hanzo AI SDK

from __future__ import annotations
from typing import Dict, Any
import httpx
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_raw_response_wrapper, to_streamed_response_wrapper, async_to_raw_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options

__all__ = ["QueuesResource", "AsyncQueuesResource"]


class QueuesResource(SyncAPIResource):
    """Job queue service."""

    @cached_property
    def with_raw_response(self) -> QueuesResourceWithRawResponse:
        return QueuesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> QueuesResourceWithStreamingResponse:
        return QueuesResourceWithStreamingResponse(self)

    def list(self, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List all queues."""
        return self._get("/queues", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def create(self, *, name: str, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Create a new queue."""
        return self._post("/queues", body={"name": name}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def delete(self, queue_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Delete a queue."""
        return self._delete(f"/queues/{queue_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def send(self, queue_id: str, *, message: Dict[str, Any], delay: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Send a message to a queue."""
        return self._post(f"/queues/{queue_id}/messages", body={"message": message, "delay": delay}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def receive(self, queue_id: str, *, batch_size: int | NotGiven = NOT_GIVEN, visibility_timeout: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Receive messages from a queue."""
        return self._get(f"/queues/{queue_id}/messages", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"batch_size": batch_size, "visibility_timeout": visibility_timeout}), cast_to=object)

    def ack(self, queue_id: str, message_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Acknowledge a message."""
        return self._post(f"/queues/{queue_id}/messages/{message_id}/ack", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def stats(self, queue_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get queue statistics."""
        return self._get(f"/queues/{queue_id}/stats", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AsyncQueuesResource(AsyncAPIResource):
    """Job queue service (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncQueuesResourceWithRawResponse:
        return AsyncQueuesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncQueuesResourceWithStreamingResponse:
        return AsyncQueuesResourceWithStreamingResponse(self)

    async def list(self, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get("/queues", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def create(self, *, name: str, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post("/queues", body={"name": name}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def delete(self, queue_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._delete(f"/queues/{queue_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def send(self, queue_id: str, *, message: Dict[str, Any], delay: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/queues/{queue_id}/messages", body={"message": message, "delay": delay}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def receive(self, queue_id: str, *, batch_size: int | NotGiven = NOT_GIVEN, visibility_timeout: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/queues/{queue_id}/messages", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"batch_size": batch_size, "visibility_timeout": visibility_timeout}), cast_to=object)

    async def ack(self, queue_id: str, message_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/queues/{queue_id}/messages/{message_id}/ack", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def stats(self, queue_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/queues/{queue_id}/stats", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class QueuesResourceWithRawResponse:
    def __init__(self, queues: QueuesResource) -> None:
        self._queues = queues
        self.list = to_raw_response_wrapper(queues.list)
        self.create = to_raw_response_wrapper(queues.create)
        self.delete = to_raw_response_wrapper(queues.delete)
        self.send = to_raw_response_wrapper(queues.send)
        self.receive = to_raw_response_wrapper(queues.receive)
        self.ack = to_raw_response_wrapper(queues.ack)
        self.stats = to_raw_response_wrapper(queues.stats)


class AsyncQueuesResourceWithRawResponse:
    def __init__(self, queues: AsyncQueuesResource) -> None:
        self._queues = queues
        self.list = async_to_raw_response_wrapper(queues.list)
        self.create = async_to_raw_response_wrapper(queues.create)
        self.delete = async_to_raw_response_wrapper(queues.delete)
        self.send = async_to_raw_response_wrapper(queues.send)
        self.receive = async_to_raw_response_wrapper(queues.receive)
        self.ack = async_to_raw_response_wrapper(queues.ack)
        self.stats = async_to_raw_response_wrapper(queues.stats)


class QueuesResourceWithStreamingResponse:
    def __init__(self, queues: QueuesResource) -> None:
        self._queues = queues
        self.list = to_streamed_response_wrapper(queues.list)
        self.create = to_streamed_response_wrapper(queues.create)
        self.delete = to_streamed_response_wrapper(queues.delete)
        self.send = to_streamed_response_wrapper(queues.send)
        self.receive = to_streamed_response_wrapper(queues.receive)
        self.ack = to_streamed_response_wrapper(queues.ack)
        self.stats = to_streamed_response_wrapper(queues.stats)


class AsyncQueuesResourceWithStreamingResponse:
    def __init__(self, queues: AsyncQueuesResource) -> None:
        self._queues = queues
        self.list = async_to_streamed_response_wrapper(queues.list)
        self.create = async_to_streamed_response_wrapper(queues.create)
        self.delete = async_to_streamed_response_wrapper(queues.delete)
        self.send = async_to_streamed_response_wrapper(queues.send)
        self.receive = async_to_streamed_response_wrapper(queues.receive)
        self.ack = async_to_streamed_response_wrapper(queues.ack)
        self.stats = async_to_streamed_response_wrapper(queues.stats)
