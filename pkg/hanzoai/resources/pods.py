# Hanzo AI SDK

from __future__ import annotations
from typing import Dict, Any, List
import httpx
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_raw_response_wrapper, to_streamed_response_wrapper, async_to_raw_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options

__all__ = ["PodsResource", "AsyncPodsResource"]


class PodsResource(SyncAPIResource):
    """Kubernetes pod management."""

    @cached_property
    def with_raw_response(self) -> PodsResourceWithRawResponse:
        return PodsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PodsResourceWithStreamingResponse:
        return PodsResourceWithStreamingResponse(self)

    def list(self, *, namespace: str | NotGiven = NOT_GIVEN, label_selector: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List all pods."""
        return self._get("/infrastructure/pods", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"namespace": namespace, "label_selector": label_selector}), cast_to=object)

    def get(self, pod_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get a specific pod."""
        return self._get(f"/infrastructure/pods/{pod_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def create(self, *, name: str, namespace: str, image: str, command: List[str] | NotGiven = NOT_GIVEN, env: Dict[str, str] | NotGiven = NOT_GIVEN, resources: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Create a new pod."""
        return self._post("/infrastructure/pods", body={"name": name, "namespace": namespace, "image": image, "command": command, "env": env, "resources": resources}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def delete(self, pod_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Delete a pod."""
        return self._delete(f"/infrastructure/pods/{pod_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def logs(self, pod_id: str, *, container: str | NotGiven = NOT_GIVEN, tail: int | NotGiven = NOT_GIVEN, follow: bool | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get pod logs."""
        return self._get(f"/infrastructure/pods/{pod_id}/logs", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"container": container, "tail": tail, "follow": follow}), cast_to=object)

    def exec(self, pod_id: str, *, command: List[str], container: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Execute a command in a pod."""
        return self._post(f"/infrastructure/pods/{pod_id}/exec", body={"command": command, "container": container}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AsyncPodsResource(AsyncAPIResource):
    """Kubernetes pod management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncPodsResourceWithRawResponse:
        return AsyncPodsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPodsResourceWithStreamingResponse:
        return AsyncPodsResourceWithStreamingResponse(self)

    async def list(self, *, namespace: str | NotGiven = NOT_GIVEN, label_selector: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get("/infrastructure/pods", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"namespace": namespace, "label_selector": label_selector}), cast_to=object)

    async def get(self, pod_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/infrastructure/pods/{pod_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def create(self, *, name: str, namespace: str, image: str, command: List[str] | NotGiven = NOT_GIVEN, env: Dict[str, str] | NotGiven = NOT_GIVEN, resources: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post("/infrastructure/pods", body={"name": name, "namespace": namespace, "image": image, "command": command, "env": env, "resources": resources}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def delete(self, pod_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._delete(f"/infrastructure/pods/{pod_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def logs(self, pod_id: str, *, container: str | NotGiven = NOT_GIVEN, tail: int | NotGiven = NOT_GIVEN, follow: bool | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/infrastructure/pods/{pod_id}/logs", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"container": container, "tail": tail, "follow": follow}), cast_to=object)

    async def exec(self, pod_id: str, *, command: List[str], container: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/infrastructure/pods/{pod_id}/exec", body={"command": command, "container": container}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class PodsResourceWithRawResponse:
    def __init__(self, pods: PodsResource) -> None:
        self._pods = pods
        self.list = to_raw_response_wrapper(pods.list)
        self.get = to_raw_response_wrapper(pods.get)
        self.create = to_raw_response_wrapper(pods.create)
        self.delete = to_raw_response_wrapper(pods.delete)
        self.logs = to_raw_response_wrapper(pods.logs)
        self.exec = to_raw_response_wrapper(pods.exec)


class AsyncPodsResourceWithRawResponse:
    def __init__(self, pods: AsyncPodsResource) -> None:
        self._pods = pods
        self.list = async_to_raw_response_wrapper(pods.list)
        self.get = async_to_raw_response_wrapper(pods.get)
        self.create = async_to_raw_response_wrapper(pods.create)
        self.delete = async_to_raw_response_wrapper(pods.delete)
        self.logs = async_to_raw_response_wrapper(pods.logs)
        self.exec = async_to_raw_response_wrapper(pods.exec)


class PodsResourceWithStreamingResponse:
    def __init__(self, pods: PodsResource) -> None:
        self._pods = pods
        self.list = to_streamed_response_wrapper(pods.list)
        self.get = to_streamed_response_wrapper(pods.get)
        self.create = to_streamed_response_wrapper(pods.create)
        self.delete = to_streamed_response_wrapper(pods.delete)
        self.logs = to_streamed_response_wrapper(pods.logs)
        self.exec = to_streamed_response_wrapper(pods.exec)


class AsyncPodsResourceWithStreamingResponse:
    def __init__(self, pods: AsyncPodsResource) -> None:
        self._pods = pods
        self.list = async_to_streamed_response_wrapper(pods.list)
        self.get = async_to_streamed_response_wrapper(pods.get)
        self.create = async_to_streamed_response_wrapper(pods.create)
        self.delete = async_to_streamed_response_wrapper(pods.delete)
        self.logs = async_to_streamed_response_wrapper(pods.logs)
        self.exec = async_to_streamed_response_wrapper(pods.exec)
