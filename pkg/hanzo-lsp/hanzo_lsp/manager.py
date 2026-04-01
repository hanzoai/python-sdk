"""LspManager -- routes LSP requests by file extension."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import unquote, urlparse
from .client import LspClient, LspError
from .types import (FileDiagnostics, LspContextEnrichment, LspServerConfig,
                    SymbolLocation, WorkspaceDiagnostics, _normalize_ext)


class LspManager:
    def __init__(self, configs: list[LspServerConfig]) -> None:
        self._configs: dict[str, LspServerConfig] = {}
        self._ext_map: dict[str, str] = {}
        self._clients: dict[str, LspClient] = {}
        for cfg in configs:
            for ext in cfg.extension_to_language:
                norm = _normalize_ext(ext)
                if norm in self._ext_map:
                    raise LspError(f"duplicate extension {norm}: {self._ext_map[norm]} and {cfg.name}")
                self._ext_map[norm] = cfg.name
            self._configs[cfg.name] = cfg

    def supports_path(self, path: Path) -> bool:
        return bool(path.suffix) and _normalize_ext(path.suffix) in self._ext_map

    async def open_document(self, path: Path, text: str) -> None:
        await (await self._client_for(path)).open_document(path, text)

    async def sync_document_from_disk(self, path: Path) -> None:
        c = await self._client_for(path)
        await c.change_document(path, path.read_text())
        await c.save_document(path)

    async def change_document(self, path: Path, text: str) -> None:
        await (await self._client_for(path)).change_document(path, text)

    async def save_document(self, path: Path) -> None:
        await (await self._client_for(path)).save_document(path)

    async def close_document(self, path: Path) -> None:
        await (await self._client_for(path)).close_document(path)

    async def go_to_definition(self, path: Path, line: int, char: int) -> list[SymbolLocation]:
        return _dedupe(await (await self._client_for(path)).go_to_definition(path, line, char))

    async def find_references(
        self, path: Path, line: int, char: int, *, include_declaration: bool = True,
    ) -> list[SymbolLocation]:
        return _dedupe(await (await self._client_for(path)).find_references(
            path, line, char, include_declaration=include_declaration))

    async def collect_workspace_diagnostics(self) -> WorkspaceDiagnostics:
        files: list[FileDiagnostics] = []
        for c in self._clients.values():
            for uri, ds in c.diagnostics_snapshot().items():
                if not ds: continue
                p = urlparse(uri)
                if p.scheme == "file":
                    files.append(FileDiagnostics(Path(unquote(p.path)), uri, list(ds)))
        files.sort(key=lambda f: f.path)
        return WorkspaceDiagnostics(files=files)

    async def context_enrichment(self, path: Path, line: int, char: int) -> LspContextEnrichment:
        return LspContextEnrichment(
            file_path=path, diagnostics=await self.collect_workspace_diagnostics(),
            definitions=await self.go_to_definition(path, line, char),
            references=await self.find_references(path, line, char))

    async def shutdown(self) -> None:
        for client in self._clients.values():
            await client.shutdown()
        self._clients.clear()

    async def _client_for(self, path: Path) -> LspClient:
        ext = _normalize_ext(path.suffix) if path.suffix else ""
        name = self._ext_map.get(ext)
        if not name: raise LspError(f"no LSP server for {path}")
        if name not in self._clients:
            client = LspClient(self._configs[name])
            await client.connect()
            self._clients[name] = client
        return self._clients[name]


def _dedupe(locs: list[SymbolLocation]) -> list[SymbolLocation]:
    seen: set[tuple[Path, int, int, int, int]] = set()
    out: list[SymbolLocation] = []
    for loc in locs:
        key = (loc.path, loc.start_line, loc.start_character, loc.end_line, loc.end_character)
        if key not in seen:
            seen.add(key); out.append(loc)
    return out
