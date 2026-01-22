# Hanzo AI SDK

from __future__ import annotations
from typing import Dict, Any
import httpx
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_raw_response_wrapper, to_streamed_response_wrapper, async_to_raw_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options

__all__ = ["AgentsResource", "AsyncAgentsResource"]


class AgentsResource(SyncAPIResource):
    """AI Agent management."""

    @cached_property
    def with_raw_response(self) -> AgentsResourceWithRawResponse:
        return AgentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AgentsResourceWithStreamingResponse:
        return AgentsResourceWithStreamingResponse(self)

    def list(self, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List all agents."""
        return self._get("/agents", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def get(self, agent_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get a specific agent."""
        return self._get(f"/agents/{agent_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def create(self, *, name: str, config: Dict[str, Any], description: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Create a new agent."""
        return self._post("/agents", body={"name": name, "config": config, "description": description}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def update(self, agent_id: str, *, config: Dict[str, Any] | NotGiven = NOT_GIVEN, name: str | NotGiven = NOT_GIVEN, description: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Update an agent."""
        return self._put(f"/agents/{agent_id}", body={"config": config, "name": name, "description": description}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def delete(self, agent_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Delete an agent."""
        return self._delete(f"/agents/{agent_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def run(self, agent_id: str, *, prompt: str, context: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Run an agent with a prompt."""
        return self._post(f"/agents/{agent_id}/run", body={"prompt": prompt, "context": context}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def stop(self, agent_id: str, run_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Stop a running agent."""
        return self._post(f"/agents/{agent_id}/runs/{run_id}/stop", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def list_runs(self, agent_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List agent runs."""
        return self._get(f"/agents/{agent_id}/runs", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def get_run(self, agent_id: str, run_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get a specific run."""
        return self._get(f"/agents/{agent_id}/runs/{run_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AsyncAgentsResource(AsyncAPIResource):
    """AI Agent management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncAgentsResourceWithRawResponse:
        return AsyncAgentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAgentsResourceWithStreamingResponse:
        return AsyncAgentsResourceWithStreamingResponse(self)

    async def list(self, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get("/agents", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def get(self, agent_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/agents/{agent_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def create(self, *, name: str, config: Dict[str, Any], description: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post("/agents", body={"name": name, "config": config, "description": description}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def update(self, agent_id: str, *, config: Dict[str, Any] | NotGiven = NOT_GIVEN, name: str | NotGiven = NOT_GIVEN, description: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._put(f"/agents/{agent_id}", body={"config": config, "name": name, "description": description}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def delete(self, agent_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._delete(f"/agents/{agent_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def run(self, agent_id: str, *, prompt: str, context: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/agents/{agent_id}/run", body={"prompt": prompt, "context": context}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def stop(self, agent_id: str, run_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/agents/{agent_id}/runs/{run_id}/stop", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def list_runs(self, agent_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/agents/{agent_id}/runs", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def get_run(self, agent_id: str, run_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/agents/{agent_id}/runs/{run_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AgentsResourceWithRawResponse:
    def __init__(self, agents: AgentsResource) -> None:
        self._agents = agents
        self.list = to_raw_response_wrapper(agents.list)
        self.get = to_raw_response_wrapper(agents.get)
        self.create = to_raw_response_wrapper(agents.create)
        self.update = to_raw_response_wrapper(agents.update)
        self.delete = to_raw_response_wrapper(agents.delete)
        self.run = to_raw_response_wrapper(agents.run)
        self.stop = to_raw_response_wrapper(agents.stop)
        self.list_runs = to_raw_response_wrapper(agents.list_runs)
        self.get_run = to_raw_response_wrapper(agents.get_run)


class AsyncAgentsResourceWithRawResponse:
    def __init__(self, agents: AsyncAgentsResource) -> None:
        self._agents = agents
        self.list = async_to_raw_response_wrapper(agents.list)
        self.get = async_to_raw_response_wrapper(agents.get)
        self.create = async_to_raw_response_wrapper(agents.create)
        self.update = async_to_raw_response_wrapper(agents.update)
        self.delete = async_to_raw_response_wrapper(agents.delete)
        self.run = async_to_raw_response_wrapper(agents.run)
        self.stop = async_to_raw_response_wrapper(agents.stop)
        self.list_runs = async_to_raw_response_wrapper(agents.list_runs)
        self.get_run = async_to_raw_response_wrapper(agents.get_run)


class AgentsResourceWithStreamingResponse:
    def __init__(self, agents: AgentsResource) -> None:
        self._agents = agents
        self.list = to_streamed_response_wrapper(agents.list)
        self.get = to_streamed_response_wrapper(agents.get)
        self.create = to_streamed_response_wrapper(agents.create)
        self.update = to_streamed_response_wrapper(agents.update)
        self.delete = to_streamed_response_wrapper(agents.delete)
        self.run = to_streamed_response_wrapper(agents.run)
        self.stop = to_streamed_response_wrapper(agents.stop)
        self.list_runs = to_streamed_response_wrapper(agents.list_runs)
        self.get_run = to_streamed_response_wrapper(agents.get_run)


class AsyncAgentsResourceWithStreamingResponse:
    def __init__(self, agents: AsyncAgentsResource) -> None:
        self._agents = agents
        self.list = async_to_streamed_response_wrapper(agents.list)
        self.get = async_to_streamed_response_wrapper(agents.get)
        self.create = async_to_streamed_response_wrapper(agents.create)
        self.update = async_to_streamed_response_wrapper(agents.update)
        self.delete = async_to_streamed_response_wrapper(agents.delete)
        self.run = async_to_streamed_response_wrapper(agents.run)
        self.stop = async_to_streamed_response_wrapper(agents.stop)
        self.list_runs = async_to_streamed_response_wrapper(agents.list_runs)
        self.get_run = async_to_streamed_response_wrapper(agents.get_run)
