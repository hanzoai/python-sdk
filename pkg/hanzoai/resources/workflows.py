# Hanzo AI SDK

from __future__ import annotations

from typing import Optional, Dict, Any, List

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

__all__ = ["WorkflowsResource", "AsyncWorkflowsResource"]


class WorkflowsResource(SyncAPIResource):
    """AI Workflow pipeline management."""

    @cached_property
    def with_raw_response(self) -> WorkflowsResourceWithRawResponse:
        return WorkflowsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WorkflowsResourceWithStreamingResponse:
        return WorkflowsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all workflows."""
        return self._get(
            "/workflows",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        workflow_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific workflow."""
        return self._get(
            f"/workflows/{workflow_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: str,
        steps: List[Dict[str, Any]],
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new workflow."""
        return self._post(
            "/workflows",
            body={"name": name, "steps": steps, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update(
        self,
        workflow_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        steps: List[Dict[str, Any]] | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a workflow."""
        return self._put(
            f"/workflows/{workflow_id}",
            body={"name": name, "steps": steps, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete(
        self,
        workflow_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a workflow."""
        return self._delete(
            f"/workflows/{workflow_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def run(
        self,
        workflow_id: str,
        *,
        inputs: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Run a workflow."""
        return self._post(
            f"/workflows/{workflow_id}/run",
            body={"inputs": inputs},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncWorkflowsResource(AsyncAPIResource):
    """AI Workflow pipeline management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncWorkflowsResourceWithRawResponse:
        return AsyncWorkflowsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWorkflowsResourceWithStreamingResponse:
        return AsyncWorkflowsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all workflows."""
        return await self._get(
            "/workflows",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        workflow_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific workflow."""
        return await self._get(
            f"/workflows/{workflow_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: str,
        steps: List[Dict[str, Any]],
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new workflow."""
        return await self._post(
            "/workflows",
            body={"name": name, "steps": steps, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update(
        self,
        workflow_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        steps: List[Dict[str, Any]] | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a workflow."""
        return await self._put(
            f"/workflows/{workflow_id}",
            body={"name": name, "steps": steps, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete(
        self,
        workflow_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a workflow."""
        return await self._delete(
            f"/workflows/{workflow_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def run(
        self,
        workflow_id: str,
        *,
        inputs: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Run a workflow."""
        return await self._post(
            f"/workflows/{workflow_id}/run",
            body={"inputs": inputs},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class WorkflowsResourceWithRawResponse:
    def __init__(self, workflows: WorkflowsResource) -> None:
        self._workflows = workflows
        self.list = to_raw_response_wrapper(workflows.list)
        self.get = to_raw_response_wrapper(workflows.get)
        self.create = to_raw_response_wrapper(workflows.create)
        self.update = to_raw_response_wrapper(workflows.update)
        self.delete = to_raw_response_wrapper(workflows.delete)
        self.run = to_raw_response_wrapper(workflows.run)


class AsyncWorkflowsResourceWithRawResponse:
    def __init__(self, workflows: AsyncWorkflowsResource) -> None:
        self._workflows = workflows
        self.list = async_to_raw_response_wrapper(workflows.list)
        self.get = async_to_raw_response_wrapper(workflows.get)
        self.create = async_to_raw_response_wrapper(workflows.create)
        self.update = async_to_raw_response_wrapper(workflows.update)
        self.delete = async_to_raw_response_wrapper(workflows.delete)
        self.run = async_to_raw_response_wrapper(workflows.run)


class WorkflowsResourceWithStreamingResponse:
    def __init__(self, workflows: WorkflowsResource) -> None:
        self._workflows = workflows
        self.list = to_streamed_response_wrapper(workflows.list)
        self.get = to_streamed_response_wrapper(workflows.get)
        self.create = to_streamed_response_wrapper(workflows.create)
        self.update = to_streamed_response_wrapper(workflows.update)
        self.delete = to_streamed_response_wrapper(workflows.delete)
        self.run = to_streamed_response_wrapper(workflows.run)


class AsyncWorkflowsResourceWithStreamingResponse:
    def __init__(self, workflows: AsyncWorkflowsResource) -> None:
        self._workflows = workflows
        self.list = async_to_streamed_response_wrapper(workflows.list)
        self.get = async_to_streamed_response_wrapper(workflows.get)
        self.create = async_to_streamed_response_wrapper(workflows.create)
        self.update = async_to_streamed_response_wrapper(workflows.update)
        self.delete = async_to_streamed_response_wrapper(workflows.delete)
        self.run = async_to_streamed_response_wrapper(workflows.run)
