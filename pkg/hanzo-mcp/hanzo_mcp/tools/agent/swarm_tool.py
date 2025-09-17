"""Swarm tool implementation using hanzo-agents SDK.

This module implements the SwarmTool that leverages the hanzo-agents SDK
for sophisticated multi-agent orchestration with flexible network topologies.
"""

import os
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

# Import hanzo-agents SDK with fallback
try:
    from hanzo_agents import (
        Tool,
        Agent,
        State,
        Router,
        History,
        Network,
        ToolCall,
        ModelRegistry,
        InferenceResult,
    )

    HANZO_AGENTS_AVAILABLE = True
except ImportError:
    # Define minimal stubs if hanzo-agents is not available
    HANZO_AGENTS_AVAILABLE = False

    class Agent:
        pass

    class State:
        pass

    class Network:
        pass

    class Tool:
        pass

    class History:
        pass

    class ModelRegistry:
        pass

    class InferenceResult:
        pass

    class ToolCall:
        pass

    class Router:
        pass


# Import optional components with fallbacks
try:
    from hanzo_agents import LLMRouter, HybridRouter, DeterministicRouter
except ImportError:
    try:
        # Try core module import
        from hanzo_agents.core.router import (
            LLMRouter,
            HybridRouter,
            DeterministicRouter,
        )
    except ImportError:
        # Define stubs if not available
        class DeterministicRouter:
            pass

        class LLMRouter:
            pass

        class HybridRouter:
            pass


try:
    from hanzo_agents import create_memory_kv, create_memory_vector
except ImportError:
    try:
        # Try core module import
        from hanzo_agents.core.memory import create_memory_kv, create_memory_vector
    except ImportError:
        # Define stubs if not available
        def create_memory_kv(*args, **kwargs):
            pass

        def create_memory_vector(*args, **kwargs):
            pass


try:
    from hanzo_agents import sequential_router, conditional_router, state_based_router
except ImportError:
    try:
        # Try core module import
        from hanzo_agents.core.router import (
            sequential_router,
            conditional_router,
            state_based_router,
        )
    except ImportError:
        # Define stubs if not available
        def sequential_router(*args, **kwargs):
            pass

        def conditional_router(*args, **kwargs):
            pass

        def state_based_router(*args, **kwargs):
            pass


try:
    from hanzo_agents.core.cli_agent import (
        GrokAgent,
        GeminiAgent,
        ClaudeCodeAgent,
        OpenAICodexAgent,
    )
except ImportError:
    # Define stub classes if not available
    class ClaudeCodeAgent(Agent):
        pass

    class OpenAICodexAgent(Agent):
        pass

    class GeminiAgent(Agent):
        pass

    class GrokAgent(Agent):
        pass


from hanzo_mcp.tools.jupyter import get_read_only_jupyter_tools
from hanzo_mcp.tools.filesystem import Edit, MultiEdit, get_read_only_filesystem_tools
from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.agent.agent_tool import MCPAgent
from hanzo_mcp.tools.common.batch_tool import BatchTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class AgentNode(TypedDict):
    """Node in the agent network."""

    id: str
    query: str
    model: Optional[str]
    role: Optional[str]
    connections: Optional[List[str]]
    receives_from: Optional[List[str]]
    file_path: Optional[str]


class SwarmConfig(TypedDict):
    """Configuration for an agent network."""

    agents: Dict[str, AgentNode]
    entry_point: Optional[str]
    topology: Optional[str]


class SwarmToolParams(TypedDict):
    """Parameters for the SwarmTool."""

    config: SwarmConfig
    query: str
    context: Optional[str]
    max_concurrent: Optional[int]
    use_memory: Optional[bool]
    memory_backend: Optional[str]


class SwarmState(State):
    """State for swarm execution."""

    def __init__(self, config: SwarmConfig, initial_query: str, context: Optional[str] = None):
        """Initialize swarm state."""
        super().__init__()
        self.config = config
        self.initial_query = initial_query
        self.context = context
        self.agent_results = {}
        self.completed_agents = set()
        self.current_agent = None
        self.execution_order = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "config": self.config,
                "initial_query": self.initial_query,
                "context": self.context,
                "agent_results": self.agent_results,
                "completed_agents": list(self.completed_agents),
                "current_agent": self.current_agent,
                "execution_order": self.execution_order,
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwarmState":
        """Create from dictionary."""
        state = cls(
            config=data.get("config", {}),
            initial_query=data.get("initial_query", ""),
            context=data.get("context"),
        )
        state.agent_results = data.get("agent_results", {})
        state.completed_agents = set(data.get("completed_agents", []))
        state.current_agent = data.get("current_agent")
        state.execution_order = data.get("execution_order", [])
        return state


class SwarmAgent(MCPAgent):
    """Agent that executes within a swarm network."""

    def __init__(
        self,
        agent_id: str,
        agent_config: AgentNode,
        available_tools: List[BaseTool],
        permission_manager: PermissionManager,
        ctx: MCPContext,
        **kwargs,
    ):
        """Initialize swarm agent."""
        # Set name and description from config
        self.name = agent_id
        self.description = agent_config.get("role", f"Agent {agent_id}")
        self.agent_config = agent_config

        # Initialize with specified model
        model = agent_config.get("model")
        if model:
            model = self._normalize_model(model)
        else:
            model = "model://anthropic/claude-3-5-sonnet-20241022"

        super().__init__(
            available_tools=available_tools,
            permission_manager=permission_manager,
            ctx=ctx,
            model=model,
            **kwargs,
        )

    def _normalize_model(self, model: str) -> str:
        """Normalize model names to full format."""
        model_map = {
            "claude-3-5-sonnet": "model://anthropic/claude-3-5-sonnet-20241022",
            "claude-3-opus": "model://anthropic/claude-3-opus-20240229",
            "gpt-4o": "model://openai/gpt-4o",
            "gpt-4": "model://openai/gpt-4",
            "gemini-1.5-pro": "model://google/gemini-1.5-pro",
            "gemini-1.5-flash": "model://google/gemini-1.5-flash",
        }

        # Check if it's already a model:// URI
        if model.startswith("model://"):
            return model

        # Check mapping
        if model in model_map:
            return model_map[model]

        # Assume it's a provider/model format
        if "/" in model:
            return f"model://{model}"

        # Default to anthropic
        return f"model://anthropic/{model}"

    async def run(self, state: SwarmState, history: History, network: Network) -> InferenceResult:
        """Execute the swarm agent."""
        # Build prompt with context
        prompt_parts = []

        # Add role context
        if self.agent_config.get("role"):
            prompt_parts.append(f"Your role: {self.agent_config['role']}")

        # Add shared context
        if state.context:
            prompt_parts.append(f"Context:\n{state.context}")

        # Add inputs from connected agents
        receives_from = self.agent_config.get("receives_from", [])
        if receives_from:
            inputs = {}
            for agent_id in receives_from:
                if agent_id in state.agent_results:
                    inputs[agent_id] = state.agent_results[agent_id]

            if inputs:
                prompt_parts.append("Input from previous agents:")
                for input_agent, input_result in inputs.items():
                    prompt_parts.append(f"\n--- From {input_agent} ---\n{input_result}")

        # Add file context if specified
        if self.agent_config.get("file_path"):
            prompt_parts.append(f"\nFile to work on: {self.agent_config['file_path']}")

        # Add the main query
        prompt_parts.append(f"\nTask: {self.agent_config['query']}")

        # Add initial query if this is entry point
        if state.current_agent == state.config.get("entry_point"):
            prompt_parts.append(f"\nMain objective: {state.initial_query}")

        full_prompt = "\n\n".join(prompt_parts)

        # Execute using base class
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": full_prompt},
        ]

        # Call model
        from hanzo_agents import ModelRegistry

        adapter = ModelRegistry.get_adapter(self.model)
        response = await adapter.chat(messages)

        # Store result in state
        state.agent_results[self.name] = response
        state.completed_agents.add(self.name)
        state.execution_order.append(self.name)

        # Return result
        return InferenceResult(
            agent=self.name,
            content=response,
            metadata={
                "agent_id": self.name,
                "role": self.agent_config.get("role"),
                "connections": self.agent_config.get("connections", []),
            },
        )


class SwarmRouter(DeterministicRouter):
    """Router for swarm agent orchestration."""

    def __init__(self, swarm_config: SwarmConfig):
        """Initialize swarm router."""
        self.swarm_config = swarm_config
        self.agents_config = swarm_config["agents"]
        self.entry_point = swarm_config.get("entry_point")

        # Build dependency graph
        self.dependencies = {}
        self.dependents = {}

        for agent_id, config in self.agents_config.items():
            # Dependencies (agents this one waits for)
            self.dependencies[agent_id] = set(config.get("receives_from", []))

            # Dependents (agents that wait for this one)
            connections = config.get("connections", [])
            for conn in connections:
                if conn not in self.dependents:
                    self.dependents[conn] = set()
                self.dependents[conn].add(agent_id)

    def route(self, network, call_count, last_result, agent_stack):
        """Determine next agent to execute."""
        state = network.state

        # First call - start with entry point or roots
        if call_count == 0:
            if self.entry_point:
                state.current_agent = self.entry_point
                return self._get_agent_class(self.entry_point, agent_stack)
            else:
                # Find roots (no dependencies)
                roots = [aid for aid, deps in self.dependencies.items() if not deps]
                if roots:
                    state.current_agent = roots[0]
                    return self._get_agent_class(roots[0], agent_stack)

        # Find next agent to execute
        for agent_id in self.agents_config:
            if agent_id in state.completed_agents:
                continue

            # Check if all dependencies are met
            deps = self.dependencies.get(agent_id, set())
            if deps.issubset(state.completed_agents):
                state.current_agent = agent_id
                return self._get_agent_class(agent_id, agent_stack)

        # No more agents to execute
        return None

    def _get_agent_class(self, agent_id: str, agent_stack: List[type[Agent]]) -> type[Agent]:
        """Get agent class for given agent ID."""
        # Find matching agent by name
        for agent_class in agent_stack:
            if hasattr(agent_class, "name") and agent_class.name == agent_id:
                return agent_class

        # Not found - this shouldn't happen
        return None


@final
class SwarmTool(BaseTool):
    """Tool for executing agent networks using hanzo-agents SDK."""

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
- Memory and state management via hanzo-agents SDK

Common Topologies:
1. Tree (Architect pattern):
   architect → [frontend, backend, database] → reviewer

2. Pipeline (Sequential processing):
   analyzer → planner → implementer → tester → reviewer

3. Star (Central coordinator):
   coordinator ← → [agent1, agent2, agent3, agent4]

4. DAG (Complex dependencies):
   Multiple agents with custom connections

Models can be specified as:
- Full: 'anthropic/claude-3-5-sonnet-20241022'
- Short: 'claude-3-5-sonnet', 'gpt-4o', 'gemini-1.5-pro'
- CLI tools: 'claude_cli', 'codex_cli', 'gemini_cli', 'grok_cli'
- Model URIs: 'model://anthropic/claude-3-opus'
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
        """Initialize the swarm tool."""
        self.permission_manager = permission_manager
        # Default to latest Claude Sonnet if no model specified
        from hanzo_mcp.tools.agent.code_auth import get_latest_claude_model

        self.model = model or f"anthropic/{get_latest_claude_model()}"
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.agent_max_iterations = agent_max_iterations
        self.agent_max_tool_uses = agent_max_tool_uses

        # Set up available tools for agents
        self.available_tools: list[BaseTool] = []
        self.available_tools.extend(get_read_only_filesystem_tools(self.permission_manager))
        self.available_tools.extend(get_read_only_jupyter_tools(self.permission_manager))

        # Add edit tools
        self.available_tools.append(Edit(self.permission_manager))
        self.available_tools.append(MultiEdit(self.permission_manager))

        # Add batch tool
        self.available_tools.append(BatchTool({t.name: t for t in self.available_tools}))

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[SwarmToolParams],
    ) -> str:
        """Execute the swarm tool."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Extract parameters
        config = params.get("config", {})
        initial_query = params.get("query", "")
        context = params.get("context", "")
        max_concurrent = params.get("max_concurrent", 10)
        use_memory = params.get("use_memory", False)
        memory_backend = params.get("memory_backend", "sqlite")

        agents_config = config.get("agents", {})

        if not agents_config:
            await tool_ctx.error("No agents provided")
            return "Error: At least one agent must be provided."

        # hanzo-agents SDK is required (already imported above)

        await tool_ctx.info(f"Starting swarm execution with {len(agents_config)} agents using hanzo-agents SDK")

        # Create state
        state = SwarmState(config=config, initial_query=initial_query, context=context)

        # Create agent classes dynamically
        agent_classes = []
        for agent_id, agent_config in agents_config.items():
            # Check for CLI agents
            model = agent_config.get("model", self.model)

            cli_agents = {
                "claude_cli": ClaudeCodeAgent,
                "codex_cli": OpenAICodexAgent,
                "gemini_cli": GeminiAgent,
                "grok_cli": GrokAgent,
            }

            if model in cli_agents:
                # Use CLI agent
                agent_class = type(
                    f"Swarm{agent_id}",
                    (cli_agents[model],),
                    {
                        "name": agent_id,
                        "description": agent_config.get("role", f"Agent {agent_id}"),
                        "agent_config": agent_config,
                    },
                )
            else:
                # Create dynamic SwarmAgent class
                agent_class = type(
                    f"Swarm{agent_id}",
                    (SwarmAgent,),
                    {
                        "name": agent_id,
                        "__init__": lambda self, aid=agent_id, acfg=agent_config: SwarmAgent.__init__(
                            self,
                            agent_id=aid,
                            agent_config=acfg,
                            available_tools=self.available_tools,
                            permission_manager=self.permission_manager,
                            ctx=ctx,
                        ),
                    },
                )

            agent_classes.append(agent_class)

        # Create memory if requested
        memory_kv = None
        memory_vector = None
        if use_memory:
            memory_kv = create_memory_kv(memory_backend)
            memory_vector = create_memory_vector("simple")

        # Create router
        router = SwarmRouter(config)

        # Create network
        network = Network(
            state=state,
            agents=agent_classes,
            router=router,
            memory_kv=memory_kv,
            memory_vector=memory_vector,
            max_steps=self.agent_max_iterations * len(agents_config),
        )

        # Execute
        try:
            final_state = await network.run()

            # Format results
            return self._format_network_results(
                agents_config,
                final_state.agent_results,
                final_state.execution_order,
                config.get("entry_point"),
            )

        except Exception as e:
            await tool_ctx.error(f"Swarm execution failed: {str(e)}")
            return f"Error: {str(e)}"

    def _format_network_results(
        self,
        agents_config: Dict[str, Any],
        results: Dict[str, str],
        execution_order: List[str],
        entry_point: Optional[str],
    ) -> str:
        """Format results from agent network execution."""
        output = ["Agent Network Execution Results (hanzo-agents SDK)"]
        output.append("=" * 80)
        output.append(f"Total agents: {len(agents_config)}")
        output.append(f"Completed: {len(results)}")
        output.append(f"Failed: {len([r for r in results.values() if r.startswith('Error:')])}")

        if entry_point:
            output.append(f"Entry point: {entry_point}")

        output.append(f"\nExecution Order: {' → '.join(execution_order)}")
        output.append("-" * 40)

        # Detailed results
        output.append("\n\nDetailed Results:")
        output.append("=" * 80)

        for agent_id in execution_order:
            if agent_id in results:
                config = agents_config.get(agent_id, {})
                role = config.get("role", "Agent")
                model = config.get("model", "default")

                output.append(f"\n### {agent_id} ({role}) [{model}]")
                output.append("-" * 40)

                result = results[agent_id]
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
            use_memory: bool = False,
            memory_backend: str = "sqlite",
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
                use_memory=use_memory,
                memory_backend=memory_backend,
            )
