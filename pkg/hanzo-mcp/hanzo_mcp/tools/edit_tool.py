"""
Edit Tool - Semantic refactoring via LSP
========================================

Purpose: semantic refactors via LSP across languages.

Operations:
- rename: Rename symbol across workspace
- code_action: Apply LSP code actions
- organize_imports: Organize imports
- apply_workspace_edit: Apply arbitrary WorkspaceEdit

Supports gopls, tsserver, pyright, rust-analyzer, clangd
"""

from typing import Any, Dict, List, Optional

from .dev_tools import DevResult, DevToolBase, create_dev_result


class EditTool(DevToolBase):
    """LSP-powered semantic editing tool"""

    def __init__(self, target: str, op: str, **kwargs):
        super().__init__(target, **kwargs)
        self.op = op
        self.file = kwargs.get("file")
        self.pos = kwargs.get("pos")  # {line: int, character: int}
        self.range = kwargs.get("range")  # {start: {line, ch}, end: {line, ch}}
        self.new_name = kwargs.get("new_name")
        self.only = kwargs.get("only", [])  # code action kinds
        self.apply = kwargs.get("apply", True)

    async def execute(self) -> DevResult:
        """Execute edit operation"""
        try:
            if self.op == "rename":
                return await self._rename()
            elif self.op == "code_action":
                return await self._code_action()
            elif self.op == "organize_imports":
                return await self._organize_imports()
            elif self.op == "apply_workspace_edit":
                return await self._apply_workspace_edit()
            else:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used=self.backend,
                    scope_resolved=self.target,
                    errors=[f"Unknown operation: {self.op}"],
                )
        except Exception as e:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[str(e)],
            )

    async def _rename(self) -> DevResult:
        """Rename symbol using LSP"""
        if not self.file or not self.pos or not self.new_name:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=["rename requires file, pos, and new_name"],
            )

        # Use appropriate LSP client based on language
        if self.language == "go":
            return await self._gopls_rename()
        elif self.language == "ts":
            return await self._typescript_rename()
        elif self.language == "py":
            return await self._pyright_rename()
        elif self.language == "rs":
            return await self._rust_analyzer_rename()
        else:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[f"Rename not supported for language: {self.language}"],
            )

    async def _code_action(self) -> DevResult:
        """Apply code actions"""
        if self.language == "go":
            return await self._gopls_code_action()
        elif self.language == "ts":
            return await self._typescript_code_action()
        elif self.language == "py":
            return await self._pyright_code_action()
        else:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[f"Code actions not supported for language: {self.language}"],
            )

    async def _organize_imports(self) -> DevResult:
        """Organize imports"""
        if self.language == "go":
            # Use goimports directly
            result = self._run_command(["goimports", "-w"] + self.resolved["files"])
        elif self.language == "ts":
            # Use TypeScript organize imports
            return await self._typescript_organize_imports()
        elif self.language == "py":
            # Use ruff or isort
            result = self._run_command(["ruff", "check", "--select", "I", "--fix"] + self.resolved["files"])
        else:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[f"Organize imports not supported for language: {self.language}"],
            )

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=self.backend,
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=self.resolved["files"] if result.returncode == 0 else [],
        )

    async def _gopls_rename(self) -> DevResult:
        """Rename using gopls"""
        # Use gopls command line
        cmd = [
            "gopls",
            "rename",
            f"-w={self.workspace['root']}",
            f"{self.file}:{self.pos['line'] + 1}:{self.pos['character'] + 1}",
            self.new_name,
        ]

        result = self._run_command(cmd)

        # Parse touched files from output if available
        touched_files = []
        if result.returncode == 0:
            # gopls might output changed files - parse if available
            touched_files = self.resolved["files"]

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="gopls",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=touched_files,
        )

    async def _typescript_rename(self) -> DevResult:
        """Rename using TypeScript Language Server"""
        # For now, use a simple approach - could integrate with actual TS LSP
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="tsserver",
            scope_resolved=self.target,
            errors=["TypeScript LSP rename not implemented yet - use IDE"],
        )

    async def _pyright_rename(self) -> DevResult:
        """Rename using Pyright"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="pyright",
            scope_resolved=self.target,
            errors=["Pyright rename not implemented yet - use IDE"],
        )

    async def _rust_analyzer_rename(self) -> DevResult:
        """Rename using rust-analyzer"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="rust-analyzer",
            scope_resolved=self.target,
            errors=["rust-analyzer rename not implemented yet - use IDE"],
        )

    async def _gopls_code_action(self) -> DevResult:
        """Apply code actions using gopls"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="gopls",
            scope_resolved=self.target,
            errors=["gopls code actions not implemented yet"],
        )

    async def _typescript_code_action(self) -> DevResult:
        """Apply code actions using TypeScript"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="tsserver",
            scope_resolved=self.target,
            errors=["TypeScript code actions not implemented yet"],
        )

    async def _pyright_code_action(self) -> DevResult:
        """Apply code actions using Pyright"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="pyright",
            scope_resolved=self.target,
            errors=["Pyright code actions not implemented yet"],
        )

    async def _typescript_organize_imports(self) -> DevResult:
        """Organize TypeScript imports"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="tsserver",
            scope_resolved=self.target,
            errors=["TypeScript organize imports not implemented yet"],
        )

    async def _apply_workspace_edit(self) -> DevResult:
        """Apply arbitrary workspace edit"""
        return create_dev_result(
            ok=False,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=self.backend,
            scope_resolved=self.target,
            errors=["apply_workspace_edit not implemented yet"],
        )


# MCP tool integration
async def edit_tool_handler(
    target: str,
    op: str,
    file: Optional[str] = None,
    pos: Optional[Dict[str, int]] = None,
    range: Optional[Dict[str, Any]] = None,
    new_name: Optional[str] = None,
    only: Optional[List[str]] = None,
    apply: bool = True,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP handler for edit tool"""

    tool = EditTool(
        target=target,
        op=op,
        file=file,
        pos=pos,
        range=range,
        new_name=new_name,
        only=only or [],
        apply=apply,
        language=language,
        backend=backend,
        root=root,
        env=env,
        dry_run=dry_run,
    )

    result = await tool.execute()
    return result.dict()
