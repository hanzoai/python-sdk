"""Permission management for filesystem tools."""

import os
from pathlib import Path
from typing import Optional


class PermissionManager:
    """Manages filesystem permissions for tools.
    
    Controls which paths tools are allowed to access.
    """
    
    def __init__(
        self,
        allowed_paths: Optional[list[str | Path]] = None,
        deny_patterns: Optional[list[str]] = None,
    ):
        """Initialize permission manager.
        
        Args:
            allowed_paths: List of allowed base paths (defaults to cwd)
            deny_patterns: Patterns to deny (e.g., '.git', 'node_modules')
        """
        self.allowed_paths: list[Path] = []
        if allowed_paths:
            for p in allowed_paths:
                self.allowed_paths.append(Path(p).resolve())
        else:
            self.allowed_paths.append(Path.cwd())
        
        self.deny_patterns = deny_patterns or [
            '.git',
            '__pycache__',
            '.pyc',
            'node_modules',
            '.env',
            '.secrets',
        ]
    
    def is_path_allowed(self, path: str | Path) -> bool:
        """Check if a path is allowed.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within allowed paths and not denied
        """
        try:
            resolved = Path(path).resolve()
            
            # Check if path is under any allowed path
            is_under_allowed = any(
                self._is_subpath(resolved, allowed)
                for allowed in self.allowed_paths
            )
            
            if not is_under_allowed:
                return False
            
            # Check deny patterns
            path_str = str(resolved)
            for pattern in self.deny_patterns:
                if pattern in path_str:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _is_subpath(self, path: Path, parent: Path) -> bool:
        """Check if path is under parent."""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
    
    def add_allowed_path(self, path: str | Path) -> None:
        """Add a path to the allowed list."""
        self.allowed_paths.append(Path(path).resolve())
    
    def add_deny_pattern(self, pattern: str) -> None:
        """Add a deny pattern."""
        self.deny_patterns.append(pattern)
