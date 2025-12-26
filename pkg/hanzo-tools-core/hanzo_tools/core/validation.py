"""Validation utilities for tool parameters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    error_message: Optional[str] = None
    
    def __bool__(self) -> bool:
        return self.is_valid


def validate_path_parameter(
    path: str,
    param_name: str = "path",
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
) -> ValidationResult:
    """Validate a path parameter.
    
    Args:
        path: Path string to validate
        param_name: Name of the parameter for error messages
        must_exist: If True, path must exist
        must_be_file: If True, path must be a file
        must_be_dir: If True, path must be a directory
        
    Returns:
        ValidationResult with status and error if any
    """
    if not path:
        return ValidationResult(
            is_valid=False,
            error_message=f"{param_name} is required",
        )
    
    if not path.strip():
        return ValidationResult(
            is_valid=False,
            error_message=f"{param_name} cannot be empty",
        )
    
    try:
        p = Path(path)
        
        if must_exist and not p.exists():
            return ValidationResult(
                is_valid=False,
                error_message=f"{param_name} does not exist: {path}",
            )
        
        if must_be_file and p.exists() and not p.is_file():
            return ValidationResult(
                is_valid=False,
                error_message=f"{param_name} is not a file: {path}",
            )
        
        if must_be_dir and p.exists() and not p.is_dir():
            return ValidationResult(
                is_valid=False,
                error_message=f"{param_name} is not a directory: {path}",
            )
        
        return ValidationResult(is_valid=True)
        
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid {param_name}: {e}",
        )


def validate_string_parameter(
    value: str,
    param_name: str,
    min_length: int = 0,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
) -> ValidationResult:
    """Validate a string parameter."""
    if not value:
        return ValidationResult(
            is_valid=False,
            error_message=f"{param_name} is required",
        )
    
    if len(value) < min_length:
        return ValidationResult(
            is_valid=False,
            error_message=f"{param_name} must be at least {min_length} characters",
        )
    
    if max_length and len(value) > max_length:
        return ValidationResult(
            is_valid=False,
            error_message=f"{param_name} must be at most {max_length} characters",
        )
    
    if pattern:
        import re
        if not re.match(pattern, value):
            return ValidationResult(
                is_valid=False,
                error_message=f"{param_name} does not match required pattern",
            )
    
    return ValidationResult(is_valid=True)
