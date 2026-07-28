"""Cloud-backed vector tool (HIP-0300) — the default semantic surface.

Semantic search, indexing, and raw embeddings run against the live Hanzo Cloud
backend (api.hanzo.ai) so vectors are REAL: zen embeddings into the in-cluster
Qdrant, never a local random-vector mock.

Backend map (all verified on api.hanzo.ai /v1):
- search → GET  /v1/code/search   (type=semantic|hybrid|symbol|text over Qdrant)
- index  → POST /v1/code/index     ({repo, files:[{path,content}]})
- embed  → POST /v1/embeddings     ({model, input} → 1024-dim vectors)

A `collection` names the index namespace (the backend's `repo`). There is no
local store and no fallback: if the service is unreachable this fails loudly
rather than returning vectors it made up.
"""

import os
from typing import Any, ClassVar
from pathlib import Path

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    ToolError,
    HanzoCloud,
    NotFoundError,
    InvalidParamsError,
)

DEFAULT_EMBED_MODEL = "zen-embedding"

# Text-ish extensions worth indexing when walking a directory.
_INDEX_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".c", ".cpp", ".h",
    ".hpp", ".java", ".rb", ".php", ".swift", ".kt", ".scala", ".cs", ".lua",
    ".sh", ".bash", ".zsh", ".json", ".yaml", ".yml", ".toml", ".md", ".rst",
    ".txt", ".html", ".css", ".sql",
}
_SKIP_DIRS = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}


def _collect_files(root: Path, max_files: int, max_bytes: int) -> list[dict]:
    """Read a file or walk a directory into [{path, content}] index records."""
    candidates = [root] if root.is_file() else sorted(root.rglob("*"))
    files: list[dict] = []
    for p in candidates:
        if len(files) >= max_files:
            break
        if p.is_dir() or any(sd in p.parts for sd in _SKIP_DIRS):
            continue
        if p.suffix not in _INDEX_EXTS:
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
            content = p.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        rel = str(p.relative_to(root)) if root.is_dir() else p.name
        files.append({"path": rel, "content": content})
    return files


class VectorTool(BaseTool):
    """Unified cloud vector tool: semantic search, index, embed (HIP-0300)."""

    name: ClassVar[str] = "vector"
    VERSION: ClassVar[str] = "0.2.2"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._cloud: HanzoCloud | None = None
        self._register_vector_actions()

    @property
    def description(self) -> str:
        return """Semantic vector tool (HIP-0300), cloud-backed (real Qdrant).

Actions:
- search: Semantic/hybrid search over an indexed collection
- index: Index a file or directory into a collection
- embed: Compute embeddings for text (1024-dim zen vectors)

Vectors are computed server-side (zen embeddings) and stored in the in-cluster
Qdrant. There is no silent local mock. Set a collection to namespace an index.

Effect: NONDETERMINISTIC_EFFECT (cloud I/O)
"""

    def _get_cloud(self) -> HanzoCloud:
        if self._cloud is None:
            self._cloud = HanzoCloud()
        if not self._cloud.configured():
            raise ToolError(
                code="INVALID_PARAMS",
                message="Hanzo Cloud not configured: set HANZO_API_KEY "
                "or add .apiKey to ~/.hanzo/config.json",
            )
        return self._cloud

    def _register_vector_actions(self):
        @self.action("search", "Semantic search over an indexed collection")
        async def search(
            ctx: MCPContext,
            query: str,
            collection: str | None = None,
            limit: int = 10,
            type: str = "hybrid",
        ) -> dict:
            """Search a collection by meaning (real Qdrant vectors).

            Defaults to `hybrid` (RRF over semantic + lexical + symbolic), which
            uses the Qdrant vector signal while staying robust when the pure
            semantic path is warming up. Pass type="semantic" to force vectors.

            Args:
                query: Natural-language query
                collection: Index namespace (backend repo); optional
                limit: Max results
                type: hybrid (default) | semantic | symbol | text

            Returns:
                {query, collection, results: [{file, repo, line, endLine, kind,
                 symbol, snippet, score}]}
            """
            if not query:
                raise InvalidParamsError("query is required", param="query")
            data = await self._get_cloud().get(
                "/v1/code/search",
                {"q": query, "type": type, "repo": collection, "limit": limit},
            )
            return {
                "query": query,
                "collection": collection,
                "results": data.get("results", []),
                "count": len(data.get("results", [])),
            }

        @self.action("index", "Index a file or directory into a collection")
        async def index(
            ctx: MCPContext,
            collection: str,
            path: str | None = None,
            files: list[dict] | None = None,
            prune: bool = False,
            max_files: int = 2000,
            max_bytes: int = 1_000_000,
        ) -> dict:
            """Index content into a collection (server-side embeddings → Qdrant).

            Provide either `files` ([{path, content}]) or a `path` (file or dir).

            Returns:
                {collection, indexed, skipped, files, symbols, chunks, vectors,
                 semantic}
            """
            payload_files = files
            if payload_files is None:
                if not path:
                    raise InvalidParamsError(
                        "index requires either 'files' or 'path'", param="path"
                    )
                root = Path(path) if Path(path).is_absolute() else Path(self.cwd) / path
                if not root.exists():
                    raise NotFoundError(f"Path not found: {path}", uri=str(root))
                payload_files = _collect_files(root, max_files, max_bytes)
            if not payload_files:
                raise InvalidParamsError("no indexable files found", param="path")

            data = await self._get_cloud().post(
                "/v1/code/index",
                {"repo": collection, "files": payload_files, "prune": prune},
            )
            data.setdefault("collection", collection)
            return data

        @self.action("embed", "Compute embeddings for text")
        async def embed(
            ctx: MCPContext,
            input: Any,
            model: str = DEFAULT_EMBED_MODEL,
        ) -> dict:
            """Compute embeddings (1024-dim zen vectors).

            Args:
                input: A string or list of strings
                model: Embedding model (default zen-embedding)

            Returns:
                {model, count, dimensions, vectors: [[float, ...], ...]}
            """
            if input is None or input == "":
                raise InvalidParamsError("input is required", param="input")
            data = await self._get_cloud().post(
                "/v1/embeddings", {"model": model, "input": input}
            )
            rows = data.get("data") or []
            vectors = [r.get("embedding", []) for r in rows]
            return {
                "model": data.get("model", model),
                "count": len(vectors),
                "dimensions": len(vectors[0]) if vectors else 0,
                "vectors": vectors,
                "usage": data.get("usage"),
            }


# Singleton
vector_tool = VectorTool
