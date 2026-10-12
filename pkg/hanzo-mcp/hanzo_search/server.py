"""A stdio MCP server exposing `search` alone: `python -m hanzo_search.server --root DIR`.

Newline-delimited JSON-RPC 2.0 on stdin/stdout, standard library only, so it answers
`initialize` within a fraction of a second of starting; the index is built on the first call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from hanzo_search import DESCRIPTION, SCHEMA


def answer(msg: dict, root: str) -> dict | None:
    """The response to one message, None for a notification."""
    method = msg.get("method")
    if "id" not in msg:
        return None
    rid = msg["id"]
    params = msg.get("params") or {}
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "hanzo-search", "version": "1"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [{"name": "search", "description": DESCRIPTION, "inputSchema": SCHEMA}]}
    elif method == "tools/call":
        if params.get("name") != "search":
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": f"unknown tool: {params.get('name')}"}}
        args = params.get("arguments") or {}
        query = args.get("query")
        if not isinstance(query, str):
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": "query must be a string"}], "isError": True}}
        base = args.get("root") or root
        if not os.path.isabs(base):
            base = os.path.join(root, base)
        try:
            from hanzo_search.index import search

            text, failed = search(query, base, int(args.get("k") or 5)), False
        except Exception as e:  # a failed call is the tool's answer, never the server's exit
            text, failed = f"{type(e).__name__}: {e}", True
        result = {"content": [{"type": "text", "text": text}], "isError": failed}
    else:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m hanzo_search.server")
    ap.add_argument("--root", default=os.getcwd(), help="tree to search (default: the working directory)")
    root = os.path.realpath(ap.parse_args().root)
    out = sys.stdout
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            reply: dict | None = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
        else:
            reply = answer(msg, root) if isinstance(msg, dict) else {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "not a request"}}
        if reply is not None:
            out.write(json.dumps(reply) + "\n")
            out.flush()


if __name__ == "__main__":
    main()
