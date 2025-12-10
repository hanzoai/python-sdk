import os
import tempfile

import nox


@nox.session(reuse_venv=True, name="test-pydantic-v1")
def test_pydantic_v1(session: nox.Session) -> None:
    # Install only the core SDK package and test dependencies
    # Avoids installing heavy dependencies like torch (900MB) that would exhaust disk space
    session.install("-e", ".")
    session.install(
        "pydantic<2",
        "pytest",
        "pytest-asyncio",
        "respx",
        "time-machine",
        "dirty-equals>=0.6.0",
        "importlib-metadata>=6.7.0",
        "rich>=13.7.1",
    )

    # Create a temporary pytest.ini that doesn't include the pydantic v2-specific warning filter
    # The main pyproject.toml has a filter for pydantic.warnings.PydanticDeprecatedSince20
    # which doesn't exist in pydantic v1 and causes pytest to fail at startup
    # Note: pytest.ini uses INI format, not TOML - multiline values use indentation
    pytest_ini_content = """[pytest]
testpaths = tests
addopts = --tb=short
xfail_strict = true
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
filterwarnings =
    error
    ignore::DeprecationWarning
    ignore::UserWarning
"""

    # Write temporary config and use it
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(pytest_ini_content)
        pytest_ini_path = f.name

    try:
        session.run(
            "pytest",
            "-c", pytest_ini_path,
            "--showlocals",
            "--ignore=tests/functional",
            *session.posargs
        )
    finally:
        os.unlink(pytest_ini_path)
