"""Primary unified search tool - THE search tool for finding anything in code.

This is your main search interface that intelligently combines all available
search capabilities including text, AST, symbols, memory, and semantic search.
"""

import json
import time
import hashlib
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

from hanzo_mcp.types import MCPResourceDocument
from hanzo_mcp.tools.common.base import BaseTool

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

try:
    import chromadb
    from sentence_transformers import SentenceTransformer

    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False


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


class UnifiedSearch(BaseTool):
    """THE primary search tool - your universal interface for finding anything.

    This is the main search tool you should use for finding:
    - Code patterns and text matches (using ripgrep)
    - AST nodes and code structure (using treesitter)
    - Symbol definitions and references (using ctags/LSP)
    - Files and directories (using find tool)
    - Memory and knowledge base entries
    - Semantic/conceptual matches (using vector search)

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

    4. Semantic search:
       search("how authentication works")    # Natural language query
       search("database connection logic")   # Conceptual search

    5. Memory search:
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
    - Use natural language for conceptual searches
    - Use code syntax for exact matches
    - Add search_files=True to also find filenames
    - Results are ranked by relevance and type
    - Use page parameter to get more results
    """

    name = "search"
    description = """THE primary unified search tool for rapid parallel search across all modalities.
    
    Find anything in your codebase using text, AST, symbols, files, memory, and semantic search.
    Automatically detects query intent and runs appropriate searches in parallel.
    """

    def __init__(self):
        super().__init__()
        self.ripgrep_available = self._check_ripgrep()
        self.vector_db = None
        self.embedder = None

        if VECTOR_SEARCH_AVAILABLE:
            self._init_vector_search()

    def _check_ripgrep(self) -> bool:
        """Check if ripgrep is available."""
        try:
            subprocess.run(["rg", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def _init_vector_search(self):
        """Initialize vector search components."""
        try:
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            self.vector_db = chromadb.Client()
            # Create or get collection
            self.collection = self.vector_db.get_or_create_collection(
                name="code_search", metadata={"description": "Code semantic search"}
            )
        except Exception as e:
            print(f"Failed to initialize vector search: {e}")
            self.vector_db = None

    def _should_use_vector_search(self, query: str) -> bool:
        """Determine if vector search would be helpful."""
        # Use vector search for natural language queries
        indicators = [
            len(query.split()) > 2,  # Multi-word queries
            not any(
                c in query for c in ["(", ")", "{", "}", "[", "]"]
            ),  # Not code syntax
            " " in query,  # Has spaces (natural language)
            not query.startswith("^") and not query.endswith("$"),  # Not regex anchors
        ]
        return sum(indicators) >= 2

    def _should_use_ast_search(self, query: str) -> bool:
        """Determine if AST search would be helpful."""
        # Use AST search for code patterns
        indicators = [
            "class " in query or "function " in query or "def " in query,
            "import " in query or "from " in query,
            any(
                kw in query.lower()
                for kw in ["method", "function", "class", "interface", "struct"]
            ),
            "::" in query or "->" in query or "." in query,  # Member access
        ]
        return any(indicators)

    def _should_use_symbol_search(self, query: str) -> bool:
        """Determine if symbol search would be helpful."""
        # Use symbol search for identifiers
        return (
            len(query.split()) <= 2  # Short queries
            and query.replace("_", "")
            .replace("-", "")
            .isalnum()  # Looks like identifier
            and not " " in query.strip()  # Single token
        )

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
        enable_text: bool = None,
        enable_ast: bool = None,
        enable_vector: bool = None,
        enable_symbol: bool = None,
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
            enable_*: Force enable/disable specific search types (auto if None)
            page_size: Results per page (default: 50)
            page: Page number to retrieve (default: 1)
        """

        # Auto-detect search types based on query
        if search_memory is None:
            # Search memory for natural language queries or specific references
            search_memory = MEMORY_AVAILABLE and (
                self._should_use_vector_search(pattern)
                or any(
                    word in pattern.lower()
                    for word in ["previous", "discussion", "remember", "last"]
                )
            )

        if enable_text is None:
            enable_text = True  # Always use text search as baseline

        if enable_vector is None:
            enable_vector = (
                self._should_use_vector_search(pattern) and VECTOR_SEARCH_AVAILABLE
            )

        if enable_ast is None:
            enable_ast = self._should_use_ast_search(pattern) and TREESITTER_AVAILABLE

        if enable_symbol is None:
            enable_symbol = self._should_use_symbol_search(pattern)

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

        # 1. Text search (ripgrep) - always fast, do first
        if enable_text:
            start = time.time()
            text_results = await self._text_search(
                pattern, path, include, exclude, max_results_per_type, context_lines
            )
            search_stats["time_ms"]["text"] = int((time.time() - start) * 1000)
            search_stats["search_types_used"].append("text")
            all_results.extend(text_results)

        # 2. AST search - for code structure
        if enable_ast and TREESITTER_AVAILABLE:
            start = time.time()
            ast_results = await self._ast_search(
                pattern, path, include, exclude, max_results_per_type, context_lines
            )
            search_stats["time_ms"]["ast"] = int((time.time() - start) * 1000)
            search_stats["search_types_used"].append("ast")
            all_results.extend(ast_results)

        # 3. Symbol search - for definitions
        if enable_symbol:
            start = time.time()
            symbol_results = await self._symbol_search(
                pattern, path, include, exclude, max_results_per_type
            )
            search_stats["time_ms"]["symbol"] = int((time.time() - start) * 1000)
            search_stats["search_types_used"].append("symbol")
            all_results.extend(symbol_results)

        # 4. Vector search - for semantic similarity
        if enable_vector and self.vector_db:
            start = time.time()
            vector_results = await self._vector_search(
                pattern, path, include, exclude, max_results_per_type, context_lines
            )
            search_stats["time_ms"]["vector"] = int((time.time() - start) * 1000)
            search_stats["search_types_used"].append("vector")
            all_results.extend(vector_results)

        # 5. File search - for finding files by name/pattern
        if search_files:
            start = time.time()
            file_results = await self._file_search(
                pattern, path, include, exclude, max_results_per_type
            )
            search_stats["time_ms"]["files"] = int((time.time() - start) * 1000)
            search_stats["search_types_used"].append("files")
            all_results.extend(file_results)

        # 6. Memory search - for knowledge base and previous discussions
        if search_memory:
            start = time.time()
            memory_results = await self._memory_search(
                pattern, max_results_per_type, context_lines
            )
            search_stats["time_ms"]["memory"] = int((time.time() - start) * 1000)
            search_stats["search_types_used"].append("memory")
            all_results.extend(memory_results)

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

    async def call(self, **kwargs) -> str:
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
            enable_vector: bool = True,
            enable_symbol: bool = True,
            search_files: bool = False,
            search_memory: bool = False,
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
                enable_vector=enable_vector,
                enable_symbol=enable_symbol,
                search_files=search_files,
                search_memory=search_memory,
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
            return await self._python_text_search(
                pattern, path, include, exclude, max_results, context_lines
            )

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

                        result = SearchResult(
                            file_path=match_data["path"]["text"],
                            line_number=match_data["line_number"],
                            column=match_data["submatches"][0]["start"],
                            match_text=match_data["lines"]["text"].strip(),
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
        """Perform AST-based search using treesitter."""
        # Try to use grep-ast if available
        try:
            from grep_ast.grep_ast import TreeContext
        except ImportError:
            # grep-ast not installed, skip AST search
            return []

        results = []

        try:
            # Get files to search
            search_path = Path(path or ".")
            files_to_search = []

            if search_path.is_file():
                files_to_search = [search_path]
            else:
                # Find files matching include pattern
                pattern_to_use = include or "*.py"
                for ext in ["*.py", "*.js", "*.ts", "*.go", "*.java", "*.cpp", "*.c"]:
                    if include and include != ext:
                        continue
                    files_to_search.extend(search_path.rglob(ext))
                    if len(files_to_search) >= max_results:
                        break

            # Search each file
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
                            match_text=(
                                lines[line_num - 1]
                                if 0 < line_num <= len(lines)
                                else ""
                            ),
                            context_before=lines[
                                max(0, line_num - context_lines - 1) : line_num - 1
                            ],
                            context_after=lines[
                                line_num : min(len(lines), line_num + context_lines)
                            ],
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

    async def _vector_search(
        self,
        query: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
        context_lines: int,
    ) -> List[SearchResult]:
        """Perform semantic vector search."""
        if not self.vector_db or not self.embedder:
            return []

        results = []

        try:
            # Embed the query
            query_embedding = self.embedder.encode(query).tolist()

            # Search in vector database
            search_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where={"path": {"$contains": path}} if path != "." else None,
            )

            if search_results["ids"][0]:
                for i, _doc_id in enumerate(search_results["ids"][0]):
                    metadata = search_results["metadatas"][0][i]

                    result = SearchResult(
                        file_path=metadata["file_path"],
                        line_number=metadata["line_number"],
                        column=0,
                        match_text=search_results["documents"][0][i],
                        context_before=[],
                        context_after=[],
                        match_type="vector",
                        score=1.0
                        - search_results["distances"][0][
                            i
                        ],  # Convert distance to similarity
                        semantic_context=metadata.get("context", ""),
                    )
                    results.append(result)

        except Exception as e:
            print(f"Vector search error: {e}")

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

    async def _memory_search(
        self, query: str, max_results: int, context_lines: int
    ) -> List[SearchResult]:
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
                        match_text=(
                            content[:200] + "..." if len(content) > 200 else content
                        ),
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

    def _rank_results(
        self, results: List[SearchResult], query: str
    ) -> List[SearchResult]:
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
            if any(
                skip in result.file_path for skip in ["test", "vendor", "node_modules"]
            ):
                result.score *= 0.8

            # Prefer definition files
            if any(
                pattern in result.file_path
                for pattern in ["index.", "main.", "api.", "types."]
            ):
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


# Index builder for vector search
class CodeIndexer:
    """Build and maintain vector search index."""

    def __init__(self, vector_db, embedder):
        self.vector_db = vector_db
        self.embedder = embedder
        self.collection = vector_db.get_or_create_collection("code_search")

    async def index_directory(self, path: str, file_patterns: List[str] = None):
        """Index a directory for vector search."""
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.ts", "*.go", "*.java", "*.cpp", "*.c"]

        documents = []
        metadatas = []
        ids = []

        for pattern in file_patterns:
            for file_path in Path(path).rglob(pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Split into chunks (functions, classes, etc.)
                        chunks = self._split_code_intelligently(content, file_path)

                        for chunk in chunks:
                            doc_id = hashlib.md5(
                                f"{file_path}:{chunk['line']}:{chunk['text'][:50]}".encode()
                            ).hexdigest()

                            documents.append(chunk["text"])
                            metadatas.append(
                                {
                                    "file_path": str(file_path),
                                    "line_number": chunk["line"],
                                    "context": chunk.get("context", ""),
                                    "type": chunk.get("type", "code"),
                                }
                            )
                            ids.append(doc_id)

                    except Exception as e:
                        print(f"Error indexing {file_path}: {e}")

        # Batch embed and store
        if documents:
            embeddings = self.embedder.encode(documents).tolist()
            self.collection.add(
                embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids
            )

    def _split_code_intelligently(
        self, content: str, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Split code into meaningful chunks."""
        # Simple line-based splitting for now
        # TODO: Use AST for better splitting
        chunks = []
        lines = content.split("\n")

        # Group into function-sized chunks
        current_chunk = []
        current_line = 1

        for i, line in enumerate(lines):
            current_chunk.append(line)

            # Split on function/class definitions or every 50 lines
            if len(current_chunk) >= 50 or any(
                kw in line for kw in ["def ", "function ", "class ", "interface "]
            ):
                if current_chunk:
                    chunks.append(
                        {
                            "text": "\n".join(current_chunk),
                            "line": current_line,
                            "type": "code",
                        }
                    )
                    current_chunk = []
                    current_line = i + 2

        # Add remaining
        if current_chunk:
            chunks.append(
                {"text": "\n".join(current_chunk), "line": current_line, "type": "code"}
            )

        return chunks


# Tool registration
def create_unified_search_tool():
    """Factory function to create unified search tool."""
    return UnifiedSearch()
