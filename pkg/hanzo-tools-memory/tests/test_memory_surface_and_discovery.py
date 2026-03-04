"""Tests for memory tool surface and local context discovery."""

from pathlib import Path

from hanzo_tools.memory import TOOLS
from hanzo_tools.memory.markdown_memory import MarkdownMemoryBackend


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_memory_surface_is_single_tool() -> None:
    """Entry-point surface should expose only one MCP tool: memory."""
    assert len(TOOLS) == 1
    tool = TOOLS[0]()
    assert tool.name == "memory"


def test_context_file_priority_and_rule_detection(tmp_path: Path, monkeypatch) -> None:
    """Discover AGENTS->CLAUDE->GEMINI->LLM first and detect editor rule files."""
    _write(tmp_path / "AGENTS.md", "# agents")
    _write(tmp_path / "CLAUDE.md", "# claude")
    _write(tmp_path / "GEMINI.md", "# gemini")
    _write(tmp_path / "LLM.md", "# llm")
    _write(tmp_path / "MEMORY.md", "# memory")
    _write(tmp_path / ".cursorrules", "cursor rules")
    _write(tmp_path / ".cursor" / "rules" / "team.mdc", "cursor team rules")
    _write(
        tmp_path / ".github" / "copilot-instructions.md",
        "# copilot instructions",
    )
    _write(
        tmp_path / ".github" / "instructions" / "python.instructions.md",
        "# python instructions",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    backend = MarkdownMemoryBackend()
    files = backend._iter_context_files(tmp_path)
    rel_paths = [str(p.relative_to(tmp_path)) for p in files]

    assert rel_paths[:4] == ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "LLM.md"]
    assert ".cursorrules" in rel_paths
    assert ".cursor/rules/team.mdc" in rel_paths
    assert ".github/copilot-instructions.md" in rel_paths
    assert ".github/instructions/python.instructions.md" in rel_paths


def test_scan_is_local_first_then_parent(tmp_path: Path, monkeypatch) -> None:
    """Current directory files should be loaded before parent directory files."""
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "services" / "api"
    _write(repo_root / "AGENTS.md", "# root agents")
    _write(project_dir / "AGENTS.md", "# local agents")

    monkeypatch.chdir(project_dir)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    backend = MarkdownMemoryBackend()
    backend._ensure_loaded()

    sources = [
        Path(m.source)
        for m in backend._file_memories
        if m.source.endswith("AGENTS.md")
    ]

    assert sources
    assert sources[0] == project_dir / "AGENTS.md"
    assert repo_root / "AGENTS.md" in sources
