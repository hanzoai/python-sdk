# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict

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

__all__ = ["TasksResource", "AsyncTasksResource"]


class TasksResource(SyncAPIResource):
    """Task management and scheduling."""

    @cached_property
    def with_raw_response(self) -> TasksResourceWithRawResponse:
        return TasksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TasksResourceWithStreamingResponse:
        return TasksResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all tasks."""
        return self._get(
            "/operations/tasks",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "status": status,
                    "type": type,
                    "limit": limit,
                    "offset": offset,
                },
            ),
            cast_to=object,
        )

    def get(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific task."""
        return self._get(
            f"/operations/tasks/{task_id}",
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
        type: str,
        config: Dict[str, Any],
        schedule: str | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new task."""
        return self._post(
            "/operations/tasks",
            body={
                "name": name,
                "type": type,
                "config": config,
                "schedule": schedule,
                "priority": priority,
            },
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
        task_id: str,
        *,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        schedule: str | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a task."""
        return self._put(
            f"/operations/tasks/{task_id}",
            body={"config": config, "schedule": schedule, "priority": priority},
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
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a task."""
        return self._delete(
            f"/operations/tasks/{task_id}",
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
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Run a task immediately."""
        return self._post(
            f"/operations/tasks/{task_id}/run",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def cancel(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a running task."""
        return self._post(
            f"/operations/tasks/{task_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def logs(
        self,
        task_id: str,
        *,
        lines: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get task logs."""
        return self._get(
            f"/operations/tasks/{task_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"lines": lines},
            ),
            cast_to=object,
        )


class AsyncTasksResource(AsyncAPIResource):
    """Task management and scheduling (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncTasksResourceWithRawResponse:
        return AsyncTasksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTasksResourceWithStreamingResponse:
        return AsyncTasksResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/operations/tasks",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "status": status,
                    "type": type,
                    "limit": limit,
                    "offset": offset,
                },
            ),
            cast_to=object,
        )

    async def get(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/operations/tasks/{task_id}",
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
        type: str,
        config: Dict[str, Any],
        schedule: str | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/operations/tasks",
            body={
                "name": name,
                "type": type,
                "config": config,
                "schedule": schedule,
                "priority": priority,
            },
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
        task_id: str,
        *,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        schedule: str | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/operations/tasks/{task_id}",
            body={"config": config, "schedule": schedule, "priority": priority},
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
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/operations/tasks/{task_id}",
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
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/operations/tasks/{task_id}/run",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def cancel(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/operations/tasks/{task_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def logs(
        self,
        task_id: str,
        *,
        lines: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/operations/tasks/{task_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"lines": lines},
            ),
            cast_to=object,
        )


class TasksResourceWithRawResponse:
    def __init__(self, tasks: TasksResource) -> None:
        self._tasks = tasks
        self.list = to_raw_response_wrapper(tasks.list)
        self.get = to_raw_response_wrapper(tasks.get)
        self.create = to_raw_response_wrapper(tasks.create)
        self.update = to_raw_response_wrapper(tasks.update)
        self.delete = to_raw_response_wrapper(tasks.delete)
        self.run = to_raw_response_wrapper(tasks.run)
        self.cancel = to_raw_response_wrapper(tasks.cancel)
        self.logs = to_raw_response_wrapper(tasks.logs)


class AsyncTasksResourceWithRawResponse:
    def __init__(self, tasks: AsyncTasksResource) -> None:
        self._tasks = tasks
        self.list = async_to_raw_response_wrapper(tasks.list)
        self.get = async_to_raw_response_wrapper(tasks.get)
        self.create = async_to_raw_response_wrapper(tasks.create)
        self.update = async_to_raw_response_wrapper(tasks.update)
        self.delete = async_to_raw_response_wrapper(tasks.delete)
        self.run = async_to_raw_response_wrapper(tasks.run)
        self.cancel = async_to_raw_response_wrapper(tasks.cancel)
        self.logs = async_to_raw_response_wrapper(tasks.logs)


class TasksResourceWithStreamingResponse:
    def __init__(self, tasks: TasksResource) -> None:
        self._tasks = tasks
        self.list = to_streamed_response_wrapper(tasks.list)
        self.get = to_streamed_response_wrapper(tasks.get)
        self.create = to_streamed_response_wrapper(tasks.create)
        self.update = to_streamed_response_wrapper(tasks.update)
        self.delete = to_streamed_response_wrapper(tasks.delete)
        self.run = to_streamed_response_wrapper(tasks.run)
        self.cancel = to_streamed_response_wrapper(tasks.cancel)
        self.logs = to_streamed_response_wrapper(tasks.logs)


class AsyncTasksResourceWithStreamingResponse:
    def __init__(self, tasks: AsyncTasksResource) -> None:
        self._tasks = tasks
        self.list = async_to_streamed_response_wrapper(tasks.list)
        self.get = async_to_streamed_response_wrapper(tasks.get)
        self.create = async_to_streamed_response_wrapper(tasks.create)
        self.update = async_to_streamed_response_wrapper(tasks.update)
        self.delete = async_to_streamed_response_wrapper(tasks.delete)
        self.run = async_to_streamed_response_wrapper(tasks.run)
        self.cancel = async_to_streamed_response_wrapper(tasks.cancel)
        self.logs = async_to_streamed_response_wrapper(tasks.logs)
