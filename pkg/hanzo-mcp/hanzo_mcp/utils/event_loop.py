"""Event loop configuration with optional uvloop support.

This module provides utilities for configuring the asyncio event loop
with optional uvloop support for improved performance on Linux/macOS.
"""

import sys
import asyncio
from typing import Optional


def configure_event_loop(*, quiet: bool = False) -> Optional[str]:
    """Configure the event loop with uvloop if available.

    This should be called early in the application startup, before
    any async code runs.

    Args:
        quiet: If True, suppress info messages about uvloop status

    Returns:
        The name of the event loop policy being used, or None if default
    """
    # uvloop is not available on Windows
    if sys.platform == "win32":
        return None

    try:
        import uvloop

        # Install uvloop as the default event loop policy
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        if not quiet:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Using uvloop {uvloop.__version__} for event loop")

        return f"uvloop-{uvloop.__version__}"

    except ImportError:
        # uvloop not installed, use default asyncio event loop
        return None


def get_event_loop_info() -> dict:
    """Get information about the current event loop configuration.

    Returns:
        Dictionary with event loop details
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    info = {
        "loop_class": type(loop).__name__ if loop else None,
        "loop_module": type(loop).__module__ if loop else None,
        "platform": sys.platform,
    }

    # Check if uvloop is being used
    try:
        import uvloop

        info["uvloop_available"] = True
        info["uvloop_version"] = uvloop.__version__
        info["using_uvloop"] = isinstance(asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy)
    except ImportError:
        info["uvloop_available"] = False
        info["using_uvloop"] = False

    return info
