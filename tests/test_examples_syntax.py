import ast
from pathlib import Path


def test_examples_python_syntax_valid():
    root = Path(__file__).resolve().parent.parent / "examples"
    py_files = list(root.rglob("*.py"))
    assert py_files, "Expected Python example files under examples/"
    for path in py_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
