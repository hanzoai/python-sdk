"""Unified code semantics tool for HIP-0300 architecture.

This module provides a single unified 'code' tool that handles all semantic code operations:
- parse: Parse source to AST (tree-sitter)
- serialize: AST back to text
- symbols: List symbols in file/scope
- definition: Go to definition (LSP)
- references: Find all references (LSP)
- transform: Pure codemod → Patch (no side effects)
- summarize: Compress Diff/Log/Report to summary

Following Unix philosophy: one tool for the Symbols + Structure axis.
All operations are PURE (no side effects) except where noted.

Effect lattice position: PURE
Representation: Text → AST → Patch
Scope: File → Package → Repo
"""

import os
import json
import hashlib
import difflib
from typing import Any, ClassVar, Literal
from pathlib import Path
from dataclasses import dataclass, field

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    ToolError,
    InvalidParamsError,
    NotFoundError,
    Paging,
    content_hash,
)


# Language detection by extension
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".cs": "c_sharp",
    ".lua": "lua",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
}


@dataclass
class TransformSpec:
    """Specification for code transformation."""
    kind: Literal["rename", "extract", "inline", "move", "codemod", "generate"]

    # For rename
    old_name: str | None = None
    new_name: str | None = None
    scope: Literal["file", "package", "repo"] = "file"

    # For codemod (pattern-based)
    match_pattern: str | None = None
    replace_template: str | None = None

    # For generate
    template: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


class CodeTool(BaseTool):
    """Unified code semantics tool (HIP-0300).

    Handles all semantic code operations on a single axis:
    - parse: Parse source to AST
    - serialize: AST to text
    - symbols: List symbols
    - definition: Go to definition
    - references: Find references
    - transform: Pure codemod → Patch
    - summarize: Compress to summary

    All operations are PURE (safe to parallelize/cache).
    """

    name: ClassVar[str] = "code"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._tree_sitter = None
        self._lsp_clients: dict[str, Any] = {}
        self._register_code_actions()

    @property
    def description(self) -> str:
        return """Unified code semantics tool (HIP-0300).

Actions:
- parse: Parse source code to AST (tree-sitter)
- serialize: Convert AST back to text
- symbols: List symbols in file/scope
- definition: Go to symbol definition (LSP)
- references: Find all references to symbol (LSP)
- transform: Pure codemod producing Patch (no side effects)
- summarize: Compress Diff/Log/Report to summary

All operations are PURE - safe to cache and parallelize.
"""

    def _detect_lang(self, path: str | None, text: str | None = None) -> str:
        """Detect language from path extension or content."""
        if path:
            ext = Path(path).suffix.lower()
            if ext in LANG_MAP:
                return LANG_MAP[ext]

        # Fallback: try to detect from shebang or content
        if text:
            first_line = text.split("\n", 1)[0]
            if first_line.startswith("#!"):
                if "python" in first_line:
                    return "python"
                elif "node" in first_line or "deno" in first_line:
                    return "javascript"
                elif "bash" in first_line or "sh" in first_line:
                    return "bash"

        return "unknown"

    def _get_tree_sitter(self):
        """Lazy-load tree-sitter."""
        if self._tree_sitter is None:
            try:
                import tree_sitter_languages
                self._tree_sitter = tree_sitter_languages
            except ImportError:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message="tree-sitter-languages not installed. Run: pip install tree-sitter-languages",
                )
        return self._tree_sitter

    def _parse_with_tree_sitter(self, text: str, lang: str) -> dict:
        """Parse text to AST using tree-sitter."""
        ts = self._get_tree_sitter()

        try:
            parser = ts.get_parser(lang)
            tree = parser.parse(text.encode())

            def node_to_dict(node) -> dict:
                result = {
                    "type": node.type,
                    "start": {"line": node.start_point[0], "col": node.start_point[1]},
                    "end": {"line": node.end_point[0], "col": node.end_point[1]},
                }
                if node.child_count > 0:
                    result["children"] = [node_to_dict(c) for c in node.children]
                else:
                    result["text"] = node.text.decode() if node.text else ""
                return result

            return {
                "root": node_to_dict(tree.root_node),
                "lang": lang,
                "errors": [
                    {
                        "line": n.start_point[0],
                        "col": n.start_point[1],
                        "message": "syntax error",
                    }
                    for n in tree.root_node.children
                    if n.type == "ERROR"
                ],
            }
        except Exception as e:
            raise ToolError(
                code="INTERNAL_ERROR",
                message=f"Parse error: {e}",
                details={"lang": lang},
            )

    def _extract_symbols(self, ast: dict, lang: str) -> list[dict]:
        """Extract symbols from AST."""
        symbols = []

        # Symbol node types by language
        symbol_types = {
            "python": ["function_definition", "class_definition", "assignment"],
            "javascript": ["function_declaration", "class_declaration", "variable_declaration", "lexical_declaration"],
            "typescript": ["function_declaration", "class_declaration", "interface_declaration", "type_alias_declaration"],
            "go": ["function_declaration", "method_declaration", "type_declaration"],
            "rust": ["function_item", "struct_item", "enum_item", "impl_item", "trait_item"],
        }

        types_to_find = symbol_types.get(lang, ["function_definition", "class_definition"])

        def walk(node: dict, parent_name: str = ""):
            node_type = node.get("type", "")

            if node_type in types_to_find:
                # Try to extract name from first identifier child
                name = None
                for child in node.get("children", []):
                    if child.get("type") == "identifier":
                        name = child.get("text", "")
                        break
                    elif child.get("type") == "name":
                        name = child.get("text", "")
                        break

                if name:
                    symbols.append({
                        "name": name,
                        "kind": node_type,
                        "range": {
                            "start": node["start"],
                            "end": node["end"],
                        },
                        "parent": parent_name or None,
                    })
                    parent_name = name

            for child in node.get("children", []):
                walk(child, parent_name)

        if "root" in ast:
            walk(ast["root"])

        return symbols

    def _generate_patch(self, original: str, modified: str, path: str = "file") -> str:
        """Generate unified diff patch."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )

        return "".join(diff)

    def _apply_rename(self, text: str, old_name: str, new_name: str) -> tuple[str, int]:
        """Apply simple rename transformation. Returns (new_text, count)."""
        import re
        # Word-boundary rename to avoid partial matches
        pattern = rf"\b{re.escape(old_name)}\b"
        new_text, count = re.subn(pattern, new_name, text)
        return new_text, count

    def _apply_codemod(self, text: str, match: str, replace: str) -> tuple[str, int]:
        """Apply pattern-based codemod. Returns (new_text, count)."""
        import re
        try:
            new_text, count = re.subn(match, replace, text)
            return new_text, count
        except re.error as e:
            raise InvalidParamsError(f"Invalid regex pattern: {e}", param="match_pattern")

    def _register_code_actions(self):
        """Register all code actions."""

        @self.action("parse", "Parse source code to AST")
        async def parse(
            ctx: MCPContext,
            path: str | None = None,
            text: str | None = None,
            lang: str | None = None,
        ) -> dict:
            """Parse source to AST using tree-sitter.

            Args:
                path: File path to parse
                text: Raw text to parse (alternative to path)
                lang: Language (auto-detected if not specified)

            Returns:
                AST structure with lang and errors

            Effect: PURE
            Cache: hash(text)
            """
            if path and not text:
                full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                if not full_path.exists():
                    raise NotFoundError(f"File not found: {path}", uri=str(full_path))
                text = full_path.read_text()

            if not text:
                raise InvalidParamsError("Either path or text required", param="text")

            detected_lang = lang or self._detect_lang(path, text)

            ast = self._parse_with_tree_sitter(text, detected_lang)

            return {
                "ast": ast,
                "lang": detected_lang,
                "hash": content_hash(text),
                "source_map": {"path": path} if path else None,
            }

        @self.action("serialize", "Convert AST back to text")
        async def serialize(
            ctx: MCPContext,
            ast: dict,
            lang: str | None = None,
        ) -> dict:
            """Serialize AST back to text.

            Note: This is a simplified implementation that extracts
            leaf node text. Full round-trip requires CST preservation.

            Effect: PURE
            """
            def extract_text(node: dict) -> str:
                if "text" in node:
                    return node["text"]
                children_text = []
                for child in node.get("children", []):
                    children_text.append(extract_text(child))
                return " ".join(children_text)

            root = ast.get("root") or ast
            text = extract_text(root)

            return {
                "text": text,
                "lang": lang or ast.get("lang", "unknown"),
            }

        @self.action("symbols", "List symbols in file")
        async def symbols(
            ctx: MCPContext,
            path: str | None = None,
            text: str | None = None,
            ast: dict | None = None,
            lang: str | None = None,
        ) -> dict:
            """Extract symbols from source code.

            Args:
                path: File path
                text: Raw text (alternative)
                ast: Pre-parsed AST (alternative)
                lang: Language hint

            Returns:
                List of symbols with name, kind, range

            Effect: PURE
            """
            if ast is None:
                if path and not text:
                    full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                    if not full_path.exists():
                        raise NotFoundError(f"File not found: {path}")
                    text = full_path.read_text()

                if not text:
                    raise InvalidParamsError("path, text, or ast required")

                detected_lang = lang or self._detect_lang(path, text)
                parsed = self._parse_with_tree_sitter(text, detected_lang)
                ast = parsed
                lang = detected_lang

            symbols_list = self._extract_symbols(ast, lang or ast.get("lang", "unknown"))

            return {
                "symbols": symbols_list,
                "count": len(symbols_list),
                "path": path,
            }

        @self.action("definition", "Go to symbol definition")
        async def definition(
            ctx: MCPContext,
            path: str,
            line: int,
            col: int,
        ) -> dict:
            """Find definition of symbol at position.

            Uses LSP when available, falls back to AST search.

            Effect: PURE
            """
            # TODO: Integrate with LSP (gopls, pyright, etc.)
            # For now, return a stub indicating LSP integration needed
            return {
                "path": path,
                "position": {"line": line, "col": col},
                "definition": None,
                "note": "LSP integration required for full definition lookup",
            }

        @self.action("references", "Find all references to symbol")
        async def references(
            ctx: MCPContext,
            path: str,
            line: int,
            col: int,
            scope: str = "repo",
        ) -> dict:
            """Find all references to symbol at position.

            Uses LSP when available, falls back to text search.

            Effect: PURE
            Scope: file | package | repo
            """
            # TODO: Integrate with LSP
            return {
                "path": path,
                "position": {"line": line, "col": col},
                "references": [],
                "scope": scope,
                "note": "LSP integration required for full reference lookup",
            }

        @self.action("transform", "Generate patch from transformation spec")
        async def transform(
            ctx: MCPContext,
            path: str | None = None,
            text: str | None = None,
            kind: str = "rename",
            old_name: str | None = None,
            new_name: str | None = None,
            match_pattern: str | None = None,
            replace_template: str | None = None,
            scope: str = "file",
        ) -> dict:
            """Apply transformation and produce Patch (PURE - no side effects).

            This is the key "pure middle layer" operator:
            - Input: source + transform spec
            - Output: Patch as value (not applied)

            Kinds:
                rename: Rename symbol (old_name → new_name)
                codemod: Pattern-based replacement

            Effect: PURE
            """
            # Load text if path provided
            if path and not text:
                full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                if not full_path.exists():
                    raise NotFoundError(f"File not found: {path}")
                text = full_path.read_text()

            if not text:
                raise InvalidParamsError("path or text required")

            original_hash = content_hash(text)
            original = text
            changes_count = 0

            if kind == "rename":
                if not old_name or not new_name:
                    raise InvalidParamsError("rename requires old_name and new_name")
                text, changes_count = self._apply_rename(text, old_name, new_name)

            elif kind == "codemod":
                if not match_pattern or replace_template is None:
                    raise InvalidParamsError("codemod requires match_pattern and replace_template")
                text, changes_count = self._apply_codemod(text, match_pattern, replace_template)

            else:
                raise InvalidParamsError(
                    f"Unknown transform kind: {kind}",
                    param="kind",
                    expected="rename | codemod",
                )

            # Generate patch
            patch = self._generate_patch(original, text, path or "input")

            return {
                "patch": patch,
                "changes_count": changes_count,
                "base_hash": original_hash,
                "new_hash": content_hash(text) if changes_count > 0 else original_hash,
                "kind": kind,
                "report": {
                    "files_affected": 1 if changes_count > 0 else 0,
                    "lines_changed": patch.count("\n") if patch else 0,
                },
            }

        @self.action("summarize", "Compress diff/log/report to summary")
        async def summarize(
            ctx: MCPContext,
            diff: str | None = None,
            log: list[dict] | None = None,
            report: dict | None = None,
            text: str | None = None,
            max_length: int = 500,
        ) -> dict:
            """Summarize code artifacts for review.

            Takes one of: diff, log, report, or text
            Produces: summary, risks, next_actions

            Effect: PURE
            """
            summary_parts = []
            risks = []
            next_actions = []

            if diff:
                # Analyze diff
                lines = diff.split("\n")
                adds = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
                dels = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
                files = [l[6:] for l in lines if l.startswith("+++ b/")]

                summary_parts.append(f"Patch: +{adds}/-{dels} lines across {len(files)} file(s)")

                if adds + dels > 100:
                    risks.append("Large change - review carefully")
                if any("test" in f.lower() for f in files):
                    next_actions.append("Run tests to verify")
                else:
                    risks.append("No test files modified")
                    next_actions.append("Consider adding tests")

            if log:
                summary_parts.append(f"History: {len(log)} commit(s)")
                if log:
                    latest = log[0] if isinstance(log[0], dict) else {"message": str(log[0])}
                    summary_parts.append(f"Latest: {latest.get('message', 'N/A')[:50]}")

            if report:
                if "pass" in report:
                    status = "PASS" if report["pass"] else "FAIL"
                    summary_parts.append(f"Status: {status}")
                    if not report["pass"]:
                        risks.append("Tests failing")
                        next_actions.append("Fix failing tests before merge")

            if text:
                # Simple text summary
                word_count = len(text.split())
                summary_parts.append(f"Text: {word_count} words")
                if word_count > 1000:
                    summary_parts.append("(truncated for summary)")

            return {
                "summary": " | ".join(summary_parts) if summary_parts else "No content to summarize",
                "risks": risks,
                "next_actions": next_actions,
            }

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'code' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Singleton instance
code_tool = CodeTool
