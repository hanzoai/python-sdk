"""MCP mesh for agent-to-agent consensus.

Each agent in consensus is available as MCP to every other.
Enables N rounds of tool calling/discussion between agents.

Usage:
    from hanzo_consensus import MCPMesh, run_mcp_consensus

    mesh = MCPMesh()
    mesh.register("agent1", agent1_server)
    mesh.register("agent2", agent2_server)
    mesh.register("agent3", agent3_server)

    state = await run_mcp_consensus(
        mesh=mesh,
        prompt="Discuss the best approach",
        rounds=10,
    )
"""

import asyncio
from typing import Any, Dict, List, Callable, Optional, Coroutine
from dataclasses import field, dataclass

from .consensus import State, Result, run


@dataclass
class MCPAgent:
    """An agent in the MCP mesh."""

    id: str
    server: Any  # FastMCP server
    endpoint: Optional[str] = None  # For remote agents
    tools: List[str] = field(default_factory=list)

    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """Call a tool on this agent."""
        if self.server:
            # Local agent - call directly
            for tool in self.server._tools.values():
                if tool.name == tool_name:
                    return await tool.fn(**kwargs)
            raise ValueError(f"Tool {tool_name} not found on agent {self.id}")
        else:
            # Remote agent - would use MCP client
            raise NotImplementedError("Remote MCP agents not yet implemented")

    async def discuss(self, prompt: str, context: Dict[str, str]) -> str:
        """Have this agent respond to a discussion prompt.

        Args:
            prompt: The discussion prompt
            context: Previous responses from other agents

        Returns:
            Agent's response
        """
        # Build context string from other agents' responses
        context_str = "\n\n".join([f"[{agent_id}]: {response}" for agent_id, response in context.items()])

        full_prompt = f"""Discussion prompt: {prompt}

Previous responses:
{context_str}

Please provide your perspective, building on or responding to the above."""

        # Call the agent's "think" or "respond" tool
        for tool_name in ["think", "respond", "discuss", "agent"]:
            try:
                return await self.call_tool(tool_name, prompt=full_prompt)
            except (ValueError, KeyError):
                continue

        # Fallback - return a placeholder
        return f"[{self.id}] I acknowledge the discussion but have no specific tools to respond."


class MCPMesh:
    """Mesh network of MCP agents.

    Enables agent-to-agent communication where each agent
    can call tools on any other agent in the mesh.
    """

    def __init__(self):
        self.agents: Dict[str, MCPAgent] = {}
        self._lock = asyncio.Lock()

    def register(
        self,
        agent_id: str,
        server: Any = None,
        endpoint: Optional[str] = None,
    ) -> MCPAgent:
        """Register an agent in the mesh.

        Args:
            agent_id: Unique identifier for the agent
            server: Local FastMCP server instance
            endpoint: Remote MCP endpoint URL

        Returns:
            The registered MCPAgent
        """
        if not server and not endpoint:
            raise ValueError("Must provide either server or endpoint")

        # Extract available tools
        tools = []
        if server and hasattr(server, "_tools"):
            tools = list(server._tools.keys())

        agent = MCPAgent(
            id=agent_id,
            server=server,
            endpoint=endpoint,
            tools=tools,
        )
        self.agents[agent_id] = agent
        return agent

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from the mesh."""
        self.agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[MCPAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    @property
    def participant_ids(self) -> List[str]:
        """Get list of all agent IDs."""
        return list(self.agents.keys())

    async def call(
        self,
        from_agent: str,
        to_agent: str,
        tool_name: str,
        **kwargs,
    ) -> str:
        """Call a tool on one agent from another.

        Args:
            from_agent: ID of the calling agent
            to_agent: ID of the target agent
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        target = self.agents.get(to_agent)
        if not target:
            raise ValueError(f"Agent {to_agent} not found in mesh")

        return await target.call_tool(tool_name, **kwargs)

    async def broadcast(
        self,
        from_agent: str,
        tool_name: str,
        **kwargs,
    ) -> Dict[str, str]:
        """Call a tool on all other agents.

        Args:
            from_agent: ID of the calling agent
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Dict mapping agent_id -> result
        """
        results = {}
        tasks = []

        for agent_id in self.agents:
            if agent_id != from_agent:

                async def call_agent(aid: str):
                    try:
                        result = await self.agents[aid].call_tool(tool_name, **kwargs)
                        return (aid, result)
                    except Exception as e:
                        return (aid, f"Error: {e}")

                tasks.append(call_agent(agent_id))

        for result in await asyncio.gather(*tasks):
            results[result[0]] = result[1]

        return results


async def run_mcp_consensus(
    mesh: MCPMesh,
    prompt: str,
    rounds: int = 10,
    k: int = 3,
    alpha: float = 0.6,
    beta_1: float = 0.5,
    beta_2: float = 0.8,
) -> State:
    """Run Metastable consensus over an MCP mesh.

    Each round involves agents discussing with each other via MCP,
    then voting on the best response.

    Args:
        mesh: The MCP mesh of agents
        prompt: The consensus prompt
        rounds: Number of discussion rounds (default: 10)
        k: Sample size per round
        alpha: Agreement threshold
        beta_1: Preference threshold
        beta_2: Decision threshold

    Returns:
        Consensus state with winner and synthesis
    """
    # Track discussion history
    discussion_history: List[Dict[str, str]] = []

    async def execute(agent_id: str, round_prompt: str) -> Result:
        """Execute one round of discussion for an agent."""
        import time

        start = time.time()

        agent = mesh.get(agent_id)
        if not agent:
            return Result(
                id=agent_id,
                output="",
                ok=False,
                error=f"Agent {agent_id} not found",
            )

        try:
            # Get context from previous rounds
            context = {}
            if discussion_history:
                # Use most recent round's responses
                context = discussion_history[-1]

            response = await agent.discuss(round_prompt, context)
            ms = int((time.time() - start) * 1000)

            return Result(
                id=agent_id,
                output=response,
                ok=True,
                ms=ms,
            )
        except Exception as e:
            return Result(
                id=agent_id,
                output="",
                ok=False,
                error=str(e),
            )

    # Custom round callback to track discussion
    async def on_round_complete(round_num: int, responses: Dict[str, str]):
        discussion_history.append(responses)

    # Run consensus with the mesh's agents
    state = await run(
        prompt=prompt,
        participants=mesh.participant_ids,
        execute=execute,
        rounds=rounds,
        k=min(k, len(mesh.agents)),
        alpha=alpha,
        beta_1=beta_1,
        beta_2=beta_2,
    )

    # Attach discussion history to state
    state.discussion_history = discussion_history

    return state


# Convenience function to create mesh from agent configs
def create_mesh(
    agents: Dict[str, Any],
) -> MCPMesh:
    """Create an MCP mesh from agent configurations.

    Args:
        agents: Dict mapping agent_id -> server or endpoint

    Returns:
        Configured MCPMesh
    """
    mesh = MCPMesh()

    for agent_id, config in agents.items():
        if isinstance(config, str):
            # URL endpoint
            mesh.register(agent_id, endpoint=config)
        else:
            # Server instance
            mesh.register(agent_id, server=config)

    return mesh
