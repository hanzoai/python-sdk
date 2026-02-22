"""Markdown file reader for integrating LLM.md and similar files into memory."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from structlog import get_logger

from ..models.memory import MemoryCreate

logger = get_logger()

# Supported markdown files for memory integration
MEMORY_MD_FILES = [
    "LLM.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "QWEN.md",
    "AI.md",
    "README.md",  # Often contains important project context
    "CONTEXT.md",
    "MEMORY.md",
    "INSTRUCTIONS.md",
    "PROMPT.md",
]

# Additional patterns to look for
MEMORY_MD_PATTERNS = [
    "*_LLM.md",
    "*_AGENT.md",
    "*_AI.md",
    "*.claude.md",
    "*.gemini.md",
    "*.qwen.md",
]


class MarkdownMemoryReader:
    """Reads and processes markdown files for memory integration."""

    def __init__(self, watch_dirs: Optional[List[Path]] = None):
        """Initialize the markdown reader.

        Args:
            watch_dirs: List of directories to watch for markdown files.
                       Defaults to current directory and parent directories.
        """
        self.watch_dirs = watch_dirs or self._get_default_watch_dirs()
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}

    def _get_default_watch_dirs(self) -> List[Path]:
        """Get default directories to watch."""
        dirs = []
        current = Path.cwd()

        # Add current directory
        dirs.append(current)

        # Add parent directories up to home or 3 levels
        for _ in range(3):
            if current.parent == current or current == Path.home():
                break
            current = current.parent
            dirs.append(current)

        # Add home .config directories
        home = Path.home()
        for config_dir in [".claude", ".gemini", ".qwen", ".ai", ".llm"]:
            config_path = home / config_dir
            if config_path.exists():
                dirs.append(config_path)

        return dirs

    def _compute_file_hash(self, filepath: Path) -> str:
        """Compute hash of file contents."""
        try:
            content = filepath.read_text(encoding="utf-8")
            return hashlib.sha256(content.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {filepath}: {e}")
            return ""

    def _parse_markdown_sections(self, content: str, filepath: Path) -> List[Dict]:
        """Parse markdown content into sections."""
        sections = []
        current_section = {
            "title": f"Content from {filepath.name}",
            "content": "",
            "level": 0,
            "line_start": 0,
        }

        lines = content.split("\n")
        current_line = 0

        for line in lines:
            current_line += 1

            # Check for headers
            if line.startswith("#"):
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)

                # Start new section
                header_level = len(line) - len(line.lstrip("#"))
                header_text = line.lstrip("#").strip()

                current_section = {
                    "title": header_text or f"Section from {filepath.name}",
                    "content": "",
                    "level": header_level,
                    "line_start": current_line,
                }
            else:
                # Add line to current section
                current_section["content"] += line + "\n"

        # Don't forget the last section
        if current_section["content"].strip():
            sections.append(current_section)

        # If no sections were found, treat entire content as one section
        if not sections and content.strip():
            sections.append(
                {
                    "title": f"Content from {filepath.name}",
                    "content": content,
                    "level": 0,
                    "line_start": 0,
                }
            )

        return sections

    def find_markdown_files(self) -> List[Path]:
        """Find all relevant markdown files in watched directories."""
        md_files = []
        seen_files = set()

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue

            # Look for specific named files
            for md_file in MEMORY_MD_FILES:
                filepath = watch_dir / md_file
                if filepath.exists() and filepath not in seen_files:
                    md_files.append(filepath)
                    seen_files.add(filepath)

            # Look for pattern-matched files
            for pattern in MEMORY_MD_PATTERNS:
                for filepath in watch_dir.glob(pattern):
                    if filepath not in seen_files:
                        md_files.append(filepath)
                        seen_files.add(filepath)

        # Sort by priority (LLM.md first, then others)
        def priority(f: Path) -> int:
            name = f.name.upper()
            if name == "LLM.MD":
                return 0
            elif name == "CLAUDE.MD":
                return 1
            elif name == "GEMINI.MD":
                return 2
            elif name == "QWEN.MD":
                return 3
            elif name == "AGENTS.MD":
                return 4
            else:
                return 5

        md_files.sort(key=priority)
        return md_files

    def read_markdown_memories(self) -> List[MemoryCreate]:
        """Read all markdown files and convert to memories."""
        memories = []
        md_files = self.find_markdown_files()

        for filepath in md_files:
            try:
                # Check if file has been processed and unchanged
                file_id = str(filepath.absolute())
                current_hash = self._compute_file_hash(filepath)

                if (
                    file_id in self.file_hashes
                    and self.file_hashes[file_id] == current_hash
                ):
                    logger.debug(f"Skipping unchanged file: {filepath}")
                    continue

                # Read and parse the file
                content = filepath.read_text(encoding="utf-8")
                if not content.strip():
                    continue

                # Store hash for future comparison
                self.file_hashes[file_id] = current_hash

                # Parse into sections
                sections = self._parse_markdown_sections(content, filepath)

                # Create memories from sections
                for section in sections:
                    # Determine importance based on file and section
                    importance = self._calculate_importance(filepath, section)

                    # Determine memory type
                    memory_type = self._determine_memory_type(filepath, section)

                    # Create memory
                    memory = MemoryCreate(
                        content=section["content"],
                        memory_type=memory_type,
                        importance=importance,
                        context={
                            "source_file": str(filepath.absolute()),
                            "file_name": filepath.name,
                            "section_title": section["title"],
                            "section_level": section["level"],
                            "line_start": section["line_start"],
                            "directory": str(filepath.parent.absolute()),
                            "file_modified": datetime.fromtimestamp(
                                filepath.stat().st_mtime
                            ).isoformat(),
                        },
                        metadata={
                            "auto_imported": True,
                            "markdown_file": True,
                        },
                        source=f"markdown://{filepath.absolute()}#{section['line_start']}",
                    )
                    memories.append(memory)

                logger.info(f"Read {len(sections)} sections from {filepath.name}")

            except Exception as e:
                logger.error(f"Error reading markdown file {filepath}: {e}")
                continue

        return memories

    def _calculate_importance(self, filepath: Path, section: Dict) -> float:
        """Calculate importance score for a memory section."""
        importance = 0.5  # Base importance

        # File-based importance
        filename = filepath.name.upper()
        if filename == "LLM.MD":
            importance += 0.3
        elif filename in ["CLAUDE.MD", "GEMINI.MD", "QWEN.MD"]:
            importance += 0.25
        elif filename == "AGENTS.MD":
            importance += 0.2
        elif filename == "README.MD":
            importance += 0.1

        # Section-based importance
        title_lower = section["title"].lower()

        # High importance keywords
        high_importance_keywords = [
            "important",
            "critical",
            "essential",
            "must",
            "always",
            "never",
            "warning",
            "error",
            "security",
            "key",
            "architecture",
            "design",
            "api",
            "interface",
        ]

        for keyword in high_importance_keywords:
            if keyword in title_lower or keyword in section["content"].lower()[:200]:
                importance += 0.1
                break

        # Header level importance (H1 > H2 > H3)
        if section["level"] == 1:
            importance += 0.15
        elif section["level"] == 2:
            importance += 0.1
        elif section["level"] == 3:
            importance += 0.05

        # Cap at 1.0
        return min(importance, 1.0)

    def _determine_memory_type(self, filepath: Path, section: Dict) -> str:
        """Determine the type of memory based on content."""
        filename = filepath.name.upper()
        content_lower = section["content"].lower()
        title_lower = section["title"].lower()

        # Check filename patterns
        if "AGENT" in filename:
            return "agent_instruction"
        elif filename in ["CLAUDE.MD", "GEMINI.MD", "QWEN.MD"]:
            return "model_instruction"
        elif filename == "LLM.MD":
            return "system_context"

        # Check content patterns
        if any(
            word in content_lower[:500]
            for word in ["instruction", "prompt", "you should", "you must"]
        ):
            return "instruction"
        elif any(
            word in content_lower[:500]
            for word in ["api", "endpoint", "function", "method", "class"]
        ):
            return "technical"
        elif any(
            word in content_lower[:500]
            for word in ["example", "usage", "how to", "tutorial"]
        ):
            return "example"
        elif any(
            word in title_lower
            for word in ["config", "setting", "environment", "variable"]
        ):
            return "configuration"
        elif any(
            word in title_lower
            for word in ["architecture", "design", "structure", "pattern"]
        ):
            return "architectural"

        return "knowledge"

    def watch_for_changes(self) -> List[MemoryCreate]:
        """Check for new or modified markdown files and return new memories."""
        new_memories = []

        # Get current memories
        current_memories = self.read_markdown_memories()

        # Track which files were processed
        for memory in current_memories:
            source_file = memory.context.get("source_file")
            if source_file:
                self.processed_files.add(source_file)

        return current_memories

    def get_project_context(self, project_path: Optional[Path] = None) -> Dict:
        """Get comprehensive project context from markdown files."""
        project_path = project_path or Path.cwd()

        context = {
            "project_path": str(project_path.absolute()),
            "project_name": project_path.name,
            "markdown_files": [],
            "instructions": [],
            "configurations": [],
            "examples": [],
            "architecture": [],
        }

        # Find and categorize markdown content
        md_files = self.find_markdown_files()

        for filepath in md_files:
            try:
                content = filepath.read_text(encoding="utf-8")
                sections = self._parse_markdown_sections(content, filepath)

                file_info = {
                    "path": str(filepath.absolute()),
                    "name": filepath.name,
                    "modified": datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).isoformat(),
                    "sections": len(sections),
                }
                context["markdown_files"].append(file_info)

                # Categorize sections
                for section in sections:
                    memory_type = self._determine_memory_type(filepath, section)

                    section_info = {
                        "title": section["title"],
                        "content_preview": (
                            section["content"][:200] + "..."
                            if len(section["content"]) > 200
                            else section["content"]
                        ),
                        "source": filepath.name,
                    }

                    if memory_type in [
                        "instruction",
                        "agent_instruction",
                        "model_instruction",
                    ]:
                        context["instructions"].append(section_info)
                    elif memory_type == "configuration":
                        context["configurations"].append(section_info)
                    elif memory_type == "example":
                        context["examples"].append(section_info)
                    elif memory_type == "architectural":
                        context["architecture"].append(section_info)

            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")

        return context
