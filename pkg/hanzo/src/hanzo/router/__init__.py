"""Router module - re-exports from router package."""

try:
    # Import directly from the installed router package
    import router
    from router import Router, embedding, aembedding, completion, acompletion

    # Re-export the entire router module
    __all__ = [
        "router",
        "Router",
        "completion",
        "acompletion",
        "embedding",
        "aembedding",
    ]

    # Make router available as a submodule
    import sys

    sys.modules["hanzo.router"] = router

except ImportError as e:
    # If router is not installed, provide helpful error
    import sys

    print(f"Error importing router: {e}", file=sys.stderr)
    print(
        "Please install router from the main repository: pip install -e /Users/z/work/hanzo/router",
        file=sys.stderr,
    )

    # Define placeholders to avoid complete failure
    router = None
    Router = None
    completion = None
    acompletion = None
    embedding = None
    aembedding = None
