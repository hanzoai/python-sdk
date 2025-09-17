"""Test FindTool with ffind for performance."""

import time
import tempfile
from pathlib import Path

import pytest
from hanzo_mcp.tools.search.find_tool import FFIND_AVAILABLE, FindTool


class TestFindToolFFind:
    """Test FindTool ffind functionality and performance."""

    @pytest.fixture
    def find_tool(self):
        """Create FindTool instance."""
        return FindTool()

    @pytest.fixture
    def test_directory(self):
        """Create a test directory structure with many files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a realistic directory structure
            # src/
            #   ├── main.py
            #   ├── utils.py
            #   ├── config.json
            #   └── modules/
            #       ├── auth.py
            #       ├── database.py
            #       └── api/
            #           ├── routes.py
            #           ├── handlers.py
            #           └── middleware.py
            # tests/
            #   ├── test_main.py
            #   ├── test_utils.py
            #   └── fixtures/
            #       └── data.json
            # docs/
            #   ├── README.md
            #   ├── API.md
            #   └── images/
            #       ├── logo.png
            #       └── diagram.svg
            # node_modules/ (should be ignored)
            #   └── package/
            #       └── index.js
            # .git/ (should be ignored)
            #   └── config

            # Create directories
            dirs = [
                "src",
                "src/modules",
                "src/modules/api",
                "tests",
                "tests/fixtures",
                "docs",
                "docs/images",
                "node_modules",
                "node_modules/package",
                ".git",
                "__pycache__",
                ".venv",
            ]

            for dir_name in dirs:
                Path(tmpdir, dir_name).mkdir(parents=True, exist_ok=True)

            # Create files with different sizes and content
            files = {
                "src/main.py": "# Main application\nimport sys\n\ndef main():\n    pass\n" * 100,
                "src/utils.py": "# Utilities\ndef helper():\n    return 'TODO: implement'\n",
                "src/config.json": '{"debug": true, "port": 8080}\n',
                "src/modules/auth.py": "# Authentication module\nclass Auth:\n    pass\n",
                "src/modules/database.py": "# Database module\nimport sqlite3\n" * 50,
                "src/modules/api/routes.py": "# API routes\nfrom flask import Flask\n",
                "src/modules/api/handlers.py": "# Request handlers\ndef handle_request():\n    pass\n",
                "src/modules/api/middleware.py": "# Middleware\ndef auth_middleware():\n    pass\n",
                "tests/test_main.py": "# Test main\nimport pytest\ndef test_main():\n    assert True\n",
                "tests/test_utils.py": "# Test utils\ndef test_helper():\n    pass\n",
                "tests/fixtures/data.json": '{"test": "data"}\n',
                "docs/README.md": "# Project README\n\nTODO: Write documentation\n",
                "docs/API.md": "# API Documentation\n\n## Endpoints\n\n### GET /api/users\n",
                "docs/images/logo.png": b"PNG fake image data" * 1000,  # Binary file
                "docs/images/diagram.svg": "<svg>TODO: Add diagram</svg>\n",
                "node_modules/package/index.js": "module.exports = {};\n",
                ".git/config": "[core]\nrepositoryformatversion = 0\n",
                "__pycache__/cache.pyc": b"Python bytecode",
                ".gitignore": "node_modules/\n__pycache__/\n*.pyc\n.venv/\n",
                "large_file.dat": "x" * 1024 * 1024,  # 1MB file
            }

            for file_path, content in files.items():
                full_path = Path(tmpdir, file_path)
                if isinstance(content, bytes):
                    full_path.write_bytes(content)
                else:
                    full_path.write_text(content)

            yield tmpdir

    def test_ffind_availability(self):
        """Test if ffind is available."""
        print(f"\nffind available: {FFIND_AVAILABLE}")
        # Don't fail if ffind is not installed, just report it
        if not FFIND_AVAILABLE:
            pytest.skip("ffind not installed - skipping performance tests")

    @pytest.mark.asyncio
    async def test_find_all_python_files(self, tool_helper, find_tool, test_directory):
        """Test finding all Python files."""
        if not FFIND_AVAILABLE:
            pytest.skip("ffind not installed - skipping ffind-specific tests")

        result = await find_tool.run(pattern="*.py", path=test_directory, type="file")

        # Check results
        assert "results" in result.data
        results = result.data["results"]

        # Should find Python files
        py_files = [r["name"] for r in results]
        assert "main.py" in py_files
        assert "utils.py" in py_files
        assert "auth.py" in py_files
        assert "test_main.py" in py_files

        # Should not find non-Python files
        assert "config.json" not in py_files
        assert "README.md" not in py_files

        # Should respect gitignore (no __pycache__)
        assert "cache.pyc" not in py_files

    @pytest.mark.asyncio
    async def test_find_with_size_filter(self, tool_helper, find_tool, test_directory):
        """Test finding files by size."""
        # Find large files (> 500KB)
        result = await find_tool.run(pattern="*", path=test_directory, type="file", min_size="500KB")

        results = result.data["results"]
        # Should only find large_file.dat
        assert len(results) == 1
        assert results[0]["name"] == "large_file.dat"

    @pytest.mark.asyncio
    async def test_find_directories(self, tool_helper, find_tool, test_directory):
        """Test finding directories."""
        result = await find_tool.run(
            pattern="*",
            path=test_directory,
            type="dir",
            max_depth=0,  # Only immediate children
        )

        results = result.data["results"]
        dir_names = [r["name"] for r in results]

        # Should find top-level directories
        assert "src" in dir_names
        assert "tests" in dir_names
        assert "docs" in dir_names

        # Should not find nested directories (max_depth=0)
        assert "modules" not in dir_names
        assert "api" not in dir_names

    @pytest.mark.asyncio
    async def test_find_with_pattern_in_content(self, tool_helper, find_tool, test_directory):
        """Test finding files containing specific text."""
        result = await find_tool.run(pattern="TODO", path=test_directory, in_content=True, type="file")

        results = result.data["results"]
        file_names = [r["name"] for r in results]

        # Should find files containing "TODO"
        assert "utils.py" in file_names  # Has TODO in content
        assert "README.md" in file_names  # Has TODO in content
        assert "diagram.svg" in file_names  # Has TODO in content

        # Should not find files without TODO
        assert "main.py" not in file_names
        assert "auth.py" not in file_names

    @pytest.mark.asyncio
    async def test_pagination(self, tool_helper, find_tool, test_directory):
        """Test pagination functionality."""
        # Get first page
        result_page1 = await find_tool.run(
            pattern="*",
            path=test_directory,
            type="file",
            page_size=5,
            page=1,
            sort_by="name",
        )

        page1_data = result_page1.data
        assert len(page1_data["results"]) == 5
        assert page1_data["pagination"]["page"] == 1
        assert page1_data["pagination"]["has_next"] == True

        # Get second page
        result_page2 = await find_tool.run(
            pattern="*",
            path=test_directory,
            type="file",
            page_size=5,
            page=2,
            sort_by="name",
        )

        page2_data = result_page2.data
        assert page2_data["pagination"]["page"] == 2

        # Results should be different
        page1_names = [r["name"] for r in page1_data["results"]]
        page2_names = [r["name"] for r in page2_data["results"]]
        assert set(page1_names).isdisjoint(set(page2_names))

    @pytest.mark.asyncio
    async def test_performance_comparison(self, tool_helper, find_tool, test_directory):
        """Compare performance with and without ffind."""
        if not FFIND_AVAILABLE:
            pytest.skip("ffind not installed - skipping performance comparison")
        # Force Python implementation
        import hanzo_mcp.tools.search.find_tool as find_module

        original_ffind = find_module.FFIND_AVAILABLE
        find_module.FFIND_AVAILABLE = False
        find_tool._available_backends = None

        start_time = time.time()
        result_python = await find_tool.run(pattern="*.py", path=test_directory, type="file")
        python_time = time.time() - start_time

        # Restore ffind if available
        find_module.FFIND_AVAILABLE = original_ffind
        find_tool._available_backends = None

        if FFIND_AVAILABLE:
            start_time = time.time()
            result_ffind = await find_tool.run(pattern="*.py", path=test_directory, type="file")
            ffind_time = time.time() - start_time

            print(f"\nPerformance comparison:")
            print(f"Python implementation: {python_time:.3f}s")
            print(f"ffind implementation: {ffind_time:.3f}s")
            print(f"Speedup: {python_time / ffind_time:.1f}x")

            # Results should be the same
            assert len(result_python.data["results"]) == len(result_ffind.data["results"])

    @pytest.mark.asyncio
    async def test_fuzzy_search(self, tool_helper, find_tool, test_directory):
        """Test fuzzy pattern matching."""
        result = await find_tool.run(
            pattern="tst",  # Fuzzy match for "test"
            path=test_directory,
            fuzzy=True,
            type="file",
        )

        results = result.data["results"]
        file_names = [r["name"] for r in results]

        # Should find test files with fuzzy matching
        assert any("test" in name for name in file_names)

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, tool_helper, find_tool, test_directory):
        """Test case-insensitive search."""
        result = await find_tool.run(
            pattern="*.MD",  # Uppercase extension
            path=test_directory,
            case_sensitive=False,
            type="file",
        )

        results = result.data["results"]
        file_names = [r["name"] for r in results]

        # Should find .md files despite case difference
        assert "README.md" in file_names
        assert "API.md" in file_names

    @pytest.mark.asyncio
    async def test_statistics(self, tool_helper, find_tool, test_directory):
        """Test that statistics are included in results."""
        result = await find_tool.run(pattern="*.py", path=test_directory)

        stats = result.data.get("statistics")
        assert stats is not None
        assert "total_found" in stats
        assert "search_time_ms" in stats
        assert "search_method" in stats
        assert stats["search_method"] in ["ffind", "python"]
        assert stats["search_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_gitignore_respect(self, tool_helper, find_tool, test_directory):
        """Test that .gitignore patterns are respected."""
        result = await find_tool.run(pattern="*", path=test_directory, respect_gitignore=True)

        results = result.data["results"]
        file_paths = [r["path"] for r in results]

        # Should not include gitignored files/dirs
        assert not any("node_modules" in path for path in file_paths)
        assert not any("__pycache__" in path for path in file_paths)
        assert not any(".pyc" in path for path in file_paths)

        # Test with gitignore disabled
        result_no_ignore = await find_tool.run(pattern="*", path=test_directory, respect_gitignore=False)

        results_no_ignore = result_no_ignore.data["results"]
        file_paths_no_ignore = [r["path"] for r in results_no_ignore]

        # Should include gitignored files when disabled
        assert any("node_modules" in path for path in file_paths_no_ignore)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
