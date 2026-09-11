"""Every module in ``hanzoai`` imports on every Python that requires-python admits.

2.1.2 declared ``requires-python >= 3.9`` and could not be imported on 3.9 at all:
``grpo/enhanced_api_model_adapter.py`` annotated a return as ``str | Tuple[...]``,
which 3.9 evaluates at class-body time and rejects with ``TypeError``, and
``hanzoai/__init__.py`` imports ``grpo`` eagerly. The test job runs only
``.python-version`` (3.12), where that line is valid, so nothing could see it.

The module list comes from the filesystem rather than from importing the package,
so a package that fails to import shows up as a failing module instead of an
empty list.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest


def _module_names() -> list[str]:
    spec = importlib.util.find_spec("hanzoai")
    assert spec is not None and spec.submodule_search_locations
    root = Path(next(iter(spec.submodule_search_locations)))
    names = []
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root.parent).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(parts))
    return names


@pytest.mark.parametrize("name", _module_names())
def test_module_imports(name: str) -> None:
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:
        # An optional dependency that is not installed says nothing about this
        # interpreter; a missing hanzoai module does.
        if exc.name and exc.name.split(".")[0] != "hanzoai":
            pytest.skip(f"optional dependency {exc.name} is not installed")
        raise
