# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, Optional

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

__all__ = ["JobsResource", "AsyncJobsResource"]


class JobsResource(SyncAPIResource):
    """Background job management."""

    @cached_property
    def with_raw_response(self) -> JobsResourceWithRawResponse:
        return JobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> JobsResourceWithStreamingResponse:
        return JobsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all jobs."""
        return self._get(
            "/jobs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "limit": limit},
            ),
            cast_to=object,
        )

    def get(
        self,
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific job."""
        return self._get(
            f"/jobs/{job_id}",
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
        handler: str,
        payload: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new background job."""
        return self._post(
            "/jobs",
            body={"name": name, "handler": handler, "payload": payload},
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
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a running job."""
        return self._post(
            f"/jobs/{job_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retry(
        self,
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retry a failed job."""
        return self._post(
            f"/jobs/{job_id}/retry",
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
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get job logs."""
        return self._get(
            f"/jobs/{job_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def stats(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get job statistics."""
        return self._get(
            "/jobs/stats",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_schedules(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List job schedules."""
        return self._get(
            "/jobs/schedules",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_schedule(
        self,
        *,
        cron: str,
        job_config: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a job schedule."""
        return self._post(
            "/jobs/schedules",
            body={"cron": cron, "job_config": job_config},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_schedule(
        self,
        schedule_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a job schedule."""
        return self._delete(
            f"/jobs/schedules/{schedule_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncJobsResource(AsyncAPIResource):
    """Background job management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncJobsResourceWithRawResponse:
        return AsyncJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncJobsResourceWithStreamingResponse:
        return AsyncJobsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all jobs."""
        return await self._get(
            "/jobs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "limit": limit},
            ),
            cast_to=object,
        )

    async def get(
        self,
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific job."""
        return await self._get(
            f"/jobs/{job_id}",
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
        handler: str,
        payload: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new background job."""
        return await self._post(
            "/jobs",
            body={"name": name, "handler": handler, "payload": payload},
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
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a running job."""
        return await self._post(
            f"/jobs/{job_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retry(
        self,
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Retry a failed job."""
        return await self._post(
            f"/jobs/{job_id}/retry",
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
        job_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get job logs."""
        return await self._get(
            f"/jobs/{job_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def stats(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get job statistics."""
        return await self._get(
            "/jobs/stats",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_schedules(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List job schedules."""
        return await self._get(
            "/jobs/schedules",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_schedule(
        self,
        *,
        cron: str,
        job_config: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a job schedule."""
        return await self._post(
            "/jobs/schedules",
            body={"cron": cron, "job_config": job_config},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_schedule(
        self,
        schedule_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a job schedule."""
        return await self._delete(
            f"/jobs/schedules/{schedule_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class JobsResourceWithRawResponse:
    def __init__(self, jobs: JobsResource) -> None:
        self._jobs = jobs
        self.list = to_raw_response_wrapper(jobs.list)
        self.get = to_raw_response_wrapper(jobs.get)
        self.create = to_raw_response_wrapper(jobs.create)
        self.cancel = to_raw_response_wrapper(jobs.cancel)
        self.retry = to_raw_response_wrapper(jobs.retry)
        self.logs = to_raw_response_wrapper(jobs.logs)
        self.stats = to_raw_response_wrapper(jobs.stats)
        self.list_schedules = to_raw_response_wrapper(jobs.list_schedules)
        self.create_schedule = to_raw_response_wrapper(jobs.create_schedule)
        self.delete_schedule = to_raw_response_wrapper(jobs.delete_schedule)


class AsyncJobsResourceWithRawResponse:
    def __init__(self, jobs: AsyncJobsResource) -> None:
        self._jobs = jobs
        self.list = async_to_raw_response_wrapper(jobs.list)
        self.get = async_to_raw_response_wrapper(jobs.get)
        self.create = async_to_raw_response_wrapper(jobs.create)
        self.cancel = async_to_raw_response_wrapper(jobs.cancel)
        self.retry = async_to_raw_response_wrapper(jobs.retry)
        self.logs = async_to_raw_response_wrapper(jobs.logs)
        self.stats = async_to_raw_response_wrapper(jobs.stats)
        self.list_schedules = async_to_raw_response_wrapper(jobs.list_schedules)
        self.create_schedule = async_to_raw_response_wrapper(jobs.create_schedule)
        self.delete_schedule = async_to_raw_response_wrapper(jobs.delete_schedule)


class JobsResourceWithStreamingResponse:
    def __init__(self, jobs: JobsResource) -> None:
        self._jobs = jobs
        self.list = to_streamed_response_wrapper(jobs.list)
        self.get = to_streamed_response_wrapper(jobs.get)
        self.create = to_streamed_response_wrapper(jobs.create)
        self.cancel = to_streamed_response_wrapper(jobs.cancel)
        self.retry = to_streamed_response_wrapper(jobs.retry)
        self.logs = to_streamed_response_wrapper(jobs.logs)
        self.stats = to_streamed_response_wrapper(jobs.stats)
        self.list_schedules = to_streamed_response_wrapper(jobs.list_schedules)
        self.create_schedule = to_streamed_response_wrapper(jobs.create_schedule)
        self.delete_schedule = to_streamed_response_wrapper(jobs.delete_schedule)


class AsyncJobsResourceWithStreamingResponse:
    def __init__(self, jobs: AsyncJobsResource) -> None:
        self._jobs = jobs
        self.list = async_to_streamed_response_wrapper(jobs.list)
        self.get = async_to_streamed_response_wrapper(jobs.get)
        self.create = async_to_streamed_response_wrapper(jobs.create)
        self.cancel = async_to_streamed_response_wrapper(jobs.cancel)
        self.retry = async_to_streamed_response_wrapper(jobs.retry)
        self.logs = async_to_streamed_response_wrapper(jobs.logs)
        self.stats = async_to_streamed_response_wrapper(jobs.stats)
        self.list_schedules = async_to_streamed_response_wrapper(jobs.list_schedules)
        self.create_schedule = async_to_streamed_response_wrapper(jobs.create_schedule)
        self.delete_schedule = async_to_streamed_response_wrapper(jobs.delete_schedule)
