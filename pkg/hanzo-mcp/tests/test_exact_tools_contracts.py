from pathlib import Path

import pytest

from hanzo_mcp.exact_tools import EditArgs, GuardArgs, GuardRule, HanzoTools, TargetSpec


@pytest.mark.asyncio
async def test_targetspec_rejects_unknown_keys():
    with pytest.raises(TypeError):
        TargetSpec(target="ws", unexpected=123)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_dry_run_envelope_and_no_fs_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    (root / "go.work").write_text("go 1.21\n\nuse (\n  ./mod\n)\n")
    mod_dir = root / "mod"
    mod_dir.mkdir()
    (mod_dir / "go.mod").write_text("module example.com/mod\n\ngo 1.21\n")
    file_path = mod_dir / "main.go"
    file_path.write_text("package main\n\nfunc main() {}\n")

    tools = HanzoTools()

    # Patch LSP bridge to avoid external LSP servers
    async def fake_rename(*_args, **_kwargs):
        return {"touched_files": [str(file_path)]}

    tools.lsp_bridge.rename_symbol = fake_rename  # type: ignore[assignment]

    target = TargetSpec(target=f"file:{file_path}", language="go", dry_run=True)
    before = file_path.read_text()

    edit_result = await tools.edit(
        target, EditArgs(op="rename", file=str(file_path), pos={"line": 1, "character": 1}, new_name="Main")
    )
    assert hasattr(edit_result, "ok")
    assert hasattr(edit_result, "root")
    assert hasattr(edit_result, "language_used")
    assert hasattr(edit_result, "backend_used")
    assert hasattr(edit_result, "scope_resolved")
    assert hasattr(edit_result, "touched_files")
    assert hasattr(edit_result, "stdout")
    assert hasattr(edit_result, "stderr")
    assert hasattr(edit_result, "exit_code")
    assert hasattr(edit_result, "errors")

    after = file_path.read_text()
    assert before == after
    assert edit_result.touched_files == [str(file_path)]


@pytest.mark.asyncio
async def test_error_exit_contract(tmp_path: Path):
    tools = HanzoTools()
    target = TargetSpec(target="ws", root=str(tmp_path), dry_run=True)
    result = await tools.edit(target, EditArgs(op="rename"))
    assert result.ok is False
    assert result.exit_code != 0
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_workspace_detection_go_work_priority(tmp_path: Path):
    root = tmp_path
    (root / "go.work").write_text("go 1.21\n\nuse (\n  ./a\n  ./b\n)\n")
    a = root / "a"
    b = root / "b"
    a.mkdir()
    b.mkdir()
    (a / "go.mod").write_text("module example.com/a\n\ngo 1.21\n")
    (b / "go.mod").write_text("module example.com/b\n\ngo 1.21\n")

    tools = HanzoTools()
    resolved = tools.target_resolver.resolve(TargetSpec(target="ws", root=str(root), language="go", dry_run=True))
    assert resolved["workspace"]["root"] == str(root)


@pytest.mark.asyncio
async def test_workspace_detection_root_boundary(tmp_path: Path):
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (outer / "go.work").write_text("go 1.21\n\nuse (\n  ./inner\n)\n")
    (inner / "go.mod").write_text("module example.com/inner\n\ngo 1.21\n")

    tools = HanzoTools()
    resolved = tools.target_resolver.resolve(TargetSpec(target="ws", root=str(inner), language="go", dry_run=True))
    assert resolved["workspace"]["root"] == str(inner)


@pytest.mark.asyncio
async def test_guard_transitive_go_import(tmp_path: Path):
    root = tmp_path
    (root / "go.mod").write_text("module example.com/root\n\ngo 1.21\n")
    (root / "main.go").write_text('package main\n\nimport "net/http"\n\nfunc main() {}\n')

    tools = HanzoTools()
    target = TargetSpec(target=f"dir:{root}", language="go", dry_run=True)
    guard = GuardArgs(
        rules=[GuardRule(id="no-net-http", type="import", glob="**/*.go", forbid_import_prefix="net/http")]
    )
    result = await tools.guard(target, guard)
    assert result.exit_code == 1
    assert len(result.errors) > 0
