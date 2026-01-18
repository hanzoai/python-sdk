"""Event loop configuration with optional uvloop support.

This module provides utilities for configuring the asyncio event loop
with optional uvloop support for improved performance on Linux/macOS.

Uses hanzo_async for unified async I/O configuration.
"""

import sys
import asyncio
from typing import Optional

from hanzo_async import using_uvloop, configure_loop


def configure_event_loop(*, quiet: bool = False) -> Optional[str]:
    """Configure the event loop with uvloop if available.

    This should be called early in the application startup, before
    any async code runs.

    Args:
        quiet: If True, suppress info messages about uvloop status

    Returns:
        The name of the event loop policy being used, or None if default
    """
    # Use hanzo_async for unified configuration
    if configure_loop():
        if not quiet:
            import logging

            try:
                import uvloop

                logger = logging.getLogger(__name__)
                logger.debug(f"Using uvloop {uvloop.__version__} for event loop")
            except ImportError:
                pass

        try:
            import uvloop

            return f"uvloop-{uvloop.__version__}"
        except ImportError:
            return None

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
        "using_uvloop": using_uvloop(),
    }

    # Check if uvloop is available
    try:
        import uvloop

        info["uvloop_available"] = True
        info["uvloop_version"] = uvloop.__version__
    except ImportError:
        info["uvloop_available"] = False

    return info
