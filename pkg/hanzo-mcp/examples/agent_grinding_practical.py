#!/usr/bin/env python3
"""Practical Agent Grinding Examples.

This shows real-world examples of using the agent grinding pattern
with the swarm tool to solve common development tasks efficiently.
"""

# Example 1: Fix all linting errors in parallel
fix_lint_errors = """
# Fix all Python linting errors across the codebase

swarm(
    query="Fix all Python linting errors (ruff/flake8) in the codebase",
    agents=[
        {
            "id": "lint_runner",
            "query": "Run 'ruff check . --output-format=json' to get all linting errors organized by file"
        },
        {
            "id": "error_distributor", 
            "query": "Group linting errors by file and distribute to fixers. Create 3 groups for parallel processing",
            "receives_from": ["lint_runner"]
        },
        {
            "id": "lint_fixer_1",
            "query": "Fix linting errors in group 1 files. For each file: read it, understand the errors, make precise fixes",
            "receives_from": ["error_distributor"]
        },
        {
            "id": "lint_fixer_2",
            "query": "Fix linting errors in group 2 files. For each file: read it, understand the errors, make precise fixes",
            "receives_from": ["error_distributor"]
        },
        {
            "id": "lint_fixer_3",
            "query": "Fix linting errors in group 3 files. For each file: read it, understand the errors, make precise fixes",
            "receives_from": ["error_distributor"]
        },
        {
            "id": "lint_verifier",
            "query": "Run ruff check again on all modified files to ensure all errors are fixed",
            "receives_from": ["lint_fixer_1", "lint_fixer_2", "lint_fixer_3"]
        }
    ]
)
"""

# Example 2: Add docstrings to all functions
add_docstrings = """
# Add missing docstrings to all Python functions

swarm(
    query="Add comprehensive docstrings to all Python functions missing them",
    agents=[
        {
            "id": "docstring_finder",
            "query": "Use grep_ast to find all Python functions without docstrings or with incomplete docstrings"
        },
        {
            "id": "code_analyzer",
            "query": "For each function without docstring, analyze its code to understand what it does, its parameters, and return values",
            "receives_from": ["docstring_finder"]
        },
        {
            "id": "docstring_writer_1",
            "query": "Write Google-style docstrings for functions in files A-M. Include description, Args, Returns, Raises sections as appropriate",
            "receives_from": ["code_analyzer"]
        },
        {
            "id": "docstring_writer_2", 
            "query": "Write Google-style docstrings for functions in files N-Z. Include description, Args, Returns, Raises sections as appropriate",
            "receives_from": ["code_analyzer"]
        },
        {
            "id": "docstring_reviewer",
            "query": "Review all added docstrings for accuracy, completeness, and style consistency",
            "receives_from": ["docstring_writer_1", "docstring_writer_2"]
        }
    ]
)
"""

# Example 3: Upgrade dependency usage
upgrade_dependencies = """
# Upgrade from requests to httpx across codebase

swarm(
    query="Migrate all code from requests library to httpx with async support",
    agents=[
        {
            "id": "usage_finder",
            "query": "Find all files importing or using requests library. Note different usage patterns (get, post, sessions, etc.)"
        },
        {
            "id": "migration_planner",
            "query": "Create migration plan mapping requests patterns to httpx equivalents. Consider sync vs async contexts",
            "receives_from": ["usage_finder"]
        },
        {
            "id": "simple_migrator",
            "query": "Migrate simple requests.get/post calls to httpx. These can be done mechanically",
            "receives_from": ["migration_planner"]
        },
        {
            "id": "session_migrator",
            "query": "Migrate requests.Session usage to httpx.Client. Handle context managers properly", 
            "receives_from": ["migration_planner"]
        },
        {
            "id": "async_migrator",
            "query": "For async functions, migrate to httpx.AsyncClient. Add proper async/await",
            "receives_from": ["migration_planner"]
        },
        {
            "id": "import_updater",
            "query": "Update all import statements from requests to httpx. Update requirements files",
            "receives_from": ["simple_migrator", "session_migrator", "async_migrator"]
        },
        {
            "id": "test_runner",
            "query": "Run all tests to ensure migration didn't break anything. Note any failures",
            "receives_from": ["import_updater"]
        }
    ]
)
"""

# Example 4: Security audit and fixes
security_audit = """
# Security audit and automated fixes

swarm(
    query="Perform security audit and fix common vulnerabilities",
    consensus_mode=true,
    agents=[
        {
            "id": "secret_scanner",
            "query": "Search for hardcoded secrets, API keys, passwords using patterns and entropy analysis"
        },
        {
            "id": "sql_scanner",
            "query": "Find potential SQL injection vulnerabilities in database queries"
        },
        {
            "id": "input_scanner",
            "query": "Find user input that isn't properly validated or sanitized"
        },
        {
            "id": "dependency_scanner",
            "query": "Check for known vulnerabilities in dependencies"
        },
        {
            "id": "security_consensus",
            "query": "Review all findings and prioritize fixes. Discuss best approaches",
            "receives_from": ["secret_scanner", "sql_scanner", "input_scanner", "dependency_scanner"],
            "participants": 3
        },
        {
            "id": "secret_fixer",
            "query": "Move secrets to environment variables or secure vaults",
            "receives_from": ["security_consensus"]
        },
        {
            "id": "sql_fixer",
            "query": "Fix SQL injections using parameterized queries",
            "receives_from": ["security_consensus"]
        },
        {
            "id": "input_fixer",
            "query": "Add proper input validation and sanitization",
            "receives_from": ["security_consensus"]
        },
        {
            "id": "security_reviewer",
            "query": "Review all security fixes and create security report",
            "receives_from": ["secret_fixer", "sql_fixer", "input_fixer"]
        }
    ]
)
"""

# Example 5: Performance optimization
performance_optimization = """
# Find and fix performance bottlenecks

swarm(
    query="Identify and optimize performance bottlenecks in Python code",
    agents=[
        {
            "id": "profiler",
            "query": "Run performance profiling on key code paths. Identify slow functions"
        },
        {
            "id": "complexity_analyzer",
            "query": "Find functions with high algorithmic complexity (nested loops, etc.)"
        },
        {
            "id": "db_analyzer",
            "query": "Find database queries that could be optimized (N+1, missing indexes, etc.)"
        },
        {
            "id": "optimization_planner",
            "query": "Create optimization plan for each bottleneck. Consider tradeoffs",
            "receives_from": ["profiler", "complexity_analyzer", "db_analyzer"]
        },
        {
            "id": "algorithm_optimizer",
            "query": "Optimize algorithmic bottlenecks. Use better data structures, reduce complexity",
            "receives_from": ["optimization_planner"]
        },
        {
            "id": "query_optimizer",
            "query": "Optimize database queries. Add indexes, use joins, batch operations",
            "receives_from": ["optimization_planner"]
        },
        {
            "id": "cache_implementer",
            "query": "Add caching where appropriate. Use functools.lru_cache, Redis, etc.",
            "receives_from": ["optimization_planner"]
        },
        {
            "id": "benchmark_runner",
            "query": "Run benchmarks to measure improvements. Create performance report",
            "receives_from": ["algorithm_optimizer", "query_optimizer", "cache_implementer"]
        }
    ]
)
"""

# Example 6: Test coverage improvement
improve_test_coverage = """
# Improve test coverage to 90%+

swarm(
    query="Improve test coverage to at least 90% across all modules",
    agents=[
        {
            "id": "coverage_runner",
            "query": "Run pytest with coverage. Identify files and functions with low coverage"
        },
        {
            "id": "test_planner",
            "query": "For each low-coverage file, plan what tests are needed. Group by complexity",
            "receives_from": ["coverage_runner"]
        },
        {
            "id": "unit_test_writer_1",
            "query": "Write unit tests for simple functions (pure functions, clear inputs/outputs)",
            "receives_from": ["test_planner"]
        },
        {
            "id": "unit_test_writer_2",
            "query": "Write unit tests for complex functions (side effects, dependencies). Use mocks",
            "receives_from": ["test_planner"]
        },
        {
            "id": "integration_test_writer",
            "query": "Write integration tests for components that interact with external services",
            "receives_from": ["test_planner"]
        },
        {
            "id": "edge_case_hunter",
            "query": "Add tests for edge cases: empty inputs, large inputs, error conditions",
            "receives_from": ["test_planner"]
        },
        {
            "id": "coverage_validator",
            "query": "Run coverage again. Ensure we hit 90%+. Identify any remaining gaps",
            "receives_from": ["unit_test_writer_1", "unit_test_writer_2", "integration_test_writer", "edge_case_hunter"]
        }
    ]
)
"""


def print_example(title: str, example: str):
    """Print a formatted example."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print("=" * 60)
    print(example)
    print()


if __name__ == "__main__":
    print("PRACTICAL AGENT GRINDING EXAMPLES")
    print("=================================")
    print("\nThese examples show how to use the swarm tool with agent grinding")
    print("pattern to solve real development tasks efficiently.\n")

    print_example("Example 1: Fix All Linting Errors", fix_lint_errors)
    print_example("Example 2: Add Missing Docstrings", add_docstrings)
    print_example("Example 3: Upgrade Dependencies", upgrade_dependencies)
    print_example("Example 4: Security Audit & Fixes", security_audit)
    print_example("Example 5: Performance Optimization", performance_optimization)
    print_example("Example 6: Improve Test Coverage", improve_test_coverage)

    print("\nKEY PATTERNS:")
    print("-------------")
    print("1. FINDER → ANALYZER → FIXERS → VALIDATOR")
    print("   - Common pattern for search-and-fix tasks")
    print("   - Finder locates issues, analyzer understands them")
    print("   - Multiple fixers work in parallel")
    print("   - Validator ensures fixes are correct")
    print()
    print("2. SCANNER → PLANNER → IMPLEMENTERS → TESTER")
    print("   - For complex migrations or refactoring")
    print("   - Scanner finds all instances")
    print("   - Planner creates strategy")
    print("   - Multiple implementers execute in parallel")
    print("   - Tester verifies nothing broke")
    print()
    print("3. MULTI-SCANNER → CONSENSUS → TARGETED-FIXERS")
    print("   - For security or code quality audits")
    print("   - Multiple scanners look for different issues")
    print("   - Consensus group prioritizes fixes")
    print("   - Specialized fixers handle each issue type")
    print()
    print("BENEFITS:")
    print("---------")
    print("• Parallel processing - multiple agents work simultaneously")
    print("• Specialization - each agent focuses on one task")
    print("• Context preservation - agents read and understand before editing")
    print("• Scalability - add more agents for larger codebases")
    print("• Reliability - validators ensure quality")
