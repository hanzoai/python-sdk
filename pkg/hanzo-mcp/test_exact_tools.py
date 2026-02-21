#!/usr/bin/env python3
"""
Test Runner for Exact 6-Tool Implementation
===========================================

Test the exact tool specifications with real workspace scenarios.
"""

import asyncio
import json
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

from hanzo_mcp.exact_tools import (
    BuildArgs,
    EditArgs,
    FmtArgs,
    GuardArgs,
    GuardRule,
    LintArgs,
    TargetSpec,
    TestArgs,
    tools,
)


async def test_go_workspace_scenario():
    """Test Go workspace with go.work file"""
    print("🔧 Testing Go workspace scenario...")

    # Create temporary Go workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create go.work file
        go_work = workspace_dir / "go.work"
        go_work.write_text("""go 1.21

use (
    ./api
    ./cli
)
""")

        # Create api module
        api_dir = workspace_dir / "api"
        api_dir.mkdir()

        api_go_mod = api_dir / "go.mod"
        api_go_mod.write_text("module github.com/luxfi/api\n\ngo 1.21\n")

        api_main = api_dir / "main.go"
        api_main.write_text("""package main

import (
	"fmt"
	"net/http"
)

func UserHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello User")
}

func main() {
	http.HandleFunc("/user", UserHandler)
	http.ListenAndServe(":8080", nil)
}
""")

        # Create cli module
        cli_dir = workspace_dir / "cli"
        cli_dir.mkdir()

        cli_go_mod = cli_dir / "go.mod"
        cli_go_mod.write_text("module github.com/luxfi/cli\n\ngo 1.21\n")

        cli_main = cli_dir / "main.go"
        cli_main.write_text("""package main

import "fmt"

func GreetUser(name string) {
	fmt.Printf("Hello %s\\n", name)
}

func main() {
	GreetUser("World")
}
""")

        # Test workspace detection
        target_spec = TargetSpec(target="ws", root=str(workspace_dir))

        # Test fmt tool
        fmt_result = await tools.fmt(
            target_spec, FmtArgs(opts={"local_prefix": "github.com/luxfi"})
        )
        print(
            f"  fmt result: {'✅' if fmt_result.ok else '❌'} {fmt_result.language_used}"
        )
        print(f"    root: {fmt_result.root}")
        print(f"    backend: {fmt_result.backend_used}")

        # Test edit tool - organize imports
        edit_result = await tools.edit(target_spec, EditArgs(op="organize_imports"))
        print(
            f"  edit result: {'✅' if edit_result.ok else '❌'} {edit_result.backend_used}"
        )

        # Test guard tool
        guard_rules = [
            GuardRule(
                id="no-net-http-in-api",
                type="import",
                glob="api/*.go",
                forbid_import_prefix="net/http",
            )
        ]
        guard_result = await tools.guard(target_spec, GuardArgs(rules=guard_rules))
        print(
            f"  guard result: {'✅' if guard_result.ok else '❌'} violations: {len(guard_result.errors)}"
        )

        # Test specific package
        pkg_target = TargetSpec(target="pkg:./cli/...", root=str(workspace_dir))

        test_result = await tools.test(pkg_target, TestArgs(opts={"dry_run": True}))
        print(f"  test result: {'✅' if test_result.ok else '❌'} {test_result.stdout}")


async def test_typescript_project():
    """Test TypeScript project scenario"""
    print("🔧 Testing TypeScript project scenario...")

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create package.json with workspaces
        package_json = workspace_dir / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test-workspace",
                    "workspaces": ["packages/*"],
                    "scripts": {"test": "jest", "build": "tsc"},
                    "devDependencies": {"typescript": "^5.0.0", "jest": "^29.0.0"},
                },
                indent=2,
            )
        )

        # Create TypeScript config
        tsconfig = workspace_dir / "tsconfig.json"
        tsconfig.write_text(
            json.dumps(
                {
                    "compilerOptions": {
                        "target": "ES2022",
                        "module": "commonjs",
                        "strict": True,
                    }
                },
                indent=2,
            )
        )

        # Create packages
        packages_dir = workspace_dir / "packages"
        packages_dir.mkdir()

        # Core package
        core_dir = packages_dir / "core"
        core_dir.mkdir()

        core_package = core_dir / "package.json"
        core_package.write_text(
            json.dumps({"name": "@test/core", "version": "1.0.0"}, indent=2)
        )

        core_index = core_dir / "index.ts"
        core_index.write_text("""export interface User {
  id: string;
  name: string;
}

export class UserService {
  getUser(id: string): User | null {
    return { id, name: 'Test User' };
  }
}
""")

        # Test TypeScript workspace
        target_spec = TargetSpec(target="ws", root=str(workspace_dir), language="ts")

        fmt_result = await tools.fmt(target_spec, FmtArgs())
        print(
            f"  fmt result: {'✅' if fmt_result.ok else '❌'} {fmt_result.backend_used}"
        )

        build_result = await tools.build(target_spec, BuildArgs(opts={"dry_run": True}))
        print(
            f"  build result: {'✅' if build_result.ok else '❌'} {build_result.stdout}"
        )

        lint_result = await tools.lint(target_spec, LintArgs(opts={"dry_run": True}))
        print(
            f"  lint result: {'✅' if lint_result.ok else '❌'} {lint_result.backend_used}"
        )


async def test_target_resolution():
    """Test target resolution scenarios"""
    print("🔧 Testing target resolution...")

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create simple Go project
        go_mod = workspace_dir / "go.mod"
        go_mod.write_text("module test\n\ngo 1.21\n")

        main_go = workspace_dir / "main.go"
        main_go.write_text("""package main

import "fmt"

func main() {
    fmt.Println("Hello")
}
""")

        src_dir = workspace_dir / "src"
        src_dir.mkdir()

        helper_go = src_dir / "helper.go"
        helper_go.write_text("""package src

func Helper() string {
    return "helper"
}
""")

        # Test different target types
        test_cases = [
            ("file:" + str(main_go), "Single file"),
            ("dir:" + str(src_dir), "Directory"),
            ("ws", "Workspace"),
            ("pkg:.", "Current package"),
        ]

        for target, description in test_cases:
            target_spec = TargetSpec(
                target=target, root=str(workspace_dir), dry_run=True
            )

            result = await tools.fmt(target_spec, FmtArgs())
            print(
                f"  {description}: {'✅' if result.ok else '❌'} scope={len(result.scope_resolved)}"
            )


async def test_composition_workflow():
    """Test tool composition workflow"""
    print("🔧 Testing composition workflow...")

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create Python project
        pyproject = workspace_dir / "pyproject.toml"
        pyproject.write_text("""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
version = "0.1.0"
""")

        src_dir = workspace_dir / "src"
        src_dir.mkdir()

        main_py = src_dir / "main.py"
        main_py.write_text("""import os
import sys
from typing import Optional


def process_user(user_id: str) -> Optional[str]:
    if not user_id:
        return None
    return f"User: {user_id}"


if __name__ == "__main__":
    print(process_user("123"))
""")

        # Composition workflow: edit -> fmt -> lint -> test
        target_spec = TargetSpec(
            target="file:" + str(main_py), root=str(workspace_dir), language="py"
        )

        # 1. Organize imports
        print("  Step 1: Organize imports")
        edit_result = await tools.edit(
            target_spec, EditArgs(op="organize_imports", dry_run=True)
        )
        print(f"    {'✅' if edit_result.ok else '❌'} {edit_result.stdout}")

        # 2. Format code
        print("  Step 2: Format code")
        fmt_result = await tools.fmt(target_spec, FmtArgs())
        print(f"    {'✅' if fmt_result.ok else '❌'} {fmt_result.backend_used}")

        # 3. Lint code
        print("  Step 3: Lint code")
        lint_result = await tools.lint(target_spec, LintArgs(opts={"dry_run": True}))
        print(f"    {'✅' if lint_result.ok else '❌'} {lint_result.backend_used}")

        # 4. Test code
        print("  Step 4: Test code")
        test_result = await tools.test(target_spec, TestArgs(opts={"dry_run": True}))
        print(f"    {'✅' if test_result.ok else '❌'} {test_result.stdout}")


async def test_guard_rules():
    """Test guard rule scenarios"""
    print("🔧 Testing guard rules...")

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create SDK structure
        sdk_dir = workspace_dir / "sdk"
        sdk_dir.mkdir()

        # Bad import in SDK
        sdk_file = sdk_dir / "bad.py"
        sdk_file.write_text("""import node
from node.crypto import hash

def bad_function():
    return node.process()
""")

        # API contracts
        api_dir = workspace_dir / "api"
        api_dir.mkdir()

        api_file = api_dir / "contract.py"
        api_file.write_text("""import requests
from http.client import HTTPConnection

def api_call():
    return requests.get("http://example.com")
""")

        # Generated files
        generated_dir = workspace_dir / "api" / "pb"
        generated_dir.mkdir(parents=True)

        generated_file = generated_dir / "user_pb2.py"
        generated_file.write_text("# Generated file - do not edit")

        # Test guard rules
        guard_rules = [
            GuardRule(
                id="no-node-in-sdk",
                type="import",
                glob="sdk/**/*.py",
                forbid_import_prefix="node",
            ),
            GuardRule(
                id="no-http-in-contracts",
                type="import",
                glob="api/*.py",
                forbid_import_prefix="requests",
            ),
            GuardRule(
                id="no-edits-in-generated",
                type="generated",
                glob="api/pb/**",
                forbid_writes=True,
            ),
        ]

        target_spec = TargetSpec(target="ws", root=str(workspace_dir))

        guard_result = await tools.guard(target_spec, GuardArgs(rules=guard_rules))
        print(f"  guard result: {'✅' if guard_result.ok else '❌'}")
        print(f"  violations found: {len(guard_result.errors)}")
        for error in guard_result.errors:
            print(f"    - {error}")


async def main():
    """Run all tests"""
    print("🚀 Testing Exact 6-Tool Implementation\n")

    try:
        await test_go_workspace_scenario()
        print()

        await test_typescript_project()
        print()

        await test_target_resolution()
        print()

        await test_composition_workflow()
        print()

        await test_guard_rules()
        print()

        print("🎉 All tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
