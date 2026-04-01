"""LSP types: config, diagnostics, symbols, context enrichment."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_MAX_D, _MAX_L = 12, 12
_SEV = {1: "error", 2: "warning", 3: "info", 4: "hint"}


def _normalize_ext(ext: str) -> str:
    ext = ext.lower()
    return ext if ext.startswith(".") else f".{ext}"


@dataclass
class LspServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    workspace_root: Path = field(default_factory=Path.cwd)
    initialization_options: dict[str, Any] | None = None
    extension_to_language: dict[str, str] = field(default_factory=dict)

    def language_id_for(self, path: Path) -> str | None:
        return self.extension_to_language.get(_normalize_ext(path.suffix)) if path.suffix else None


@dataclass
class Diagnostic:
    range_start_line: int
    range_start_char: int
    range_end_line: int
    range_end_char: int
    severity: int
    message: str
    source: str = ""

    @property
    def severity_label(self) -> str:
        return _SEV.get(self.severity, "unknown")


@dataclass
class FileDiagnostics:
    path: Path
    uri: str
    diagnostics: list[Diagnostic] = field(default_factory=list)


@dataclass
class WorkspaceDiagnostics:
    files: list[FileDiagnostics] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.files

    @property
    def total_diagnostics(self) -> int:
        return sum(len(f.diagnostics) for f in self.files)


@dataclass
class SymbolLocation:
    path: Path
    start_line: int
    start_character: int
    end_line: int
    end_character: int

    @property
    def display_line(self) -> int:
        return self.start_line + 1

    @property
    def display_character(self) -> int:
        return self.start_character + 1

    def __str__(self) -> str:
        return f"{self.path}:{self.display_line}:{self.display_character}"


@dataclass
class LspContextEnrichment:
    file_path: Path = field(default_factory=lambda: Path("."))
    diagnostics: WorkspaceDiagnostics = field(default_factory=WorkspaceDiagnostics)
    definitions: list[SymbolLocation] = field(default_factory=list)
    references: list[SymbolLocation] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.diagnostics.is_empty and not self.definitions and not self.references

    def render_prompt_section(self) -> str:
        o = ["# LSP context", f" - Focus file: {self.file_path}",
             f" - Workspace diagnostics: {self.diagnostics.total_diagnostics}"
             f" across {len(self.diagnostics.files)} file(s)"]
        if self.diagnostics.files:
            o += ["", "Diagnostics:"]
            n = 0
            for fd in self.diagnostics.files:
                for d in fd.diagnostics:
                    if n >= _MAX_D:
                        o.append(" - Additional diagnostics omitted for brevity."); break
                    o.append(f" - {fd.path}:{d.range_start_line+1}:{d.range_start_char+1}"
                             f" [{d.severity_label}] {d.message.replace(chr(10), ' ')}")
                    n += 1
                if n >= _MAX_D: break
        for label, locs in [("Definitions", self.definitions), ("References", self.references)]:
            if not locs: continue
            o += ["", f"{label}:"] + [f" - {l}" for l in locs[:_MAX_L]]
            if len(locs) > _MAX_L:
                o.append(f" - Additional {label.lower()} omitted for brevity.")
        return "\n".join(o)
