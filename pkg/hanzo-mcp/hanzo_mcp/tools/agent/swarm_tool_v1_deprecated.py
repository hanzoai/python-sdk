"""Swarm tool implementation for parallel and hierarchical agent execution.

This module implements the SwarmTool that enables both parallel execution of multiple
agent instances and hierarchical workflows with specialized roles.
"""

import os
import asyncio
from typing import (
    Any,
    Dict,
    List,
    Unpack,
    Optional,
    TypedDict,
    final,
    override,
)

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.agent.agent_tool import AgentTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class AgentNode(TypedDict):
    """Node in the agent network.

    Attributes:
        id: Unique identifier for this agent
        query: The specific query/task for this agent
        model: Optional model override (e.g., 'claude-3-5-sonnet', 'gpt-4o')
        role: Optional role description (e.g., 'architect', 'frontend', 'reviewer')
        connections: List of agent IDs this agent connects to (sends results to)
        receives_from: Optional list of agent IDs this agent receives input from
        file_path: Optional specific file for the agent to work on
    """

    id: str
    query: str
    model: Optional[str]
    role: Optional[str]
    connections: Optional[List[str]]
    receives_from: Optional[List[str]]
    file_path: Optional[str]


class SwarmConfig(TypedDict):
    """Configuration for an agent network.

    Attributes:
        agents: Dictionary of agent configurations keyed by ID
        entry_point: ID of the first agent to execute (optional, defaults to finding roots)
        topology: Optional topology type (tree, dag, pipeline, star, mesh)
    """

    agents: Dict[str, AgentNode]
    entry_point: Optional[str]
    topology: Optional[str]


class SwarmToolParams(TypedDict):
    """Parameters for the SwarmTool.

    Attributes:
        config: Agent network configuration
        query: Initial query to send to entry point agent(s)
        context: Optional context shared by all agents
        max_concurrent: Maximum number of concurrent agents (default: 10)
    """

    config: SwarmConfig
    query: str
    context: Optional[str]
    max_concurrent: Optional[int]


@final
class SwarmTool(BaseTool):
    """Tool for executing multiple agent tasks in parallel.

    The SwarmTool enables efficient parallel processing of multiple files or tasks
    by spawning independent agent instances for each task.
    """

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "swarm"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Execute a network of AI agents with flexible connection topologies.

This tool enables sophisticated agent orchestration where agents can be connected
in various network patterns. Each agent can pass results to connected agents,
enabling complex workflows.

Features:
- Flexible agent networks (tree, DAG, pipeline, star, mesh)
- Each agent can use different models (Claude, GPT-4, Gemini, etc.)
- Agents automatically pass results to connected agents
- Parallel execution with dependency management
- Full editing capabilities for each agent

Common Topologies:

1. Tree (Architect pattern):
   architect → [frontend, backend, database] → reviewer

2. Pipeline (Sequential processing):
   analyzer → planner → implementer → tester → reviewer

3. Star (Central coordinator):
   coordinator ← → [agent1, agent2, agent3, agent4]

4. DAG (Complex dependencies):
   Multiple agents with custom connections

Usage Example:

swarm(
    config={
        "agents": {
            "architect": {
                "id": "architect",
                "query": "Analyze codebase and create refactoring plan",
                "model": "claude-3-5-sonnet",
                "connections": ["frontend", "backend", "database"]
            },
            "frontend": {
                "id": "frontend",
                "query": "Refactor UI components based on architect's plan",
                "role": "Frontend Developer",
                "connections": ["reviewer"]
            },
            "backend": {
                "id": "backend", 
                "query": "Refactor API endpoints based on architect's plan",
                "role": "Backend Developer",
                "connections": ["reviewer"]
            },
            "database": {
                "id": "database",
                "query": "Optimize database schema based on architect's plan",
                "role": "Database Expert",
                "connections": ["reviewer"]
            },
            "reviewer": {
                "id": "reviewer",
                "query": "Review all changes and ensure consistency",
                "model": "gpt-4o",
                "receives_from": ["frontend", "backend", "database"]
            }
        },
        "entry_point": "architect"
    },
    query="Refactor the authentication system for better security and performance"
)

Models can be specified as:
- Full: 'anthropic/claude-3-5-sonnet-20241022'
- Short: 'claude-3-5-sonnet', 'gpt-4o', 'gemini-1.5-pro'
- CLI tools: 'claude_cli', 'codex_cli', 'gemini_cli', 'grok_cli'
"""

    def __init__(
        self,
        permission_manager: PermissionManager,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int | None = None,
        agent_max_iterations: int = 10,
        agent_max_tool_uses: int = 30,
    ):
        """Initialize the swarm tool.

        Args:
            permission_manager: Permission manager for access control
            model: Optional model name override (defaults to Claude Sonnet)
            api_key: Optional API key for the model provider
            base_url: Optional base URL for the model provider
            max_tokens: Optional maximum tokens for model responses
            agent_max_iterations: Max iterations per agent (default: 10)
            agent_max_tool_uses: Max tool uses per agent (default: 30)
        """
        self.permission_manager = permission_manager
        # Default to latest Claude Sonnet if no model specified
        from hanzo_mcp.tools.agent.code_auth import get_latest_claude_model

        self.model = model or f"anthropic/{get_latest_claude_model()}"
        self.api_key = (
            api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("CLAUDE_API_KEY")
        )
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.agent_max_iterations = agent_max_iterations
        self.agent_max_tool_uses = agent_max_tool_uses

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[SwarmToolParams],
    ) -> str:
        """Execute the swarm tool.

        Args:
            ctx: MCP context
            **params: Tool parameters

        Returns:
            Combined results from all agents
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Extract parameters
        agents = params.get("agents", [])
        manager_query = params.get("manager_query")
        reviewer_query = params.get("reviewer_query")
        common_context = params.get("common_context", "")
        max_concurrent = params.get("max_concurrent", 10)

        if not agents:
            await tool_ctx.error("No agents provided")
            return "Error: At least one agent must be provided."

        # Extract parameters
        config = params.get("config", {})
        initial_query = params.get("query", "")
        context = params.get("context", "")

        agents_config = config.get("agents", {})
        entry_point = config.get("entry_point")

        await tool_ctx.info(
            f"Starting swarm execution with {len(agents_config)} agents"
        )

        # Build agent network
        agent_instances = {}
        agent_results = {}
        execution_queue = asyncio.Queue()
        completed_agents = set()

        # Create agent instances
        for agent_id, agent_config in agents_config.items():
            model = agent_config.get("model", self.model)

            # Support CLI tools
            cli_tools = {
                "claude_cli": self._get_cli_tool("claude_cli"),
                "codex_cli": self._get_cli_tool("codex_cli"),
                "gemini_cli": self._get_cli_tool("gemini_cli"),
                "grok_cli": self._get_cli_tool("grok_cli"),
            }

            if model in cli_tools:
                agent = cli_tools[model]
            else:
                # Regular agent with model
                agent = AgentTool(
                    permission_manager=self.permission_manager,
                    model=self._normalize_model(model),
                    api_key=self.api_key,
                    base_url=self.base_url,
                    max_tokens=self.max_tokens,
                    max_iterations=self.agent_max_iterations,
                    max_tool_uses=self.agent_max_tool_uses,
                )

            agent_instances[agent_id] = agent

        # Find entry points (agents with no incoming connections)
        if entry_point:
            await execution_queue.put((entry_point, initial_query, {}))
        else:
            # Find root agents (no receives_from)
            roots = []
            for agent_id, agent_config in agents_config.items():
                if not agent_config.get("receives_from"):
                    # Check if any other agent connects to this one
                    has_incoming = False
                    for other_config in agents_config.values():
                        if (
                            other_config.get("connections")
                            and agent_id in other_config["connections"]
                        ):
                            has_incoming = True
                            break
                    if not has_incoming:
                        roots.append(agent_id)

            if not roots:
                await tool_ctx.error("No entry point found in agent network")
                return "Error: Could not determine entry point for agent network"

            for root in roots:
                await execution_queue.put((root, initial_query, {}))

        # Execute agents in network order
        async def execute_agent(
            agent_id: str, query: str, inputs: Dict[str, str]
        ) -> str:
            """Execute a single agent in the network."""
            async with semaphore:
                try:
                    agent_config = agents_config[agent_id]
                    agent = agent_instances[agent_id]

                    await tool_ctx.info(
                        f"Executing agent: {agent_id} ({agent_config.get('role', 'Agent')})"
                    )

                    # Build prompt with context and inputs
                    prompt_parts = []

                    # Add role context
                    if agent_config.get("role"):
                        prompt_parts.append(f"Your role: {agent_config['role']}")

                    # Add shared context
                    if context:
                        prompt_parts.append(f"Context:\n{context}")

                    # Add inputs from connected agents
                    if inputs:
                        prompt_parts.append("Input from previous agents:")
                        for input_agent, input_result in inputs.items():
                            prompt_parts.append(
                                f"\n--- From {input_agent} ---\n{input_result}"
                            )

                    # Add file context if specified
                    if agent_config.get("file_path"):
                        prompt_parts.append(
                            f"\nFile to work on: {agent_config['file_path']}"
                        )

                    # Add the main query
                    prompt_parts.append(f"\nTask: {agent_config['query']}")

                    # Combine query with initial query if this is entry point
                    if query and query != agent_config["query"]:
                        prompt_parts.append(f"\nMain objective: {query}")

                    full_prompt = "\n\n".join(prompt_parts)

                    # Execute the agent
                    result = await agent.call(ctx, prompts=full_prompt)

                    await tool_ctx.info(f"Agent {agent_id} completed")
                    return result

                except Exception as e:
                    error_msg = f"Agent {agent_id} failed: {str(e)}"
                    await tool_ctx.error(error_msg)
                    return f"Error: {error_msg}"

        # Process agent network
        running_tasks = set()

        while not execution_queue.empty() or running_tasks:
            # Start new tasks up to concurrency limit
            while not execution_queue.empty() and len(running_tasks) < max_concurrent:
                agent_id, query, inputs = await execution_queue.get()

                if agent_id not in completed_agents:
                    # Check if all dependencies are met
                    agent_config = agents_config[agent_id]
                    receives_from = agent_config.get("receives_from", [])

                    # Collect inputs from dependencies
                    ready = True
                    for dep in receives_from:
                        if dep not in agent_results:
                            ready = False
                            # Re-queue for later
                            await execution_queue.put((agent_id, query, inputs))
                            break
                        else:
                            inputs[dep] = agent_results[dep]

                    if ready:
                        # Execute agent
                        task = asyncio.create_task(
                            execute_agent(agent_id, query, inputs)
                        )
                        running_tasks.add(task)

                        async def handle_completion(task, agent_id=agent_id):
                            result = await task
                            agent_results[agent_id] = result
                            completed_agents.add(agent_id)
                            running_tasks.discard(task)

                            # Queue connected agents
                            agent_config = agents_config[agent_id]
                            connections = agent_config.get("connections", [])
                            for next_agent in connections:
                                if next_agent in agents_config:
                                    await execution_queue.put(
                                        (next_agent, "", {agent_id: result})
                                    )

                        asyncio.create_task(handle_completion(task))

            # Wait a bit if we're at capacity
            if running_tasks:
                await asyncio.sleep(0.1)

        # Wait for all tasks to complete
        if running_tasks:
            await asyncio.gather(*running_tasks, return_exceptions=True)

        # Format results
        return self._format_network_results(agents_config, agent_results, entry_point)

    def _normalize_model(self, model: str) -> str:
        """Normalize model names to full format."""
        model_map = {
            "claude-3-5-sonnet": "anthropic/claude-3-5-sonnet-20241022",
            "claude-3-opus": "anthropic/claude-3-opus-20240229",
            "gpt-4o": "openai/gpt-4o",
            "gpt-4": "openai/gpt-4",
            "gemini-1.5-pro": "google/gemini-1.5-pro",
            "gemini-1.5-flash": "google/gemini-1.5-flash",
        }
        return model_map.get(model, model)

    def _get_cli_tool(self, tool_name: str):
        """Get CLI tool instance."""
        # Import here to avoid circular imports
        if tool_name == "claude_cli":
            from hanzo_mcp.tools.agent.claude_cli_tool import ClaudeCLITool

            return ClaudeCLITool(self.permission_manager)
        elif tool_name == "codex_cli":
            from hanzo_mcp.tools.agent.codex_cli_tool import CodexCLITool

            return CodexCLITool(self.permission_manager)
        elif tool_name == "gemini_cli":
            from hanzo_mcp.tools.agent.gemini_cli_tool import GeminiCLITool

            return GeminiCLITool(self.permission_manager)
        elif tool_name == "grok_cli":
            from hanzo_mcp.tools.agent.grok_cli_tool import GrokCLITool

            return GrokCLITool(self.permission_manager)
        return None

    def _format_network_results(
        self,
        agents_config: Dict[str, Any],
        results: Dict[str, str],
        entry_point: Optional[str],
    ) -> str:
        """Format results from agent network execution."""
        output = ["Agent Network Execution Results"]
        output.append("=" * 80)
        output.append(f"Total agents: {len(agents_config)}")
        output.append(f"Completed: {len(results)}")
        output.append(
            f"Failed: {len([r for r in results.values() if r.startswith('Error:')])}"
        )

        if entry_point:
            output.append(f"Entry point: {entry_point}")

        output.append("\nExecution Flow:")
        output.append("-" * 40)

        # Show results in execution order
        def format_agent_tree(agent_id: str, level: int = 0) -> List[str]:
            lines = []
            indent = "  " * level

            if agent_id in agents_config:
                config = agents_config[agent_id]
                role = config.get("role", "Agent")
                model = config.get("model", "default")

                status = (
                    "✅"
                    if agent_id in results
                    and not results[agent_id].startswith("Error:")
                    else "❌"
                )
                lines.append(f"{indent}{status} {agent_id} ({role}) [{model}]")

                # Show connections
                connections = config.get("connections", [])
                for conn in connections:
                    if conn in agents_config:
                        lines.extend(format_agent_tree(conn, level + 1))

            return lines

        # Start from entry point or roots
        if entry_point:
            output.extend(format_agent_tree(entry_point))
        else:
            # Find roots
            roots = []
            for agent_id in agents_config:
                has_incoming = False
                for config in agents_config.values():
                    if config.get("connections") and agent_id in config["connections"]:
                        has_incoming = True
                        break
                if not has_incoming:
                    roots.append(agent_id)

            for root in roots:
                output.extend(format_agent_tree(root))

        # Detailed results
        output.append("\n\nDetailed Results:")
        output.append("=" * 80)

        for agent_id, result in results.items():
            config = agents_config.get(agent_id, {})
            role = config.get("role", "Agent")

            output.append(f"\n### {agent_id} ({role})")
            output.append("-" * 40)

            if result.startswith("Error:"):
                output.append(result)
            else:
                # Show first part of result
                lines = result.split("\n")
                preview_lines = lines[:10]
                output.extend(preview_lines)

                if len(lines) > 10:
                    output.append(f"... ({len(lines) - 10} more lines)")

        return "\n".join(output)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this swarm tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def swarm(
            ctx: MCPContext,
            config: dict[str, Any],
            query: str,
            context: Optional[str] = None,
            max_concurrent: int = 10,
        ) -> str:
            # Convert to typed format
            typed_config = SwarmConfig(
                agents=config.get("agents", {}),
                entry_point=config.get("entry_point"),
                topology=config.get("topology"),
            )

            return await tool_self.call(
                ctx,
                config=typed_config,
                query=query,
                context=context,
                max_concurrent=max_concurrent,
            )
