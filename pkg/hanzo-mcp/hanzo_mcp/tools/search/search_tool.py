"""Primary unified search tool - THE search tool for finding anything in code.

This is your main search interface that intelligently combines all available
search capabilities including text, AST, symbols, memory, and semantic search.
"""

import json
import time
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

from hanzo_mcp.types import MCPResourceDocument
from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.auto_timeout import auto_timeout

# Import memory tools if available
try:
    from hanzo_mcp.tools.memory.memory_tools import KnowledgeRetrieval

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    import tree_sitter

    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False

# Vector search removed - too heavy for MCP tools
# If semantic search is needed, use external services (hanzo-node, hanzo desktop)

# LSP availability check
try:
    from hanzo_mcp.tools.lsp.lsp_tool import LSPTool, LSP_SERVERS

    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False

# Git search availability
try:
    from hanzo_mcp.tools.filesystem.git_search import GitSearchTool

    GIT_SEARCH_AVAILABLE = True
except ImportError:
    GIT_SEARCH_AVAILABLE = False


@dataclass
class SearchResult:
    """Unified search result."""

    file_path: str
    line_number: int
    column: int
    match_text: str
    context_before: List[str]
    context_after: List[str]
    match_type: str  # 'text', 'ast', 'vector', 'symbol', 'memory', 'file'
    score: float = 1.0
    node_type: Optional[str] = None
    semantic_context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "line": self.line_number,
            "column": self.column,
            "match": self.match_text,
            "type": self.match_type,
            "score": self.score,
            "context": {
                "before": self.context_before,
                "after": self.context_after,
                "node_type": self.node_type,
                "semantic": self.semantic_context,
            },
        }

    def __hash__(self):
        """Make result hashable for deduplication."""
        return hash((self.file_path, self.line_number, self.column, self.match_text))


class SearchTool(BaseTool):
    """THE primary search tool - your universal interface for finding anything.

    This is the main search tool you should use for finding:
    - Code patterns and text matches (using ripgrep)
    - AST nodes and code structure (using treesitter)
    - Symbol definitions and references (using ctags/LSP)
    - Files and directories (using find tool)
    - Memory and knowledge base entries

    The tool automatically determines the best search strategy based on your query
    and runs multiple search types in parallel for comprehensive results.

    USAGE EXAMPLES:

    1. Find code patterns:
       search("error handling")  # Finds all error handling code
       search("TODO|FIXME")     # Regex search for TODOs
       search("async function") # Find async functions

    2. Find symbols/definitions:
       search("class UserService")      # Find class definition
       search("handleRequest")          # Find function/method
       search("MAX_RETRIES")           # Find constant

    3. Find files:
       search("test_*.py", search_files=True)  # Find test files
       search("config", search_files=True)      # Find config files

    4. Memory search:
       search("previous discussion about API design")  # Search memories
       search("that bug we fixed last week")          # Search knowledge

    The tool automatically:
    - Detects query intent and chooses appropriate search methods
    - Runs searches in parallel for speed
    - Deduplicates and ranks results by relevance
    - Provides context around matches
    - Paginates results to stay within token limits
    - Respects .gitignore and other exclusions

    PRO TIPS:
    - Use code syntax for exact matches
    - Add search_files=True to also find filenames
    - Results are ranked by relevance and type
    - Use page parameter to get more results
    """

    name = "search"
    description = """THE primary unified search tool for rapid parallel search.

    Find anything in your codebase using text, AST, symbols, files, and memory search.
    Fast and lightweight - no heavy ML dependencies.
    """

    def __init__(self):
        """Initialize search tool - fast and lightweight."""
        super().__init__()
        self.ripgrep_available = self._check_ripgrep()
        self.git_available = self._check_git()

    def _check_ripgrep(self) -> bool:
        """Check if ripgrep is available."""
        try:
            subprocess.run(["rg", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def _check_git(self) -> bool:
        """Check if git is available."""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def _should_use_ast_search(self, query: str) -> bool:
        """Determine if AST search would be helpful."""
        # Use AST search for code patterns
        indicators = [
            "class " in query or "function " in query or "def " in query,
            "import " in query or "from " in query,
            any(kw in query.lower() for kw in ["method", "function", "class", "interface", "struct"]),
            "::" in query or "->" in query or "." in query,  # Member access
        ]
        return any(indicators)

    def _should_use_symbol_search(self, query: str) -> bool:
        """Determine if symbol search would be helpful."""
        # Use symbol search for identifiers
        return (
            len(query.split()) <= 2  # Short queries
            and query.replace("_", "").replace("-", "").isalnum()  # Looks like identifier
            and not " " in query.strip()  # Single token
        )

    def _is_git_repo(self, path: str) -> bool:
        """Check if path is inside a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                cwd=path or ".",
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def run(
        self,
        pattern: str,
        path: str = ".",
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        max_results_per_type: int = 20,
        context_lines: int = 3,
        search_files: bool = False,
        search_memory: bool = None,
        search_git_history: bool = None,
        enable_text: bool = None,
        enable_ast: bool = None,
        enable_symbol: bool = None,
        enable_lsp: bool = None,
        page_size: int = 50,
        page: int = 1,
        **kwargs,
    ) -> MCPResourceDocument:
        """Execute unified search across all available search modalities.

        Args:
            pattern: Search query (text, regex, natural language, or glob for files)
            path: Directory to search in (default: current directory)
            include: File pattern to include (e.g., "*.py", "*.js")
            exclude: File pattern to exclude (e.g., "*.test.py")
            max_results_per_type: Max results from each search type
            context_lines: Lines of context around text matches
            search_files: Also search for matching filenames
            search_memory: Search in memory/knowledge base (auto-detected if None)
            search_git_history: Search git commit history (auto-detected if None)
            enable_*: Force enable/disable specific search types (auto if None)
            enable_lsp: Enable LSP-based reference search (auto if None)
            page_size: Results per page (default: 50)
            page: Page number to retrieve (default: 1)
        """

        # Auto-detect search types based on query
        if search_memory is None:
            # Search memory for natural language queries or specific references
            search_memory = MEMORY_AVAILABLE and any(
                word in pattern.lower() for word in ["previous", "discussion", "remember", "last"]
            )

        if enable_text is None:
            enable_text = True  # Always use text search as baseline

        if enable_ast is None:
            enable_ast = self._should_use_ast_search(pattern) and TREESITTER_AVAILABLE

        if enable_symbol is None:
            enable_symbol = self._should_use_symbol_search(pattern)

        if enable_lsp is None:
            # Use LSP for symbol-like queries when LSP is available
            enable_lsp = LSP_AVAILABLE and self._should_use_symbol_search(pattern)

        if search_git_history is None:
            # Auto-enable git history for identifier-like patterns in git repos
            search_git_history = (GIT_SEARCH_AVAILABLE or self.git_available) and self._is_git_repo(path) and self._should_use_symbol_search(pattern)

        # Collect results from all enabled search types
        all_results = []
        search_stats = {
            "query": pattern,
            "path": path,
            "search_types_used": [],
            "total_matches": 0,
            "unique_matches": 0,
            "time_ms": {},
        }

        # Run all searches in PARALLEL using asyncio.gather
        import asyncio
        
        async def timed_search(name: str, coro):
            """Wrapper to time each search."""
            start = time.time()
            try:
                results = await coro
            except Exception as e:
                print(f"{name} search error: {e}")
                results = []
            elapsed = int((time.time() - start) * 1000)
            return name, results, elapsed
        
        # Build list of search coroutines to run in parallel
        search_tasks = []
        
        if enable_text:
            search_tasks.append(timed_search(
                "text", 
                self._text_search(pattern, path, include, exclude, max_results_per_type, context_lines)
            ))
        
        if enable_ast and TREESITTER_AVAILABLE:
            search_tasks.append(timed_search(
                "ast",
                self._ast_search(pattern, path, include, exclude, max_results_per_type, context_lines)
            ))
        
        if enable_symbol:
            search_tasks.append(timed_search(
                "symbol",
                self._symbol_search(pattern, path, include, exclude, max_results_per_type)
            ))
        
        if search_files:
            search_tasks.append(timed_search(
                "files",
                self._file_search(pattern, path, include, exclude, max_results_per_type)
            ))
        
        if search_memory:
            search_tasks.append(timed_search(
                "memory",
                self._memory_search(pattern, max_results_per_type, context_lines)
            ))
        
        if enable_lsp and LSP_AVAILABLE:
            search_tasks.append(timed_search(
                "lsp",
                self._lsp_search(pattern, path, include, max_results_per_type)
            ))

        if search_git_history and self.git_available:
            search_tasks.append(timed_search(
                "git",
                self._git_history_search(pattern, path, max_results_per_type)
            ))

        # Execute all searches in parallel
        if search_tasks:
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for result in results_list:
                if isinstance(result, Exception):
                    continue
                name, results, elapsed = result
                search_stats["time_ms"][name] = elapsed
                search_stats["search_types_used"].append(name)
                all_results.extend(results)

        # Deduplicate and rank results
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, pattern)

        search_stats["total_matches"] = len(all_results)
        search_stats["unique_matches"] = len(ranked_results)

        # Paginate results
        total_results = len(ranked_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = ranked_results[start_idx:end_idx]

        # Format results for output
        formatted_results = []
        for result in page_results:
            formatted = result.to_dict()
            # Add match preview with context
            formatted["preview"] = self._format_preview(result)
            formatted_results.append(formatted)

        # Create paginated response
        response_data = {
            "results": formatted_results,
            "statistics": search_stats,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_results": total_results,
                "total_pages": (total_results + page_size - 1) // page_size,
                "has_next": end_idx < total_results,
                "has_prev": page > 1,
            },
        }

        return MCPResourceDocument(data=response_data)

    @auto_timeout("search")
    async def call(self, ctx=None, **kwargs) -> str:
        """Tool interface for MCP - converts result to JSON string."""
        result = await self.run(**kwargs)
        return result.to_json_string()

    def register(self, mcp_server) -> None:
        """Register tool with MCP server."""

        @mcp_server.tool(name=self.name, description=self.description)
        async def search_handler(
            pattern: str,
            path: str = ".",
            include: Optional[str] = None,
            exclude: Optional[str] = None,
            max_results_per_type: int = 20,
            context_lines: int = 2,
            page_size: int = 50,
            page: int = 1,
            enable_text: bool = True,
            enable_ast: bool = True,
            enable_symbol: bool = True,
            search_files: bool = False,
            search_memory: bool = False,
            search_git_history: bool = False,
        ) -> str:
            """Execute unified search."""
            return await self.call(
                pattern=pattern,
                path=path,
                include=include,
                exclude=exclude,
                max_results_per_type=max_results_per_type,
                context_lines=context_lines,
                page_size=page_size,
                page=page,
                enable_text=enable_text,
                enable_ast=enable_ast,
                enable_symbol=enable_symbol,
                search_files=search_files,
                search_memory=search_memory,
                search_git_history=search_git_history,
            )

    async def _text_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
        context_lines: int,
    ) -> List[SearchResult]:
        """Perform text search using ripgrep."""
        results = []

        if not self.ripgrep_available:
            # Fallback to Python implementation
            return await self._python_text_search(pattern, path, include, exclude, max_results, context_lines)

        # Build ripgrep command
        cmd = ["rg", "--json", "--max-count", str(max_results)]

        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])

        if include:
            cmd.extend(["--glob", include])

        if exclude:
            cmd.extend(["--glob", f"!{exclude}"])

        cmd.extend([pattern, path])

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)

            for line in proc.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        match_data = data["data"]

                        # Handle different ripgrep output formats
                        lines_data = match_data.get("lines", {})
                        match_text = lines_data.get("text", "") if isinstance(lines_data, dict) else str(lines_data)

                        # Get file path - handle both dict and str formats
                        path_data = match_data.get("path", {})
                        file_path = path_data.get("text", str(path_data)) if isinstance(path_data, dict) else str(path_data)

                        # Get column safely
                        submatches = match_data.get("submatches", [{}])
                        column = submatches[0].get("start", 0) if submatches else 0

                        result = SearchResult(
                            file_path=file_path,
                            line_number=match_data.get("line_number", 0),
                            column=column,
                            match_text=match_text.strip() if isinstance(match_text, str) else str(match_text),
                            context_before=[],
                            context_after=[],
                            match_type="text",
                            score=1.0,
                        )

                        # Extract context if available
                        if "context" in data:
                            # Parse context lines
                            pass

                        results.append(result)

                except json.JSONDecodeError:
                    continue

        except subprocess.CalledProcessError:
            pass

        return results

    async def _ast_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
        context_lines: int,
    ) -> List[SearchResult]:
        """Perform AST-based search using treesitter.
        
        OPTIMIZED: Uses ripgrep first to narrow down files before tree-sitter parsing.
        """
        # Try to use grep-ast if available
        try:
            from grep_ast.grep_ast import TreeContext
        except ImportError:
            # grep-ast not installed, skip AST search
            return []

        results = []

        try:
            search_path = Path(path or ".")
            files_to_search = []

            if search_path.is_file():
                files_to_search = [search_path]
            else:
                # OPTIMIZATION: Use ripgrep first to find files containing the pattern
                # This is MUCH faster than scanning all files with rglob + tree-sitter
                if self.ripgrep_available:
                    cmd = ["rg", "--files-with-matches", "-l", "--max-count", "1"]
                    
                    # Add file type filters
                    if include:
                        cmd.extend(["--glob", include])
                    else:
                        # Default to common source files
                        for ext in ["*.py", "*.js", "*.ts", "*.go", "*.java", "*.cpp", "*.c", "*.rs"]:
                            cmd.extend(["--glob", ext])
                    
                    if exclude:
                        cmd.extend(["--glob", f"!{exclude}"])
                    
                    cmd.extend([pattern, str(search_path)])
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            files_to_search = [Path(f) for f in result.stdout.strip().split("\n") if f]
                    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                        pass
                
                # Fallback to limited rglob if ripgrep didn't find anything or isn't available
                if not files_to_search:
                    exts = [include] if include else ["*.py", "*.js", "*.ts", "*.go"]
                    for ext in exts[:3]:  # Limit extensions to check
                        for f in search_path.rglob(ext):
                            files_to_search.append(f)
                            if len(files_to_search) >= max_results:
                                break
                        if len(files_to_search) >= max_results:
                            break

            # Search each file with tree-sitter (now limited to files that actually contain pattern)
            for file_path in files_to_search[:max_results]:
                if not file_path.is_file():
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()

                    # Process with grep-ast
                    tc = TreeContext(
                        str(file_path),
                        code,
                        color=False,
                        verbose=False,
                        line_number=True,
                    )

                    # Find matches
                    matches = tc.grep(pattern, ignore_case=False)

                    for match in matches:
                        # Extract context
                        lines = code.split("\n")
                        line_num = match  # This might need adjustment based on actual return type

                        result = SearchResult(
                            file_path=str(file_path),
                            line_number=line_num,
                            column=0,
                            match_text=(lines[line_num - 1] if 0 < line_num <= len(lines) else ""),
                            context_before=lines[max(0, line_num - context_lines - 1) : line_num - 1],
                            context_after=lines[line_num : min(len(lines), line_num + context_lines)],
                            match_type="ast",
                            score=0.9,
                            node_type="ast_match",
                            semantic_context=None,
                        )
                        results.append(result)

                except Exception:
                    # Skip files that can't be parsed
                    continue

        except Exception as e:
            print(f"AST search error: {e}")

        return results

    async def _symbol_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
    ) -> List[SearchResult]:
        """Search for symbol definitions."""
        results = []

        # Use ctags or similar for symbol search
        # For now, use specialized ripgrep patterns
        symbol_patterns = [
            f"^\\s*(def|function|func)\\s+{pattern}",  # Function definitions
            f"^\\s*class\\s+{pattern}",  # Class definitions
            f"^\\s*(const|let|var)\\s+{pattern}",  # Variable declarations
            f"^\\s*type\\s+{pattern}",  # Type definitions
            f"interface\\s+{pattern}",  # Interface definitions
        ]

        for symbol_pattern in symbol_patterns:
            symbol_results = await self._text_search(
                symbol_pattern,
                path,
                include,
                exclude,
                max_results // len(symbol_patterns),
                0,
            )

            for res in symbol_results:
                res.match_type = "symbol"
                res.score = 1.1  # Boost symbol definitions
                results.append(res)

        return results

    async def _file_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
    ) -> List[SearchResult]:
        """Search for files by name/pattern using find tool."""
        results = []

        try:
            # Import and use find tool
            from hanzo_mcp.tools.search.find_tool import FindTool

            find_tool = FindTool()

            # Call find tool with pattern
            find_result = await find_tool.run(
                pattern=pattern,
                path=path,
                type="file",  # Only files for now
                max_results=max_results,
                regex=False,  # Use glob patterns by default
                fuzzy=False,
                case_sensitive=False,
            )

            # Convert find results to SearchResult format
            if find_result.data and "results" in find_result.data:
                for file_match in find_result.data["results"]:
                    result = SearchResult(
                        file_path=file_match["path"],
                        line_number=1,  # File matches don't have line numbers
                        column=0,
                        match_text=file_match["name"],
                        context_before=[],
                        context_after=[],
                        match_type="file",
                        score=1.0,
                        semantic_context=f"File: {file_match['extension']} ({file_match['size']} bytes)",
                    )
                    results.append(result)

        except Exception as e:
            print(f"File search error: {e}")

        return results

    async def _memory_search(self, query: str, max_results: int, context_lines: int) -> List[SearchResult]:
        """Search in memory/knowledge base."""
        results = []

        if not MEMORY_AVAILABLE:
            return results

        try:
            # Create memory retrieval tool
            retrieval_tool = KnowledgeRetrieval()

            # Search memories
            memory_result = await retrieval_tool.run(
                query=query,
                top_k=max_results,
                threshold=0.5,  # Minimum relevance threshold
            )

            # Convert memory results to SearchResult format
            if memory_result.data and "results" in memory_result.data:
                for mem in memory_result.data["results"]:
                    # Extract content and metadata
                    content = mem.get("content", "")
                    metadata = mem.get("metadata", {})

                    # Create a virtual file path for memories
                    memory_type = metadata.get("type", "memory")
                    memory_id = metadata.get("id", "unknown")
                    virtual_path = f"memory://{memory_type}/{memory_id}"

                    result = SearchResult(
                        file_path=virtual_path,
                        line_number=1,
                        column=0,
                        match_text=(content[:200] + "..." if len(content) > 200 else content),
                        context_before=[],
                        context_after=[],
                        match_type="memory",
                        score=mem.get("score", 0.8),
                        semantic_context=f"Memory type: {memory_type}, Created: {metadata.get('created_at', 'unknown')}",
                    )
                    results.append(result)

        except Exception as e:
            print(f"Memory search error: {e}")

        return results

    async def _lsp_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        max_results: int,
    ) -> List[SearchResult]:
        """Search using LSP for precise symbol references.

        Uses AST search to find initial symbol locations, then LSP to find
        all references across the codebase.
        """
        results = []

        if not LSP_AVAILABLE:
            return results

        try:
            # First, find files that might contain the symbol
            root_path = Path(path).resolve()

            # Get file extensions we can search with LSP
            supported_extensions = set()
            for lang_info in LSP_SERVERS.values():
                supported_extensions.update(lang_info.get("extensions", []))

            # Find matching files using grep to locate the symbol
            grep_cmd = ["rg", "--files-with-matches", "-l", pattern]
            if include:
                grep_cmd.extend(["--glob", include])
            grep_cmd.append(str(root_path))

            try:
                result = subprocess.run(
                    grep_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                matching_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            except (subprocess.SubprocessError, FileNotFoundError):
                matching_files = []

            if not matching_files:
                return results

            # Create LSP tool
            lsp_tool = LSPTool()

            # For each matching file, try to find references using LSP
            files_checked = 0
            for file_path in matching_files[:5]:  # Limit to first 5 files to avoid slowdown
                if files_checked >= 3:  # Also limit files we actually query LSP on
                    break

                # Check if file extension is supported
                ext = Path(file_path).suffix
                if ext not in supported_extensions:
                    continue

                # Find the symbol's line and column in this file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            col = line.find(pattern)
                            if col >= 0:
                                # Found the pattern, try to get LSP references
                                try:
                                    lsp_result = await lsp_tool.run(
                                        action="references",
                                        file=file_path,
                                        line=line_num,
                                        character=col,
                                    )

                                    if lsp_result.data and "references" in lsp_result.data:
                                        for ref in lsp_result.data["references"][:max_results]:
                                            ref_path = ref.get("uri", "").replace("file://", "")
                                            ref_line = ref.get("range", {}).get("start", {}).get("line", 0) + 1

                                            # Read the line content
                                            try:
                                                with open(ref_path, "r", encoding="utf-8", errors="ignore") as rf:
                                                    lines = rf.readlines()
                                                    match_text = lines[ref_line - 1].strip() if ref_line <= len(lines) else pattern
                                            except (IOError, IndexError):
                                                match_text = pattern

                                            result = SearchResult(
                                                file_path=ref_path,
                                                line_number=ref_line,
                                                column=ref.get("range", {}).get("start", {}).get("character", 0),
                                                match_text=match_text,
                                                context_before=[],
                                                context_after=[],
                                                match_type="lsp",
                                                score=0.95,  # High confidence from LSP
                                                semantic_context=f"LSP reference to '{pattern}'",
                                            )
                                            results.append(result)

                                            if len(results) >= max_results:
                                                return results

                                except Exception:
                                    # LSP query failed, continue to next occurrence
                                    pass

                                files_checked += 1
                                break  # Only check first occurrence in each file

                except (IOError, UnicodeDecodeError):
                    continue

        except Exception as e:
            print(f"LSP search error: {e}")

        return results

    async def _git_history_search(
        self,
        pattern: str,
        path: str,
        max_results: int,
    ) -> List[SearchResult]:
        """Search git commit history for pattern using git log -S (pickaxe)."""
        results = []

        if not self.git_available:
            return results

        try:
            # Use git log -S to find commits that added/removed the pattern
            # This is much faster than searching through all commits
            cmd = [
                "git", "log",
                f"-S{pattern}",  # Search for commits that add/remove pattern
                "--oneline",
                f"-n{max_results}",
                "--pretty=format:%h|%s|%an|%ar",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=path or ".",
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("|", 3)
                    if len(parts) >= 4:
                        commit_hash, subject, author, date = parts
                        
                        # Create a result for this commit
                        search_result = SearchResult(
                            file_path=f"git://{commit_hash}",
                            line_number=0,
                            column=0,
                            match_text=subject.strip(),
                            context_before=[],
                            context_after=[],
                            match_type="git",
                            score=0.85,
                            semantic_context=f"Commit by {author} ({date})",
                        )
                        results.append(search_result)

            # Also try git grep for current HEAD if we don't have many results
            if len(results) < max_results // 2:
                grep_cmd = [
                    "git", "grep",
                    "-n",  # Line numbers
                    "-I",  # Skip binary files
                    f"--max-count={max_results - len(results)}",
                    pattern,
                ]

                grep_result = subprocess.run(
                    grep_cmd,
                    capture_output=True,
                    text=True,
                    cwd=path or ".",
                    timeout=10,
                )

                if grep_result.returncode == 0 and grep_result.stdout.strip():
                    for line in grep_result.stdout.strip().split("\n")[:max_results - len(results)]:
                        # Format: file:line:content
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            file_path, line_num, content = parts
                            
                            search_result = SearchResult(
                                file_path=str(Path(path or ".").resolve() / file_path),
                                line_number=int(line_num) if line_num.isdigit() else 1,
                                column=0,
                                match_text=content.strip(),
                                context_before=[],
                                context_after=[],
                                match_type="git",
                                score=0.9,
                                semantic_context="git grep match",
                            )
                            results.append(search_result)

        except subprocess.TimeoutExpired:
            print("Git history search timed out")
        except Exception as e:
            print(f"Git history search error: {e}")

        return results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results across search types."""
        seen = set()
        unique = []

        for result in results:
            key = (result.file_path, result.line_number, result.match_text.strip())
            if key not in seen:
                seen.add(key)
                unique.append(result)
            else:
                # Merge information from duplicate
                for existing in unique:
                    if (
                        existing.file_path,
                        existing.line_number,
                        existing.match_text.strip(),
                    ) == key:
                        # Update with better context or node type
                        if result.node_type and not existing.node_type:
                            existing.node_type = result.node_type
                        if result.semantic_context and not existing.semantic_context:
                            existing.semantic_context = result.semantic_context
                        # Take best score
                        existing.score = max(existing.score, result.score)
                        break

        return unique

    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results by relevance."""
        # Simple ranking based on:
        # 1. Match type score
        # 2. Exact match bonus
        # 3. File path relevance

        for result in results:
            # Exact match bonus
            if query.lower() in result.match_text.lower():
                result.score *= 1.2

            # Path relevance (prefer non-test, non-vendor files)
            if any(skip in result.file_path for skip in ["test", "vendor", "node_modules"]):
                result.score *= 0.8

            # Prefer definition files
            if any(pattern in result.file_path for pattern in ["index.", "main.", "api.", "types."]):
                result.score *= 1.1

        # Sort by score descending, then by file path
        results.sort(key=lambda r: (-r.score, r.file_path, r.line_number))

        return results

    def _format_preview(self, result: SearchResult) -> str:
        """Format result preview with context."""
        lines = []

        # Add context before
        for line in result.context_before[-2:]:
            lines.append(f"  {line}")

        # Add match line with highlighting
        match_line = result.match_text
        if result.column > 0:
            # Add column indicator
            lines.append(f"> {match_line}")
            lines.append(f"  {' ' * result.column}^")
        else:
            lines.append(f"> {match_line}")

        # Add context after
        for line in result.context_after[:2]:
            lines.append(f"  {line}")

        return "\n".join(lines)

    async def _python_text_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
        context_lines: int,
    ) -> List[SearchResult]:
        """Fallback Python text search when ripgrep not available."""
        results = []
        count = 0

        import re

        # Compile pattern
        try:
            regex = re.compile(pattern)
        except re.error:
            # Treat as literal string
            regex = re.compile(re.escape(pattern))

        # Find files
        for file_path in Path(path).rglob(include or "*"):
            if count >= max_results:
                break

            if file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines):
                        if count >= max_results:
                            break

                        match = regex.search(line)
                        if match:
                            result = SearchResult(
                                file_path=str(file_path),
                                line_number=i + 1,
                                column=match.start(),
                                match_text=line.strip(),
                                context_before=lines[max(0, i - context_lines) : i],
                                context_after=lines[i + 1 : i + 1 + context_lines],
                                match_type="text",
                                score=1.0,
                            )
                            results.append(result)
                            count += 1

                except Exception:
                    continue

        return results


# Tool registration
def create_search_tool():
    """Factory function to create search tool - fast and lightweight."""
    return SearchTool()
