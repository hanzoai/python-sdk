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

    session.run("pytest", "--showlocals", "--ignore=tests/functional", *session.posargs)
