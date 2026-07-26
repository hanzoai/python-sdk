"""Entry point for `python -m hanzo_cli`.

This package no longer installs a `hanzo` console script — that command name
belongs to the `hanzo` package alone. This module is how hanzo_cli's own
command tree is invoked directly, which is what its test suite targets.
"""

from hanzo_cli.cli import main

if __name__ == "__main__":
    main()
