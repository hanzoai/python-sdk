"""Agent tool - multi-agent orchestration.

Lightweight agent spawning with DAG execution, work distribution (swarm),
and Metastable consensus protocol.

Consensus: https://github.com/luxfi/consensus
"""

import os
import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Annotated, final, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_metastable_consensus import Consensus as MetastableConsensus
from hanzo_metastable_consensus import Result as ConsensusResult
from hanzo_metastable_consensus import run as run_consensus


Action = Annotated[
    Literal[
        "run",        # Run single agent
        "dag",        # DAG execution with dependencies
        "swarm",      # Work distribution across agents
        "consensus",  # Metastable multi-model consensus
        "dispatch",   # Different agents for different tasks
        "list",       # List available agents
        "status",     # Check agent availability
        "config",     # Show configuration
    ],
    Field(description="Agent action"),
]


@dataclass
class Result:
    """Agent execution result."""
    agent: str
    prompt: str
    output: str
    ok: bool
    error: Optional[str] = None
    item: Optional[str] = None
    id: Optional[str] = None
    round: int = 0
    ms: int = 0
    lux: float = 1.0  # Luminance (Photon) - faster agents get higher weight





# Agent configurations
# Format: {name: AgentConfig}
# AgentConfig: (command, args, env_key, priority, base_url, auth_env)
# For Anthropic-compatible APIs: base_url + auth_env override ANTHROPIC_BASE_URL/ANTHROPIC_AUTH_TOKEN

@dataclass
class AgentConfig:
    """Agent configuration."""
    cmd: str
    args: List[str] = field(default_factory=list)
    env_key: Optional[str] = None
    priority: int = 10
    base_url: Optional[str] = None  # Anthropic-compatible base URL
    auth_env: Optional[str] = None  # Env var for auth token (uses this instead of ANTHROPIC_API_KEY)
    model: Optional[str] = None     # Model name override


# Native CLI agents
NATIVE_AGENTS = {
    "claude": AgentConfig("claude", ["-p"], "ANTHROPIC_API_KEY", 1),
    "codex": AgentConfig("codex", [], "OPENAI_API_KEY", 2),
    "gemini": AgentConfig("gemini", [], "GOOGLE_API_KEY", 3),
    "grok": AgentConfig("grok", [], "XAI_API_KEY", 4),
    "qwen": AgentConfig("qwen", [], "DASHSCOPE_API_KEY", 5),
    "vibe": AgentConfig("vibe", [], None, 6),
    "dev": AgentConfig("hanzo-dev", [], None, 8),
}

# Anthropic-compatible API agents (use claude CLI with custom base URL)
ANTHROPIC_COMPAT_AGENTS = {
    # MiniMax M2.1 - https://api.minimax.io
    "minimax": AgentConfig(
        "claude", ["-p"], None, 10,
        base_url="https://api.minimax.io/anthropic",
        auth_env="MINIMAX_API_KEY",
        model="MiniMax-M2.1",
    ),
    # Kimi K2 (Moonshot) - https://api.moonshot.cn
    "kimi": AgentConfig(
        "claude", ["-p"], None, 11,
        base_url="https://api.moonshot.cn/anthropic",
        auth_env="MOONSHOT_API_KEY",
        model="kimi-k2",
    ),
    # DeepSeek - https://api.deepseek.com
    "deepseek": AgentConfig(
        "claude", ["-p"], None, 12,
        base_url="https://api.deepseek.com/anthropic",
        auth_env="DEEPSEEK_API_KEY",
        model="deepseek-chat",
    ),
    # Yi/01.AI - https://api.01.ai
    "yi": AgentConfig(
        "claude", ["-p"], None, 13,
        base_url="https://api.01.ai/anthropic",
        auth_env="YI_API_KEY",
        model="yi-large",
    ),
    # Zhipu GLM-4 - https://open.bigmodel.cn
    "glm": AgentConfig(
        "claude", ["-p"], None, 14,
        base_url="https://open.bigmodel.cn/api/paas/v4/anthropic",
        auth_env="ZHIPU_API_KEY",
        model="glm-4",
    ),
    # Baichuan - https://api.baichuan-ai.com
    "baichuan": AgentConfig(
        "claude", ["-p"], None, 15,
        base_url="https://api.baichuan-ai.com/anthropic",
        auth_env="BAICHUAN_API_KEY",
        model="Baichuan4",
    ),
    # StepFun - https://api.stepfun.com
    "step": AgentConfig(
        "claude", ["-p"], None, 16,
        base_url="https://api.stepfun.com/anthropic",
        auth_env="STEPFUN_API_KEY",
        model="step-2",
    ),
    # Qwen via DashScope Claude Code proxy - https://dashscope-intl.aliyuncs.com
    "dashscope": AgentConfig(
        "claude", ["-p"], None, 17,
        base_url="https://dashscope-intl.aliyuncs.com/api/v2/apps/claude-code-proxy",
        auth_env="DASHSCOPE_API_KEY",
        model="qwen-max",
    ),
    # Qwen via DashScope (alias)
    "qwen-cc": AgentConfig(
        "claude", ["-p"], None, 18,
        base_url="https://dashscope-intl.aliyuncs.com/api/v2/apps/claude-code-proxy",
        auth_env="DASHSCOPE_API_KEY",
        model="qwen-plus",
    ),
}

# Combined agents dict
AGENTS = {**NATIVE_AGENTS, **ANTHROPIC_COMPAT_AGENTS}


def detect_env() -> Dict[str, Any]:
    """Detect Claude Code environment."""
    result = {"in_claude": False, "session": None, "api_key": None}
    
    if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_SESSION_ID"):
        result["in_claude"] = True
        result["session"] = os.environ.get("CLAUDE_SESSION_ID")
    
    if os.environ.get("ANTHROPIC_API_KEY"):
        result["api_key"] = os.environ.get("ANTHROPIC_API_KEY")[:8] + "..."
    
    return result


def get_mcp_env() -> Dict[str, str]:
    """Get MCP environment to share with agents."""
    env = {}
    keys = [
        "HANZO_MCP_MODE", "HANZO_MCP_ALLOWED_PATHS", "HANZO_MCP_ENABLED_TOOLS",
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY",
    ]
    for k in keys:
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


@final
class AgentTool(BaseTool):
    """Multi-agent orchestration tool.
    
    Actions:
    - run: Single agent execution (default: claude -p)
    - dag: DAG execution with dependencies
    - swarm: Work distribution across parallel agents
    - consensus: Metastable multi-model consensus
    - dispatch: Different agents for different tasks
    """
    
    name = "agent"
    
    def __init__(self):
        super().__init__()
        self._env = detect_env()
        self._mcp_env = get_mcp_env()
    
    @property
    @override
    def description(self) -> str:
        default = self._default_agent()
        native = ', '.join(NATIVE_AGENTS.keys())
        compat = ', '.join(ANTHROPIC_COMPAT_AGENTS.keys())
        return f"""Multi-agent orchestration. Default: {default}

Actions:
- run: Execute single agent (default: {default})
- dag: DAG execution with dependencies
- swarm: Work distribution across N agents
- consensus: Lux Quasar multi-model agreement
- dispatch: Different agents for different tasks
- list/status/config: Management

Native: {native}
Anthropic-compatible: {compat}

Examples:
  agent run --prompt "Explain this code"
  agent run --name minimax --prompt "Analyze with MiniMax"
  agent dag --tasks '[{{"id":"a","prompt":"analyze"}},{{"id":"b","prompt":"fix {{a}}","after":["a"]}}]'
  agent swarm --items '["f1.py","f2.py"]' --template "Review {{item}}" --max_concurrent 10
  agent consensus --prompt "Best approach?" --agents '["claude","minimax","deepseek"]' --rounds 3
  agent dispatch --tasks '[{{"agent":"claude","prompt":"review"}},{{"agent":"kimi","prompt":"test"}}]'

Consensus: https://github.com/luxfi/consensus
"""
    
    def _default_agent(self) -> str:
        """Get default agent based on environment."""
        if self._env.get("in_claude"):
            return "claude"
        # Check native agents first by priority
        for name, cfg in sorted(NATIVE_AGENTS.items(), key=lambda x: x[1].priority):
            if cfg.env_key and os.environ.get(cfg.env_key):
                return name
        # Then check Anthropic-compatible agents
        for name, cfg in sorted(ANTHROPIC_COMPAT_AGENTS.items(), key=lambda x: x[1].priority):
            if cfg.auth_env and os.environ.get(cfg.auth_env):
                return name
        return "dev"
    
    @override
    @auto_timeout("agent")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "run",
        # run/dispatch
        name: Optional[str] = None,
        prompt: Optional[str] = None,
        cwd: Optional[str] = None,
        timeout: int = 300,
        # dag
        tasks: Optional[List[Dict]] = None,
        # swarm
        items: Optional[List[str]] = None,
        template: Optional[str] = None,
        max_concurrent: int = 100,
        # consensus
        agents: Optional[List[str]] = None,
        rounds: int = 3,
        k: int = 3,
        alpha: float = 0.6,
        beta_1: float = 0.5,
        beta_2: float = 0.8,
        **kwargs,
    ) -> str:
        """Execute agent action."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)
        
        if action == "list":
            return self._list()
        elif action == "status":
            return await self._status(name)
        elif action == "config":
            return self._config()
        elif action == "run":
            agent = name or self._default_agent()
            return await self._run(agent, prompt, cwd, timeout)
        elif action == "dag":
            return await self._dag(tasks or [], name, cwd, timeout)
        elif action == "swarm":
            return await self._swarm(items or [], template or "", name, max_concurrent, cwd, timeout)
        elif action == "consensus":
            return await self._consensus(prompt or "", agents or ["claude", "gemini", "codex"], rounds, k, alpha, beta_1, beta_2, cwd, timeout)
        elif action == "dispatch":
            return await self._dispatch(tasks or [], cwd, timeout)
        else:
            return f"Unknown action: {action}. Use: run, dag, swarm, consensus, dispatch, list, status, config"
    
    def _list(self) -> str:
        """List available agents."""
        default = self._default_agent()
        lines = ["Agents:"]
        
        # Native agents
        lines.append("  Native:")
        for name, cfg in sorted(NATIVE_AGENTS.items(), key=lambda x: x[1].priority):
            mark = " (default)" if name == default else ""
            lines.append(f"    • {name}: {cfg.cmd}{mark}")
        
        # Anthropic-compatible agents
        lines.append("  Anthropic-compatible:")
        for name, cfg in sorted(ANTHROPIC_COMPAT_AGENTS.items(), key=lambda x: x[1].priority):
            has_key = bool(cfg.auth_env and os.environ.get(cfg.auth_env))
            key_mark = " ✓" if has_key else ""
            lines.append(f"    • {name}: {cfg.model}{key_mark}")
        
        lines.append("")
        lines.append("Actions: run, dag, swarm, consensus, dispatch")
        if self._env.get("in_claude"):
            lines.append("⚡ Running in Claude Code")
        return "\n".join(lines)
    
    def _config(self) -> str:
        """Show configuration."""
        lines = [
            f"Default: {self._default_agent()}",
            f"In Claude: {self._env.get('in_claude', False)}",
        ]
        if self._env.get("session"):
            lines.append(f"Session: {self._env['session'][:8]}...")
        lines.append("")
        lines.append("MCP env shared with agents:")
        for k, v in self._mcp_env.items():
            display = v[:8] + "..." if "KEY" in k else v
            lines.append(f"  {k}: {display}")
        return "\n".join(lines)
    
    async def _status(self, name: Optional[str]) -> str:
        """Check agent availability."""
        if name:
            if name not in AGENTS:
                return f"Unknown: {name}. Available: {', '.join(AGENTS.keys())}"
            cfg = AGENTS[name]
            ok = await self._available(cfg.cmd)
            # For Anthropic-compat, check auth_env; for native, check env_key
            env_to_check = cfg.auth_env or cfg.env_key
            has_key = bool(env_to_check and os.environ.get(env_to_check))
            return f"{'✓' if ok else '✗'} {name} ({'✓ key' if has_key else '○ no key'})"
        
        lines = ["Status:"]
        
        # Native agents
        lines.append("  Native:")
        for agent, cfg in sorted(NATIVE_AGENTS.items(), key=lambda x: x[1].priority):
            ok = await self._available(cfg.cmd)
            has_key = bool(cfg.env_key and os.environ.get(cfg.env_key))
            key_status = "✓ key" if has_key else "○ no key"
            status = f"✓ ({key_status})" if ok else "✗ not found"
            lines.append(f"    {agent}: {status}")
        
        # Anthropic-compatible agents
        lines.append("  Anthropic-compatible (via claude):")
        claude_ok = await self._available("claude")
        for agent, cfg in sorted(ANTHROPIC_COMPAT_AGENTS.items(), key=lambda x: x[1].priority):
            has_key = bool(cfg.auth_env and os.environ.get(cfg.auth_env))
            if claude_ok and has_key:
                status = f"✓ ready ({cfg.model})"
            elif claude_ok:
                status = f"○ need {cfg.auth_env}"
            else:
                status = "✗ need claude CLI"
            lines.append(f"    {agent}: {status}")
        
        return "\n".join(lines)
    
    async def _available(self, cmd: str) -> bool:
        """Check if command is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                cmd, "--version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            return proc.returncode == 0
        except Exception:
            return False
    
    async def _exec(self, agent: str, prompt: str, cwd: Optional[str], timeout: int) -> Result:
        """Execute single agent."""
        if agent not in AGENTS:
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=f"Unknown agent: {agent}")
        
        cfg = AGENTS[agent]
        
        # Build command
        full_cmd = [cfg.cmd] + cfg.args
        
        # For Anthropic-compatible APIs, add required flags
        if cfg.base_url:
            full_cmd.append("--dangerously-skip-permissions")
        
        # Add model override for Anthropic-compatible APIs
        if cfg.model:
            full_cmd.extend(["--model", cfg.model])
        
        full_cmd.append(prompt)
        
        # Build environment
        env = os.environ.copy()
        env.update(self._mcp_env)
        env["HANZO_AGENT_PARENT"] = "true"
        env["HANZO_AGENT_NAME"] = agent
        
        # Set Anthropic-compatible API overrides
        if cfg.base_url:
            env["ANTHROPIC_BASE_URL"] = cfg.base_url
        if cfg.auth_env and os.environ.get(cfg.auth_env):
            env["ANTHROPIC_AUTH_TOKEN"] = os.environ[cfg.auth_env]
        
        start = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or os.getcwd(),
                env=env,
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            ms = int((time.time() - start) * 1000)
            output = stdout.decode("utf-8", errors="replace")
            
            if proc.returncode != 0:
                err = stderr.decode("utf-8", errors="replace")
                return Result(agent=agent, prompt=prompt, output=output, ok=False, error=err, ms=ms)
            
            return Result(agent=agent, prompt=prompt, output=output, ok=True, ms=ms)
        
        except asyncio.TimeoutError:
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=f"Timeout after {timeout}s", ms=timeout * 1000)
        except FileNotFoundError:
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=f"{cfg.cmd} not found")
        except Exception as e:
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=str(e))
    
    async def _run(self, agent: str, prompt: Optional[str], cwd: Optional[str], timeout: int) -> str:
        """Run single agent."""
        if not prompt:
            return "Error: prompt required"
        
        result = await self._exec(agent, prompt, cwd, timeout)
        
        if result.ok:
            return f"[{agent}] {result.output}"
        return f"[{agent}] Error: {result.error}\n{result.output}"
    
    async def _dag(self, tasks: List[Dict], name: Optional[str], cwd: Optional[str], timeout: int) -> str:
        """Execute DAG with dependencies.
        
        Tasks: [{id, prompt, agent?, after?: [ids]}]
        Uses topological sort, executes in waves.
        Injects {dep_id} outputs into prompts.
        """
        if not tasks:
            return "Error: tasks required"
        
        agent = name or self._default_agent()
        
        # Build dependency graph
        graph: Dict[str, Dict] = {}
        for t in tasks:
            tid = t.get("id", str(len(graph)))
            graph[tid] = {
                "prompt": t.get("prompt", ""),
                "agent": t.get("agent", agent),
                "after": set(t.get("after", [])),
                "done": False,
                "result": None,
            }
        
        results: List[Result] = []
        outputs: Dict[str, str] = {}
        
        # Execute in waves (topological order)
        while True:
            # Find ready tasks (dependencies satisfied)
            ready = [
                tid for tid, task in graph.items()
                if not task["done"] and task["after"].issubset(set(outputs.keys()))
            ]
            
            if not ready:
                # Check for cycles or completion
                pending = [tid for tid, task in graph.items() if not task["done"]]
                if pending:
                    return f"Error: Dependency cycle or missing deps: {pending}"
                break
            
            # Execute wave in parallel
            wave_tasks = []
            for tid in ready:
                task = graph[tid]
                # Inject dependency outputs into prompt
                prompt = task["prompt"]
                for dep_id, dep_out in outputs.items():
                    prompt = prompt.replace(f"{{{dep_id}}}", dep_out)
                wave_tasks.append((tid, task["agent"], prompt))
            
            wave_results = await asyncio.gather(*[
                self._exec(task_agent, prompt, cwd, timeout)
                for tid, task_agent, prompt in wave_tasks
            ])
            
            for (tid, _, _), result in zip(wave_tasks, wave_results):
                result.id = tid
                results.append(result)
                outputs[tid] = result.output
                graph[tid]["done"] = True
                graph[tid]["result"] = result
        
        # Format results
        lines = [f"DAG completed: {len(results)} tasks"]
        for r in results:
            status = "✓" if r.ok else "✗"
            lines.append(f"  {status} {r.id}: {r.agent} ({r.ms}ms)")
            if not r.ok and r.error:
                lines.append(f"      Error: {r.error}")
        
        lines.append("")
        lines.append("Outputs:")
        for r in results:
            lines.append(f"--- {r.id} ---")
            lines.append(r.output[:500] + ("..." if len(r.output) > 500 else ""))
        
        return "\n".join(lines)
    
    async def _swarm(self, items: List[str], template: str, name: Optional[str], max_concurrent: int, cwd: Optional[str], timeout: int) -> str:
        """Distribute work across agents.
        
        Each item processed once. Uses {item} substitution.
        Semaphore controls max concurrency.
        """
        if not items:
            return "Error: items required"
        if not template:
            return "Error: template required (use {item} for substitution)"
        
        agent = name or self._default_agent()
        sem = asyncio.Semaphore(max_concurrent)
        
        async def process(item: str) -> Result:
            async with sem:
                prompt = template.replace("{item}", item)
                result = await self._exec(agent, prompt, cwd, timeout)
                result.item = item
                return result
        
        start = time.time()
        results = await asyncio.gather(*[process(item) for item in items])
        elapsed = time.time() - start
        
        ok = sum(1 for r in results if r.ok)
        fail = len(results) - ok
        
        lines = [
            f"Swarm completed: {len(items)} items in {elapsed:.1f}s",
            f"  Agent: {agent}",
            f"  Success: {ok}, Failed: {fail}",
            f"  Concurrency: {max_concurrent}",
        ]
        
        if fail > 0:
            lines.append("")
            lines.append("Failures:")
            for r in results:
                if not r.ok:
                    lines.append(f"  ✗ {r.item}: {r.error}")
        
        return "\n".join(lines)
    
    async def _consensus(self, prompt: str, agents: List[str], rounds: int, k: int, alpha: float, beta_1: float, beta_2: float, cwd: Optional[str], timeout: int) -> str:
        """Metastable consensus. https://github.com/luxfi/consensus"""
        if not prompt:
            return "Error: prompt required"
        if not agents:
            return "Error: agents required"
        
        # Executor adapter
        async def execute(agent_id: str, agent_prompt: str) -> ConsensusResult:
            result = await self._exec(agent_id, agent_prompt, cwd, timeout)
            return ConsensusResult(
                id=result.agent,
                output=result.output,
                ok=result.ok,
                error=result.error,
                ms=result.ms,
            )
        
        start = time.time()
        state = await run_consensus(
            prompt=prompt,
            participants=agents,
            execute=execute,
            rounds=rounds,
            k=k,
            alpha=alpha,
            beta_1=beta_1,
            beta_2=beta_2,
        )
        elapsed = time.time() - start
        
        return f"[Metastable] {elapsed:.1f}s, winner: {state.winner}, finalized: {state.finalized}\n\n{state.synthesis or ''}"
    
    async def _dispatch(self, tasks: List[Dict], cwd: Optional[str], timeout: int) -> str:
        """Execute different agents for different tasks in parallel.
        
        Tasks: [{agent, prompt}]
        """
        if not tasks:
            return "Error: tasks required"
        
        async def run_task(t: Dict) -> Result:
            agent = t.get("agent", self._default_agent())
            prompt = t.get("prompt", "")
            return await self._exec(agent, prompt, cwd, timeout)
        
        results = await asyncio.gather(*[run_task(t) for t in tasks])
        
        lines = [f"Dispatched: {len(tasks)} tasks"]
        for i, r in enumerate(results):
            status = "✓" if r.ok else "✗"
            lines.append(f"  {status} Task {i+1}: {r.agent} ({r.ms}ms)")
        
        lines.append("")
        for i, r in enumerate(results):
            lines.append(f"--- Task {i+1} ({r.agent}) ---")
            if r.ok:
                lines.append(r.output[:500] + ("..." if len(r.output) > 500 else ""))
            else:
                lines.append(f"Error: {r.error}")
        
        return "\n".join(lines)
    
    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool = self
        
        @mcp_server.tool()
        async def agent(
            action: Action = "run",
            name: Annotated[Optional[str], Field(description="Agent: claude, codex, gemini, grok, qwen, dev")] = None,
            prompt: Annotated[Optional[str], Field(description="Prompt for run/consensus")] = None,
            cwd: Annotated[Optional[str], Field(description="Working directory")] = None,
            timeout: Annotated[int, Field(description="Timeout seconds")] = 300,
            tasks: Annotated[Optional[List[Dict]], Field(description="Tasks for dag/dispatch")] = None,
            items: Annotated[Optional[List[str]], Field(description="Items for swarm")] = None,
            template: Annotated[Optional[str], Field(description="Template for swarm ({item})")] = None,
            max_concurrent: Annotated[int, Field(description="Max concurrency for swarm")] = 100,
            agents: Annotated[Optional[List[str]], Field(description="Agents for consensus")] = None,
            rounds: Annotated[int, Field(description="Consensus rounds")] = 3,
            k: Annotated[int, Field(description="Sample size per round")] = 3,
            alpha: Annotated[float, Field(description="Agreement threshold")] = 0.6,
            beta_1: Annotated[float, Field(description="Preference threshold")] = 0.5,
            beta_2: Annotated[float, Field(description="Decision threshold")] = 0.8,
            ctx: MCPContext = None,
        ) -> str:
            """Multi-agent orchestration: run, dag, swarm, consensus, dispatch.
            
            Consensus: https://github.com/luxfi/consensus
            """
            return await tool.call(
                ctx,
                action=action,
                name=name,
                prompt=prompt,
                cwd=cwd,
                timeout=timeout,
                tasks=tasks,
                items=items,
                template=template,
                max_concurrent=max_concurrent,
                agents=agents,
                rounds=rounds,
                k=k,
                alpha=alpha,
                beta_1=beta_1,
                beta_2=beta_2,
            )
