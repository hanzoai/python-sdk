#!/usr/bin/env python3
"""
Simple test of the exact tool specifications
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import os

# Add the package to path
sys.path.insert(0, '/Users/z/work/hanzo/python-sdk/pkg/hanzo-mcp')

async def simple_test():
    """Simple test without external dependencies"""
    print("🔧 Testing basic functionality...")
    
    # Test workspace detection
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)
        
        # Create a simple Go project structure
        go_mod = workspace_dir / "go.mod"
        go_mod.write_text("module test\n\ngo 1.21\n")
        
        main_go = workspace_dir / "main.go"
        main_go.write_text("""package main

import "fmt"

func main() {
    fmt.Println("Hello World")
}
""")
        
        # Import and test workspace detection
        try:
            from hanzo_mcp.exact_tools import WorkspaceDetector
            
            detector = WorkspaceDetector()
            workspace = detector.detect(str(main_go))
            
            print(f"  Workspace type: {workspace['type']}")
            print(f"  Root: {workspace['root']}")
            print(f"  Language: {workspace['language']}")
            print("  ✅ Workspace detection working")
            
        except Exception as e:
            print(f"  ❌ Workspace detection failed: {e}")
            return False
        
        # Test target resolution
        try:
            from hanzo_mcp.exact_tools import TargetResolver, TargetSpec
            
            resolver = TargetResolver(detector)
            
            # Test file target
            target_spec = TargetSpec(target=f"file:{main_go}")
            resolved = resolver.resolve(target_spec)
            
            print(f"  File resolution: {len(resolved['paths'])} files")
            print(f"  Language inferred: {resolved['language']}")
            print("  ✅ Target resolution working")
            
        except Exception as e:
            print(f"  ❌ Target resolution failed: {e}")
            return False
        
        # Test backend selection
        try:
            from hanzo_mcp.exact_tools import BackendSelector
            
            selector = BackendSelector()
            
            go_fmt_backend = selector.select_backend("go", "fmt")
            py_lint_backend = selector.select_backend("py", "lint")
            ts_test_backend = selector.select_backend("ts", "test")
            
            print(f"  Go fmt backend: {go_fmt_backend}")
            print(f"  Python lint backend: {py_lint_backend}")
            print(f"  TypeScript test backend: {ts_test_backend}")
            print("  ✅ Backend selection working")
            
        except Exception as e:
            print(f"  ❌ Backend selection failed: {e}")
            return False
    
    return True


async def test_tool_schemas():
    """Test tool schema definitions"""
    print("🔧 Testing tool schemas...")
    
    try:
        from hanzo_mcp.exact_tools import (
            TargetSpec, EditArgs, FmtArgs, TestArgs, BuildArgs, LintArgs, GuardArgs, GuardRule
        )
        
        # Test target spec
        target = TargetSpec(target="ws", language="go", dry_run=True)
        print(f"  Target spec: {target.target}, {target.language}")
        
        # Test edit args
        edit = EditArgs(op="rename", new_name="NewName")
        print(f"  Edit args: {edit.op}, {edit.new_name}")
        
        # Test guard rule
        rule = GuardRule(
            id="test-rule",
            type="import",
            glob="**/*.py",
            forbid_import_prefix="forbidden"
        )
        print(f"  Guard rule: {rule.id}, {rule.type}")
        
        print("  ✅ All schemas working")
        return True
        
    except Exception as e:
        print(f"  ❌ Schema test failed: {e}")
        return False


async def main():
    print("🚀 Simple Test of Exact 6-Tool Implementation\n")
    
    success = True
    success &= await simple_test()
    print()
    success &= await test_tool_schemas()
    print()
    
    if success:
        print("🎉 Basic functionality tests passed!")
        print("\n✨ Implementation Features:")
        print("  • Workspace detection (go.work, package.json, pyproject.toml, etc.)")
        print("  • Target resolution (file:, dir:, pkg:, ws, changed)")
        print("  • Backend selection (language-specific tools)")
        print("  • 6 universal tools (edit, fmt, test, build, lint, guard)")
        print("  • LSP integration framework")
        print("  • Guard rule engine")
        print("  • Composition support")
    else:
        print("❌ Some tests failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())