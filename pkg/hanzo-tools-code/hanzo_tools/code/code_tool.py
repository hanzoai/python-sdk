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

import difflib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    InvalidParamsError,
    NotFoundError,
    ToolError,
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
            # Try tree-sitter-language-pack first (works with tree-sitter 0.24+)
            try:
                import tree_sitter_language_pack
                self._tree_sitter = tree_sitter_language_pack
            except ImportError:
                try:
                    import tree_sitter_languages
                    self._tree_sitter = tree_sitter_languages
                except ImportError:
                    raise ToolError(
                        code="INTERNAL_ERROR",
                        message="tree-sitter-languages not installed. Run: pip install tree-sitter-language-pack",
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
            "javascript": [
                "function_declaration",
                "class_declaration",
                "variable_declaration",
                "lexical_declaration",
            ],
            "typescript": [
                "function_declaration",
                "class_declaration",
                "interface_declaration",
                "type_alias_declaration",
            ],
            "go": ["function_declaration", "method_declaration", "type_declaration"],
            "rust": [
                "function_item",
                "struct_item",
                "enum_item",
                "impl_item",
                "trait_item",
            ],
        }

        types_to_find = symbol_types.get(
            lang, ["function_definition", "class_definition"]
        )

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
                    symbols.append(
                        {
                            "name": name,
                            "kind": node_type,
                            "range": {
                                "start": node["start"],
                                "end": node["end"],
                            },
                            "parent": parent_name or None,
                        }
                    )
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
            raise InvalidParamsError(
                f"Invalid regex pattern: {e}", param="match_pattern"
            )

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
                full_path = (
                    Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                )
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
                    full_path = (
                        Path(path)
                        if Path(path).is_absolute()
                        else Path(self.cwd) / path
                    )
                    if not full_path.exists():
                        raise NotFoundError(f"File not found: {path}")
                    text = full_path.read_text()

                if not text:
                    raise InvalidParamsError("path, text, or ast required")

                detected_lang = lang or self._detect_lang(path, text)
                parsed = self._parse_with_tree_sitter(text, detected_lang)
                ast = parsed
                lang = detected_lang

            symbols_list = self._extract_symbols(
                ast, lang or ast.get("lang", "unknown")
            )

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
                full_path = (
                    Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                )
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
                    raise InvalidParamsError(
                        "codemod requires match_pattern and replace_template"
                    )
                text, changes_count = self._apply_codemod(
                    text, match_pattern, replace_template
                )

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
                adds = sum(
                    1
                    for line in lines
                    if line.startswith("+") and not line.startswith("+++")
                )
                dels = sum(
                    1
                    for line in lines
                    if line.startswith("-") and not line.startswith("---")
                )
                files = [line[6:] for line in lines if line.startswith("+++ b/")]

                summary_parts.append(
                    f"Patch: +{adds}/-{dels} lines across {len(files)} file(s)"
                )

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
                    latest = (
                        log[0] if isinstance(log[0], dict) else {"message": str(log[0])}
                    )
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
                "summary": (
                    " | ".join(summary_parts)
                    if summary_parts
                    else "No content to summarize"
                ),
                "risks": risks,
                "next_actions": next_actions,
            }

        # ── TS-parity actions ──────────────────────────────────────────

        @self.action("search_symbol", "Find symbols across project")
        async def search_symbol(
            ctx: MCPContext,
            query: str,
            path: str | None = None,
            max_results: int = 20,
        ) -> dict:
            import re
            search_dir = Path(path) if path else Path(self.cwd)
            results = []
            skip_dirs = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}
            for p in search_dir.rglob("*"):
                if len(results) >= max_results:
                    break
                if any(sd in p.parts for sd in skip_dirs) or not p.is_file() or p.suffix not in LANG_MAP:
                    continue
                try:
                    text = p.read_text(errors="ignore")
                    for i, line in enumerate(text.splitlines(), 1):
                        if query in line and re.search(r'\b(def|class|function|fn|struct|enum|interface|type|const|let|var|pub)\b', line):
                            results.append({"uri": str(p), "line": i, "text": line.strip(), "type": "definition"})
                            if len(results) >= max_results:
                                break
                except (OSError, UnicodeDecodeError):
                    continue
            return {"query": query, "results": results, "count": len(results)}

        @self.action("outline", "List symbols with import count and export flag")
        async def outline(ctx: MCPContext, path: str, text: str | None = None) -> dict:
            import re
            full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
            if text is None:
                if not full_path.exists():
                    raise NotFoundError(f"File not found: {path}")
                text = full_path.read_text()
            lines = text.splitlines()
            syms = []
            imports = 0
            sym_re = re.compile(r'(?:export\s+)?(?:async\s+)?(?:function|class|interface|type|enum|const|let|var|def|fn|pub\s+fn|pub\s+struct|struct|impl)\s+(\w+)')
            imp_re = re.compile(r'^(?:import|from|require|use)\b')
            for i, line in enumerate(lines, 1):
                if imp_re.match(line.strip()):
                    imports += 1
                m = sym_re.search(line)
                if m:
                    kind_m = re.search(r'\b(class|interface|type|enum|function|const|struct|impl|fn|def)\b', line)
                    syms.append({"name": m.group(1), "kind": kind_m.group(1) if kind_m else "symbol", "line": i, "exported": line.strip().startswith(("export ", "pub "))})
            return {"uri": str(full_path), "symbols": syms, "imports": imports, "lines": len(lines)}

        @self.action("metrics", "Count files and lines by extension")
        async def metrics(ctx: MCPContext, path: str | None = None) -> dict:
            search_dir = Path(path) if path else Path(self.cwd)
            skip_dirs = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}
            by_ext: dict[str, dict[str, int]] = {}
            total_files = 0
            total_lines = 0
            for p in search_dir.rglob("*"):
                if any(sd in p.parts for sd in skip_dirs) or not p.is_file():
                    continue
                ext = p.suffix or "other"
                try:
                    lines = len(p.read_text(errors="ignore").splitlines())
                    if ext not in by_ext:
                        by_ext[ext] = {"files": 0, "lines": 0}
                    by_ext[ext]["files"] += 1
                    by_ext[ext]["lines"] += lines
                    total_files += 1
                    total_lines += lines
                except (OSError, UnicodeDecodeError):
                    continue
            return {"total_files": total_files, "total_lines": total_lines, "by_extension": by_ext}

        @self.action("exports", "Extract public exports from file")
        async def exports(ctx: MCPContext, path: str) -> dict:
            full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
            if not full_path.exists():
                raise NotFoundError(f"File not found: {path}")
            text = full_path.read_text()
            export_lines = [l.strip() for l in text.splitlines() if l.strip().startswith(("export ", "pub ", "__all__"))]
            return {"uri": str(full_path), "exports": export_lines, "count": len(export_lines)}

        @self.action("types", "Find type definitions in file")
        async def types(ctx: MCPContext, path: str) -> dict:
            import re
            full_path = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
            if not full_path.exists():
                raise NotFoundError(f"File not found: {path}")
            text = full_path.read_text()
            type_defs = []
            type_re = re.compile(r'(?:interface|type|enum|struct|class)\s+(\w+)')
            for i, line in enumerate(text.splitlines(), 1):
                m = type_re.search(line)
                if m:
                    type_defs.append({"name": m.group(1), "line": i, "text": line.strip()})
            return {"uri": str(full_path), "types": type_defs, "count": len(type_defs)}

        @self.action("hierarchy", "Build class inheritance tree")
        async def hierarchy(ctx: MCPContext, query: str, path: str | None = None) -> dict:
            import re
            search_dir = Path(path) if path else Path(self.cwd)
            skip_dirs = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}
            classes: dict[str, list[str]] = {}
            class_re = re.compile(r'class\s+(\w+)(?:\s*\(([^)]+)\)|\s+extends\s+(\w+))?')
            for p in search_dir.rglob("*"):
                if any(sd in p.parts for sd in skip_dirs) or not p.is_file() or p.suffix not in LANG_MAP:
                    continue
                try:
                    for m in class_re.finditer(p.read_text(errors="ignore")):
                        name = m.group(1)
                        parent = m.group(3) or (m.group(2).split(",")[0].strip() if m.group(2) else None)
                        if name not in classes:
                            classes[name] = []
                        if parent and parent not in ("object", "Object"):
                            classes.setdefault(parent, []).append(name)
                except (OSError, UnicodeDecodeError):
                    continue
            def build(n: str, d: int = 0) -> str:
                out = "  " * d + n + "\n"
                for c in classes.get(n, []):
                    out += build(c, d + 1)
                return out
            return {"root": query, "tree": build(query), "children": classes.get(query, [])}

        @self.action("rename", "Rename symbol across files")
        async def rename(ctx: MCPContext, query: str, new_name: str, path: str | None = None) -> dict:
            import re
            search_dir = Path(path) if path else Path(self.cwd)
            skip_dirs = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}
            total_changes = 0
            changed = []
            word_re = re.compile(rf'\b{re.escape(query)}\b')
            for p in search_dir.rglob("*"):
                if any(sd in p.parts for sd in skip_dirs) or not p.is_file() or p.suffix not in LANG_MAP:
                    continue
                try:
                    text = p.read_text(errors="ignore")
                    if word_re.search(text):
                        count = len(word_re.findall(text))
                        p.write_text(word_re.sub(new_name, text))
                        total_changes += count
                        changed.append(f"{p}: {count} replacements")
                except (OSError, UnicodeDecodeError):
                    continue
            return {"old_name": query, "new_name": new_name, "files_changed": len(changed), "total_replacements": total_changes, "changed": changed}

        @self.action("grep_replace", "Pattern replacement across codebase")
        async def grep_replace(ctx: MCPContext, query: str, replacement: str, path: str | None = None) -> dict:
            import re as re_mod
            search_dir = Path(path) if path else Path(self.cwd)
            skip_dirs = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}
            total_changes = 0
            changed = []
            try:
                regex = re_mod.compile(query)
            except re_mod.error as e:
                raise InvalidParamsError(f"Invalid regex: {e}", param="query")
            for p in search_dir.rglob("*"):
                if any(sd in p.parts for sd in skip_dirs) or not p.is_file() or p.suffix not in LANG_MAP:
                    continue
                try:
                    text = p.read_text(errors="ignore")
                    if regex.search(text):
                        count = len(regex.findall(text))
                        p.write_text(regex.sub(replacement, text))
                        total_changes += count
                        changed.append(f"{p}: {count}")
                except (OSError, UnicodeDecodeError):
                    continue
            return {"pattern": query, "replacement": replacement, "files_changed": len(changed), "total_replacements": total_changes, "changed": changed}


# Singleton instance
code_tool = CodeTool
