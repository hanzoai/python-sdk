"""Tests for hanzo-tools-database."""

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_package(self):
        from hanzo_tools import database

        assert database is not None

    def test_import_tools(self):
        from hanzo_tools.database import TOOLS

        assert len(TOOLS) > 0
