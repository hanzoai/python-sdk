#!/usr/bin/env python3
"""
Main CLI entry point for hanzo-dev command
"""

import sys
import asyncio

from hanzo_mcp.dev_tools import DevToolsCore


async def main():
    """Main CLI entry point for hanzo-dev"""
    tools = DevToolsCore()

    if len(sys.argv) < 2:
        print("Usage: hanzo-dev <tool> [args]")
        print("Tools: edit, fmt, test, build, lint, guard")
        print("\nExamples:")
        print("  hanzo-dev fmt ws                  # Format workspace")
        print("  hanzo-dev test file:main.py       # Test specific file")
        print("  hanzo-dev lint dir:src --fix      # Lint and fix directory")
        print("  hanzo-dev guard ws                # Check boundaries")
        return 1

    tool = sys.argv[1]
    args = sys.argv[2:]

    try:
        if tool == "edit":
            if len(args) < 2:
                print("Usage: hanzo-dev edit <target> <operation> [--new-name NAME]")
                return 1
            target, op = args[0], args[1]
            new_name = None
            if "--new-name" in args:
                idx = args.index("--new-name")
                if idx + 1 < len(args):
                    new_name = args[idx + 1]
            result = await tools.edit(target=target, op=op, new_name=new_name)

        elif tool == "fmt":
            if len(args) < 1:
                print("Usage: hanzo-dev fmt <target> [--local-prefix PREFIX]")
                return 1
            target = args[0]
            local_prefix = None
            if "--local-prefix" in args:
                idx = args.index("--local-prefix")
                if idx + 1 < len(args):
                    local_prefix = args[idx + 1]
            result = await tools.fmt(target=target, local_prefix=local_prefix)

        elif tool == "test":
            if len(args) < 1:
                print("Usage: hanzo-dev test <target> [--run PATTERN] [--count N]")
                return 1
            target = args[0]
            run_pattern = None
            count = None
            if "--run" in args:
                idx = args.index("--run")
                if idx + 1 < len(args):
                    run_pattern = args[idx + 1]
            if "--count" in args:
                idx = args.index("--count")
                if idx + 1 < len(args):
                    count = int(args[idx + 1])
            result = await tools.test(target=target, run=run_pattern, count=count)

        elif tool == "build":
            if len(args) < 1:
                print("Usage: hanzo-dev build <target> [--release]")
                return 1
            target = args[0]
            release = "--release" in args
            result = await tools.build(target=target, release=release)

        elif tool == "lint":
            if len(args) < 1:
                print("Usage: hanzo-dev lint <target> [--fix]")
                return 1
            target = args[0]
            fix = "--fix" in args
            result = await tools.lint(target=target, fix=fix)

        elif tool == "guard":
            if len(args) < 1:
                print("Usage: hanzo-dev guard <target>")
                return 1
            target = args[0]
            result = await tools.guard(target=target)

        else:
            print(f"Unknown tool: {tool}")
            print("Available tools: edit, fmt, test, build, lint, guard")
            return 1

        # Output results
        print(f"✅ Success: {result.ok}")
        print(f"🌱 Language: {result.language_used}")
        print(f"🛠️  Backend: {result.backend_used}")
        print(f"📂 Root: {result.root}")

        if result.touched_files:
            print(f"📝 Modified files ({len(result.touched_files)}):")
            for file in result.touched_files:
                print(f"  - {file}")

        if result.stdout:
            print(f"📤 Output:\n{result.stdout}")

        if result.stderr:
            print(f"⚠️  Error output:\n{result.stderr}")

        if result.violations:
            print(f"🚨 Violations ({len(result.violations)}):")
            for violation in result.violations:
                print(f"  - {violation}")

        return 0 if result.ok else 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
