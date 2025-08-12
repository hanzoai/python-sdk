"""Agent tool implementation using hanzo-agents SDK.

This module implements the AgentTool that leverages the hanzo-agents SDK
for sophisticated agent orchestration and execution.
"""

import re
import time
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

# Import hanzo-agents SDK
try:
    from hanzo_agents import (
        Tool,
        Agent,
        State,
        History,
        Network,
        InferenceResult,
        create_memory_kv,
        sequential_router,
        create_memory_vector,
    )
    from hanzo_agents.core.cli_agent import (
        GrokAgent,
        GeminiAgent,
        ClaudeCodeAgent,
        OpenAICodexAgent,
    )

    HANZO_AGENTS_AVAILABLE = True
except ImportError:
    HANZO_AGENTS_AVAILABLE = False

    # Define stub classes when hanzo-agents is not available
    class State:
        """Stub State class when hanzo-agents is not available."""

        def __init__(self):
            pass

        def to_dict(self):
            return {}

        @classmethod
        def from_dict(cls, data):
            return cls()

    class Tool:
        """Stub Tool class when hanzo-agents is not available."""

        pass

    class Agent:
        """Stub Agent class when hanzo-agents is not available."""

        pass

    class Network:
        """Stub Network class when hanzo-agents is not available."""

        pass

    class History:
        """Stub History class when hanzo-agents is not available."""

        pass

    class InferenceResult:
        """Stub InferenceResult class when hanzo-agents is not available."""

        def __init__(self, agent=None, content=None, metadata=None):
            self.agent = agent
            self.content = content
            self.metadata = metadata or {}


from hanzo_mcp.tools.jupyter import get_read_only_jupyter_tools
from hanzo_mcp.tools.filesystem import Edit, MultiEdit, get_read_only_filesystem_tools
from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.agent.critic_tool import CriticTool
from hanzo_mcp.tools.agent.iching_tool import IChingTool
from hanzo_mcp.tools.agent.review_tool import ReviewTool
from hanzo_mcp.tools.common.batch_tool import BatchTool
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.clarification_tool import ClarificationTool
from hanzo_mcp.tools.agent.clarification_protocol import (
    AgentClarificationMixin,
)


class AgentToolParams(TypedDict, total=False):
    """Parameters for the AgentTool."""

    prompts: str | list[str]
    model: Optional[str]
    use_memory: Optional[bool]
    memory_backend: Optional[str]


class MCPAgentState(State):
    """State for MCP agents."""

    def __init__(self, prompts: List[str], context: Dict[str, Any]):
        """Initialize agent state."""
        super().__init__()
        self.prompts = prompts
        self.context = context
        self.current_prompt_index = 0
        self.results = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "prompts": self.prompts,
                "context": self.context,
                "current_prompt_index": self.current_prompt_index,
                "results": self.results,
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPAgentState":
        """Create from dictionary."""
        state = cls(prompts=data.get("prompts", []), context=data.get("context", {}))
        state.current_prompt_index = data.get("current_prompt_index", 0)
        state.results = data.get("results", [])
        for k, v in data.items():
            if k not in ["prompts", "context", "current_prompt_index", "results"]:
                state[k] = v
        return state


class MCPToolAdapter(Tool):
    """Adapter to wrap MCP tools for hanzo-agents."""

    def __init__(self, mcp_tool: BaseTool, ctx: MCPContext):
        """Initialize adapter."""
        self.mcp_tool = mcp_tool
        self.ctx = ctx

    @property
    def name(self) -> str:
        """Get tool name."""
        return self.mcp_tool.name

    @property
    def description(self) -> str:
        """Get tool description."""
        return self.mcp_tool.description

    async def execute(self, **kwargs) -> str:
        """Execute the MCP tool."""
        return await self.mcp_tool.call(self.ctx, **kwargs)


class MCPAgent(Agent):
    """Agent that executes MCP tasks."""

    name = "mcp_agent"
    description = "Agent for executing MCP tasks"

    def __init__(
        self,
        available_tools: List[BaseTool],
        permission_manager: PermissionManager,
        ctx: MCPContext,
        model: str = "model://anthropic/claude-3-5-sonnet-20241022",
        **kwargs,
    ):
        """Initialize MCP agent."""
        super().__init__(model=model, **kwargs)

        self.available_tools = available_tools
        self.permission_manager = permission_manager
        self.ctx = ctx

        # Register MCP tools as agent tools
        for mcp_tool in available_tools:
            adapter = MCPToolAdapter(mcp_tool, ctx)
            self.register_tool(adapter)

    async def run(
        self, state: MCPAgentState, history: History, network: Network
    ) -> InferenceResult:
        """Execute the agent."""
        # Get current prompt
        if state.current_prompt_index >= len(state.prompts):
            return InferenceResult(
                agent=self.name,
                content="All prompts completed",
                metadata={"completed": True},
            )

        prompt = state.prompts[state.current_prompt_index]

        # Execute with tools
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt},
        ]

        # Add history context
        for entry in history[-10:]:
            if entry.role == "assistant":
                messages.append({"role": "assistant", "content": entry.content})
            elif entry.role == "user":
                messages.append({"role": "user", "content": entry.content})

        # Call model
        from hanzo_agents import ModelRegistry

        adapter = ModelRegistry.get_adapter(self.model)
        response = await adapter.chat(messages)

        # Update state
        state.current_prompt_index += 1
        state.results.append(response)

        # Return result
        return InferenceResult(
            agent=self.name,
            content=response,
            metadata={
                "prompt_index": state.current_prompt_index - 1,
                "total_prompts": len(state.prompts),
            },
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        tool_descriptions = []
        for tool in self.tools.values():
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return f"""You are an AI assistant with access to the following tools:

{chr(10).join(tool_descriptions)}

When you need to use a tool, respond with:
TOOL: tool_name(arg1="value1", arg2="value2")

Important guidelines:
- Always include absolute paths starting with / when working with files
- Be thorough in your searches and analysis
- Provide clear, actionable results
- Edit files when requested to make changes
"""


@final
class AgentTool(AgentClarificationMixin, BaseTool):
    """Tool for delegating tasks to sub-agents using hanzo-agents SDK."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "agent"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        if not HANZO_AGENTS_AVAILABLE:
            return "Agent tool (hanzo-agents SDK not available - using fallback)"

        at = [t.name for t in self.available_tools]
        return f"""Launch a new agent that has access to the following tools: {at}.

When to use the Agent tool:
- If you are searching for a keyword like "config" or "logger"
- When you need to perform edits across multiple files
- When you need to delegate complex file modification tasks

When NOT to use the Agent tool:
- If you want to read a specific file path
- If you are searching for a specific class definition
- Writing code and running bash commands
- Other tasks that are not related to searching

Usage notes:
1. Launch multiple agents concurrently whenever possible
2. Agent results are not visible to the user - summarize them
3. Each agent invocation is stateless
4. The agent's outputs should generally be trusted
5. Clearly tell the agent whether you expect it to write code or just do research"""

    def __init__(
        self,
        permission_manager: PermissionManager,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int | None = None,
        max_iterations: int = 10,
        max_tool_uses: int = 30,
    ) -> None:
        """Initialize the agent tool."""
        self.permission_manager = permission_manager
        self.model_override = model
        self.api_key_override = api_key
        self.base_url_override = base_url
        self.max_tokens_override = max_tokens
        self.max_iterations = max_iterations
        self.max_tool_uses = max_tool_uses

        # Set up available tools
        self.available_tools: list[BaseTool] = []
        self.available_tools.extend(
            get_read_only_filesystem_tools(self.permission_manager)
        )
        self.available_tools.extend(
            get_read_only_jupyter_tools(self.permission_manager)
        )

        # Add edit tools
        self.available_tools.append(Edit(self.permission_manager))
        self.available_tools.append(MultiEdit(self.permission_manager))

        # Add special tools
        self.available_tools.append(ClarificationTool())
        self.available_tools.append(CriticTool())
        self.available_tools.append(ReviewTool())
        self.available_tools.append(IChingTool())

        self.available_tools.append(
            BatchTool({t.name: t for t in self.available_tools})
        )

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[AgentToolParams],
    ) -> str:
        """Execute the tool with the given parameters."""
        start_time = time.time()

        # Create tool context
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Extract parameters
        prompts = params.get("prompts")
        if prompts is None:
            await tool_ctx.error("No prompts provided")
            return "Error: At least one prompt must be provided."

        # Handle both string and list inputs
        if isinstance(prompts, str):
            prompt_list = [prompts]
        elif isinstance(prompts, list):
            if not prompts:
                await tool_ctx.error("Empty prompts list provided")
                return "Error: At least one prompt must be provided."
            prompt_list = prompts
        else:
            await tool_ctx.error("Invalid prompts parameter type")
            return "Error: Parameter 'prompts' must be a string or list of strings."

        # Validate absolute paths
        absolute_path_pattern = r"/(?:[^/\s]+/)*[^/\s]+"
        for prompt in prompt_list:
            if not re.search(absolute_path_pattern, prompt):
                await tool_ctx.error(f"Prompt missing absolute path: {prompt[:50]}...")
                return "Error: All prompts must contain at least one absolute path."

        # Require hanzo-agents SDK
        if not HANZO_AGENTS_AVAILABLE:
            await tool_ctx.error("hanzo-agents SDK is required but not available")
            return "Error: hanzo-agents SDK is required for agent tool functionality. Please install it with: pip install hanzo-agents"

        # Use hanzo-agents SDK
        await tool_ctx.info(
            f"Launching {len(prompt_list)} agent(s) using hanzo-agents SDK"
        )

        # Determine model and agent type
        model = params.get("model", self.model_override)
        use_memory = params.get("use_memory", False)
        memory_backend = params.get("memory_backend", "sqlite")

        # Get appropriate agent class
        agent_class = self._get_agent_class(model)

        # Create state
        state = MCPAgentState(
            prompts=prompt_list,
            context={
                "permission_manager": self.permission_manager,
                "api_key": self.api_key_override,
                "base_url": self.base_url_override,
                "max_tokens": self.max_tokens_override,
            },
        )

        # Create memory if requested
        memory_kv = None
        memory_vector = None
        if use_memory:
            memory_kv = create_memory_kv(memory_backend)
            memory_vector = create_memory_vector("simple")

        # Create network
        network = Network(
            state=state,
            agents=[agent_class],
            router=sequential_router([agent_class] * len(prompt_list)),
            memory_kv=memory_kv,
            memory_vector=memory_vector,
            max_steps=self.max_iterations * len(prompt_list),
        )

        # Execute
        try:
            final_state = await network.run()
            execution_time = time.time() - start_time

            # Format results
            results = final_state.results
            if len(results) == 1:
                formatted_result = f"""Agent execution completed in {execution_time:.2f} seconds.

AGENT RESPONSE:
{results[0]}"""
            else:
                formatted_results = []
                for i, result in enumerate(results):
                    formatted_results.append(f"Agent {i + 1} Result:\n{result}")

                formatted_result = f"""Multi-agent execution completed in {execution_time:.2f} seconds ({len(results)} agents).

AGENT RESPONSES:
{chr(10).join(formatted_results)}"""

            await tool_ctx.info(f"Execution completed in {execution_time:.2f}s")
            return formatted_result

        except Exception as e:
            await tool_ctx.error(f"Agent execution failed: {str(e)}")
            return f"Error: {str(e)}"

    def _get_agent_class(self, model: Optional[str]) -> type[Agent]:
        """Get appropriate agent class based on model."""
        if not model:
            model = "model://anthropic/claude-3-5-sonnet-20241022"

        # Check for CLI agents
        cli_agents = {
            "claude_cli": ClaudeCodeAgent,
            "codex_cli": OpenAICodexAgent,
            "gemini_cli": GeminiAgent,
            "grok_cli": GrokAgent,
        }

        if model in cli_agents:
            return cli_agents[model]

        # Return generic MCP agent
        return type(
            "DynamicMCPAgent",
            (MCPAgent,),
            {
                "model": model,
                "__init__": lambda self: MCPAgent.__init__(
                    self,
                    available_tools=self.available_tools,
                    permission_manager=self.permission_manager,
                    ctx=self.ctx,
                    model=model,
                ),
            },
        )

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this agent tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def dispatch_agent(
            prompts: str | list[str],
            ctx: MCPContext,
            model: Optional[str] = None,
            use_memory: bool = False,
            memory_backend: str = "sqlite",
        ) -> str:
            return await tool_self.call(
                ctx,
                prompts=prompts,
                model=model,
                use_memory=use_memory,
                memory_backend=memory_backend,
            )
