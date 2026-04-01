"""Async LSP client -- Content-Length framed JSON-RPC over subprocess stdio."""
from __future__ import annotations
import asyncio, json, os
from pathlib import Path
from typing import Any
from .types import Diagnostic, LspServerConfig, SymbolLocation


class LspError(Exception):
    pass


class LspClient:
    def __init__(self, config: LspServerConfig) -> None:
        self._cfg, self._proc, self._id = config, None, 1
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._diagnostics: dict[str, list[Diagnostic]] = {}
        self._open: dict[Path, int] = {}
        self._reader: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        P = asyncio.subprocess.PIPE
        self._proc = await asyncio.create_subprocess_exec(
            self._cfg.command, *self._cfg.args, stdin=P, stdout=P, stderr=P,
            cwd=str(self._cfg.workspace_root), env={**os.environ, **self._cfg.env})
        if not self._proc.stdout or not self._proc.stdin:
            raise LspError("failed to open LSP subprocess pipes")
        self._reader = asyncio.get_event_loop().create_task(self._read_loop())
        ws = self._cfg.workspace_root.as_uri()
        await self._request("initialize", {
            "processId": os.getpid(), "rootUri": ws,
            "rootPath": str(self._cfg.workspace_root),
            "workspaceFolders": [{"uri": ws, "name": self._cfg.name}],
            "initializationOptions": self._cfg.initialization_options or {},
            "capabilities": {
                "textDocument": {"publishDiagnostics": {"relatedInformation": True},
                                 "definition": {"linkSupport": True}, "references": {}},
                "workspace": {"configuration": False, "workspaceFolders": True},
                "general": {"positionEncodings": ["utf-16"]}},
        })
        await self._notify("initialized", {})

    async def open_document(self, path: Path, text: str) -> None:
        lang = self._cfg.language_id_for(path)
        if lang is None:
            raise LspError(f"no language mapping for {path}")
        await self._notify("textDocument/didOpen", {
            "textDocument": {"uri": path.as_uri(), "languageId": lang, "version": 1, "text": text},
        })
        self._open[path] = 1

    async def ensure_open(self, path: Path) -> None:
        if path not in self._open:
            await self.open_document(path, path.read_text())

    async def change_document(self, path: Path, text: str) -> None:
        if path not in self._open:
            return await self.open_document(path, text)
        self._open[path] += 1
        await self._notify("textDocument/didChange", {
            "textDocument": {"uri": path.as_uri(), "version": self._open[path]},
            "contentChanges": [{"text": text}],
        })

    async def save_document(self, path: Path) -> None:
        if path in self._open:
            await self._notify("textDocument/didSave", {"textDocument": {"uri": path.as_uri()}})

    async def close_document(self, path: Path) -> None:
        if path in self._open:
            await self._notify("textDocument/didClose", {"textDocument": {"uri": path.as_uri()}})
            del self._open[path]

    async def go_to_definition(self, path: Path, line: int, char: int) -> list[SymbolLocation]:
        await self.ensure_open(path)
        p = {"textDocument": {"uri": path.as_uri()}, "position": {"line": line, "character": char}}
        return _parse_locations(await self._request("textDocument/definition", p))

    async def find_references(
        self, path: Path, line: int, char: int, *, include_declaration: bool = True,
    ) -> list[SymbolLocation]:
        await self.ensure_open(path)
        p = {"textDocument": {"uri": path.as_uri()}, "position": {"line": line, "character": char},
             "context": {"includeDeclaration": include_declaration}}
        return _parse_locations(await self._request("textDocument/references", p))

    def diagnostics_snapshot(self) -> dict[str, list[Diagnostic]]:
        return dict(self._diagnostics)

    async def shutdown(self) -> None:
        try: await self._request("shutdown", {})
        except Exception: pass
        try: await self._notify("exit", None)
        except Exception: pass
        if self._proc:
            try: self._proc.kill()
            except ProcessLookupError: pass
            await self._proc.wait()
        if self._reader and not self._reader.done():
            self._reader.cancel()
            try: await self._reader
            except asyncio.CancelledError: pass

    async def _request(self, method: str, params: Any) -> Any:
        rid = self._id; self._id += 1
        fut: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending[rid] = fut
        try: await self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        except Exception: self._pending.pop(rid, None); raise
        return await fut

    async def _notify(self, method: str, params: Any) -> None:
        await self._send({"jsonrpc": "2.0", "method": method, "params": params})

    async def _send(self, msg: dict[str, Any]) -> None:
        assert self._proc and self._proc.stdin
        b = json.dumps(msg).encode()
        self._proc.stdin.write(f"Content-Length: {len(b)}\r\n\r\n".encode() + b)
        await self._proc.stdin.drain()

    async def _read_loop(self) -> None:
        assert self._proc and self._proc.stdout
        reader = self._proc.stdout
        try:
            while True:
                msg = await _read_message(reader)
                if msg is None: break
                if "id" in msg and "method" not in msg:
                    fut = self._pending.pop(msg["id"], None)
                    if fut and not fut.done():
                        if "error" in msg:
                            fut.set_exception(LspError(json.dumps(msg["error"])))
                        else:
                            fut.set_result(msg.get("result"))
                elif msg.get("method") == "textDocument/publishDiagnostics":
                    p = msg.get("params", {})
                    uri, raw = p.get("uri", ""), p.get("diagnostics", [])
                    if raw:
                        self._diagnostics[uri] = [_parse_diag(d) for d in raw]
                    else:
                        self._diagnostics.pop(uri, None)
        except (asyncio.CancelledError, ConnectionError): pass
        finally:
            for f in self._pending.values():
                if not f.done(): f.set_exception(LspError("LSP connection closed"))
            self._pending.clear()


async def _read_message(reader: asyncio.StreamReader) -> dict[str, Any] | None:
    length: int | None = None
    while True:
        line = await reader.readline()
        if not line: return None
        s = line.decode("utf-8")
        if s == "\r\n": break
        if ":" in s:
            k, v = s.split(":", 1)
            if k.strip().lower() == "content-length":
                length = int(v.strip())
    if length is None: raise LspError("missing Content-Length header")
    return json.loads(await reader.readexactly(length))


def _parse_diag(raw: dict[str, Any]) -> Diagnostic:
    r = raw.get("range", {}); s = r.get("start", {}); e = r.get("end", {})
    return Diagnostic(
        s.get("line", 0), s.get("character", 0), e.get("line", 0), e.get("character", 0),
        raw.get("severity", 0), raw.get("message", ""), raw.get("source", ""),
    )


def _parse_locations(result: Any) -> list[SymbolLocation]:
    if result is None: return []
    if isinstance(result, dict): result = [result]
    out: list[SymbolLocation] = []
    for item in result:
        uri = item.get("targetUri") or item.get("uri")
        r = item.get("targetSelectionRange") or item.get("range", {})
        if not uri or not uri.startswith("file://"): continue
        s = r.get("start", {}); e = r.get("end", {})
        out.append(SymbolLocation(
            Path(uri[7:]), s.get("line", 0), s.get("character", 0),
            e.get("line", 0), e.get("character", 0),
        ))
    return out
