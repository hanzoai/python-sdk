"""Primary unified search tool - THE search tool for finding anything in code.

Automatically runs ALL available search engines in parallel.
No configuration needed. Just search.
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

# Check available search backends
try:
    import tree_sitter

    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False

try:
    from hanzo_mcp.tools.lsp.lsp_tool import LSP_SERVERS, LSPTool

    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False


@dataclass
class SearchResult:
    """Unified search result."""

    file_path: str
    line_number: int
    column: int
    match_text: str
    context_before: List[str]
    context_after: List[str]
    match_type: str  # 'grep', 'ast', 'lsp', 'file', 'git'
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
        return hash((self.file_path, self.line_number, self.column, self.match_text))


class SearchTool(BaseTool):
    """THE search tool - finds anything, fast.

    Runs ALL available search engines in parallel:
    - grep (ripgrep) - fast text/regex
    - ast (tree-sitter) - code structure
    - lsp - precise references
    - file - filename matching
    - git - history search

    No toggles. No configuration. Just search.

    For manual control: exec.parallel([grep(...), ast(...), lsp(...)])
    """

    name = "search"
    description = """THE search tool - finds anything, fast.

    Runs ALL available engines in parallel (grep, ast, lsp, file, git).
    No configuration needed. Results deduplicated and ranked.
    
    For manual control: exec.parallel([grep(...), ast(...), lsp(...)])
    """

    def __init__(self):
        super().__init__()
        self.ripgrep_available = self._check_cmd("rg")
        self.git_available = self._check_cmd("git")

    def _check_cmd(self, cmd: str) -> bool:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def _is_git_repo(self, path: str) -> bool:
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
        max_results: int = 50,
        context_lines: int = 2,
        page: int = 1,
        page_size: int = 50,
        **kwargs,
    ) -> MCPResourceDocument:
        """Search everything in parallel. No configuration needed."""
        import asyncio

        max_per_engine = max(5, max_results // 5)
        is_git_repo = self._is_git_repo(path)

        # Stats tracking
        stats = {"query": pattern, "path": path, "engines": [], "time_ms": {}}
        all_results = []

        async def timed(name: str, coro, timeout: float = 30.0):
            """Run coroutine with timeout and timing."""
            start = time.time()
            try:
                results = await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                results = []  # Engine timed out
            except Exception:
                results = []
            elapsed = int((time.time() - start) * 1000)
            return name, results, elapsed

        # Always run ALL available engines in parallel
        tasks = [
            timed("grep", self._grep_search(pattern, path, include, exclude, max_per_engine, context_lines)),
            timed("file", self._file_search(pattern, path, include, exclude, max_per_engine)),
        ]

        if TREESITTER_AVAILABLE:
            tasks.append(timed("ast", self._ast_search(pattern, path, include, exclude, max_per_engine, context_lines)))

        if LSP_AVAILABLE:
            tasks.append(timed("lsp", self._lsp_search(pattern, path, include, max_per_engine)))

        if is_git_repo and self.git_available:
            tasks.append(timed("git", self._git_search(pattern, path, max_per_engine)))

        # Execute all in parallel
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results_list:
            if isinstance(result, Exception):
                continue
            name, results, elapsed = result
            stats["time_ms"][name] = elapsed
            stats["engines"].append(name)
            all_results.extend(results)

        # Dedupe and rank
        unique = self._deduplicate(all_results)
        ranked = self._rank(unique, pattern)

        stats["total"] = len(all_results)
        stats["unique"] = len(ranked)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = ranked[start_idx:end_idx]

        return MCPResourceDocument(
            data={
                "results": [r.to_dict() for r in page_results],
                "stats": stats,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": len(ranked),
                    "has_next": end_idx < len(ranked),
                },
            }
        )

    @auto_timeout("search")
    async def call(self, ctx=None, **kwargs) -> str:
        result = await self.run(**kwargs)
        # Use readable format for better Claude Code display
        # Structured data still available via result.to_json_string() if needed
        return result.to_readable_string()

    def register(self, mcp_server) -> None:
        @mcp_server.tool(name=self.name, description=self.description)
        async def search_handler(
            pattern: str,
            path: str = ".",
            include: Optional[str] = None,
            exclude: Optional[str] = None,
            max_results: int = 50,
            context_lines: int = 2,
            page: int = 1,
            page_size: int = 50,
        ) -> str:
            """Search everything in parallel."""
            return await self.call(
                pattern=pattern,
                path=path,
                include=include,
                exclude=exclude,
                max_results=max_results,
                context_lines=context_lines,
                page=page,
                page_size=page_size,
            )

    # --- Search Engines ---

    async def _grep_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
        context_lines: int,
    ) -> List[SearchResult]:
        """Text search using ripgrep."""
        if not self.ripgrep_available:
            return await self._python_grep(pattern, path, include, exclude, max_results, context_lines)

        cmd = ["rg", "--json", "--max-count", str(max_results)]
        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])
        if include:
            cmd.extend(["--glob", include])
        if exclude:
            cmd.extend(["--glob", f"!{exclude}"])
        cmd.extend([pattern, path])

        results = []
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in proc.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        m = data["data"]
                        lines_data = m.get("lines", {})
                        match_text = lines_data.get("text", "") if isinstance(lines_data, dict) else str(lines_data)
                        path_data = m.get("path", {})
                        file_path = (
                            path_data.get("text", str(path_data)) if isinstance(path_data, dict) else str(path_data)
                        )
                        submatches = m.get("submatches", [{}])
                        column = submatches[0].get("start", 0) if submatches else 0

                        results.append(
                            SearchResult(
                                file_path=file_path,
                                line_number=m.get("line_number", 0),
                                column=column,
                                match_text=match_text.strip() if isinstance(match_text, str) else str(match_text),
                                context_before=[],
                                context_after=[],
                                match_type="grep",
                                score=1.0,
                            )
                        )
                except json.JSONDecodeError:
                    continue
        except Exception:
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
        """AST search using tree-sitter via grep-ast."""
        try:
            from grep_ast.grep_ast import TreeContext
        except ImportError:
            return []

        results = []
        search_path = Path(path or ".")

        # Use ripgrep to find candidate files first (fast)
        files = []
        if self.ripgrep_available:
            cmd = ["rg", "--files-with-matches", "-l", "--max-count", "1"]
            if include:
                cmd.extend(["--glob", include])
            else:
                for ext in ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java"]:
                    cmd.extend(["--glob", ext])
            if exclude:
                cmd.extend(["--glob", f"!{exclude}"])
            cmd.extend([pattern, str(search_path)])

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    files = [Path(f) for f in result.stdout.strip().split("\n") if f]
            except Exception:
                pass

        for file_path in files[:max_results]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                tc = TreeContext(str(file_path), code, color=False, verbose=False, line_number=True)
                matches = tc.grep(pattern, ignore_case=False)
                lines = code.split("\n")

                for line_num in matches:
                    results.append(
                        SearchResult(
                            file_path=str(file_path),
                            line_number=line_num,
                            column=0,
                            match_text=lines[line_num - 1] if 0 < line_num <= len(lines) else "",
                            context_before=lines[max(0, line_num - context_lines - 1) : line_num - 1],
                            context_after=lines[line_num : min(len(lines), line_num + context_lines)],
                            match_type="ast",
                            score=0.9,
                            node_type="ast_match",
                        )
                    )
            except Exception:
                continue
        return results

    async def _file_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
    ) -> List[SearchResult]:
        """Filename search."""
        results = []
        try:
            from hanzo_mcp.tools.search.find_tool import FindTool

            find = FindTool()
            find_result = await find.run(
                pattern=pattern,
                path=path,
                type="file",
                max_results=max_results,
                regex=False,
                fuzzy=False,
                case_sensitive=False,
            )
            if find_result.data and "results" in find_result.data:
                for f in find_result.data["results"]:
                    results.append(
                        SearchResult(
                            file_path=f["path"],
                            line_number=1,
                            column=0,
                            match_text=f["name"],
                            context_before=[],
                            context_after=[],
                            match_type="file",
                            score=1.0,
                            semantic_context=f"File: {f.get('extension', '')} ({f.get('size', 0)} bytes)",
                        )
                    )
        except Exception:
            pass
        return results

    async def _lsp_search(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        max_results: int,
    ) -> List[SearchResult]:
        """LSP reference search."""
        if not LSP_AVAILABLE:
            return []

        results = []
        try:
            root_path = Path(path).resolve()

            # Find files containing pattern
            cmd = ["rg", "--files-with-matches", "-l", pattern]
            if include:
                cmd.extend(["--glob", include])
            cmd.append(str(root_path))

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                matching_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            except Exception:
                return []

            lsp = LSPTool()
            for file_path in matching_files[:3]:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            col = line.find(pattern)
                            if col >= 0:
                                lsp_result = await lsp.run(
                                    action="references", file=file_path, line=line_num, character=col
                                )
                                if lsp_result.data and "references" in lsp_result.data:
                                    for ref in lsp_result.data["references"][:max_results]:
                                        ref_path = ref.get("uri", "").replace("file://", "")
                                        ref_line = ref.get("range", {}).get("start", {}).get("line", 0) + 1
                                        results.append(
                                            SearchResult(
                                                file_path=ref_path,
                                                line_number=ref_line,
                                                column=ref.get("range", {}).get("start", {}).get("character", 0),
                                                match_text=pattern,
                                                context_before=[],
                                                context_after=[],
                                                match_type="lsp",
                                                score=0.95,
                                                semantic_context=f"LSP ref to '{pattern}'",
                                            )
                                        )
                                break
                except Exception:
                    continue
        except Exception:
            pass
        return results

    async def _git_search(self, pattern: str, path: str, max_results: int) -> List[SearchResult]:
        """Git history and grep search."""
        results = []
        try:
            # git log -S (pickaxe)
            cmd = ["git", "log", f"-S{pattern}", "--oneline", f"-n{max_results}", "--pretty=format:%h|%s|%an|%ar"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=path or ".", timeout=10)

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("|", 3)
                    if len(parts) >= 4:
                        commit, subject, author, date = parts
                        results.append(
                            SearchResult(
                                file_path=f"git://{commit}",
                                line_number=0,
                                column=0,
                                match_text=subject.strip(),
                                context_before=[],
                                context_after=[],
                                match_type="git",
                                score=0.85,
                                semantic_context=f"Commit by {author} ({date})",
                            )
                        )

            # git grep
            if len(results) < max_results:
                grep_cmd = ["git", "grep", "-n", "-I", f"--max-count={max_results - len(results)}", pattern]
                grep_result = subprocess.run(grep_cmd, capture_output=True, text=True, cwd=path or ".", timeout=10)

                if grep_result.returncode == 0:
                    for line in grep_result.stdout.strip().split("\n"):
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            fp, ln, content = parts
                            results.append(
                                SearchResult(
                                    file_path=str(Path(path or ".").resolve() / fp),
                                    line_number=int(ln) if ln.isdigit() else 1,
                                    column=0,
                                    match_text=content.strip(),
                                    context_before=[],
                                    context_after=[],
                                    match_type="git",
                                    score=0.9,
                                )
                            )
        except Exception:
            pass
        return results

    async def _python_grep(
        self,
        pattern: str,
        path: str,
        include: Optional[str],
        exclude: Optional[str],
        max_results: int,
        context_lines: int,
    ) -> List[SearchResult]:
        """Fallback Python text search."""
        import re

        results = []
        try:
            regex = re.compile(pattern)
        except re.error:
            regex = re.compile(re.escape(pattern))

        count = 0
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
                            results.append(
                                SearchResult(
                                    file_path=str(file_path),
                                    line_number=i + 1,
                                    column=match.start(),
                                    match_text=line.strip(),
                                    context_before=lines[max(0, i - context_lines) : i],
                                    context_after=lines[i + 1 : i + 1 + context_lines],
                                    match_type="grep",
                                    score=1.0,
                                )
                            )
                            count += 1
                except Exception:
                    continue
        return results

    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        seen = set()
        unique = []
        for r in results:
            key = (r.file_path, r.line_number, r.match_text.strip())
            if key not in seen:
                seen.add(key)
                unique.append(r)
            else:
                # Merge info
                for existing in unique:
                    if (existing.file_path, existing.line_number, existing.match_text.strip()) == key:
                        existing.score = max(existing.score, r.score)
                        if r.node_type and not existing.node_type:
                            existing.node_type = r.node_type
                        break
        return unique

    def _rank(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        for r in results:
            if query.lower() in r.match_text.lower():
                r.score *= 1.2
            if any(skip in r.file_path for skip in ["test", "vendor", "node_modules"]):
                r.score *= 0.8
            if any(p in r.file_path for p in ["index.", "main.", "api.", "types."]):
                r.score *= 1.1
        results.sort(key=lambda r: (-r.score, r.file_path, r.line_number))
        return results


def create_search_tool():
    return SearchTool()
