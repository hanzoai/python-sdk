"""Lightweight markdown-based memory backend.

No backend required — reads from local .md files (MEMORY.md, LLM.md, CLAUDE.md, etc.)
and provides simple in-memory storage for the current session.

This is the default backend when hanzo-memory is not installed.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4


# Files to scan for context
CONTEXT_MD_FILES = [
    "MEMORY.md",
    "LLM.md",
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    "QWEN.md",
    "AI.md",
    "CONTEXT.md",
    "INSTRUCTIONS.md",
]

# Per-scope memory files we write to
SCOPE_MEMORY_FILES = {
    "global": Path.home() / ".claude" / "MEMORY.md",
    "project": None,  # Determined by CWD
    "session": None,  # In-memory only
}


@dataclass
class MarkdownMemory:
    """Simple memory entry."""

    memory_id: str
    content: str
    scope: str
    created_at: str
    source: str = "user"  # "user" or "file"
    tags: List[str] = field(default_factory=list)


@dataclass
class MarkdownFact:
    """Simple fact entry."""

    fact_id: str
    statement: str
    kb_name: str
    scope: str
    created_at: str


class MarkdownMemoryBackend:
    """Lightweight memory backend using local markdown files.

    - Reads context from LLM.md, CLAUDE.md, MEMORY.md, etc.
    - Stores new memories in MEMORY.md files (per scope)
    - Session memories are in-process only
    - No embedding search — uses simple keyword matching
    """

    def __init__(self) -> None:
        self._session_memories: List[MarkdownMemory] = []
        self._session_facts: List[MarkdownFact] = []
        self._file_memories: List[MarkdownMemory] = []
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazily load memories from markdown files."""
        if self._loaded:
            return
        self._loaded = True
        self._file_memories = []

        # Scan current directory chain for context files
        scan_dirs = self._get_scan_dirs()
        for d in scan_dirs:
            for fname in CONTEXT_MD_FILES:
                fpath = d / fname
                if fpath.exists() and fpath.stat().st_size > 0:
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        # Split into sections/chunks
                        chunks = self._chunk_markdown(content)
                        for chunk in chunks:
                            if chunk.strip():
                                self._file_memories.append(MarkdownMemory(
                                    memory_id=str(uuid4()),
                                    content=chunk.strip(),
                                    scope="global",
                                    created_at=datetime.now().isoformat(),
                                    source=str(fpath),
                                ))
                    except Exception:
                        pass

    def _get_scan_dirs(self) -> List[Path]:
        """Get directories to scan for context files."""
        dirs: List[Path] = []
        cwd = Path.cwd()

        # Walk up from CWD (max 4 levels)
        current = cwd
        for _ in range(4):
            dirs.append(current)
            if current.parent == current:
                break
            current = current.parent

        # Add home/.claude
        home_claude = Path.home() / ".claude"
        if home_claude.exists():
            dirs.append(home_claude)

        return dirs

    def _chunk_markdown(self, content: str, max_chunk: int = 800) -> List[str]:
        """Split markdown into meaningful chunks by heading."""
        # Split by ## headings first, then by size
        sections = re.split(r"\n(?=#{1,3} )", content)
        chunks: List[str] = []
        for section in sections:
            if len(section) <= max_chunk:
                chunks.append(section)
            else:
                # Split large sections into paragraphs
                paras = section.split("\n\n")
                current = ""
                for para in paras:
                    if len(current) + len(para) > max_chunk and current:
                        chunks.append(current)
                        current = para
                    else:
                        current = (current + "\n\n" + para).strip()
                if current:
                    chunks.append(current)
        return chunks

    def _keyword_score(self, text: str, query: str) -> float:
        """Simple keyword relevance score (0-1)."""
        query_words = set(query.lower().split())
        text_lower = text.lower()
        matches = sum(1 for w in query_words if w in text_lower and len(w) > 2)
        return matches / max(len(query_words), 1)

    def search_memories(
        self,
        queries: List[str],
        limit: int = 10,
        scope: Optional[str] = None,
    ) -> List[MarkdownMemory]:
        """Search memories by keyword relevance."""
        self._ensure_loaded()

        all_memories = self._file_memories + self._session_memories
        if scope and scope != "global":
            # Filter by scope
            all_memories = [m for m in all_memories if m.scope == scope]

        # Score and rank
        scored: List[tuple[float, MarkdownMemory]] = []
        for memory in all_memories:
            best_score = max(
                self._keyword_score(memory.content, q) for q in queries
            )
            if best_score > 0:
                scored.append((best_score, memory))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]

    def add_memory(self, content: str, scope: str = "project") -> MarkdownMemory:
        """Add a new memory (session or persisted)."""
        memory = MarkdownMemory(
            memory_id=str(uuid4()),
            content=content,
            scope=scope,
            created_at=datetime.now().isoformat(),
            source="user",
        )
        self._session_memories.append(memory)

        # Persist to appropriate MEMORY.md
        if scope != "session":
            self._append_to_memory_file(content, scope)

        return memory

    def _get_memory_file(self, scope: str) -> Optional[Path]:
        """Get the path to the appropriate MEMORY.md file."""
        if scope == "global":
            path = Path.home() / ".claude" / "MEMORY.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        else:  # project
            # Find project root (has .git, package.json, pyproject.toml, etc.)
            cwd = Path.cwd()
            root_markers = [".git", "package.json", "pyproject.toml", "go.mod"]
            current = cwd
            for _ in range(4):
                if any((current / m).exists() for m in root_markers):
                    return current / "MEMORY.md"
                if current.parent == current:
                    break
                current = current.parent
            return cwd / "MEMORY.md"

    def _append_to_memory_file(self, content: str, scope: str) -> None:
        """Append a memory entry to the appropriate MEMORY.md file."""
        path = self._get_memory_file(scope)
        if path is None:
            return
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n- [{timestamp}] {content}\n"
            with open(path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def update_memory(self, memory_id: str, new_content: str) -> Optional[MarkdownMemory]:
        """Update a session memory by ID."""
        for m in self._session_memories:
            if m.memory_id == memory_id:
                m.content = new_content
                return m
        return None

    def delete_memory(self, memory_id: str) -> bool:
        """Remove a session memory."""
        before = len(self._session_memories)
        self._session_memories = [m for m in self._session_memories if m.memory_id != memory_id]
        return len(self._session_memories) < before

    # --- Facts API (session-only, lightweight) ---

    def recall_facts(
        self,
        queries: List[str],
        kb_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[MarkdownFact]:
        """Search facts by keyword."""
        facts = self._session_facts
        if kb_name:
            facts = [f for f in facts if f.kb_name == kb_name]

        scored: List[tuple[float, MarkdownFact]] = []
        for fact in facts:
            best = max(self._keyword_score(fact.statement, q) for q in queries)
            if best > 0:
                scored.append((best, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:limit]]

    def store_fact(self, statement: str, kb_name: str = "general", scope: str = "project") -> MarkdownFact:
        """Store a fact."""
        fact = MarkdownFact(
            fact_id=str(uuid4()),
            statement=statement,
            kb_name=kb_name,
            scope=scope,
            created_at=datetime.now().isoformat(),
        )
        self._session_facts.append(fact)
        return fact

    def delete_fact(self, fact_id: str) -> bool:
        """Remove a fact."""
        before = len(self._session_facts)
        self._session_facts = [f for f in self._session_facts if f.fact_id != fact_id]
        return len(self._session_facts) < before


# Singleton
_backend: Optional[MarkdownMemoryBackend] = None


def get_markdown_backend() -> MarkdownMemoryBackend:
    """Get the singleton markdown memory backend."""
    global _backend
    if _backend is None:
        _backend = MarkdownMemoryBackend()
    return _backend
