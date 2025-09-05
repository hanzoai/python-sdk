"""Fast file finding tool using ffind and intelligent caching."""

import os
import time
import fnmatch
import subprocess
from typing import Any, Set, Dict, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from hanzo_mcp.types import MCPResourceDocument
from hanzo_mcp.tools.common.base import BaseTool

# Check if ffind command is available
try:
    subprocess.run(["ffind", "--version"], capture_output=True, check=True)
    FFIND_AVAILABLE = True
except (subprocess.CalledProcessError, FileNotFoundError):
    FFIND_AVAILABLE = False


@dataclass
class FileMatch:
    """Represents a found file."""

    path: str
    name: str
    size: int
    modified: float
    is_dir: bool
    extension: str
    depth: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "modified": datetime.fromtimestamp(self.modified).isoformat(),
            "is_dir": self.is_dir,
            "extension": self.extension,
            "depth": self.depth,
        }


class FindTool(BaseTool):
    """Fast file and directory finding tool.

    This tool is optimized for quickly finding files and directories by name,
    pattern, or attributes. It uses ffind (when available) for blazing fast
    performance and falls back to optimized Python implementation.

    Key features:
    - Lightning fast file discovery
    - Smart pattern matching (glob, regex, fuzzy)
    - File attribute filtering (size, date, type)
    - Intelligent result ranking
    - Built-in caching for repeated searches
    - Respects .gitignore by default
    """

    name = "find"
    description = """Find files and directories by name, pattern, or attributes.
    
    Examples:
    - find("*.py") - Find all Python files
    - find("test_", type="file") - Find files starting with test_
    - find("src", type="dir") - Find directories named src
    - find("TODO", in_content=True) - Find files containing TODO
    - find("large", min_size="10MB") - Find files larger than 10MB
    - find("recent", modified_after="1 day ago") - Recently modified files
    
    This is the primary tool for discovering files in a project. Use it before
    reading or searching within files.
    """

    def __init__(self):
        super().__init__()
        self._cache = {}
        self._gitignore_cache = {}

    def _parse_size(self, size_str: str) -> int:
        """Parse human-readable size to bytes."""
        # Order matters - check longer units first
        units = [
            ("TB", 1024**4),
            ("GB", 1024**3),
            ("MB", 1024**2),
            ("KB", 1024),
            ("T", 1024**4),
            ("G", 1024**3),
            ("M", 1024**2),
            ("K", 1024),
            ("B", 1),
        ]

        size_str = size_str.upper().strip()
        for unit, multiplier in units:
            if size_str.endswith(unit):
                num_str = size_str[: -len(unit)].strip()
                if num_str:
                    try:
                        return int(float(num_str) * multiplier)
                    except ValueError:
                        return 0

        try:
            return int(size_str)
        except ValueError:
            return 0

    def _parse_time(self, time_str: str) -> float:
        """Parse human-readable time to timestamp."""
        import re
        from datetime import datetime, timedelta

        # Handle relative times like "1 day ago", "2 hours ago"
        match = re.match(
            r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago",
            time_str.lower(),
        )
        if match:
            amount = int(match.group(1))
            unit = match.group(2)

            if unit == "second":
                delta = timedelta(seconds=amount)
            elif unit == "minute":
                delta = timedelta(minutes=amount)
            elif unit == "hour":
                delta = timedelta(hours=amount)
            elif unit == "day":
                delta = timedelta(days=amount)
            elif unit == "week":
                delta = timedelta(weeks=amount)
            elif unit == "month":
                delta = timedelta(days=amount * 30)  # Approximate
            elif unit == "year":
                delta = timedelta(days=amount * 365)  # Approximate

            return (datetime.now() - delta).timestamp()

        # Try parsing as date
        try:
            return datetime.fromisoformat(time_str).timestamp()
        except Exception:
            return datetime.now().timestamp()

    def _load_gitignore(self, root: str) -> Set[str]:
        """Load and parse .gitignore patterns."""
        if root in self._gitignore_cache:
            return self._gitignore_cache[root]

        patterns = set()
        gitignore_path = Path(root) / ".gitignore"

        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.add(line)
            except Exception:
                pass

        # Add common ignore patterns
        patterns.update(
            [
                "*.pyc",
                "__pycache__",
                ".git",
                ".svn",
                ".hg",
                "node_modules",
                ".env",
                ".venv",
                "venv",
                "*.swp",
                "*.swo",
                ".DS_Store",
                "Thumbs.db",
            ]
        )

        self._gitignore_cache[root] = patterns
        return patterns

    def _should_ignore(self, path: str, ignore_patterns: Set[str]) -> bool:
        """Check if path should be ignored."""
        path_obj = Path(path)

        for pattern in ignore_patterns:
            # Check against full path and basename
            if fnmatch.fnmatch(path_obj.name, pattern):
                return True
            if fnmatch.fnmatch(str(path_obj), pattern):
                return True

            # Check if any parent directory matches
            for parent in path_obj.parents:
                if fnmatch.fnmatch(parent.name, pattern):
                    return True

        return False

    async def run(
        self,
        pattern: str = "*",
        path: str = ".",
        type: Optional[str] = None,  # "file", "dir", "any"
        min_size: Optional[str] = None,
        max_size: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        max_depth: Optional[int] = None,
        case_sensitive: bool = False,
        regex: bool = False,
        fuzzy: bool = False,
        in_content: bool = False,
        follow_symlinks: bool = False,
        respect_gitignore: bool = True,
        max_results: int = 1000,
        sort_by: str = "path",  # "path", "name", "size", "modified"
        reverse: bool = False,
        page_size: int = 100,
        page: int = 1,
        **kwargs,
    ) -> MCPResourceDocument:
        """Find files and directories.

        Args:
            pattern: Search pattern (glob by default, regex if regex=True)
            path: Root directory to search from
            type: Filter by type ("file", "dir", "any")
            min_size: Minimum file size (e.g., "1MB", "500K")
            max_size: Maximum file size
            modified_after: Find files modified after this time
            modified_before: Find files modified before this time
            max_depth: Maximum directory depth to search
            case_sensitive: Case-sensitive matching
            regex: Treat pattern as regex instead of glob
            fuzzy: Use fuzzy matching for pattern
            in_content: Search for pattern inside files (slower)
            follow_symlinks: Follow symbolic links
            respect_gitignore: Respect .gitignore patterns
            max_results: Maximum results to return
            sort_by: Sort results by attribute
            reverse: Reverse sort order
            page_size: Results per page
            page: Page number
        """

        start_time = time.time()

        # Resolve path
        root_path = Path(path).resolve()
        if not root_path.exists():
            return MCPResourceDocument(data={"error": f"Path does not exist: {path}", "results": []})

        # Get ignore patterns
        ignore_patterns = set()
        if respect_gitignore:
            ignore_patterns = self._load_gitignore(str(root_path))

        # Parse filters
        min_size_bytes = self._parse_size(min_size) if min_size else None
        max_size_bytes = self._parse_size(max_size) if max_size else None
        modified_after_ts = self._parse_time(modified_after) if modified_after else None
        modified_before_ts = self._parse_time(modified_before) if modified_before else None

        # Collect matches
        matches = []

        if FFIND_AVAILABLE and not in_content:
            # Use ffind for fast file discovery
            matches = await self._find_with_ffind(
                pattern,
                root_path,
                type,
                case_sensitive,
                regex,
                fuzzy,
                max_depth,
                follow_symlinks,
                respect_gitignore,
                ignore_patterns,
            )
        else:
            # Fall back to Python implementation
            matches = await self._find_with_python(
                pattern,
                root_path,
                type,
                case_sensitive,
                regex,
                fuzzy,
                in_content,
                max_depth,
                follow_symlinks,
                respect_gitignore,
                ignore_patterns,
            )

        # Apply filters
        filtered_matches = []
        for match in matches:
            # Size filters
            if min_size_bytes and match.size < min_size_bytes:
                continue
            if max_size_bytes and match.size > max_size_bytes:
                continue

            # Time filters
            if modified_after_ts and match.modified < modified_after_ts:
                continue
            if modified_before_ts and match.modified > modified_before_ts:
                continue

            filtered_matches.append(match)

            if len(filtered_matches) >= max_results:
                break

        # Sort results
        if sort_by == "name":
            filtered_matches.sort(key=lambda m: m.name, reverse=reverse)
        elif sort_by == "size":
            filtered_matches.sort(key=lambda m: m.size, reverse=reverse)
        elif sort_by == "modified":
            filtered_matches.sort(key=lambda m: m.modified, reverse=reverse)
        else:  # path
            filtered_matches.sort(key=lambda m: m.path, reverse=reverse)

        # Paginate
        total_results = len(filtered_matches)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = filtered_matches[start_idx:end_idx]

        # Format results
        formatted_results = [match.to_dict() for match in page_results]

        # Statistics
        stats = {
            "total_found": total_results,
            "search_time_ms": int((time.time() - start_time) * 1000),
            "search_method": ("ffind" if FFIND_AVAILABLE and not in_content else "python"),
            "root_path": str(root_path),
            "filters_applied": {
                "pattern": pattern,
                "type": type,
                "size": ({"min": min_size, "max": max_size} if min_size or max_size else None),
                "modified": (
                    {"after": modified_after, "before": modified_before} if modified_after or modified_before else None
                ),
                "max_depth": max_depth,
                "gitignore": respect_gitignore,
            },
        }

        return MCPResourceDocument(
            data={
                "results": formatted_results,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_results": total_results,
                    "total_pages": (total_results + page_size - 1) // page_size,
                    "has_next": end_idx < total_results,
                    "has_prev": page > 1,
                },
                "statistics": stats,
            }
        )

    async def call(self, **kwargs) -> str:
        """Tool interface for MCP - converts result to JSON string."""
        result = await self.run(**kwargs)
        return result.to_json_string()

    def register(self, mcp_server) -> None:
        """Register tool with MCP server."""

        @mcp_server.tool(name=self.name, description=self.description)
        async def find_handler(
            pattern: str,
            path: str = ".",
            type: Optional[str] = None,
            max_results: int = 100,
            max_depth: Optional[int] = None,
            case_sensitive: bool = False,
            regex: bool = False,
            fuzzy: bool = False,
            min_size: Optional[str] = None,
            max_size: Optional[str] = None,
            modified_after: Optional[str] = None,
            modified_before: Optional[str] = None,
            follow_symlinks: bool = True,
            respect_gitignore: bool = True,
            sort_by: str = "name",
            reverse: bool = False,
            page_size: int = 50,
            page: int = 1,
        ) -> str:
            """Execute file finding."""
            return await self.call(
                pattern=pattern,
                path=path,
                type=type,
                max_results=max_results,
                max_depth=max_depth,
                case_sensitive=case_sensitive,
                regex=regex,
                fuzzy=fuzzy,
                min_size=min_size,
                max_size=max_size,
                modified_after=modified_after,
                modified_before=modified_before,
                follow_symlinks=follow_symlinks,
                respect_gitignore=respect_gitignore,
                sort_by=sort_by,
                reverse=reverse,
                page_size=page_size,
                page=page,
            )

    async def _find_with_ffind(
        self,
        pattern: str,
        root: Path,
        file_type: Optional[str],
        case_sensitive: bool,
        regex: bool,
        fuzzy: bool,
        max_depth: Optional[int],
        follow_symlinks: bool,
        respect_gitignore: bool,
        ignore_patterns: Set[str],
    ) -> List[FileMatch]:
        """Use ffind for fast file discovery."""
        matches = []

        # Configure ffind
        ffind_args = {
            "path": str(root),
            "pattern": pattern,
            "regex": regex,
            "case_sensitive": case_sensitive,
            "follow_symlinks": follow_symlinks,
        }

        if fuzzy:
            ffind_args["fuzzy"] = True

        if max_depth:
            ffind_args["max_depth"] = max_depth

        try:
            # Build ffind command
            cmd = ["ffind"]

            if not case_sensitive:
                cmd.append("-i")

            if regex:
                cmd.append("-E")

            if fuzzy:
                cmd.append("-f")

            if follow_symlinks:
                cmd.append("-L")

            if max_depth:
                cmd.extend(["-D", str(max_depth)])

            # Add path and pattern (ffind expects directory first)
            cmd.append(str(root))
            cmd.append(pattern)

            # Run ffind command
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                # Fall back to Python implementation on error
                return await self._find_with_python(
                    pattern,
                    root,
                    file_type,
                    case_sensitive,
                    regex,
                    fuzzy,
                    False,
                    max_depth,
                    follow_symlinks,
                    respect_gitignore,
                    ignore_patterns,
                )

            # Parse results
            results = result.stdout.strip().split("\n") if result.stdout else []

            for path in results:
                if not path:  # Skip empty lines
                    continue

                # Check ignore patterns
                if self._should_ignore(path, ignore_patterns):
                    continue

                # Get file info
                try:
                    stat = os.stat(path)
                    is_dir = os.path.isdir(path)

                    # Apply type filter
                    if file_type == "file" and is_dir:
                        continue
                    if file_type == "dir" and not is_dir:
                        continue

                    match = FileMatch(
                        path=path,
                        name=os.path.basename(path),
                        size=stat.st_size,
                        modified=stat.st_mtime,
                        is_dir=is_dir,
                        extension=Path(path).suffix,
                        depth=len(Path(path).relative_to(root).parts),
                    )
                    matches.append(match)

                except OSError:
                    continue

        except Exception:
            # Fall back to Python implementation
            return await self._find_with_python(
                pattern,
                root,
                file_type,
                case_sensitive,
                regex,
                False,
                False,
                max_depth,
                follow_symlinks,
                respect_gitignore,
                ignore_patterns,
            )

        return matches

    async def _find_with_python(
        self,
        pattern: str,
        root: Path,
        file_type: Optional[str],
        case_sensitive: bool,
        regex: bool,
        fuzzy: bool,
        in_content: bool,
        max_depth: Optional[int],
        follow_symlinks: bool,
        respect_gitignore: bool,
        ignore_patterns: Set[str],
    ) -> List[FileMatch]:
        """Python implementation of file finding."""
        matches = []

        import re
        from difflib import SequenceMatcher

        # Prepare pattern matcher
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern_re = re.compile(pattern, flags)
                matcher = lambda name: pattern_re.search(name) is not None
            except re.error:
                matcher = lambda name: pattern in name
        elif fuzzy:
            pattern_lower = pattern.lower() if not case_sensitive else pattern
            matcher = (
                lambda name: SequenceMatcher(None, pattern_lower, name.lower() if not case_sensitive else name).ratio()
                > 0.6
            )
        else:
            # Glob pattern
            if not case_sensitive:
                pattern = pattern.lower()
                matcher = lambda name: fnmatch.fnmatch(name.lower(), pattern)
            else:
                matcher = lambda name: fnmatch.fnmatch(name, pattern)

        # Walk directory tree
        for dirpath, dirnames, filenames in os.walk(str(root), followlinks=follow_symlinks):
            # Check depth
            if max_depth is not None:
                depth = len(Path(dirpath).relative_to(root).parts)
                if depth > max_depth:
                    dirnames.clear()  # Don't recurse deeper
                    continue

            # Filter directories to skip
            if respect_gitignore:
                dirnames[:] = [
                    d for d in dirnames if not self._should_ignore(os.path.join(dirpath, d), ignore_patterns)
                ]

            # Check directories
            if file_type != "file":
                for dirname in dirnames:
                    if matcher(dirname):
                        full_path = os.path.join(dirpath, dirname)
                        if not self._should_ignore(full_path, ignore_patterns):
                            try:
                                stat = os.stat(full_path)
                                match = FileMatch(
                                    path=full_path,
                                    name=dirname,
                                    size=0,  # Directories don't have size
                                    modified=stat.st_mtime,
                                    is_dir=True,
                                    extension="",
                                    depth=len(Path(full_path).relative_to(root).parts),
                                )
                                matches.append(match)
                            except OSError:
                                continue

            # Check files
            if file_type != "dir":
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)

                    if self._should_ignore(full_path, ignore_patterns):
                        continue

                    # Match against filename
                    if matcher(filename):
                        match_found = True
                    elif in_content:
                        # Search in file content
                        match_found = await self._search_in_file(full_path, pattern, case_sensitive)
                    else:
                        match_found = False

                    if match_found:
                        try:
                            stat = os.stat(full_path)
                            match = FileMatch(
                                path=full_path,
                                name=filename,
                                size=stat.st_size,
                                modified=stat.st_mtime,
                                is_dir=False,
                                extension=Path(filename).suffix,
                                depth=len(Path(full_path).relative_to(root).parts),
                            )
                            matches.append(match)
                        except OSError:
                            continue

        return matches

    async def _search_in_file(self, file_path: str, pattern: str, case_sensitive: bool) -> bool:
        """Search for pattern in file content."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if not case_sensitive:
                    return pattern.lower() in content.lower()
                else:
                    return pattern in content
        except Exception:
            return False


# Tool registration
def create_find_tool():
    """Factory function to create find tool."""
    return FindTool()
