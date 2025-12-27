"""Shellflow - minimal DSL for DAG execution.

Syntax:
    A ; B ; C           → sequential (do)
    { A & B & C }       → parallel (all)
    A ; { B & C } ; D   → mixed

Compiles to JSON AST:
    {"type": "do", "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"]}

Examples:
    mkdir -p dist ; { cp a.txt dist/ & cp b.txt dist/ } ; zip -r out.zip dist/
"""

import re
from typing import Any, List, Union

# AST types
ASTNode = Union[str, dict]


def parse(source: str) -> dict:
    """Parse shellflow source to AST.
    
    Args:
        source: Shellflow source string
        
    Returns:
        AST in object form: {"type": "do"|"all", "steps": [...]}
    """
    source = source.strip()
    if not source:
        return {"type": "do", "steps": []}
    
    # Tokenize: split on ; and & while respecting { }
    tokens = _tokenize(source)
    
    # Parse tokens to AST
    ast = _parse_tokens(tokens)
    
    # Normalize (flatten nested do/all, drop singletons)
    ast = _normalize(ast)
    
    return ast


def _tokenize(source: str) -> List[str]:
    """Tokenize shellflow into commands and operators."""
    tokens = []
    current = []
    depth = 0
    i = 0
    
    while i < len(source):
        char = source[i]
        
        if char == '{':
            if depth == 0 and current:
                # Flush current command before block
                cmd = ''.join(current).strip()
                if cmd:
                    tokens.append(cmd)
                current = []
            depth += 1
            current.append(char)
        elif char == '}':
            current.append(char)
            depth -= 1
            if depth == 0:
                # End of block
                block = ''.join(current).strip()
                if block:
                    tokens.append(block)
                current = []
        elif char == ';' and depth == 0:
            # Sequential separator at top level
            cmd = ''.join(current).strip()
            if cmd:
                tokens.append(cmd)
            tokens.append(';')
            current = []
        elif char == '&' and depth == 0:
            # Parallel separator at top level (shouldn't happen outside {})
            cmd = ''.join(current).strip()
            if cmd:
                tokens.append(cmd)
            tokens.append('&')
            current = []
        else:
            current.append(char)
        
        i += 1
    
    # Flush remaining
    if current:
        cmd = ''.join(current).strip()
        if cmd:
            tokens.append(cmd)
    
    return tokens


def _parse_tokens(tokens: List[str]) -> dict:
    """Parse token list to AST."""
    if not tokens:
        return {"type": "do", "steps": []}
    
    # Check if this is a block
    if len(tokens) == 1 and tokens[0].startswith('{') and tokens[0].endswith('}'):
        # Parse inner block as parallel
        inner = tokens[0][1:-1].strip()
        inner_tokens = _tokenize_parallel(inner)
        steps = [_parse_single(t) for t in inner_tokens if t and t != '&']
        return {"type": "all", "steps": steps}
    
    # Parse as sequential
    steps = []
    for token in tokens:
        if token == ';':
            continue
        elif token.startswith('{') and token.endswith('}'):
            # Parallel block
            inner = token[1:-1].strip()
            inner_tokens = _tokenize_parallel(inner)
            inner_steps = [_parse_single(t) for t in inner_tokens if t and t != '&']
            if len(inner_steps) == 1:
                steps.append(inner_steps[0])
            else:
                steps.append({"type": "all", "steps": inner_steps})
        else:
            steps.append(token)
    
    if len(steps) == 1:
        if isinstance(steps[0], dict):
            return steps[0]
        return {"type": "do", "steps": steps}
    
    return {"type": "do", "steps": steps}


def _tokenize_parallel(source: str) -> List[str]:
    """Tokenize content inside { } splitting on &."""
    tokens = []
    current = []
    depth = 0
    
    for char in source:
        if char == '{':
            depth += 1
            current.append(char)
        elif char == '}':
            depth -= 1
            current.append(char)
        elif char == '&' and depth == 0:
            cmd = ''.join(current).strip()
            if cmd:
                tokens.append(cmd)
            current = []
        else:
            current.append(char)
    
    if current:
        cmd = ''.join(current).strip()
        if cmd:
            tokens.append(cmd)
    
    return tokens


def _parse_single(token: str) -> ASTNode:
    """Parse a single token (command or nested block)."""
    token = token.strip()
    if token.startswith('{') and token.endswith('}'):
        inner = token[1:-1].strip()
        inner_tokens = _tokenize_parallel(inner)
        steps = [_parse_single(t) for t in inner_tokens if t]
        return {"type": "all", "steps": steps}
    return token


def _normalize(ast: dict) -> dict:
    """Normalize AST: flatten nested do/all, drop singletons."""
    if not isinstance(ast, dict):
        return ast
    
    node_type = ast.get("type")
    steps = ast.get("steps", [])
    
    # Recursively normalize children
    normalized_steps = []
    for step in steps:
        if isinstance(step, dict):
            step = _normalize(step)
            # Flatten same-type nesting
            if step.get("type") == node_type:
                normalized_steps.extend(step.get("steps", []))
            else:
                normalized_steps.append(step)
        elif step:  # Skip empty strings
            normalized_steps.append(step)
    
    # Drop singleton wrappers
    if len(normalized_steps) == 1:
        return normalized_steps[0] if isinstance(normalized_steps[0], dict) else {"type": "do", "steps": normalized_steps}
    
    if not normalized_steps:
        return {"type": "do", "steps": []}
    
    return {"type": node_type, "steps": normalized_steps}


def to_sexp(ast: ASTNode) -> list:
    """Convert object-form AST to S-expression form.
    
    {"type": "do", "steps": ["A", {"type": "all", "steps": ["B", "C"]}]}
    → ["do", "A", ["all", "B", "C"]]
    """
    if isinstance(ast, str):
        return ast
    
    node_type = ast.get("type", "do")
    steps = ast.get("steps", [])
    
    return [node_type] + [to_sexp(s) for s in steps]


def from_sexp(sexp: Union[str, list]) -> ASTNode:
    """Convert S-expression to object-form AST.
    
    ["do", "A", ["all", "B", "C"]]
    → {"type": "do", "steps": ["A", {"type": "all", "steps": ["B", "C"]}]}
    """
    if isinstance(sexp, str):
        return sexp
    
    if not sexp:
        return {"type": "do", "steps": []}
    
    node_type = sexp[0]
    steps = [from_sexp(s) for s in sexp[1:]]
    
    return {"type": node_type, "steps": steps}


def to_commands(ast: ASTNode) -> List[Any]:
    """Convert AST to commands list for existing DAG executor.
    
    Transforms:
    - {"type": "do", "steps": [...]} → [...] (serial)
    - {"type": "all", "steps": [...]} → [[...]] (nested = parallel)
    - str → str
    """
    if isinstance(ast, str):
        return [ast]
    
    node_type = ast.get("type", "do")
    steps = ast.get("steps", [])
    
    if node_type == "all":
        # Parallel: return as nested list
        result = []
        for step in steps:
            if isinstance(step, str):
                result.append(step)
            else:
                # Nested structure
                result.extend(to_commands(step))
        return [result]  # Wrap in list to trigger parallel
    
    # Sequential (do)
    result = []
    for step in steps:
        if isinstance(step, str):
            result.append(step)
        elif step.get("type") == "all":
            # Parallel block: wrap in list
            parallel_cmds = []
            for s in step.get("steps", []):
                if isinstance(s, str):
                    parallel_cmds.append(s)
                else:
                    parallel_cmds.extend(to_commands(s))
            result.append(parallel_cmds)
        else:
            # Nested do: flatten
            result.extend(to_commands(step))
    
    return result


def render_ascii(ast: ASTNode, indent: int = 0) -> str:
    """Render AST as ASCII tree."""
    prefix = "  " * indent
    
    if isinstance(ast, str):
        return f"{prefix}└─ {ast}\n"
    
    node_type = ast.get("type", "do")
    steps = ast.get("steps", [])
    
    lines = [f"{prefix}{'├─' if indent else ''}[{node_type}]\n"]
    for i, step in enumerate(steps):
        is_last = i == len(steps) - 1
        if isinstance(step, str):
            marker = "└─" if is_last else "├─"
            lines.append(f"{prefix}  {marker} {step}\n")
        else:
            lines.append(render_ascii(step, indent + 1))
    
    return "".join(lines)


# Convenience function for direct execution
def compile(source: str, format: str = "commands") -> Any:
    """Compile shellflow to various formats.
    
    Args:
        source: Shellflow source string
        format: Output format - "ast", "sexp", "commands", "ascii"
        
    Returns:
        Compiled output in requested format
    """
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
