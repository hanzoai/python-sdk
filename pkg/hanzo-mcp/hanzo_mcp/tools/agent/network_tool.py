"""Network tool for dispatching work to agent networks.

This tool enables distributed AI workloads across local and remote agent networks,
with support for both local-only execution (via hanzo-miner) and cloud fallback.
"""

import os
import json
from typing import (
    List,
    Unpack,
    Optional,
    Annotated,
    TypedDict,
    final,
    override,
)

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.permissions import PermissionManager

# Import hanzo cluster if available
try:
    from hanzoai import cluster

    CLUSTER_AVAILABLE = True
except ImportError:
    CLUSTER_AVAILABLE = False


class NetworkToolParams(TypedDict, total=False):
    """Parameters for the network tool."""

    task: str
    agents: Optional[List[str]]
    mode: Optional[str]  # "local", "distributed", "hybrid"
    model: Optional[str]
    routing: Optional[str]  # "sequential", "parallel", "consensus"
    require_local: Optional[bool]


@final
class NetworkTool(BaseTool):
    """Dispatch work to agent networks for distributed AI processing.

    Modes:
    - local: Use only local compute (via hanzo-cluster/miner)
    - distributed: Use available network resources
    - hybrid: Prefer local, fallback to cloud

    This tool is the evolution of the swarm tool, providing:
    - True distributed execution across devices
    - Local-first privacy-preserving AI
    - Automatic routing and load balancing
    - Integration with hanzo-miner for compute contribution
    """

    name = "network"
    description = "Dispatch tasks to agent networks for distributed AI processing"

    def __init__(
        self,
        permission_manager: PermissionManager,
        default_mode: str = "hybrid",
        cluster_endpoint: str = None,
    ):
        """Initialize the network tool.

        Args:
            permission_manager: Permission manager
            default_mode: Default execution mode
            cluster_endpoint: Optional cluster endpoint
        """
        self.permission_manager = permission_manager
        self.default_mode = default_mode
        self.cluster_endpoint = cluster_endpoint or os.environ.get("HANZO_CLUSTER_ENDPOINT", "http://localhost:8000")
        self._cluster = None

    async def _ensure_cluster(self):
        """Ensure we have a cluster connection."""
        if not CLUSTER_AVAILABLE:
            return None

        if not self._cluster:
            try:
                # Try to connect to existing cluster
                self._cluster = cluster.HanzoCluster()
                # Check if cluster is running
                import httpx

                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.cluster_endpoint}/health")
                    if response.status_code != 200:
                        # Start local cluster if not running
                        await self._cluster.start()
            except Exception:
                # Cluster not available
                self._cluster = None

        return self._cluster

    @override
    async def call(self, ctx: MCPContext, **params: Unpack[NetworkToolParams]) -> str:
        """Execute a task on the agent network.

        Args:
            ctx: MCP context
            task: Task description to execute
            agents: Optional list of specific agents to use
            mode: Execution mode (local/distributed/hybrid)
            model: Optional model preference
            routing: Routing strategy
            require_local: Require local-only execution

        Returns:
            JSON string with results
        """
        task = params.get("task", "")
        if not task:
            return json.dumps({"error": "Task description required", "success": False})

        mode = params.get("mode", self.default_mode)
        agents_list = params.get("agents", [])
        model_pref = params.get("model")
        routing = params.get("routing", "sequential")
        require_local = params.get("require_local", False)

        # Check if we should use local cluster
        use_local = mode in ["local", "hybrid"] or require_local

        results = {
            "task": task,
            "mode": mode,
            "routing": routing,
            "agents_used": [],
            "results": [],
            "success": False,
        }

        try:
            # Try local execution first if requested
            if use_local:
                cluster = await self._ensure_cluster()
                if cluster:
                    try:
                        # Execute on local cluster
                        local_result = await cluster.inference(
                            prompt=task,
                            model=model_pref or "llama-3.2-3b",
                            max_tokens=4000,
                        )

                        results["agents_used"].append("local-cluster")
                        results["results"].append(
                            {
                                "agent": "local-cluster",
                                "response": local_result.get("choices", [{}])[0].get("text", ""),
                                "local": True,
                            }
                        )
                        results["success"] = True

                        # If local succeeded and not hybrid, return
                        if mode == "local" or (mode == "hybrid" and results["results"]):
                            return json.dumps(results, indent=2)

                    except Exception as e:
                        if require_local:
                            results["error"] = f"Local execution failed: {str(e)}"
                            return json.dumps(results, indent=2)

                # Agent-based execution with concurrency
                if not results["success"] or mode in ["distributed", "hybrid"]:
                    from hanzo_mcp.tools.agent.agent_tool import AgentTool

                    agent = AgentTool(permission_manager=self.permission_manager, model=model_pref)
                    concurrency = max(1, len(agents_list)) if agents_list else 5 if routing == "parallel" else 1
                    agent_params = {"prompts": task, "concurrency": concurrency}
                    agent_result = await agent.call(ctx, **agent_params)
                    # Wrap agent_result as a simple result list
                    results["agents_used"].append("agent")
                    results["results"].append({"agent": "agent", "response": agent_result})
                    results["success"] = True

        except Exception as e:
            results["error"] = str(e)

        return json.dumps(results, indent=2)

    def register(self, server: FastMCP):
        """Register the network tool with the server.

        Args:
            server: FastMCP server instance
        """
        tool = self

        @server.tool(name=tool.name, description=tool.description)
        async def network_handler(
            ctx: MCPContext,
            task: Annotated[str, Field(description="Task to execute on the network")],
            agents: Annotated[Optional[List[str]], Field(description="Specific agents to use")] = None,
            mode: Annotated[
                Optional[str],
                Field(description="Execution mode: local, distributed, or hybrid"),
            ] = None,
            model: Annotated[Optional[str], Field(description="Model preference")] = None,
            routing: Annotated[
                Optional[str],
                Field(description="Routing strategy: sequential, parallel, or consensus"),
            ] = None,
            require_local: Annotated[Optional[bool], Field(description="Require local-only execution")] = None,
        ) -> str:
            """Dispatch work to agent networks."""
            params = NetworkToolParams(
                task=task,
                agents=agents,
                mode=mode,
                model=model,
                routing=routing,
                require_local=require_local,
            )
            return await tool.call(ctx, **params)

        return tool


# Remove swarm compatibility tool; swarm is an alias of agent with concurrency
