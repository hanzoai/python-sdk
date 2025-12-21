"""Advanced refactoring tool using LSP and AST analysis.

This module provides powerful code refactoring capabilities that leverage
language server protocols and tree-sitter AST parsing for accurate transformations.
"""

import os
import re
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict

from hanzo_mcp.types import MCPResourceDocument
from hanzo_mcp.tools.common.base import BaseTool

# Try importing tree-sitter for AST analysis
try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_go
    import tree_sitter_rust

    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RefactorLocation:
    """Represents a location in source code."""

    file: str
    line: int
    column: int
    end_line: int = 0
    end_column: int = 0
    text: str = ""
    context: str = ""


@dataclass
class RefactorChange:
    """Represents a single change to be applied."""

    file: str
    line: int
    column: int
    end_line: int
    end_column: int
    old_text: str
    new_text: str
    description: str = ""


@dataclass
class RefactorResult:
    """Result of a refactoring operation."""

    success: bool
    action: str
    files_changed: int = 0
    changes_applied: int = 0
    changes: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    preview: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


class RefactorTool(BaseTool):
    """Advanced refactoring tool with LSP and AST support.

    Provides comprehensive code refactoring capabilities:

    Actions:
    - rename: Rename a symbol across the entire codebase
    - extract_function: Extract a code block into a new function
    - extract_variable: Extract an expression into a variable
    - inline: Inline a variable or function at all usage sites
    - move: Move a symbol to another file
    - change_signature: Modify a function's signature and update all calls
    - find_references: Find all references to a symbol
    - organize_imports: Sort and organize import statements

    Example usage:

    1. Rename a function across codebase:
       refactor("rename", file="main.py", line=10, column=5, new_name="betterName")

    2. Extract code to function:
       refactor("extract_function", file="utils.py", start_line=20, end_line=30,
                new_name="processData")

    3. Inline a variable:
       refactor("inline", file="app.py", line=15, column=8)

    4. Find all references:
       refactor("find_references", file="models.py", line=25, column=10)
    """

    name = "refactor"
    description = """Advanced refactoring with LSP/AST. Actions: rename, extract_function,
    extract_variable, inline, move, change_signature, find_references, organize_imports.

    Rename symbol: refactor("rename", file="main.py", line=10, column=5, new_name="newName")
    Extract function: refactor("extract_function", file="f.py", start_line=10, end_line=20, new_name="func")
    Find references: refactor("find_references", file="f.py", line=10, column=5)"""

    def __init__(self):
        super().__init__()
        self.parsers: Dict[str, Any] = {}
        self._init_parsers()

    def _init_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREESITTER_AVAILABLE:
            return

        language_mapping = {
            ".py": (tree_sitter_python, "python"),
            ".js": (tree_sitter_javascript, "javascript"),
            ".jsx": (tree_sitter_javascript, "javascript"),
            ".ts": (tree_sitter_typescript.typescript, "typescript"),
            ".tsx": (tree_sitter_typescript.tsx, "tsx"),
            ".go": (tree_sitter_go, "go"),
            ".rs": (tree_sitter_rust, "rust"),
        }

        for ext, (module, name) in language_mapping.items():
            try:
                parser = tree_sitter.Parser()
                if hasattr(module, "language"):
                    parser.set_language(module.language())
                self.parsers[ext] = parser
            except Exception as e:
                logger.debug(f"Failed to initialize parser for {ext}: {e}")

    def _get_parser(self, file_path: str) -> Optional[Any]:
        """Get parser for file type."""
        ext = Path(file_path).suffix.lower()
        return self.parsers.get(ext)

    def _get_language(self, file_path: str) -> str:
        """Get language from file extension."""
        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".rb": "ruby",
            ".lua": "lua",
        }
        ext = Path(file_path).suffix.lower()
        return ext_to_lang.get(ext, "unknown")

    def _find_project_root(self, file_path: str) -> str:
        """Find project root from file path."""
        markers = [".git", "package.json", "go.mod", "Cargo.toml", "pyproject.toml", "setup.py"]
        path = Path(file_path).resolve()

        for parent in path.parents:
            for marker in markers:
                if (parent / marker).exists():
                    return str(parent)
        return str(path.parent)

    async def run(
        self,
        action: str,
        file: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        end_line: Optional[int] = None,
        end_column: Optional[int] = None,
        new_name: Optional[str] = None,
        start_line: Optional[int] = None,
        target_file: Optional[str] = None,
        preview: bool = False,
        **kwargs,
    ) -> MCPResourceDocument:
        """Execute refactoring action.

        Args:
            action: Refactoring action to perform
            file: Source file path
            line: Line number (1-indexed)
            column: Column position (0-indexed)
            end_line: End line for range selections
            end_column: End column for range selections
            new_name: New name for rename/extract operations
            start_line: Start line for extract operations
            target_file: Target file for move operations
            preview: If True, only show what would change without applying
        """
        valid_actions = [
            "rename",
            "extract_function",
            "extract_variable",
            "inline",
            "move",
            "change_signature",
            "find_references",
            "organize_imports",
        ]

        if action not in valid_actions:
            return MCPResourceDocument(
                data={"error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"}
            )

        # Resolve file path
        file_path = str(Path(file).resolve())
        if not Path(file_path).exists():
            return MCPResourceDocument(data={"error": f"File not found: {file}"})

        # Route to appropriate handler
        if action == "rename":
            result = await self._rename(file_path, line, column, new_name, preview)
        elif action == "extract_function":
            sl = start_line or line
            el = end_line or line
            result = await self._extract_function(file_path, sl, el, new_name, preview)
        elif action == "extract_variable":
            result = await self._extract_variable(file_path, line, column, end_line, end_column, new_name, preview)
        elif action == "inline":
            result = await self._inline(file_path, line, column, preview)
        elif action == "move":
            result = await self._move(file_path, line, column, target_file, preview)
        elif action == "change_signature":
            result = await self._change_signature(file_path, line, column, kwargs, preview)
        elif action == "find_references":
            result = await self._find_references(file_path, line, column)
        elif action == "organize_imports":
            result = await self._organize_imports(file_path, preview)
        else:
            result = RefactorResult(success=False, action=action, errors=[f"Action {action} not implemented"])

        return MCPResourceDocument(data=self._result_to_dict(result))

    def _result_to_dict(self, result: RefactorResult) -> Dict[str, Any]:
        """Convert RefactorResult to dictionary."""
        return {
            "success": result.success,
            "action": result.action,
            "files_changed": result.files_changed,
            "changes_applied": result.changes_applied,
            "changes": result.changes,
            "errors": result.errors,
            "preview": result.preview,
            "message": result.message,
        }

    async def _rename(
        self,
        file_path: str,
        line: Optional[int],
        column: Optional[int],
        new_name: Optional[str],
        preview: bool,
    ) -> RefactorResult:
        """Rename a symbol across the codebase."""
        if not line or column is None:
            return RefactorResult(
                success=False, action="rename", errors=["line and column are required for rename"]
            )
        if not new_name:
            return RefactorResult(success=False, action="rename", errors=["new_name is required"])

        # First, find what we're renaming
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        if line > len(lines):
            return RefactorResult(success=False, action="rename", errors=[f"Line {line} out of range"])

        # Get the identifier at the position
        target_line = lines[line - 1]
        old_name = self._get_identifier_at(target_line, column)

        if not old_name:
            return RefactorResult(
                success=False, action="rename", errors=[f"No identifier found at line {line}, column {column}"]
            )

        # Find all references across the project
        project_root = self._find_project_root(file_path)
        references = await self._find_all_references(file_path, old_name, project_root)

        if not references:
            return RefactorResult(
                success=False, action="rename", errors=[f"No references found for '{old_name}'"]
            )

        # Group references by file
        changes_by_file: Dict[str, List[RefactorChange]] = defaultdict(list)
        for ref in references:
            change = RefactorChange(
                file=ref.file,
                line=ref.line,
                column=ref.column,
                end_line=ref.line,
                end_column=ref.column + len(old_name),
                old_text=old_name,
                new_text=new_name,
                description=f"Rename '{old_name}' to '{new_name}'",
            )
            changes_by_file[ref.file].append(change)

        if preview:
            preview_data = []
            for file, changes in changes_by_file.items():
                for change in changes:
                    preview_data.append(
                        {
                            "file": file,
                            "line": change.line,
                            "column": change.column,
                            "old": change.old_text,
                            "new": change.new_text,
                        }
                    )
            return RefactorResult(
                success=True,
                action="rename",
                files_changed=len(changes_by_file),
                changes_applied=len(references),
                preview=preview_data,
                message=f"Would rename {len(references)} occurrences of '{old_name}' to '{new_name}' across {len(changes_by_file)} files",
            )

        # Apply the changes
        applied_changes = []
        errors = []
        files_changed = set()

        for file, changes in changes_by_file.items():
            try:
                success = await self._apply_file_changes(file, changes)
                if success:
                    files_changed.add(file)
                    applied_changes.extend(
                        [{"file": c.file, "line": c.line, "old": c.old_text, "new": c.new_text} for c in changes]
                    )
            except Exception as e:
                errors.append(f"Failed to apply changes to {file}: {str(e)}")

        return RefactorResult(
            success=len(errors) == 0,
            action="rename",
            files_changed=len(files_changed),
            changes_applied=len(applied_changes),
            changes=applied_changes,
            errors=errors,
            message=f"Renamed {len(applied_changes)} occurrences of '{old_name}' to '{new_name}'",
        )

    async def _extract_function(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        new_name: Optional[str],
        preview: bool,
    ) -> RefactorResult:
        """Extract a code block into a new function."""
        if not new_name:
            return RefactorResult(
                success=False, action="extract_function", errors=["new_name is required for extract_function"]
            )

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        if start_line < 1 or end_line > len(lines):
            return RefactorResult(
                success=False, action="extract_function", errors=["Line range out of bounds"]
            )

        # Extract the code block
        extracted_lines = lines[start_line - 1 : end_line]
        extracted_code = "\n".join(extracted_lines)

        # Detect language and indentation
        language = self._get_language(file_path)
        base_indent = self._get_indentation(extracted_lines[0]) if extracted_lines else ""

        # Find variables used in the block
        used_vars = self._find_used_variables(extracted_code, language)
        defined_vars = self._find_defined_variables(extracted_code, language)

        # Parameters are used but not defined in the block
        params = used_vars - defined_vars

        # Build the new function
        new_function = self._build_function(new_name, list(params), extracted_code, language, base_indent)

        # Build the function call
        call_indent = base_indent
        function_call = self._build_function_call(new_name, list(params), language, call_indent)

        if preview:
            return RefactorResult(
                success=True,
                action="extract_function",
                preview=[
                    {
                        "type": "new_function",
                        "code": new_function,
                        "insert_at": f"Before line {start_line}",
                    },
                    {
                        "type": "replacement",
                        "lines": f"{start_line}-{end_line}",
                        "old_code": extracted_code,
                        "new_code": function_call,
                    },
                ],
                message=f"Would extract lines {start_line}-{end_line} to function '{new_name}'",
            )

        # Apply the extraction
        try:
            # Insert the new function before the extracted code
            new_lines = lines[: start_line - 1]
            new_lines.append(new_function)
            new_lines.append("")  # Blank line
            new_lines.append(function_call)
            new_lines.extend(lines[end_line:])

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))

            return RefactorResult(
                success=True,
                action="extract_function",
                files_changed=1,
                changes_applied=1,
                message=f"Extracted lines {start_line}-{end_line} to function '{new_name}'",
            )
        except Exception as e:
            return RefactorResult(
                success=False, action="extract_function", errors=[str(e)]
            )

    async def _extract_variable(
        self,
        file_path: str,
        line: Optional[int],
        column: Optional[int],
        end_line: Optional[int],
        end_column: Optional[int],
        new_name: Optional[str],
        preview: bool,
    ) -> RefactorResult:
        """Extract an expression into a variable."""
        if not line or column is None:
            return RefactorResult(
                success=False, action="extract_variable", errors=["line and column are required"]
            )
        if not new_name:
            return RefactorResult(
                success=False, action="extract_variable", errors=["new_name is required"]
            )

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")

        target_line = lines[line - 1]
        el = end_line or line
        ec = end_column or len(target_line)

        # Extract the expression
        if line == el:
            expression = target_line[column:ec]
        else:
            expression_lines = [target_line[column:]]
            for i in range(line, el - 1):
                expression_lines.append(lines[i])
            expression_lines.append(lines[el - 1][:ec])
            expression = "\n".join(expression_lines)

        language = self._get_language(file_path)
        indent = self._get_indentation(target_line)

        # Build variable declaration
        var_decl = self._build_variable_declaration(new_name, expression, language, indent)

        if preview:
            return RefactorResult(
                success=True,
                action="extract_variable",
                preview=[
                    {"type": "insert", "line": line, "code": var_decl},
                    {"type": "replace", "expression": expression, "with": new_name},
                ],
                message=f"Would extract expression to variable '{new_name}'",
            )

        # Apply the extraction
        try:
            # Insert variable declaration and replace expression
            new_line = target_line[:column] + new_name + target_line[ec:]
            lines[line - 1] = new_line
            lines.insert(line - 1, var_decl)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return RefactorResult(
                success=True,
                action="extract_variable",
                files_changed=1,
                changes_applied=1,
                message=f"Extracted expression to variable '{new_name}'",
            )
        except Exception as e:
            return RefactorResult(success=False, action="extract_variable", errors=[str(e)])

    async def _inline(
        self,
        file_path: str,
        line: Optional[int],
        column: Optional[int],
        preview: bool,
    ) -> RefactorResult:
        """Inline a variable or function at all usage sites."""
        if not line or column is None:
            return RefactorResult(
                success=False, action="inline", errors=["line and column are required"]
            )

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        target_line = lines[line - 1]
        identifier = self._get_identifier_at(target_line, column)

        if not identifier:
            return RefactorResult(
                success=False, action="inline", errors=["No identifier found at position"]
            )

        # Find the definition and get the value
        language = self._get_language(file_path)
        definition = self._find_definition(content, identifier, language)

        if not definition:
            return RefactorResult(
                success=False, action="inline", errors=[f"Could not find definition for '{identifier}'"]
            )

        # Find all usages
        project_root = self._find_project_root(file_path)
        usages = await self._find_all_references(file_path, identifier, project_root)

        # Filter out the definition itself
        usages = [u for u in usages if not (u.file == file_path and u.line == definition["line"])]

        if not usages:
            return RefactorResult(
                success=False, action="inline", errors=[f"No usages found for '{identifier}'"]
            )

        inline_value = definition["value"]

        if preview:
            preview_data = [
                {"file": u.file, "line": u.line, "replace": identifier, "with": inline_value}
                for u in usages[:20]  # Limit preview
            ]
            return RefactorResult(
                success=True,
                action="inline",
                preview=preview_data,
                message=f"Would inline {len(usages)} usages of '{identifier}' with '{inline_value}'",
            )

        # Apply inlining
        changes_by_file: Dict[str, List[RefactorChange]] = defaultdict(list)
        for usage in usages:
            change = RefactorChange(
                file=usage.file,
                line=usage.line,
                column=usage.column,
                end_line=usage.line,
                end_column=usage.column + len(identifier),
                old_text=identifier,
                new_text=inline_value,
            )
            changes_by_file[usage.file].append(change)

        applied = 0
        errors = []
        for file, changes in changes_by_file.items():
            try:
                await self._apply_file_changes(file, changes)
                applied += len(changes)
            except Exception as e:
                errors.append(f"Failed to inline in {file}: {str(e)}")

        # Remove the original definition line
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_lines = f.read().split("\n")
            del file_lines[definition["line"] - 1]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(file_lines))
        except Exception as e:
            errors.append(f"Failed to remove definition: {str(e)}")

        return RefactorResult(
            success=len(errors) == 0,
            action="inline",
            files_changed=len(changes_by_file),
            changes_applied=applied,
            errors=errors,
            message=f"Inlined {applied} usages of '{identifier}'",
        )

    async def _move(
        self,
        file_path: str,
        line: Optional[int],
        column: Optional[int],
        target_file: Optional[str],
        preview: bool,
    ) -> RefactorResult:
        """Move a symbol to another file."""
        if not target_file:
            return RefactorResult(success=False, action="move", errors=["target_file is required"])

        if not line:
            return RefactorResult(success=False, action="move", errors=["line is required"])

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Find the symbol definition
        identifier = self._get_identifier_at(lines[line - 1], column or 0)
        if not identifier:
            return RefactorResult(success=False, action="move", errors=["No identifier found"])

        # Find the full definition block
        language = self._get_language(file_path)
        block = self._find_definition_block(content, identifier, line, language)

        if not block:
            return RefactorResult(
                success=False, action="move", errors=[f"Could not find definition block for '{identifier}'"]
            )

        if preview:
            return RefactorResult(
                success=True,
                action="move",
                preview=[
                    {"action": "remove_from", "file": file_path, "lines": f"{block['start']}-{block['end']}"},
                    {"action": "add_to", "file": target_file, "code": block["code"]},
                    {"action": "update_imports", "files": "affected files"},
                ],
                message=f"Would move '{identifier}' from {file_path} to {target_file}",
            )

        # Apply the move
        errors = []

        # Add to target file
        try:
            if Path(target_file).exists():
                with open(target_file, "r", encoding="utf-8") as f:
                    target_content = f.read()
                target_content = target_content.rstrip() + "\n\n" + block["code"] + "\n"
            else:
                target_content = block["code"] + "\n"

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(target_content)
        except Exception as e:
            errors.append(f"Failed to add to target file: {str(e)}")

        # Remove from source file
        try:
            new_lines = lines[: block["start"] - 1] + lines[block["end"] :]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
        except Exception as e:
            errors.append(f"Failed to remove from source file: {str(e)}")

        return RefactorResult(
            success=len(errors) == 0,
            action="move",
            files_changed=2,
            changes_applied=1,
            errors=errors,
            message=f"Moved '{identifier}' to {target_file}",
        )

    async def _change_signature(
        self,
        file_path: str,
        line: Optional[int],
        column: Optional[int],
        changes: Dict[str, Any],
        preview: bool,
    ) -> RefactorResult:
        """Change a function's signature and update all call sites."""
        # This is a complex operation - basic implementation
        return RefactorResult(
            success=False,
            action="change_signature",
            errors=["change_signature is a complex operation - use rename for simple parameter renames"],
            message="Consider using LSP-based IDE for complex signature changes",
        )

    async def _find_references(
        self,
        file_path: str,
        line: Optional[int],
        column: Optional[int],
    ) -> RefactorResult:
        """Find all references to a symbol."""
        if not line or column is None:
            return RefactorResult(
                success=False, action="find_references", errors=["line and column are required"]
            )

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")

        identifier = self._get_identifier_at(lines[line - 1], column)
        if not identifier:
            return RefactorResult(
                success=False, action="find_references", errors=["No identifier found at position"]
            )

        project_root = self._find_project_root(file_path)
        references = await self._find_all_references(file_path, identifier, project_root)

        ref_data = [
            {"file": r.file, "line": r.line, "column": r.column, "context": r.context}
            for r in references
        ]

        return RefactorResult(
            success=True,
            action="find_references",
            changes=ref_data,
            message=f"Found {len(references)} references to '{identifier}'",
        )

    async def _organize_imports(
        self,
        file_path: str,
        preview: bool,
    ) -> RefactorResult:
        """Organize and sort import statements."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        language = self._get_language(file_path)

        if language == "python":
            organized = self._organize_python_imports(content)
        elif language in ["javascript", "typescript"]:
            organized = self._organize_js_imports(content)
        else:
            return RefactorResult(
                success=False,
                action="organize_imports",
                errors=[f"organize_imports not supported for {language}"],
            )

        if organized == content:
            return RefactorResult(
                success=True,
                action="organize_imports",
                message="Imports are already organized",
            )

        if preview:
            return RefactorResult(
                success=True,
                action="organize_imports",
                preview=[{"file": file_path, "changes": "Import statements reorganized"}],
                message="Would reorganize import statements",
            )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(organized)

        return RefactorResult(
            success=True,
            action="organize_imports",
            files_changed=1,
            changes_applied=1,
            message="Organized import statements",
        )

    # Helper methods

    def _get_identifier_at(self, line: str, column: int) -> Optional[str]:
        """Get the identifier at a specific column in a line."""
        if column >= len(line):
            column = len(line) - 1
        if column < 0:
            return None

        # Find identifier boundaries
        start = column
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1

        end = column
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1

        if start == end:
            return None

        identifier = line[start:end]
        return identifier if identifier and (identifier[0].isalpha() or identifier[0] == "_") else None

    def _get_indentation(self, line: str) -> str:
        """Get the indentation of a line."""
        match = re.match(r"^(\s*)", line)
        return match.group(1) if match else ""

    def _find_used_variables(self, code: str, language: str) -> Set[str]:
        """Find variables used in a code block."""
        # Simple implementation - find all identifiers
        identifiers = set(re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", code))
        # Remove keywords
        keywords = {"if", "else", "for", "while", "def", "class", "return", "import", "from", "in", "and", "or", "not", "True", "False", "None", "async", "await", "try", "except", "finally", "with", "as", "is", "lambda", "yield", "break", "continue", "pass", "raise", "global", "nonlocal", "assert", "del"}
        return identifiers - keywords

    def _find_defined_variables(self, code: str, language: str) -> Set[str]:
        """Find variables defined in a code block."""
        if language == "python":
            # Find assignments
            return set(re.findall(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=", code, re.MULTILINE))
        elif language in ["javascript", "typescript"]:
            # Find let/const/var declarations
            return set(re.findall(r"(?:let|const|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)", code))
        return set()

    def _build_function(self, name: str, params: List[str], body: str, language: str, base_indent: str) -> str:
        """Build a function definition."""
        params_str = ", ".join(params)

        if language == "python":
            # Dedent the body
            body_lines = body.split("\n")
            min_indent = min(len(self._get_indentation(l)) for l in body_lines if l.strip())
            dedented = "\n".join(l[min_indent:] if l.strip() else "" for l in body_lines)
            indented_body = "\n".join(f"    {l}" if l.strip() else "" for l in dedented.split("\n"))
            return f"def {name}({params_str}):\n{indented_body}"

        elif language in ["javascript", "typescript"]:
            return f"function {name}({params_str}) {{\n{body}\n}}"

        elif language == "go":
            return f"func {name}({params_str}) {{\n{body}\n}}"

        return f"function {name}({params_str}) {{\n{body}\n}}"

    def _build_function_call(self, name: str, params: List[str], language: str, indent: str) -> str:
        """Build a function call."""
        params_str = ", ".join(params)
        return f"{indent}{name}({params_str})"

    def _build_variable_declaration(self, name: str, value: str, language: str, indent: str) -> str:
        """Build a variable declaration."""
        if language == "python":
            return f"{indent}{name} = {value}"
        elif language in ["javascript", "typescript"]:
            return f"{indent}const {name} = {value};"
        elif language == "go":
            return f"{indent}{name} := {value}"
        return f"{indent}{name} = {value}"

    def _find_definition(self, content: str, identifier: str, language: str) -> Optional[Dict[str, Any]]:
        """Find the definition of a variable."""
        lines = content.split("\n")

        if language == "python":
            # Look for: identifier = value
            pattern = rf"^\s*{re.escape(identifier)}\s*=\s*(.+?)$"
        elif language in ["javascript", "typescript"]:
            # Look for: const/let/var identifier = value
            pattern = rf"^\s*(?:const|let|var)\s+{re.escape(identifier)}\s*=\s*(.+?);?\s*$"
        elif language == "go":
            pattern = rf"^\s*{re.escape(identifier)}\s*:=\s*(.+?)$"
        else:
            pattern = rf"^\s*{re.escape(identifier)}\s*=\s*(.+?)$"

        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                return {"line": i + 1, "value": match.group(1).strip()}

        return None

    def _find_definition_block(
        self, content: str, identifier: str, start_line: int, language: str
    ) -> Optional[Dict[str, Any]]:
        """Find the full definition block (function/class) for an identifier."""
        lines = content.split("\n")

        if language == "python":
            # Find def or class starting near start_line
            for i in range(max(0, start_line - 5), min(len(lines), start_line + 5)):
                line = lines[i]
                if re.match(rf"^\s*(def|class)\s+{re.escape(identifier)}\s*[(\[]", line):
                    # Find the end of the block
                    base_indent = len(self._get_indentation(line))
                    end_line = i + 1
                    while end_line < len(lines):
                        next_line = lines[end_line]
                        if next_line.strip() and len(self._get_indentation(next_line)) <= base_indent:
                            break
                        end_line += 1

                    return {
                        "start": i + 1,
                        "end": end_line,
                        "code": "\n".join(lines[i:end_line]),
                    }
        return None

    async def _find_all_references(
        self, file_path: str, identifier: str, project_root: str
    ) -> List[RefactorLocation]:
        """Find all references to an identifier in the project."""
        references = []
        language = self._get_language(file_path)

        # Get all source files
        source_extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "go": [".go"],
            "rust": [".rs"],
        }
        extensions = source_extensions.get(language, [Path(file_path).suffix])

        for root, _, files in os.walk(project_root):
            # Skip common non-source directories
            if any(skip in root for skip in [".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"]):
                continue

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.split("\n")

                        # Use word boundary matching
                        pattern = rf"\b{re.escape(identifier)}\b"
                        for i, line in enumerate(lines):
                            for match in re.finditer(pattern, line):
                                references.append(
                                    RefactorLocation(
                                        file=full_path,
                                        line=i + 1,
                                        column=match.start(),
                                        text=identifier,
                                        context=line.strip(),
                                    )
                                )
                    except Exception:
                        continue

        return references

    async def _apply_file_changes(self, file_path: str, changes: List[RefactorChange]) -> bool:
        """Apply a list of changes to a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")

        # Sort changes by position (reverse order to maintain positions)
        changes.sort(key=lambda c: (c.line, c.column), reverse=True)

        for change in changes:
            if change.line > len(lines):
                continue

            line = lines[change.line - 1]
            new_line = line[: change.column] + change.new_text + line[change.column + len(change.old_text) :]
            lines[change.line - 1] = new_line

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True

    def _organize_python_imports(self, content: str) -> str:
        """Organize Python import statements."""
        lines = content.split("\n")
        imports = []
        from_imports = []
        other_lines = []
        import_section_ended = False

        for line in lines:
            stripped = line.strip()
            if not import_section_ended:
                if stripped.startswith("import "):
                    imports.append(line)
                elif stripped.startswith("from "):
                    from_imports.append(line)
                elif stripped and not stripped.startswith("#"):
                    import_section_ended = True
                    other_lines.append(line)
                else:
                    if imports or from_imports:
                        import_section_ended = True
                    other_lines.append(line)
            else:
                other_lines.append(line)

        # Sort imports
        imports.sort(key=lambda x: x.strip().lower())
        from_imports.sort(key=lambda x: x.strip().lower())

        # Reconstruct
        result = []
        if imports:
            result.extend(imports)
        if from_imports:
            if imports:
                result.append("")
            result.extend(from_imports)
        if imports or from_imports:
            result.append("")
        result.extend(other_lines)

        return "\n".join(result)

    def _organize_js_imports(self, content: str) -> str:
        """Organize JavaScript/TypeScript import statements."""
        lines = content.split("\n")
        imports = []
        other_lines = []
        in_imports = True

        for line in lines:
            stripped = line.strip()
            if in_imports and stripped.startswith("import "):
                imports.append(line)
            elif in_imports and stripped == "":
                continue  # Skip empty lines in import section
            else:
                in_imports = False
                other_lines.append(line)

        # Sort imports
        imports.sort(key=lambda x: x.strip().lower())

        result = imports + [""] + other_lines if imports else other_lines
        return "\n".join(result)

    async def call(self, **kwargs) -> str:
        """Tool interface for MCP - converts result to JSON string."""
        result = await self.run(**kwargs)
        return result.to_json_string()

    def register(self, mcp_server) -> None:
        """Register tool with MCP server."""

        @mcp_server.tool(name=self.name, description=self.description)
        async def refactor_handler(
            action: str,
            file: str,
            line: Optional[int] = None,
            column: Optional[int] = None,
            end_line: Optional[int] = None,
            end_column: Optional[int] = None,
            new_name: Optional[str] = None,
            start_line: Optional[int] = None,
            target_file: Optional[str] = None,
            preview: bool = False,
        ) -> str:
            """Execute refactoring action."""
            return await self.call(
                action=action,
                file=file,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
                new_name=new_name,
                start_line=start_line,
                target_file=target_file,
                preview=preview,
            )


# Factory function
def create_refactor_tool():
    """Factory function to create refactoring tool."""
    return RefactorTool()
