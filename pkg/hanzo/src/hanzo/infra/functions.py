"""Nuclio serverless functions client wrapper for Hanzo infrastructure.

Provides async interface to Nuclio for deploying and invoking
serverless functions with auto-scaling and GPU support.
"""

from __future__ import annotations

import os
from typing import Any, Optional
from datetime import datetime
from dataclasses import field, dataclass

from pydantic import Field, BaseModel


class FunctionsConfig(BaseModel):
    """Configuration for Nuclio connection."""

    dashboard_url: str = Field(default="http://localhost:8070", description="Nuclio dashboard URL")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    namespace: str = Field(default="nuclio", description="Kubernetes namespace")
    default_runtime: str = Field(default="python:3.11", description="Default function runtime")
    default_handler: str = Field(default="main:handler", description="Default function handler")
    registry: Optional[str] = Field(default=None, description="Container registry URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    @classmethod
    def from_env(cls) -> FunctionsConfig:
        """Create config from environment variables.

        Environment variables:
            NUCLIO_DASHBOARD_URL: Dashboard URL (default: http://localhost:8070)
            NUCLIO_API_KEY: API key for authentication
            NUCLIO_NAMESPACE: Kubernetes namespace (default: nuclio)
            NUCLIO_RUNTIME: Default runtime (default: python:3.11)
            NUCLIO_REGISTRY: Container registry URL
        """
        return cls(
            dashboard_url=os.getenv("NUCLIO_DASHBOARD_URL", "http://localhost:8070"),
            api_key=os.getenv("NUCLIO_API_KEY"),
            namespace=os.getenv("NUCLIO_NAMESPACE", "nuclio"),
            default_runtime=os.getenv("NUCLIO_RUNTIME", "python:3.11"),
            registry=os.getenv("NUCLIO_REGISTRY"),
        )


@dataclass
class FunctionSpec:
    """Specification for a Nuclio function."""

    name: str
    handler: str = "main:handler"
    runtime: str = "python:3.11"
    code: Optional[str] = None  # Inline code
    code_path: Optional[str] = None  # Path to code directory
    image: Optional[str] = None  # Pre-built image
    env: dict[str, str] = field(default_factory=dict)
    min_replicas: int = 0
    max_replicas: int = 10
    target_cpu: int = 75  # CPU utilization target for scaling
    triggers: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    build_commands: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)  # pip requirements
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def to_nuclio_spec(self) -> dict[str, Any]:
        """Convert to Nuclio API spec format."""
        spec: dict[str, Any] = {
            "spec": {
                "handler": self.handler,
                "runtime": self.runtime,
                "minReplicas": self.min_replicas,
                "maxReplicas": self.max_replicas,
                "targetCPU": self.target_cpu,
                "env": [{"name": k, "value": v} for k, v in self.env.items()],
            },
            "metadata": {
                "name": self.name,
                "labels": self.labels,
                "annotations": self.annotations,
            },
        }

        if self.code:
            spec["spec"]["build"] = {
                "functionSourceCode": self.code,
            }
        elif self.code_path:
            spec["spec"]["build"] = {
                "path": self.code_path,
            }
        elif self.image:
            spec["spec"]["image"] = self.image

        if self.build_commands:
            spec["spec"]["build"] = spec["spec"].get("build", {})
            spec["spec"]["build"]["commands"] = self.build_commands

        if self.requirements:
            # Add pip install to build commands
            pip_cmd = f"pip install {' '.join(self.requirements)}"
            commands = spec["spec"].get("build", {}).get("commands", [])
            commands.insert(0, pip_cmd)
            spec["spec"]["build"] = spec["spec"].get("build", {})
            spec["spec"]["build"]["commands"] = commands

        if self.triggers:
            spec["spec"]["triggers"] = self.triggers

        if self.resources:
            spec["spec"]["resources"] = self.resources

        return spec


@dataclass
class FunctionStatus:
    """Status of a deployed function."""

    name: str
    state: str  # ready, building, error, etc.
    replicas: int = 0
    version: str = ""
    invoke_url: Optional[str] = None
    internal_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message: Optional[str] = None


@dataclass
class InvokeResult:
    """Result of a function invocation."""

    status_code: int
    body: Any
    headers: dict[str, str] = field(default_factory=dict)
    duration_ms: int = 0


class FunctionsClient:
    """Async client for Nuclio serverless functions.

        Wraps Nuclio HTTP API for deploying, managing, and invoking
        serverless functions with Hanzo conventions.

        Example:
            ```python
            client = FunctionsClient(FunctionsConfig.from_env())
            await client.connect()

            # Deploy a function
            spec = FunctionSpec(
                name="hello",
                code='''
    def handler(context, event):
        return "Hello, " + event.body.decode()
    ''',
                runtime="python:3.11",
            )
            await client.deploy(spec)

            # Invoke the function
            result = await client.invoke("hello", body=b"World")
            print(result.body)  # "Hello, World"

            # List functions
            functions = await client.list_functions()
            for fn in functions:
                print(f"{fn.name}: {fn.state}")
            ```
    """

    def __init__(self, config: Optional[FunctionsConfig] = None) -> None:
        """Initialize functions client.

        Args:
            config: Nuclio configuration. If None, loads from environment.
        """
        self.config = config or FunctionsConfig.from_env()
        self._client: Any = None

    async def connect(self) -> None:
        """Establish connection (validates connectivity)."""
        try:
            import httpx
        except ImportError as e:
            raise ImportError("httpx is required for FunctionsClient. Install with: pip install httpx") from e

        self._client = httpx.AsyncClient(
            base_url=self.config.dashboard_url,
            timeout=self.config.timeout,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["X-nuclio-project-name"] = "default"
            headers["X-v3io-session-key"] = self.config.api_key
        return headers

    async def close(self) -> None:
        """Close the connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if Nuclio is healthy.

        Returns:
            True if Nuclio dashboard is reachable.
        """
        if not self._client:
            return False
        try:
            response = await self._client.get("/api/projects")
            return response.status_code == 200
        except Exception:
            return False

    # Function management

    async def deploy(
        self,
        spec: FunctionSpec,
        wait: bool = True,
        timeout: float = 300.0,
    ) -> FunctionStatus:
        """Deploy a function.

        Args:
            spec: Function specification.
            wait: Wait for deployment to complete.
            timeout: Deployment timeout in seconds.

        Returns:
            Function status after deployment.
        """
        import asyncio

        # Create/update function
        nuclio_spec = spec.to_nuclio_spec()
        response = await self._client.post(
            f"/api/functions/{spec.name}",
            json=nuclio_spec,
            params={"namespace": self.config.namespace},
        )

        if response.status_code not in (200, 201, 202):
            raise Exception(f"Failed to deploy function: {response.text}")

        if wait:
            # Poll until ready or timeout
            start_time = datetime.utcnow()
            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                status = await self.get_function(spec.name)
                if status.state in ("ready", "imported"):
                    return status
                if status.state == "error":
                    raise Exception(f"Function deployment failed: {status.message}")
                await asyncio.sleep(2)

            raise TimeoutError(f"Function deployment timed out after {timeout}s")

        return await self.get_function(spec.name)

    async def delete_function(self, name: str) -> bool:
        """Delete a function.

        Args:
            name: Function name.

        Returns:
            True if function was deleted.
        """
        response = await self._client.delete(
            f"/api/functions/{name}",
            params={"namespace": self.config.namespace},
        )
        return response.status_code in (200, 204)

    async def get_function(self, name: str) -> FunctionStatus:
        """Get function status.

        Args:
            name: Function name.

        Returns:
            Function status.
        """
        response = await self._client.get(
            f"/api/functions/{name}",
            params={"namespace": self.config.namespace},
        )

        if response.status_code == 404:
            raise Exception(f"Function not found: {name}")

        data = response.json()
        status = data.get("status", {})
        metadata = data.get("metadata", {})

        return FunctionStatus(
            name=name,
            state=status.get("state", "unknown"),
            replicas=status.get("replicas", 0),
            version=metadata.get("version", ""),
            invoke_url=status.get("httpPort"),
            internal_url=status.get("internalInvocationUrls", [None])[0]
            if status.get("internalInvocationUrls")
            else None,
            message=status.get("message"),
        )

    async def list_functions(self) -> list[FunctionStatus]:
        """List all functions.

        Returns:
            List of function statuses.
        """
        response = await self._client.get(
            "/api/functions",
            params={"namespace": self.config.namespace},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to list functions: {response.text}")

        functions = []
        for name, data in response.json().items():
            status = data.get("status", {})
            metadata = data.get("metadata", {})
            functions.append(
                FunctionStatus(
                    name=name,
                    state=status.get("state", "unknown"),
                    replicas=status.get("replicas", 0),
                    version=metadata.get("version", ""),
                    invoke_url=status.get("httpPort"),
                    message=status.get("message"),
                )
            )

        return functions

    # Function invocation

    async def invoke(
        self,
        name: str,
        body: bytes = b"",
        method: str = "POST",
        path: str = "",
        headers: Optional[dict[str, str]] = None,
        query: Optional[dict[str, str]] = None,
    ) -> InvokeResult:
        """Invoke a function.

        Args:
            name: Function name.
            body: Request body.
            method: HTTP method.
            path: Request path within function.
            headers: Additional headers.
            query: Query parameters.

        Returns:
            Invocation result.
        """
        import time

        # Get function invoke URL
        status = await self.get_function(name)
        if not status.invoke_url and not status.internal_url:
            raise Exception(f"Function {name} has no invoke URL")

        # Determine invoke URL
        if status.internal_url:
            invoke_url = status.internal_url
        else:
            # Construct URL from dashboard URL and port
            base = self.config.dashboard_url.rsplit(":", 1)[0]
            invoke_url = f"{base}:{status.invoke_url}"

        # Build request URL
        url = f"{invoke_url}/{path.lstrip('/')}" if path else invoke_url

        # Prepare headers
        req_headers = headers or {}

        start = time.monotonic()
        response = await self._client.request(
            method=method,
            url=url,
            content=body,
            headers=req_headers,
            params=query,
        )
        duration = int((time.monotonic() - start) * 1000)

        # Parse response
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return InvokeResult(
            status_code=response.status_code,
            body=response_body,
            headers=dict(response.headers),
            duration_ms=duration,
        )

    async def invoke_async(
        self,
        name: str,
        body: bytes = b"",
        headers: Optional[dict[str, str]] = None,
    ) -> str:
        """Invoke a function asynchronously.

        Args:
            name: Function name.
            body: Request body.
            headers: Additional headers.

        Returns:
            Invocation ID for checking status.
        """
        req_headers = headers or {}
        req_headers["X-Nuclio-Function-Async"] = "true"

        result = await self.invoke(name, body, headers=req_headers)

        # Return invocation ID from response
        return result.headers.get("X-Nuclio-Invoke-Id", "")

    # Scaling

    async def scale_function(
        self,
        name: str,
        replicas: Optional[int] = None,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
    ) -> FunctionStatus:
        """Scale a function.

        Args:
            name: Function name.
            replicas: Fixed replica count (overrides auto-scaling).
            min_replicas: Minimum replicas for auto-scaling.
            max_replicas: Maximum replicas for auto-scaling.

        Returns:
            Updated function status.
        """
        # Get current function
        response = await self._client.get(
            f"/api/functions/{name}",
            params={"namespace": self.config.namespace},
        )

        if response.status_code == 404:
            raise Exception(f"Function not found: {name}")

        data = response.json()
        spec = data.get("spec", {})

        # Update scaling config
        if replicas is not None:
            spec["replicas"] = replicas
        if min_replicas is not None:
            spec["minReplicas"] = min_replicas
        if max_replicas is not None:
            spec["maxReplicas"] = max_replicas

        # Update function
        data["spec"] = spec
        response = await self._client.put(
            f"/api/functions/{name}",
            json=data,
            params={"namespace": self.config.namespace},
        )

        if response.status_code not in (200, 202):
            raise Exception(f"Failed to scale function: {response.text}")

        return await self.get_function(name)

    # Logs

    async def get_logs(
        self,
        name: str,
        since: Optional[datetime] = None,
        follow: bool = False,
    ):
        """Get function logs.

        Args:
            name: Function name.
            since: Get logs since this time.
            follow: Stream logs (not implemented in basic version).

        Yields:
            Log lines.
        """
        params: dict[str, Any] = {
            "namespace": self.config.namespace,
            "function": name,
        }
        if since:
            params["since"] = since.isoformat()

        response = await self._client.get("/api/logs", params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to get logs: {response.text}")

        for line in response.text.split("\n"):
            if line.strip():
                yield line

    async def __aenter__(self) -> FunctionsClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
