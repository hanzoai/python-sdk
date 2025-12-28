"""Agent tool - multi-agent orchestration.

Lightweight agent spawning with DAG execution, work distribution (swarm),
and Metastable consensus protocol.

Supports:
- CLI mode: Spawn claude/gemini/codex/etc CLI tools
- API mode: Direct HTTP calls to OpenAI/Anthropic-compatible endpoints

Consensus: https://github.com/luxfi/consensus
"""

import os
import time
import uuid
import signal
import asyncio
from typing import Any, Dict, List, Literal, Optional, Annotated, final, override
from pathlib import Path
from contextlib import suppress
from dataclasses import field, dataclass

import aiofiles
from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context
from hanzo_tools.shell import ProcessManager

# Optional uvloop for high-performance async
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    HAS_UVLOOP = True
except ImportError:
    HAS_UVLOOP = False

# Optional httpx for API mode
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# Optional consensus import - fallback to local implementation
try:
    from hanzo_consensus import Result as ConsensusResult, Consensus as MetastableConsensus, run as run_consensus
    HAS_CONSENSUS = True
except ImportError:
    HAS_CONSENSUS = False
    MetastableConsensus = None
    ConsensusResult = None
    run_consensus = None


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
    """Agent configuration.
    
    Config files: ~/.hanzo/agents/<name>.json
    Format:
    {
        "cmd": "claude",
        "args": ["--print", "--dangerously-skip-permissions"],
        "env_key": "ANTHROPIC_API_KEY",
        "max_turns": 999,
        "session": true,
        "model": "claude-3-opus",
        "system_prompt": "You are a helpful assistant"
    }
    
    Environment overrides: HANZO_AGENT_<NAME>_ARGS="--flag1 --flag2"
    """
    cmd: str
    args: List[str] = field(default_factory=list)
    env_key: Optional[str] = None
    priority: int = 10
    base_url: Optional[str] = None  # Anthropic-compatible base URL
    auth_env: Optional[str] = None  # Env var for auth token
    model: Optional[str] = None     # Model name override
    max_turns: int = 999            # Max turns per session
    session: bool = False           # Enable session persistence
    session_id: Optional[str] = None  # Resume specific session
    system_prompt: Optional[str] = None  # System prompt to append
    endpoint: Optional[str] = None       # Direct API endpoint (no CLI needed)
    api_type: str = "cli"                # "cli", "openai", "anthropic"


CONFIG_DIR = Path.home() / ".hanzo" / "agents"


def _load_config_file(name: str) -> Optional[Dict[str, Any]]:
    """Load agent config from ~/.hanzo/agents/<name>.json"""
    config_file = CONFIG_DIR / f"{name}.json"
    if config_file.exists():
        try:
            import json
            with open(config_file) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _apply_config(base: AgentConfig, override: Dict[str, Any]) -> AgentConfig:
    """Apply config overrides to base config."""
    return AgentConfig(
        cmd=override.get("cmd", base.cmd),
        args=override.get("args", base.args),
        env_key=override.get("env_key", base.env_key),
        priority=override.get("priority", base.priority),
        base_url=override.get("base_url", base.base_url),
        auth_env=override.get("auth_env", base.auth_env),
        model=override.get("model", base.model),
        max_turns=override.get("max_turns", base.max_turns),
        session=override.get("session", base.session),
        session_id=override.get("session_id", base.session_id),
        system_prompt=override.get("system_prompt", base.system_prompt),
        endpoint=override.get("endpoint", base.endpoint),
        api_type=override.get("api_type", base.api_type),
    )


# Default system prompt for consensus agents - enables MCP communication
CONSENSUS_SYSTEM_PROMPT = """You are participating in a multi-agent consensus protocol.
You have access to hanzo-mcp tools to communicate with other agents.
Use the 'agent' tool to query other participants if needed.
Provide clear, reasoned responses that can be compared and synthesized."""


# Native CLI agents
# YOLO mode: auto-accept, non-interactive, max autonomy
# Each agent configured with its specific flags for autonomous operation
NATIVE_AGENTS = {
    # claude: --dangerously-skip-permissions (YOLO), --print (non-interactive), --output-format text
    "claude": AgentConfig("claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], "ANTHROPIC_API_KEY", 1),
    # codex: --full-auto (auto-approve everything)
    "codex": AgentConfig("codex", ["--full-auto"], "OPENAI_API_KEY", 2),
    # gemini: -y (yolo), -q (quiet/non-interactive)
    "gemini": AgentConfig("gemini", ["-y", "-q"], "GOOGLE_API_KEY", 3),
    # grok: -y (yolo) - assumed similar to others
    "grok": AgentConfig("grok", ["-y"], "XAI_API_KEY", 4),
    # qwen: --approval-mode yolo, -p (prompt mode)
    "qwen": AgentConfig("qwen", ["--approval-mode", "yolo", "-p"], "DASHSCOPE_API_KEY", 5),
    # vibe: --auto-approve, --max-turns 999, -p (prompt)
    "vibe": AgentConfig("vibe", ["--auto-approve", "--max-turns", "999", "-p"], None, 6),
    # hanzo-dev: -y (yolo)
    "dev": AgentConfig("hanzo-dev", ["-y"], None, 8),
}

# Dynamic config overrides
# Priority: 1) ~/.hanzo/agents/<name>.json  2) HANZO_AGENT_<NAME>_ARGS env
def _load_agent_overrides():
    """Load agent config overrides from files and environment."""
    # Ensure config dir exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    all_agents = list(NATIVE_AGENTS.keys())
    # Add compat agents if defined
    if 'ANTHROPIC_COMPAT_AGENTS' in globals():
        all_agents.extend(ANTHROPIC_COMPAT_AGENTS.keys())
    
    for name in all_agents:
        # Get base config
        if name in NATIVE_AGENTS:
            base = NATIVE_AGENTS[name]
            target = NATIVE_AGENTS
        elif name in globals().get('ANTHROPIC_COMPAT_AGENTS', {}):
            base = ANTHROPIC_COMPAT_AGENTS[name]
            target = ANTHROPIC_COMPAT_AGENTS
        else:
            continue
        
        # 1) Load from config file
        if file_config := _load_config_file(name):
            base = _apply_config(base, file_config)
        
        # 2) Override from environment
        env_key = f"HANZO_AGENT_{name.upper().replace('-', '_')}_ARGS"
        if env_val := os.environ.get(env_key):
            base = AgentConfig(
                cmd=base.cmd,
                args=env_val.split(),
                env_key=base.env_key,
                priority=base.priority,
                base_url=base.base_url,
                auth_env=base.auth_env,
                model=base.model,
                max_turns=base.max_turns,
                session=base.session,
            )
        
        target[name] = base

# Anthropic-compatible API agents (use claude CLI with custom base URL)
# All use claude CLI with --dangerously-skip-permissions for YOLO mode
ANTHROPIC_COMPAT_AGENTS = {
    # MiniMax M2.1 - https://api.minimax.io
    "minimax": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 10,
        base_url="https://api.minimax.io/anthropic",
        auth_env="MINIMAX_API_KEY",
        model="MiniMax-M2.1",
    ),
    # Kimi K2 (Moonshot) - https://api.moonshot.cn
    "kimi": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 11,
        base_url="https://api.moonshot.cn/anthropic",
        auth_env="MOONSHOT_API_KEY",
        model="kimi-k2",
    ),
    # DeepSeek - https://api.deepseek.com
    "deepseek": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 12,
        base_url="https://api.deepseek.com/anthropic",
        auth_env="DEEPSEEK_API_KEY",
        model="deepseek-chat",
    ),
    # Yi/01.AI - https://api.01.ai
    "yi": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 13,
        base_url="https://api.01.ai/anthropic",
        auth_env="YI_API_KEY",
        model="yi-large",
    ),
    # Zhipu GLM-4 - https://open.bigmodel.cn
    "glm": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 14,
        base_url="https://open.bigmodel.cn/api/paas/v4/anthropic",
        auth_env="ZHIPU_API_KEY",
        model="glm-4",
    ),
    # Baichuan - https://api.baichuan-ai.com
    "baichuan": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 15,
        base_url="https://api.baichuan-ai.com/anthropic",
        auth_env="BAICHUAN_API_KEY",
        model="Baichuan4",
    ),
    # StepFun - https://api.stepfun.com
    "step": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 16,
        base_url="https://api.stepfun.com/anthropic",
        auth_env="STEPFUN_API_KEY",
        model="step-2",
    ),
    # Qwen via DashScope Claude Code proxy - https://dashscope-intl.aliyuncs.com
    "dashscope": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 17,
        base_url="https://dashscope-intl.aliyuncs.com/api/v2/apps/claude-code-proxy",
        auth_env="DASHSCOPE_API_KEY",
        model="qwen-max",
    ),
    # Qwen via DashScope (alias)
    "qwen-cc": AgentConfig(
        "claude", ["--print", "--dangerously-skip-permissions", "--output-format", "text"], None, 18,
        base_url="https://dashscope-intl.aliyuncs.com/api/v2/apps/claude-code-proxy",
        auth_env="DASHSCOPE_API_KEY",
        model="qwen-plus",
    ),
}

# Combined agents dict
AGENTS = {**NATIVE_AGENTS, **ANTHROPIC_COMPAT_AGENTS}

# Apply environment overrides at import time
_load_agent_overrides()


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
    """Get MCP environment to share with agents.
    
    Includes hanzo-mcp config so spawned agents can use MCP tools
    and communicate with each other during consensus.
    """
    env = {}
    keys = [
        # Hanzo MCP config
        "HANZO_MCP_MODE", "HANZO_MCP_ALLOWED_PATHS", "HANZO_MCP_ENABLED_TOOLS",
        "HANZO_MCP_SERVER", "HANZO_MCP_TRANSPORT",
        # API keys for various providers
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY",
        "XAI_API_KEY", "DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY",
        "MINIMAX_API_KEY", "MOONSHOT_API_KEY", "YI_API_KEY",
        "ZHIPU_API_KEY", "BAICHUAN_API_KEY", "STEPFUN_API_KEY",
    ]
    for k in keys:
        if os.environ.get(k):
            env[k] = os.environ[k]
    
    # Enable hanzo-mcp for spawned agents
    # This allows agent-to-agent communication via MCP
    env["HANZO_AGENT_MCP_ENABLED"] = "true"
    
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
            "Agent Configuration",
            "=" * 40,
            f"Default agent: {self._default_agent()}",
            f"In Claude Code: {self._env.get('in_claude', False)}",
            f"Config dir: {CONFIG_DIR}",
        ]
        if self._env.get("session"):
            lines.append(f"Session: {self._env['session'][:8]}...")
        
        lines.append("")
        lines.append("Native Agents:")
        for name, cfg in sorted(NATIVE_AGENTS.items(), key=lambda x: x[1].priority):
            args_str = " ".join(cfg.args[:3]) + ("..." if len(cfg.args) > 3 else "")
            lines.append(f"  {name}: {cfg.cmd} {args_str}")
            if cfg.max_turns != 999:
                lines.append(f"    max_turns: {cfg.max_turns}")
        
        lines.append("")
        lines.append("Anthropic-compat Agents:")
        for name, cfg in sorted(ANTHROPIC_COMPAT_AGENTS.items(), key=lambda x: x[1].priority):
            lines.append(f"  {name}: {cfg.model}")
        
        lines.append("")
        lines.append("Override configs:")
        lines.append(f"  File: ~/.hanzo/agents/<name>.json")
        lines.append(f"  Env:  HANZO_AGENT_<NAME>_ARGS=\"--flag1 --flag2\"")
        
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
        """Execute single agent with auto-backgrounding.
        
        Supports two modes:
        - CLI mode (api_type="cli"): Spawn CLI subprocess
        - API mode (api_type="openai"|"anthropic"): Direct HTTP calls
        """
        if agent not in AGENTS:
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=f"Unknown agent: {agent}")
        
        cfg = AGENTS[agent]
        
        # Route to API mode if endpoint is configured
        if cfg.endpoint and cfg.api_type != "cli":
            return await self._exec_api(agent, cfg, prompt, timeout)
        
        # CLI mode: Build command with YOLO flags and max_turns
        full_cmd = [cfg.cmd]
        
        # For claude CLI, add output format first
        if cfg.cmd == "claude":
            full_cmd.extend(["--output-format", "text"])
            # Add max turns if configured (default 999)
            if cfg.max_turns and cfg.max_turns != 999:
                full_cmd.extend(["--max-turns", str(cfg.max_turns)])
            # Resume session if specified
            if cfg.session_id:
                full_cmd.extend(["--resume", cfg.session_id])
        
        # Add model override
        if cfg.model:
            full_cmd.extend(["--model", cfg.model])
        
        # For Anthropic-compatible APIs
        if cfg.base_url:
            full_cmd.append("--dangerously-skip-permissions")
        
        # Add configured args (includes YOLO flags)
        full_cmd.extend(cfg.args)
        
        # Add max_turns for agents that support it (if not already in args)
        if cfg.max_turns and "--max-turns" not in cfg.args and "--max-session-turns" not in str(cfg.args):
            if cfg.cmd in ("vibe",):
                full_cmd.extend(["--max-turns", str(cfg.max_turns)])
            elif cfg.cmd in ("qwen",):
                full_cmd.append(f"--max-session-turns={cfg.max_turns}")
        
        # Add system prompt if configured (claude CLI only)
        if cfg.system_prompt and cfg.cmd == "claude":
            full_cmd.extend(["--append-system-prompt", cfg.system_prompt])
        
        full_cmd.append(prompt)
        
        # Build environment
        env = os.environ.copy()
        env["OTEL_SDK_DISABLED"] = "true"  # Disable OpenTelemetry noise
        env.update(self._mcp_env)
        env["HANZO_AGENT_PARENT"] = "true"
        env["HANZO_AGENT_NAME"] = agent
        
        # Set Anthropic-compatible API overrides
        if cfg.base_url:
            env["ANTHROPIC_BASE_URL"] = cfg.base_url
        if cfg.auth_env and os.environ.get(cfg.auth_env):
            env["ANTHROPIC_AUTH_TOKEN"] = os.environ[cfg.auth_env]
        
        # Get shared ProcessManager for auto-backgrounding
        pm = ProcessManager()
        process_id = f"agent_{agent}_{uuid.uuid4().hex[:8]}"
        log_file = await pm.create_log_file(process_id)
        
        start = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout for logging
                cwd=cwd or os.getcwd(),
                env=env,
            )
            
            # Track process immediately for ps visibility
            pm.add_process(process_id, proc, str(log_file))
            
            # Read output with timeout, auto-background if exceeded
            output_lines: List[str] = []
            
            async def read_output():
                if proc.stdout:
                    async for line in proc.stdout:
                        line_str = line.decode("utf-8", errors="replace")
                        output_lines.append(line_str)
                        async with aiofiles.open(log_file, "a") as f:
                            await f.write(line_str)
            
            read_task = asyncio.create_task(read_output())
            wait_task = asyncio.create_task(proc.wait())
            
            done, pending = await asyncio.wait(
                [read_task, wait_task],
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            if wait_task in done:
                # Process completed
                return_code = await wait_task
                try:
                    await asyncio.wait_for(read_task, timeout=1.0)
                except asyncio.TimeoutError:
                    read_task.cancel()
                
                ms = int((time.time() - start) * 1000)
                output = "".join(output_lines)
                pm.remove_process(process_id)
                
                if return_code != 0:
                    return Result(agent=agent, prompt=prompt, output=output, ok=False, 
                                  error=f"Exit code {return_code}", ms=ms)
                return Result(agent=agent, prompt=prompt, output=output, ok=True, ms=ms)
            
            # Timeout - auto-background
            ms = int((time.time() - start) * 1000)
            partial = "".join(output_lines)
            
            # Write backgrounding message to log
            async with aiofiles.open(log_file, "a") as f:
                await f.write(f"\n[agent] Backgrounded after {timeout}s timeout\n")
                await f.write(f"[agent] Process ID: {process_id}\n")
                await f.write(f"[agent] PID: {proc.pid}\n")
            
            bg_msg = (
                f"[backgrounded] Agent {agent} running in background.\n"
                f"Process ID: {process_id}\n"
                f"Log file: {log_file}\n\n"
                f"Use 'ps --logs {process_id}' to view full output\n"
                f"Use 'ps --kill {process_id}' to stop the process\n"
            )
            if partial:
                bg_msg += f"\n=== Partial output ===\n{partial[:500]}{'...' if len(partial) > 500 else ''}"
            
            return Result(agent=agent, prompt=prompt, output=bg_msg, ok=True, 
                          error=f"backgrounded:{process_id}", ms=ms)
        
        except FileNotFoundError:
            pm.remove_process(process_id)
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=f"{cfg.cmd} not found")
        except Exception as e:
            pm.remove_process(process_id)
            return Result(agent=agent, prompt=prompt, output="", ok=False, error=str(e))
    
    async def _exec_api(self, agent: str, cfg: AgentConfig, prompt: str, timeout: int) -> Result:
        """Execute agent via direct API call (OpenAI or Anthropic format).
        
        Supports:
        - api_type="openai": OpenAI-compatible /v1/chat/completions
        - api_type="anthropic": Anthropic /v1/messages
        """
        if not HAS_HTTPX:
            return Result(agent=agent, prompt=prompt, output="", ok=False, 
                          error="httpx not installed. Run: pip install httpx")
        
        start = time.time()
        
        # Get auth token
        auth_token = None
        if cfg.auth_env:
            auth_token = os.environ.get(cfg.auth_env)
        if not auth_token and cfg.env_key:
            auth_token = os.environ.get(cfg.env_key)
        
        if not auth_token:
            return Result(agent=agent, prompt=prompt, output="", ok=False,
                          error=f"No API key. Set {cfg.auth_env or cfg.env_key}")
        
        endpoint = cfg.endpoint
        if not endpoint:
            return Result(agent=agent, prompt=prompt, output="", ok=False,
                          error="No endpoint configured for API mode")
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if cfg.api_type == "openai":
                    # OpenAI-compatible format
                    messages = []
                    if cfg.system_prompt:
                        messages.append({"role": "system", "content": cfg.system_prompt})
                    messages.append({"role": "user", "content": prompt})
                    
                    payload = {
                        "model": cfg.model or "gpt-4",
                        "messages": messages,
                        "max_tokens": 4096,
                    }
                    
                    resp = await client.post(
                        endpoint,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {auth_token}",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    if resp.status_code != 200:
                        return Result(agent=agent, prompt=prompt, output="", ok=False,
                                      error=f"API error {resp.status_code}: {resp.text[:200]}")
                    
                    data = resp.json()
                    output = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                elif cfg.api_type == "anthropic":
                    # Anthropic format
                    messages = [{"role": "user", "content": prompt}]
                    
                    payload = {
                        "model": cfg.model or "claude-3-5-sonnet-20241022",
                        "max_tokens": 4096,
                        "messages": messages,
                    }
                    
                    if cfg.system_prompt:
                        payload["system"] = cfg.system_prompt
                    
                    resp = await client.post(
                        endpoint,
                        json=payload,
                        headers={
                            "x-api-key": auth_token,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    if resp.status_code != 200:
                        return Result(agent=agent, prompt=prompt, output="", ok=False,
                                      error=f"API error {resp.status_code}: {resp.text[:200]}")
                    
                    data = resp.json()
                    content = data.get("content", [])
                    output = "".join(c.get("text", "") for c in content if c.get("type") == "text")
                    
                else:
                    return Result(agent=agent, prompt=prompt, output="", ok=False,
                                  error=f"Unknown api_type: {cfg.api_type}")
                
                ms = int((time.time() - start) * 1000)
                return Result(agent=agent, prompt=prompt, output=output, ok=True, ms=ms)
                
        except httpx.TimeoutException:
            ms = int((time.time() - start) * 1000)
            return Result(agent=agent, prompt=prompt, output="", ok=False,
                          error=f"Request timeout after {timeout}s", ms=ms)
        except Exception as e:
            ms = int((time.time() - start) * 1000)
            return Result(agent=agent, prompt=prompt, output="", ok=False,
                          error=str(e), ms=ms)

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
        """Metastable consensus with agent-to-agent MCP communication.
        
        https://github.com/luxfi/consensus
        
        Each agent gets a system prompt enabling hanzo-mcp so they can
        query each other during consensus rounds.
        """
        if not prompt:
            return "Error: prompt required"
        if not agents:
            return "Error: agents required"
        
        if not HAS_CONSENSUS:
            return "Error: hanzo-consensus not installed. Run: pip install hanzo-tools-agent[consensus]"
        
        # Build consensus prompt with MCP context
        consensus_prompt = f"""{CONSENSUS_SYSTEM_PROMPT}

Participants in this consensus: {', '.join(agents)}
Rounds: {rounds}, Sample size: {k}

Question: {prompt}

Provide your reasoned response. You may use the 'agent' tool to query other participants."""
        
        # Executor adapter - adds system prompt for MCP communication
        async def execute(agent_id: str, agent_prompt: str) -> ConsensusResult:
            # Wrap prompt with consensus context
            full_prompt = f"{agent_prompt}\n\n[Consensus context: round in progress, other agents: {', '.join(a for a in agents if a != agent_id)}]"
            result = await self._exec(agent_id, full_prompt, cwd, timeout)
            return ConsensusResult(
                id=result.agent,
                output=result.output,
                ok=result.ok,
                error=result.error,
                ms=result.ms,
            )
        
        start = time.time()
        state = await run_consensus(
            prompt=consensus_prompt,
            participants=agents,
            execute=execute,
            rounds=rounds,
            k=k,
            alpha=alpha,
            beta_1=beta_1,
            beta_2=beta_2,
        )
        elapsed = time.time() - start
        
        # Final synthesis by winner agent
        synthesis = state.synthesis or ""
        if state.winner and state.finalized:
            # Have winner agent provide final summary
            summary_prompt = f"""Consensus achieved. You ({state.winner}) are the winner.

Original question: {prompt}

Synthesize the final answer based on the consensus discussion.
Be concise but comprehensive."""
            
            summary_result = await self._exec(state.winner, summary_prompt, cwd, timeout // 2)
            if summary_result.ok:
                synthesis = summary_result.output
        
        return f"[Metastable] {elapsed:.1f}s, winner: {state.winner}, finalized: {state.finalized}\n\n{synthesis}"
    
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
