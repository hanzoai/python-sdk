"""Local test bootstrap for hanzo-mcp.

Ensures third-party pytest plugins aren't auto-loaded during local test runs,
which can cause import-time failures from globally installed packages.

This file is auto-imported by Python at startup if present on sys.path.
"""

import os as _os

# Disable pytest's auto plugin discovery unless already set by the user/CI
_os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
