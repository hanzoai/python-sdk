# Test Tool

Validation operations: check, build, test (HIP-0300 operator).

## Installation

```bash
pip install hanzo-tools-test
```

## Overview

The `test` tool provides three distinct validation loops (Vim-inspired):

| Action | Purpose | Equivalent | Effect |
|--------|---------|------------|--------|
| `check` | Fast incremental feedback | `:make` | NONDETERMINISTIC |
| `build` | Whole-project compilation | `:!make` | NONDETERMINISTIC |
| `test` | Runtime behavior validation | `:!make test` | NONDETERMINISTIC |
| `detect` | Auto-detect project tools | - | DETERMINISTIC |

## Actions

### check

Fast, incremental linting and type checking.

```python
test(action="check")
# Returns: {
#   diagnostics: [
#     {file: "src/main.py", line: 42, severity: "error", message: "..."},
#     {file: "src/utils.py", line: 10, severity: "warning", message: "..."}
#   ],
#   pass: False,
#   tool: "ruff",
#   duration_ms: 234
# }

test(action="check", path="src/auth.py")
# Check specific file

test(action="check", tool="mypy")
# Use specific tool
```

**Supported Check Tools:**
| Tool | Languages | Command |
|------|-----------|---------|
| `ruff` | Python | `ruff check .` |
| `mypy` | Python | `mypy .` |
| `pyright` | Python | `pyright .` |
| `eslint` | JavaScript/TypeScript | `eslint .` |
| `tsc` | TypeScript | `tsc --noEmit` |
| `clippy` | Rust | `cargo clippy` |
| `golangci-lint` | Go | `golangci-lint run` |

### build

Whole-project compilation and dependency resolution.

```python
test(action="build")
# Returns: {
#   success: True,
#   artifacts: ["dist/main.js", "dist/main.js.map"],
#   duration_ms: 5432,
#   tool: "npm"
# }

test(action="build", tool="cargo")
# Use specific build tool
```

**Supported Build Tools:**
| Tool | Languages | Command |
|------|-----------|---------|
| `pip` | Python | `pip install -e .` |
| `uv` | Python | `uv sync` |
| `npm` | Node.js | `npm run build` |
| `pnpm` | Node.js | `pnpm build` |
| `cargo` | Rust | `cargo build` |
| `go` | Go | `go build ./...` |
| `make` | Any | `make` |
| `cmake` | C/C++ | `cmake --build .` |

### test

Runtime behavior validation with test isolation.

```python
test(action="test")
# Returns: {
#   passed: 42,
#   failed: 2,
#   skipped: 3,
#   total: 47,
#   failures: [
#     {name: "test_auth_flow", file: "tests/test_auth.py", message: "..."}
#   ],
#   duration_ms: 8765,
#   tool: "pytest"
# }

test(action="test", selector="tests/test_auth.py")
# Run specific tests

test(action="test", selector="test_login")
# Run tests matching pattern

test(action="test", tool="jest", verbose=True)
# Use specific tool with options
```

**Supported Test Runners:**
| Tool | Languages | Command |
|------|-----------|---------|
| `pytest` | Python | `pytest -v` |
| `unittest` | Python | `python -m unittest` |
| `jest` | JavaScript/TypeScript | `jest` |
| `vitest` | JavaScript/TypeScript | `vitest run` |
| `mocha` | JavaScript | `mocha` |
| `cargo_test` | Rust | `cargo test` |
| `go_test` | Go | `go test ./...` |
| `make_test` | Any | `make test` |

### detect

Auto-detect project tools based on config files.

```python
test(action="detect")
# Returns: {
#   test_runner: {name: "pytest", cmd: ["pytest", "-v"], config: "pyproject.toml"},
#   build_tool: {name: "uv", cmd: ["uv", "sync"], config: "pyproject.toml"},
#   check_tool: {name: "ruff", cmd: ["ruff", "check", "."], config: "ruff.toml"},
#   detected_from: ["pyproject.toml", "ruff.toml"]
# }

test(action="detect", path="/path/to/project")
# Detect in specific directory
```

**Detection Priority:**
1. Check for config files (pyproject.toml, package.json, Cargo.toml, etc.)
2. Look for lock files (uv.lock, package-lock.json, Cargo.lock)
3. Examine project structure (tests/, src/, etc.)

## Three Validation Loops

The three operations serve distinct purposes:

### CHECK (Fast Feedback)
- **When:** During editing, before commits
- **Speed:** Milliseconds to seconds
- **Scope:** Single file or incremental
- **Output:** Diagnostics with line numbers
- **Goal:** Catch obvious errors immediately

### BUILD (Compilation)
- **When:** Before running, in CI
- **Speed:** Seconds to minutes
- **Scope:** Entire project
- **Output:** Artifacts or errors
- **Goal:** Verify everything compiles

### TEST (Validation)
- **When:** Before deploy, in CI
- **Speed:** Seconds to minutes
- **Scope:** Test suite
- **Output:** Pass/fail with details
- **Goal:** Verify behavior is correct

## Example Workflow

```python
# Quick check during development
check_result = test(action="check")
if not check_result["data"]["pass"]:
    print("Fix these issues first:")
    for diag in check_result["data"]["diagnostics"]:
        print(f"  {diag['file']}:{diag['line']}: {diag['message']}")

# Full build before commit
build_result = test(action="build")
if not build_result["data"]["success"]:
    print("Build failed!")

# Run tests before push
test_result = test(action="test")
if test_result["data"]["failed"] > 0:
    print(f"{test_result['data']['failed']} tests failed")
    for failure in test_result["data"]["failures"]:
        print(f"  {failure['name']}: {failure['message']}")
```

## CI Integration

```yaml
# GitHub Actions example
jobs:
  validate:
    steps:
      - name: Check
        run: |
          python -c "from hanzo_tools.test import test_tool; print(test_tool.call(action='check'))"

      - name: Build
        run: |
          python -c "from hanzo_tools.test import test_tool; print(test_tool.call(action='build'))"

      - name: Test
        run: |
          python -c "from hanzo_tools.test import test_tool; print(test_tool.call(action='test'))"
```

## See Also

- [HIP-0300](../hip/HIP-0300.md) - Unified Tools Architecture
- [Code Tool](code.md) - For code analysis before testing
- [VCS Tool](vcs.md) - For running tests on changes
- [Shell Tool](shell.md) - For custom test commands
