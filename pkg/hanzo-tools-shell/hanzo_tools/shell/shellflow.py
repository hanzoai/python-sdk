"""Shellflow - minimal DSL for DAG execution.

Syntax:
    A ; B ; C           → sequential (do)
    { A & B & C }       → parallel (all)
    A ; { B & C } ; D   → mixed

Compiles to JSON AST:
    {"type": "do", "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"]}

Examples:
    mkdir -p dist ; { cp a.txt dist/ & cp b.txt dist/ } ; zip -r out.zip dist/

Performance:
    Optimized for high throughput with:
    - Precompiled regex patterns
    - Local variable caching
    - Fast-path for simple commands
    - LRU cache for repeated patterns
    - Full type annotations for mypyc compilation

    Compile with mypyc for 2-5x speedup:
        mypyc hanzo_tools/shell/shellflow.py
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Final, Tuple, Union
from functools import lru_cache  # noqa: TID251 - not using Stainless SDK

# Type aliases with full annotations
ASTDict = Dict[str, Any]
ASTNode = Union[str, ASTDict]
ASTTuple = Tuple[str, Tuple[Any, ...]]
TokenList = List[str]
CommandList = List[Any]

# Constants
TYPE_DO: Final[str] = "do"
TYPE_ALL: Final[str] = "all"

# Precompiled regex for performance
# Match: quoted strings, braces, semicolon, shell operators, single &
_TOKEN_PATTERN: Final[str] = r"""
    (?P<dquote>"(?:[^"\\]|\\.)*")      # Double-quoted string
    |(?P<squote>'(?:[^'\\]|\\.)*')     # Single-quoted string  
    |(?P<lbrace>\{)                     # Left brace
    |(?P<rbrace>\})                     # Right brace
    |(?P<semi>;)                        # Semicolon
    |(?P<shell_op>&&|\|\|)             # Shell operators (keep together)
    |(?P<and>&)                         # Single & (parallel separator)
    |(?P<text>[^{};'"&|]+)             # Other text (no & or |)
    |(?P<pipe>\|(?!\|))                # Single | (not ||)
"""

_TOKEN_RE: Final = re.compile(_TOKEN_PATTERN, re.VERBOSE)

# Preserved token types (tuple for faster `in` check than frozenset for small n)
_PRESERVED_KINDS: Final[Tuple[str, ...]] = ("dquote", "squote", "shell_op", "pipe")

# Local reference for hot path
_finditer = _TOKEN_RE.finditer


def parse(source: str) -> ASTDict:
    """Parse shellflow source to AST.

    Args:
        source: Shellflow source string

    Returns:
        AST in object form: {"type": "do"|"all", "steps": [...]}
    """
    # Strip and fast-path empty
    source = source.strip()
    if not source:
        return {"type": TYPE_DO, "steps": []}

    # Fast path: single simple command (no operators)
    # Using 'in' is faster than regex for simple checks
    if ";" not in source and "{" not in source and "&" not in source:
        return {"type": TYPE_DO, "steps": [source]}

    # Tokenize and parse
    tokens: TokenList = _tokenize_fast(source)
    ast: ASTDict = _parse_tokens(tokens)
    return _normalize(ast)


def _tokenize_fast(source: str) -> TokenList:
    """Tokenize shellflow into commands and operators.

    Optimized with local variable caching and type hints for mypyc.
    """
    tokens: TokenList = []
    tokens_append = tokens.append
    current_parts: List[str] = []
    parts_append = current_parts.append
    depth: int = 0

    for match in _finditer(source):
        kind: str | None = match.lastgroup
        value: str = match.group()

        if kind in _PRESERVED_KINDS:
            parts_append(value)
        elif kind == "lbrace":
            if depth == 0 and current_parts:
                cmd: str = "".join(current_parts).strip()
                if cmd:
                    tokens_append(cmd)
                current_parts = []
                parts_append = current_parts.append
            depth += 1
            parts_append(value)
        elif kind == "rbrace":
            parts_append(value)
            depth -= 1
            if depth == 0:
                block: str = "".join(current_parts).strip()
                if block:
                    tokens_append(block)
                current_parts = []
                parts_append = current_parts.append
        elif kind == "semi" and depth == 0:
            cmd = "".join(current_parts).strip()
            if cmd:
                tokens_append(cmd)
            tokens_append(";")
            current_parts = []
            parts_append = current_parts.append
        elif kind == "and" and depth == 0:
            cmd = "".join(current_parts).strip()
            if cmd:
                tokens_append(cmd)
            tokens_append("&")
            current_parts = []
            parts_append = current_parts.append
        else:
            parts_append(value)

    # Flush remaining
    if current_parts:
        cmd = "".join(current_parts).strip()
        if cmd:
            tokens_append(cmd)

    return tokens


def _tokenize_parallel_fast(source: str) -> TokenList:
    """Tokenize content inside { } splitting on & (but not &&).

    Optimized version with full type hints.
    """
    tokens: TokenList = []
    tokens_append = tokens.append
    current_parts: List[str] = []
    parts_append = current_parts.append
    depth: int = 0

    for match in _finditer(source):
        kind: str | None = match.lastgroup
        value: str = match.group()

        if kind in _PRESERVED_KINDS:
            parts_append(value)
        elif kind == "lbrace":
            depth += 1
            parts_append(value)
        elif kind == "rbrace":
            depth -= 1
            parts_append(value)
        elif kind == "and" and depth == 0:
            cmd: str = "".join(current_parts).strip()
            if cmd:
                tokens_append(cmd)
            current_parts = []
            parts_append = current_parts.append
        else:
            parts_append(value)

    if current_parts:
        cmd = "".join(current_parts).strip()
        if cmd:
            tokens_append(cmd)

    return tokens


def _parse_tokens(tokens: TokenList) -> ASTDict:
    """Parse token list to AST."""
    if not tokens:
        return {"type": TYPE_DO, "steps": []}

    # Check if this is a single block
    if len(tokens) == 1:
        t: str = tokens[0]
        if t.startswith("{") and t.endswith("}"):
            inner: str = t[1:-1].strip()
            inner_tokens: TokenList = _tokenize_parallel_fast(inner)
            steps: List[ASTNode] = [_parse_single(tok) for tok in inner_tokens if tok and tok != "&"]
            return {"type": TYPE_ALL, "steps": steps}

    # Parse as sequential
    steps = []
    steps_append = steps.append

    for token in tokens:
        if token == ";":
            continue
        elif token.startswith("{") and token.endswith("}"):
            inner = token[1:-1].strip()
            inner_tokens = _tokenize_parallel_fast(inner)
            inner_steps: List[ASTNode] = [_parse_single(tok) for tok in inner_tokens if tok and tok != "&"]
            if len(inner_steps) == 1:
                steps_append(inner_steps[0])
            else:
                steps_append({"type": TYPE_ALL, "steps": inner_steps})
        else:
            steps_append(token)

    if len(steps) == 1:
        s: ASTNode = steps[0]
        if isinstance(s, dict):
            return s
        return {"type": TYPE_DO, "steps": steps}

    return {"type": TYPE_DO, "steps": steps}


def _parse_single(token: str) -> ASTNode:
    """Parse a single token (command or nested block)."""
    token = token.strip()
    if token.startswith("{") and token.endswith("}"):
        inner: str = token[1:-1].strip()
        inner_tokens: TokenList = _tokenize_parallel_fast(inner)
        steps: List[ASTNode] = [_parse_single(t) for t in inner_tokens if t]
        return {"type": TYPE_ALL, "steps": steps}
    return token


def _normalize(ast: ASTNode) -> ASTDict:
    """Normalize AST: flatten nested do/all, drop singletons."""
    if isinstance(ast, str):
        return {"type": TYPE_DO, "steps": [ast]}

    node_type: str = ast.get("type", TYPE_DO)
    steps: List[ASTNode] = ast.get("steps", [])

    # Recursively normalize children
    normalized_steps: List[ASTNode] = []
    normalized_append = normalized_steps.append

    for step in steps:
        if isinstance(step, dict):
            step = _normalize(step)
            # Flatten same-type nesting
            step_type: str = step.get("type", "")
            if step_type == node_type:
                normalized_steps.extend(step.get("steps", []))
            else:
                normalized_append(step)
        elif step:
            normalized_append(step)

    # Drop singleton wrappers
    if len(normalized_steps) == 1:
        ns: ASTNode = normalized_steps[0]
        if isinstance(ns, dict):
            return ns
        return {"type": TYPE_DO, "steps": normalized_steps}

    if not normalized_steps:
        return {"type": TYPE_DO, "steps": []}

    return {"type": node_type, "steps": normalized_steps}


def to_sexp(ast: ASTNode) -> Any:
    """Convert object-form AST to S-expression form.

    {"type": "do", "steps": ["A", {"type": "all", "steps": ["B", "C"]}]}
    → ["do", "A", ["all", "B", "C"]]
    """
    if isinstance(ast, str):
        return ast

    node_type: str = ast.get("type", TYPE_DO)
    steps: List[ASTNode] = ast.get("steps", [])

    return [node_type] + [to_sexp(s) for s in steps]


def from_sexp(sexp: Any) -> ASTNode:
    """Convert S-expression to object-form AST.

    ["do", "A", ["all", "B", "C"]]
    → {"type": "do", "steps": ["A", {"type": "all", "steps": ["B", "C"]}]}
    """
    if isinstance(sexp, str):
        return sexp

    if not sexp:
        return {"type": TYPE_DO, "steps": []}

    node_type: str = sexp[0]
    steps: List[ASTNode] = [from_sexp(s) for s in sexp[1:]]

    return {"type": node_type, "steps": steps}


def to_commands(ast: ASTNode) -> CommandList:
    """Convert AST to commands list for existing DAG executor.

    Transforms:
    - {"type": "do", "steps": [...]} → [...] (serial)
    - {"type": "all", "steps": [...]} → [[...]] (nested = parallel)
    - str → [str]
    """
    if isinstance(ast, str):
        return [ast]

    node_type: str = ast.get("type", TYPE_DO)
    steps: List[ASTNode] = ast.get("steps", [])

    if node_type == TYPE_ALL:
        # Parallel: return as nested list
        result: CommandList = []
        result_append = result.append
        for step in steps:
            if isinstance(step, str):
                result_append(step)
            else:
                result.extend(to_commands(step))
        return [result]

    # Sequential (do)
    result = []
    result_append = result.append

    for step in steps:
        if isinstance(step, str):
            result_append(step)
        elif isinstance(step, dict):
            step_type: str = step.get("type", "")
            if step_type == TYPE_ALL:
                parallel_cmds: CommandList = []
                p_append = parallel_cmds.append
                for s in step.get("steps", []):
                    if isinstance(s, str):
                        p_append(s)
                    else:
                        parallel_cmds.extend(to_commands(s))
                result_append(parallel_cmds)
            else:
                result.extend(to_commands(step))

    return result


def render_ascii(ast: ASTNode, indent: int = 0) -> str:
    """Render AST as ASCII tree."""
    prefix: str = "  " * indent

    if isinstance(ast, str):
        return f"{prefix}└─ {ast}\n"

    node_type: str = ast.get("type", TYPE_DO)
    steps: List[ASTNode] = ast.get("steps", [])

    lines: List[str] = [f"{prefix}{'├─' if indent else ''}[{node_type}]\n"]
    lines_append = lines.append

    num_steps: int = len(steps)
    for i, step in enumerate(steps):
        is_last: bool = i == num_steps - 1
        if isinstance(step, str):
            marker: str = "└─" if is_last else "├─"
            lines_append(f"{prefix}  {marker} {step}\n")
        else:
            lines_append(render_ascii(step, indent + 1))

    return "".join(lines)


# Cached compile for repeated patterns
@lru_cache(maxsize=256)
def _parse_cached(source: str) -> ASTTuple:
    """Cached version of parse that returns a hashable tuple form."""
    ast: ASTDict = parse(source)
    return _dict_to_tuple(ast)


def _dict_to_tuple(d: ASTNode) -> ASTTuple | str:
    """Convert AST dict to hashable tuple."""
    if isinstance(d, str):
        return d
    node_type: str = d.get("type", TYPE_DO)
    steps: List[ASTNode] = d.get("steps", [])
    return (node_type, tuple(_dict_to_tuple(s) for s in steps))


def _tuple_to_dict(t: ASTTuple | str) -> ASTNode:
    """Convert tuple back to AST dict."""
    if isinstance(t, str):
        return t
    return {"type": t[0], "steps": [_tuple_to_dict(s) for s in t[1]]}


def compile(source: str, format: str = "commands", cached: bool = False) -> Any:
    """Compile shellflow to various formats.

    Args:
        source: Shellflow source string
        format: Output format - "ast", "sexp", "commands", "ascii"
        cached: Use LRU cache for repeated patterns (default: False)

    Returns:
        Compiled output in requested format
    """
    ast: ASTDict
    if cached:
        ast_tuple: ASTTuple | str = _parse_cached(source)
        result: ASTNode = _tuple_to_dict(ast_tuple)
        ast = result if isinstance(result, dict) else {"type": TYPE_DO, "steps": [result]}
    else:
        ast = parse(source)

    if format == "ast":
        return ast
    elif format == "sexp":
        return to_sexp(ast)
    elif format == "commands":
        return to_commands(ast)
    elif format == "ascii":
        return render_ascii(ast)
    else:
        raise ValueError(f"Unknown format: {format}")


# ============================================================================
# Inline optimized versions for hot paths
# These use minimal function calls and are designed for mypyc compilation
# ============================================================================


def parse_fast(source: str) -> ASTDict:
    """Ultra-fast parse for simple sequential commands.

    Falls back to full parse for complex syntax.
    """
    source = source.strip()
    if not source:
        return {"type": TYPE_DO, "steps": []}

    # Fast path: no special characters at all
    if ";" not in source and "{" not in source and "&" not in source:
        return {"type": TYPE_DO, "steps": [source]}

    # Fast path: simple sequential (only semicolons, no braces or ampersands)
    if "{" not in source and "&" not in source:
        # Split on semicolon, strip each part
        parts: List[str] = [p.strip() for p in source.split(";") if p.strip()]
        if parts:
            return {"type": TYPE_DO, "steps": parts}
        return {"type": TYPE_DO, "steps": []}

    # Fall back to full parse
    return parse(source)


def compile_to_commands_fast(source: str) -> CommandList:
    """Compile directly to commands list, optimized path.

    Skips intermediate representations when possible.
    """
    source = source.strip()
    if not source:
        return []

    # Fast path: single command
    if ";" not in source and "{" not in source and "&" not in source:
        return [source]

    # Fast path: simple sequential
    if "{" not in source and "&" not in source:
        return [p.strip() for p in source.split(";") if p.strip()]

    # Full compilation
    ast: ASTDict = parse(source)
    return to_commands(ast)


# Aliases for backwards compatibility
_tokenize = _tokenize_fast
_tokenize_parallel = _tokenize_parallel_fast
