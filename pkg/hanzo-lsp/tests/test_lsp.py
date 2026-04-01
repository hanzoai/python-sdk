"""Integration tests for hanzo-lsp using mock LSP server."""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

from hanzo_lsp import LspManager, LspServerConfig

MOCK_SERVER = str(Path(__file__).parent / "mock_lsp_server.py")


def _make_config(workspace: Path) -> LspServerConfig:
    return LspServerConfig(
        name="mock",
        command=sys.executable,
        args=[MOCK_SERVER],
        workspace_root=workspace,
        extension_to_language={".py": "python", ".rs": "rust"},
    )


async def _wait_diagnostics(manager: LspManager, timeout: float = 2.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        ws = await manager.collect_workspace_diagnostics()
        if ws.total_diagnostics > 0:
            return
        await asyncio.sleep(0.01)
    raise TimeoutError("diagnostics never arrived")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    return tmp_path


class TestLspManagerIntegration:
    async def test_diagnostics_and_navigation(self, workspace: Path) -> None:
        source = workspace / "src" / "main.py"
        source.write_text("x = undefined_var\ny = x + 1\n")
        manager = LspManager([_make_config(workspace)])

        await manager.open_document(source, source.read_text())
        await _wait_diagnostics(manager)

        diags = await manager.collect_workspace_diagnostics()
        assert len(diags.files) == 1
        assert diags.total_diagnostics == 1
        assert diags.files[0].diagnostics[0].severity == 1
        assert diags.files[0].diagnostics[0].message == "mock error"

        defs = await manager.go_to_definition(source, 0, 0)
        assert len(defs) == 1
        assert defs[0].display_line == 1

        refs = await manager.find_references(source, 0, 0)
        assert len(refs) == 2
        assert refs[0].display_line == 1
        assert refs[1].display_line == 2

        await manager.shutdown()

    async def test_context_enrichment_render(self, workspace: Path) -> None:
        source = workspace / "src" / "lib.py"
        source.write_text("def answer(): return 42\n")
        manager = LspManager([_make_config(workspace)])

        await manager.open_document(source, source.read_text())
        await _wait_diagnostics(manager)

        enrichment = await manager.context_enrichment(source, 0, 0)
        rendered = enrichment.render_prompt_section()

        assert "# LSP context" in rendered
        assert "Workspace diagnostics: 1 across 1 file(s)" in rendered
        assert "Diagnostics:" in rendered
        assert "mock error" in rendered
        assert "Definitions:" in rendered
        assert "References:" in rendered

        await manager.shutdown()

    async def test_supports_path(self, workspace: Path) -> None:
        manager = LspManager([_make_config(workspace)])
        assert manager.supports_path(Path("foo.py"))
        assert manager.supports_path(Path("bar.rs"))
        assert not manager.supports_path(Path("baz.txt"))
        assert not manager.supports_path(Path("no_ext"))

    async def test_duplicate_extension_raises(self, workspace: Path) -> None:
        from hanzo_lsp import LspError

        cfg1 = LspServerConfig(
            name="a", command="x", workspace_root=workspace,
            extension_to_language={".py": "python"},
        )
        cfg2 = LspServerConfig(
            name="b", command="y", workspace_root=workspace,
            extension_to_language={".py": "python"},
        )
        with pytest.raises(LspError, match="duplicate extension"):
            LspManager([cfg1, cfg2])
