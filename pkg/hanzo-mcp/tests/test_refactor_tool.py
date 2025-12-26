"""Tests for the refactor tool."""

import os
import tempfile

import pytest
from hanzo_tools.refactor import RefactorTool, create_refactor_tool


class TestRefactorTool:
    """Tests for RefactorTool class."""

    @pytest.fixture
    def tool(self):
        """Create a refactor tool instance."""
        return create_refactor_tool()

    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def old_function(x, y):
    result = x + y
    return result

def caller():
    value = old_function(1, 2)
    return value

class MyClass:
    def method(self):
        return old_function(3, 4)
""")
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_js_file(self):
        """Create a temporary JavaScript file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("""function oldFunction(x, y) {
    const result = x + y;
    return result;
}

function caller() {
    const value = oldFunction(1, 2);
    return value;
}
""")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_tool_creation(self, tool):
        """Test that the tool can be created."""
        assert tool is not None
        assert tool.name == "refactor"

    def test_tool_has_description(self, tool):
        """Test that the tool has a description."""
        assert tool.description is not None
        assert "refactor" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_invalid_action(self, tool):
        """Test error handling for invalid action."""
        result = await tool.run(action="invalid_action", file="test.py")
        assert result.data["error"] is not None
        assert "Invalid action" in result.data["error"]

    @pytest.mark.asyncio
    async def test_file_not_found(self, tool):
        """Test error handling for non-existent file."""
        result = await tool.run(action="rename", file="/nonexistent/file.py", line=1, column=0, new_name="new")
        assert "error" in result.data
        assert "not found" in result.data["error"].lower()

    @pytest.mark.asyncio
    async def test_find_references_missing_args(self, tool, temp_python_file):
        """Test find_references without required arguments."""
        result = await tool.run(action="find_references", file=temp_python_file)
        assert result.data["success"] is False
        assert "required" in result.data["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_find_references(self, tool, temp_python_file):
        """Test finding references to a symbol."""
        result = await tool.run(
            action="find_references",
            file=temp_python_file,
            line=1,
            column=4,  # 'old_function'
        )
        assert result.data["success"] is True
        assert result.data["action"] == "find_references"
        assert len(result.data["changes"]) > 0

    @pytest.mark.asyncio
    async def test_rename_preview(self, tool, temp_python_file):
        """Test rename in preview mode."""
        result = await tool.run(
            action="rename",
            file=temp_python_file,
            line=1,
            column=4,  # 'old_function'
            new_name="new_function",
            preview=True,
        )
        assert result.data["success"] is True
        assert result.data["action"] == "rename"
        assert "preview" in result.data
        assert len(result.data["preview"]) > 0

        # Verify file wasn't modified
        with open(temp_python_file, "r") as f:
            content = f.read()
        assert "old_function" in content
        assert "new_function" not in content

    @pytest.mark.asyncio
    async def test_rename_apply(self, tool, temp_python_file):
        """Test rename with actual application."""
        result = await tool.run(
            action="rename",
            file=temp_python_file,
            line=1,
            column=4,  # 'old_function'
            new_name="new_function",
            preview=False,
        )
        assert result.data["success"] is True
        assert result.data["action"] == "rename"
        assert result.data["changes_applied"] > 0

        # Verify file was modified
        with open(temp_python_file, "r") as f:
            content = f.read()
        assert "new_function" in content
        # All occurrences should be renamed
        assert "old_function" not in content

    @pytest.mark.asyncio
    async def test_extract_function_missing_name(self, tool, temp_python_file):
        """Test extract_function without new_name."""
        result = await tool.run(
            action="extract_function",
            file=temp_python_file,
            start_line=2,
            end_line=3,
        )
        assert result.data["success"] is False
        assert "new_name" in result.data["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_extract_function_preview(self, tool, temp_python_file):
        """Test extract_function in preview mode."""
        result = await tool.run(
            action="extract_function",
            file=temp_python_file,
            start_line=2,
            end_line=3,
            new_name="compute_result",
            preview=True,
        )
        assert result.data["success"] is True
        assert result.data["action"] == "extract_function"
        assert "preview" in result.data
        assert len(result.data["preview"]) > 0

    @pytest.mark.asyncio
    async def test_extract_variable_missing_args(self, tool, temp_python_file):
        """Test extract_variable without required arguments."""
        result = await tool.run(
            action="extract_variable",
            file=temp_python_file,
        )
        assert result.data["success"] is False

    @pytest.mark.asyncio
    async def test_inline_missing_args(self, tool, temp_python_file):
        """Test inline without required arguments."""
        result = await tool.run(
            action="inline",
            file=temp_python_file,
        )
        assert result.data["success"] is False

    @pytest.mark.asyncio
    async def test_move_missing_target(self, tool, temp_python_file):
        """Test move without target_file."""
        result = await tool.run(
            action="move",
            file=temp_python_file,
            line=1,
        )
        assert result.data["success"] is False
        assert "target_file" in result.data["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_organize_imports_python(self, tool):
        """Test organize imports for Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""import os
from typing import List
import sys
from collections import defaultdict
import json

def main():
    pass
""")
            temp_path = f.name

        try:
            result = await tool.run(
                action="organize_imports",
                file=temp_path,
                preview=False,
            )
            assert result.data["success"] is True

            with open(temp_path, "r") as f:
                content = f.read()

            # Imports should be sorted
            lines = content.split("\n")
            import_lines = [l for l in lines if l.startswith("import ")]
            from_lines = [l for l in lines if l.startswith("from ")]

            # Check imports are sorted
            assert import_lines == sorted(import_lines, key=str.lower)
            assert from_lines == sorted(from_lines, key=str.lower)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_change_signature_missing_args(self, tool, temp_python_file):
        """Test change_signature without required arguments."""
        result = await tool.run(action="change_signature")
        assert result.data["success"] is False
        assert "required" in result.data["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_change_signature_add_parameter_preview(self, tool):
        """Test adding a parameter with preview."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def greet(name):
    return f"Hello, {name}!"

def main():
    msg = greet("World")
    print(msg)
""")
            temp_path = f.name

        try:
            result = await tool.run(
                action="change_signature",
                file=temp_path,
                line=1,
                add_parameter={"name": "greeting", "default": "'Hello'"},
                preview=True,
            )
            assert result.data["success"] is True
            assert result.data["action"] == "change_signature"
            assert len(result.data["preview"]) > 0

            # Verify file wasn't modified
            with open(temp_path, "r") as f:
                content = f.read()
            assert "greeting" not in content

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_change_signature_rename_parameter(self, tool):
        """Test renaming a parameter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def compute(x, y):
    return x + y

result = compute(1, 2)
""")
            temp_path = f.name

        try:
            result = await tool.run(
                action="change_signature",
                file=temp_path,
                line=1,
                rename_parameter={"old": "x", "new": "first"},
                preview=True,
            )
            assert result.data["success"] is True
            assert "first" in str(result.data["preview"])

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_change_signature_no_function(self, tool):
        """Test change_signature when no function at line."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""x = 10
y = 20
""")
            temp_path = f.name

        try:
            result = await tool.run(
                action="change_signature",
                file=temp_path,
                line=1,
                add_parameter={"name": "z"},
            )
            assert result.data["success"] is False
            assert "function signature" in result.data["errors"][0].lower()

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestRefactorToolHelpers:
    """Tests for RefactorTool helper methods."""

    @pytest.fixture
    def tool(self):
        """Create a refactor tool instance."""
        return RefactorTool()

    def test_get_identifier_at_basic(self, tool):
        """Test getting identifier at position."""
        line = "def my_function(arg1, arg2):"
        assert tool._get_identifier_at(line, 4) == "my_function"
        assert tool._get_identifier_at(line, 16) == "arg1"
        assert tool._get_identifier_at(line, 23) == "arg2"

    def test_get_identifier_at_edge_cases(self, tool):
        """Test edge cases for identifier detection."""
        # Empty line
        assert tool._get_identifier_at("", 0) is None

        # Column out of range
        assert tool._get_identifier_at("hello", 100) == "hello"

        # No identifier at position
        assert tool._get_identifier_at("    ", 2) is None

    def test_get_indentation(self, tool):
        """Test indentation detection."""
        assert tool._get_indentation("def foo():") == ""
        assert tool._get_indentation("    return x") == "    "
        assert tool._get_indentation("\t\treturn y") == "\t\t"
        assert tool._get_indentation("") == ""

    def test_get_language(self, tool):
        """Test language detection from file extension."""
        assert tool._get_language("test.py") == "python"
        assert tool._get_language("test.js") == "javascript"
        assert tool._get_language("test.ts") == "typescript"
        assert tool._get_language("test.go") == "go"
        assert tool._get_language("test.rs") == "rust"
        assert tool._get_language("test.unknown") == "unknown"

    def test_find_used_variables(self, tool):
        """Test finding used variables in code."""
        code = "result = x + y"
        vars = tool._find_used_variables(code, "python")
        assert "x" in vars
        assert "y" in vars
        assert "result" in vars

    def test_find_defined_variables_python(self, tool):
        """Test finding defined variables in Python."""
        code = "x = 10\ny = 20"
        vars = tool._find_defined_variables(code, "python")
        assert "x" in vars
        assert "y" in vars

    def test_find_defined_variables_javascript(self, tool):
        """Test finding defined variables in JavaScript."""
        code = "const x = 10;\nlet y = 20;"
        vars = tool._find_defined_variables(code, "javascript")
        assert "x" in vars
        assert "y" in vars

    def test_build_function_python(self, tool):
        """Test building Python function."""
        func = tool._build_function("my_func", ["x", "y"], "return x + y", "python", "")
        assert "def my_func(x, y):" in func
        assert "return x + y" in func

    def test_build_function_javascript(self, tool):
        """Test building JavaScript function."""
        func = tool._build_function("myFunc", ["x", "y"], "return x + y;", "javascript", "")
        assert "function myFunc(x, y)" in func
        assert "return x + y;" in func

    def test_build_variable_declaration_python(self, tool):
        """Test building Python variable declaration."""
        decl = tool._build_variable_declaration("x", "10 + 20", "python", "    ")
        assert decl == "    x = 10 + 20"

    def test_build_variable_declaration_javascript(self, tool):
        """Test building JavaScript variable declaration."""
        decl = tool._build_variable_declaration("x", "10 + 20", "javascript", "  ")
        assert decl == "  const x = 10 + 20;"

    def test_parse_python_params(self, tool):
        """Test parsing Python parameters."""
        params = tool._parse_python_params("x, y: int, z: str = 'hello'")
        assert len(params) == 3
        assert params[0]["name"] == "x"
        assert params[1]["name"] == "y"
        assert params[1]["type"] == "int"
        assert params[2]["name"] == "z"
        assert params[2]["type"] == "str"
        assert params[2]["default"] == "'hello'"

    def test_parse_python_params_empty(self, tool):
        """Test parsing empty parameters."""
        params = tool._parse_python_params("")
        assert params == []

    def test_parse_python_params_complex_default(self, tool):
        """Test parsing parameters with complex defaults."""
        params = tool._parse_python_params("items: List[int] = [1, 2, 3]")
        assert len(params) == 1
        assert params[0]["name"] == "items"
        assert params[0]["type"] == "List[int]"
        assert params[0]["default"] == "[1, 2, 3]"

    def test_build_signature_python(self, tool):
        """Test building Python function signature."""
        params = [
            {"name": "x", "type": "int", "default": None},
            {"name": "y", "type": "str", "default": "'default'"},
        ]
        sig = tool._build_signature("my_func", params, "python")
        assert "def my_func(x: int, y: str = 'default'):" in sig

    def test_build_signature_javascript(self, tool):
        """Test building JavaScript function signature."""
        params = [
            {"name": "x", "type": None, "default": None},
            {"name": "y", "type": None, "default": "10"},
        ]
        sig = tool._build_signature("myFunc", params, "javascript")
        assert "function myFunc(x, y = 10) {" in sig

    def test_parse_call_arguments(self, tool):
        """Test parsing function call arguments."""
        args = tool._parse_call_arguments("myFunc(1, 2, 'hello')", "myFunc")
        assert args == ["1", "2", "'hello'"]

    def test_parse_call_arguments_nested(self, tool):
        """Test parsing nested function call arguments."""
        args = tool._parse_call_arguments("foo(bar(1, 2), [3, 4])", "foo")
        assert len(args) == 2
        assert args[0] == "bar(1, 2)"
        assert args[1] == "[3, 4]"


# Test factory function
def test_create_refactor_tool():
    """Test the factory function."""
    tool = create_refactor_tool()
    assert isinstance(tool, RefactorTool)
    assert tool.name == "refactor"
