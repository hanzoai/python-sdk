"""Parameter validation utilities for Hanzo AI tools.

Re-exports validation utilities from hanzo-tools-core for backwards compatibility.
"""

# Re-export from hanzo-tools-core
from hanzo_tools.core.validation import (
    ValidationResult,
    validate_path_parameter,
    validate_string_parameter,
)

__all__ = [
    "ValidationResult",
    "validate_path_parameter",
    "validate_string_parameter",
]
