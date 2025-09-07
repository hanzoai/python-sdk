#!/usr/bin/env python3
"""Start the Hanzo MCP server."""

import sys
import os

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the server
from hanzo_mcp.server import main

if __name__ == "__main__":
    main()