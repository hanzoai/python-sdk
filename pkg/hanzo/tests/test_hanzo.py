"""Basic tests for hanzo package."""


def test_import():
    """Test that hanzo package can be imported."""
    import hanzo
    assert hanzo is not None


def test_cli_exists():
    """Test that CLI module exists."""
    import hanzo.cli
    assert hanzo.cli is not None