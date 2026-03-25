"""Hanzo Flow — visual workflow builder for AI applications.

This package re-exports flow and provides the `hanzo-flow` CLI command.
"""
__version__ = "1.8.0"

# Re-export for convenience
try:
    from flow import load_flow_from_json, run_flow  # noqa: F401
except ImportError:
    pass
