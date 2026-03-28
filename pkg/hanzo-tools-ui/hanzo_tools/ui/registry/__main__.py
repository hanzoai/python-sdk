"""Run the Hanzo UI Registry server.

Usage:
    python -m hanzo_tools.ui.registry
    # or
    hanzo-ui-registry
"""

import os


def main():
    import uvicorn

    host = os.environ.get("REGISTRY_HOST", "0.0.0.0")
    port = int(os.environ.get("REGISTRY_PORT", "8787"))
    dev = os.environ.get("REGISTRY_DEV", "") == "1"

    uvicorn.run(
        "hanzo_tools.ui.registry.server:app",
        host=host,
        port=port,
        reload=dev,
    )


if __name__ == "__main__":
    main()
