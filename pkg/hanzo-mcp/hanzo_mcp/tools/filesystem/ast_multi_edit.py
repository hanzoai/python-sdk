"""AST-aware multi-edit tool using treesitter for accurate code modifications."""

from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

from hanzo_mcp.types import MCPResourceDocument
from hanzo_mcp.tools.common.base import BaseTool

try:
    import tree_sitter
    import tree_sitter_go
    import tree_sitter_cpp
    import tree_sitter_java
    import tree_sitter_rust
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript

    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False


@dataclass
class ASTMatch:
    """Represents an AST match with context."""

    file_path: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    node_type: str
    text: str
    parent_context: Optional[str] = None
    semantic_context: Optional[str] = None


@dataclass
class EditOperation:
    """Enhanced edit operation with AST awareness."""

    old_string: str
    new_string: str
    node_types: Optional[List[str]] = None  # Restrict to specific AST node types
    semantic_match: bool = False  # Use semantic matching
    expect_count: Optional[int] = None  # Expected number of matches
    context_lines: int = 5  # Lines of context for uniqueness


class ASTMultiEdit(BaseTool):
    """Multi-edit tool with AST awareness and automatic reference finding."""

    name = "ast_multi_edit"
    description = """Enhanced multi-edit with AST awareness and reference finding.
    
    Features:
    - AST-based search for accurate matches
    - Automatic reference finding across codebase
    - Semantic matching (find all usages of a symbol)
    - Result pagination to avoid token limits
    - Context-aware replacements
    
    Examples:
    1. Rename a function and all its calls:
       ast_multi_edit("file.py", [
           {"old_string": "oldFunc", "new_string": "newFunc", "semantic_match": true}
       ])
    
    2. Update specific node types only:
       ast_multi_edit("file.go", [
           {"old_string": "StopTracking", "new_string": "StopTrackingWithContext",
            "node_types": ["call_expression"]}
       ])
    """

    def __init__(self):
        super().__init__()
        self.parsers = {}
        self.languages = {}

        if TREESITTER_AVAILABLE:
            self._init_parsers()

    def _init_parsers(self):
        """Initialize treesitter parsers for supported languages."""
        language_mapping = {
            ".py": (tree_sitter_python, "python"),
            ".js": (tree_sitter_javascript, "javascript"),
            ".jsx": (tree_sitter_javascript, "javascript"),
            ".ts": (tree_sitter_typescript.typescript, "typescript"),
            ".tsx": (tree_sitter_typescript.tsx, "tsx"),
            ".go": (tree_sitter_go, "go"),
            ".rs": (tree_sitter_rust, "rust"),
            ".java": (tree_sitter_java, "java"),
            ".cpp": (tree_sitter_cpp, "cpp"),
            ".cc": (tree_sitter_cpp, "cpp"),
            ".cxx": (tree_sitter_cpp, "cpp"),
            ".h": (tree_sitter_cpp, "cpp"),
            ".hpp": (tree_sitter_cpp, "cpp"),
        }

        for ext, (module, name) in language_mapping.items():
            try:
                parser = tree_sitter.Parser()
                if hasattr(module, "language"):
                    parser.set_language(module.language())
                else:
                    # For older tree-sitter bindings
                    lang = tree_sitter.Language(module.language(), name)
                    parser.set_language(lang)
                self.parsers[ext] = parser
                self.languages[ext] = name
            except Exception as e:
                print(f"Failed to initialize parser for {ext}: {e}")

    def _get_parser(self, file_path: str) -> Optional[tree_sitter.Parser]:
        """Get parser for file type."""
        ext = Path(file_path).suffix.lower()
        return self.parsers.get(ext)

    def _parse_file(self, file_path: str, content: str) -> Optional[tree_sitter.Tree]:
        """Parse file content into AST."""
        parser = self._get_parser(file_path)
        if not parser:
            return None

        return parser.parse(bytes(content, "utf-8"))

    def _find_references(self, symbol: str, file_path: str, project_root: Optional[str] = None) -> List[ASTMatch]:
        """Find all references to a symbol across the project."""
        matches = []

        if not project_root:
            project_root = self._find_project_root(file_path)

        # Get language-specific reference patterns
        patterns = self._get_reference_patterns(symbol, file_path)

        # Search across all relevant files
        for pattern in patterns:
            # Use grep_ast tool for efficient AST-aware search
            results = self._search_with_ast(pattern, project_root)
            matches.extend(results)

        return matches

    def _get_reference_patterns(self, symbol: str, file_path: str) -> List[Dict[str, Any]]:
        """Get language-specific patterns for finding references."""
        ext = Path(file_path).suffix.lower()
        lang = self.languages.get(ext, "generic")

        patterns = []

        if lang == "go":
            # Go specific patterns
            patterns.extend(
                [
                    # Function calls
                    {
                        "query": f'(call_expression function: (identifier) @func (#eq? @func "{symbol}"))',
                        "type": "call",
                    },
                    # Method calls
                    {
                        "query": f'(call_expression function: (selector_expression field: (field_identifier) @method (#eq? @method "{symbol}")))',
                        "type": "method_call",
                    },
                    # Function declarations
                    {
                        "query": f'(function_declaration name: (identifier) @name (#eq? @name "{symbol}"))',
                        "type": "declaration",
                    },
                    # Type references
                    {
                        "query": f'(type_identifier) @type (#eq? @type "{symbol}")',
                        "type": "type_ref",
                    },
                ]
            )
        elif lang in ["javascript", "typescript", "tsx"]:
            patterns.extend(
                [
                    # Function calls
                    {
                        "query": f'(call_expression function: (identifier) @func (#eq? @func "{symbol}"))',
                        "type": "call",
                    },
                    # Method calls
                    {
                        "query": f'(call_expression function: (member_expression property: (property_identifier) @prop (#eq? @prop "{symbol}")))',
                        "type": "method_call",
                    },
                    # Function declarations
                    {
                        "query": f'(function_declaration name: (identifier) @name (#eq? @name "{symbol}"))',
                        "type": "declaration",
                    },
                    # Variable declarations
                    {
                        "query": f'(variable_declarator name: (identifier) @var (#eq? @var "{symbol}"))',
                        "type": "variable",
                    },
                ]
            )
        elif lang == "python":
            patterns.extend(
                [
                    # Function calls
                    {
                        "query": f'(call function: (identifier) @func (#eq? @func "{symbol}"))',
                        "type": "call",
                    },
                    # Method calls
                    {
                        "query": f'(call function: (attribute attribute: (identifier) @attr (#eq? @attr "{symbol}")))',
                        "type": "method_call",
                    },
                    # Function definitions
                    {
                        "query": f'(function_definition name: (identifier) @name (#eq? @name "{symbol}"))',
                        "type": "declaration",
                    },
                    # Class definitions
                    {
                        "query": f'(class_definition name: (identifier) @name (#eq? @name "{symbol}"))',
                        "type": "class",
                    },
                ]
            )
        else:
            # Generic patterns
            patterns.append({"query": symbol, "type": "text"})

        return patterns

    def _search_with_ast(self, pattern: Dict[str, Any], root: str) -> List[ASTMatch]:
        """Search using AST patterns."""
        matches = []

        # This would integrate with grep_ast tool
        # For now, simulate the search
        import glob

        for file_path in glob.glob(f"{root}/**/*.*", recursive=True):
            if self._should_skip_file(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = self._parse_file(file_path, content)
                if tree and pattern["type"] != "text":
                    # Use treesitter query
                    matches.extend(self._query_ast(tree, pattern, file_path, content))
                else:
                    # Fallback to text search
                    matches.extend(self._text_search(content, pattern["query"], file_path))

            except Exception:
                continue

        return matches

    def _query_ast(
        self,
        tree: tree_sitter.Tree,
        pattern: Dict[str, Any],
        file_path: str,
        content: str,
    ) -> List[ASTMatch]:
        """Query AST with treesitter pattern."""
        matches = []

        try:
            # Get language for query
            lang_name = self.languages.get(Path(file_path).suffix.lower())
            if not lang_name:
                return matches

            # Execute query
            query = tree_sitter.Query(pattern["query"], lang_name)
            captures = query.captures(tree.root_node)

            lines = content.split("\n")

            for node, _name in captures:
                match = ASTMatch(
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    column_start=node.start_point[1],
                    column_end=node.end_point[1],
                    node_type=node.type,
                    text=content[node.start_byte : node.end_byte],
                    parent_context=self._get_parent_context(node, content),
                    semantic_context=pattern["type"],
                )
                matches.append(match)

        except Exception:
            # Fallback to simple search
            pass

        return matches

    def _get_parent_context(self, node: tree_sitter.Node, content: str) -> Optional[str]:
        """Get parent context for better understanding."""
        parent = node.parent
        if parent:
            # Get parent function/class name
            if parent.type in [
                "function_declaration",
                "function_definition",
                "method_definition",
            ]:
                for child in parent.children:
                    if child.type == "identifier":
                        return f"function: {content[child.start_byte : child.end_byte]}"
            elif parent.type in ["class_declaration", "class_definition"]:
                for child in parent.children:
                    if child.type == "identifier":
                        return f"class: {content[child.start_byte : child.end_byte]}"

        return None

    def _text_search(self, content: str, pattern: str, file_path: str) -> List[ASTMatch]:
        """Fallback text search."""
        matches = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if pattern in line:
                col = line.find(pattern)
                match = ASTMatch(
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    column_start=col,
                    column_end=col + len(pattern),
                    node_type="text",
                    text=pattern,
                    semantic_context="text_match",
                )
                matches.append(match)

        return matches

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped."""
        skip_dirs = {
            ".git",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            "venv",
            ".env",
        }
        skip_extensions = {".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe"}

        path = Path(file_path)

        # Check directories
        for part in path.parts:
            if part in skip_dirs:
                return True

        # Check extensions
        if path.suffix in skip_extensions:
            return True

        # Check if binary
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(512)
                if b"\0" in chunk:
                    return True
        except Exception:
            return True

        return False

    def _find_project_root(self, file_path: str) -> str:
        """Find project root by looking for markers."""
        markers = {
            ".git",
            "package.json",
            "go.mod",
            "Cargo.toml",
            "pyproject.toml",
            "setup.py",
        }

        path = Path(file_path).resolve()
        for parent in path.parents:
            for marker in markers:
                if (parent / marker).exists():
                    return str(parent)

        return str(path.parent)

    def _group_matches_by_file(self, matches: List[ASTMatch]) -> Dict[str, List[ASTMatch]]:
        """Group matches by file for efficient editing."""
        grouped = defaultdict(list)
        for match in matches:
            grouped[match.file_path].append(match)
        return grouped

    def _create_unique_context(self, content: str, match: ASTMatch, context_lines: int) -> str:
        """Create unique context for edit identification."""
        lines = content.split("\n")

        start_line = max(0, match.line_start - context_lines - 1)
        end_line = min(len(lines), match.line_end + context_lines)

        context_lines = lines[start_line:end_line]
        return "\n".join(context_lines)

    async def run(
        self,
        file_path: str,
        edits: List[Dict[str, Any]],
        find_references: bool = False,
        page_size: int = 50,
        preview_only: bool = False,
        **kwargs,
    ) -> MCPResourceDocument:
        """Execute AST-aware multi-edit operation.

        Args:
            file_path: Primary file to edit
            edits: List of edit operations
            find_references: Whether to find and edit references across codebase
            page_size: Number of results per page
            preview_only: Show what would be changed without applying
        """

        if not TREESITTER_AVAILABLE:
            return self._fallback_to_basic_edit(file_path, edits)

        results = {
            "primary_file": file_path,
            "edits_requested": len(edits),
            "files_analyzed": 0,
            "matches_found": 0,
            "edits_applied": 0,
            "errors": [],
            "changes": [],
        }

        # Convert edits to EditOperation objects
        edit_ops = []
        for edit in edits:
            edit_ops.append(
                EditOperation(
                    old_string=edit["old_string"],
                    new_string=edit["new_string"],
                    node_types=edit.get("node_types"),
                    semantic_match=edit.get("semantic_match", False),
                    expect_count=edit.get("expect_count"),
                    context_lines=edit.get("context_lines", 5),
                )
            )

        # Find all matches
        all_matches = []

        # First, analyze primary file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = self._parse_file(file_path, content)

            for edit_op in edit_ops:
                if edit_op.semantic_match and find_references:
                    # Find all references across codebase
                    matches = self._find_references(edit_op.old_string, file_path)
                else:
                    # Just search in current file
                    if tree:
                        pattern = {"query": edit_op.old_string, "type": "text"}
                        matches = self._query_ast(tree, pattern, file_path, content)
                    else:
                        matches = self._text_search(content, edit_op.old_string, file_path)

                # Filter by node types if specified
                if edit_op.node_types:
                    matches = [m for m in matches if m.node_type in edit_op.node_types]

                # Check expected count
                if edit_op.expect_count is not None and len(matches) != edit_op.expect_count:
                    results["errors"].append(
                        {
                            "edit": edit_op.old_string,
                            "expected": edit_op.expect_count,
                            "found": len(matches),
                            "locations": [f"{m.file_path}:{m.line_start}" for m in matches[:5]],
                        }
                    )
                    continue

                all_matches.extend([(edit_op, match) for match in matches])

        except Exception as e:
            results["errors"].append({"file": file_path, "error": str(e)})
            return MCPResourceDocument(data=results)

        results["matches_found"] = len(all_matches)
        results["files_analyzed"] = len(set(m[1].file_path for m in all_matches))

        if preview_only:
            # Return preview of changes
            preview = self._generate_preview(all_matches, page_size)
            results["preview"] = preview
            return MCPResourceDocument(data=results)

        # Apply edits
        changes_by_file = self._group_changes(all_matches)

        for file_path, changes in changes_by_file.items():
            try:
                success = await self._apply_file_changes(file_path, changes)
                if success:
                    results["edits_applied"] += len(changes)
                    results["changes"].append({"file": file_path, "edits": len(changes)})
            except Exception as e:
                results["errors"].append({"file": file_path, "error": str(e)})

        return MCPResourceDocument(data=results)

    def _group_changes(
        self, matches: List[Tuple[EditOperation, ASTMatch]]
    ) -> Dict[str, List[Tuple[EditOperation, ASTMatch]]]:
        """Group changes by file."""
        grouped = defaultdict(list)
        for edit_op, match in matches:
            grouped[match.file_path].append((edit_op, match))
        return grouped

    async def _apply_file_changes(self, file_path: str, changes: List[Tuple[EditOperation, ASTMatch]]) -> bool:
        """Apply changes to a single file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Sort changes by position (reverse order to maintain positions)
        changes.sort(key=lambda x: (x[1].line_start, x[1].column_start), reverse=True)

        lines = content.split("\n")

        for edit_op, match in changes:
            # Create unique context for this match
            context = self._create_unique_context(content, match, edit_op.context_lines)

            # Apply the edit
            if match.line_start == match.line_end:
                # Single line edit
                line = lines[match.line_start - 1]
                before = line[: match.column_start]
                after = line[match.column_end :]
                lines[match.line_start - 1] = before + edit_op.new_string + after
            else:
                # Multi-line edit
                # Remove old lines
                del lines[match.line_start - 1 : match.line_end]
                # Insert new content
                lines.insert(match.line_start - 1, edit_op.new_string)

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True

    def _generate_preview(self, matches: List[Tuple[EditOperation, ASTMatch]], page_size: int) -> List[Dict[str, Any]]:
        """Generate preview of changes."""
        preview = []

        for _i, (edit_op, match) in enumerate(matches[:page_size]):
            preview.append(
                {
                    "file": match.file_path,
                    "line": match.line_start,
                    "column": match.column_start,
                    "node_type": match.node_type,
                    "context": match.parent_context,
                    "old": edit_op.old_string,
                    "new": edit_op.new_string,
                    "semantic_type": match.semantic_context,
                }
            )

        if len(matches) > page_size:
            preview.append({"note": f"... and {len(matches) - page_size} more matches"})

        return preview

    def _fallback_to_basic_edit(self, file_path: str, edits: List[Dict[str, Any]]) -> MCPResourceDocument:
        """Fallback to basic multi-edit when treesitter not available."""
        # Delegate to existing multi_edit tool
        from hanzo_mcp.tools.filesystem.multi_edit import MultiEdit

        basic_tool = MultiEdit()
        return basic_tool.run(file_path, edits)


# Tool registration
def create_ast_multi_edit_tool():
    """Factory function to create AST multi-edit tool."""
    return ASTMultiEdit()
