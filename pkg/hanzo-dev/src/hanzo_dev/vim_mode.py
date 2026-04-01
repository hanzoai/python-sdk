"""Vim keybinding support for Textual Input widget."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol, runtime_checkable


class VimMode(Enum):
    Normal = auto()
    Insert = auto()
    Visual = auto()
    Command = auto()


@runtime_checkable
class InputWidget(Protocol):
    @property
    def cursor_position(self) -> int: ...
    @cursor_position.setter
    def cursor_position(self, value: int) -> None: ...
    @property
    def value(self) -> str: ...
    @value.setter
    def value(self, value: str) -> None: ...


@dataclass
class VimState:
    mode: VimMode = VimMode.Normal
    register: str = ""
    visual_anchor: int = 0
    command_buffer: str = ""
    _pending: str = ""
    _undo_stack: list[tuple[str, int]] = field(default_factory=list)

    def handle_key(self, key: str, widget: InputWidget) -> bool | str:
        """Handle a keypress. Returns True if consumed, a command string, or False."""
        handler = {
            VimMode.Normal: self._normal, VimMode.Insert: self._insert,
            VimMode.Visual: self._visual, VimMode.Command: self._command,
        }.get(self.mode)
        return handler(key, widget) if handler else False

    # -- Normal mode --

    def _normal(self, key: str, widget: InputWidget) -> bool | str:
        val, pos = widget.value, widget.cursor_position
        if self._pending:
            return self._do_pending(key, widget)
        # Motions
        if key == "h":
            widget.cursor_position = max(0, pos - 1); return True
        if key == "l":
            widget.cursor_position = min(len(val), pos + 1); return True
        if key in ("j", "k"):
            return True
        if key == "0":
            widget.cursor_position = 0; return True
        if key == "$":
            widget.cursor_position = len(val); return True
        if key == "w":
            widget.cursor_position = self._next_word(val, pos); return True
        if key == "b":
            widget.cursor_position = self._prev_word(val, pos); return True
        if key == "e":
            widget.cursor_position = self._end_word(val, pos); return True
        # Insert mode entries
        if key == "i":
            self._save_undo(widget); self.mode = VimMode.Insert; return True
        if key == "a":
            self._save_undo(widget); self.mode = VimMode.Insert
            widget.cursor_position = min(len(val), pos + 1); return True
        if key == "I":
            self._save_undo(widget); self.mode = VimMode.Insert
            widget.cursor_position = 0; return True
        if key == "A":
            self._save_undo(widget); self.mode = VimMode.Insert
            widget.cursor_position = len(val); return True
        if key in ("o", "O"):
            self._save_undo(widget); self.mode = VimMode.Insert
            widget.cursor_position = len(val) if key == "o" else 0; return True
        # Two-char starters
        if key in ("d", "y", "g"):
            self._pending = key; return True
        # Single-char editing
        if key == "x":
            if pos < len(val):
                self._save_undo(widget); self.register = val[pos]
                widget.value = val[:pos] + val[pos + 1:]
                widget.cursor_position = min(pos, max(0, len(widget.value) - 1))
            return True
        if key == "p" and self.register:
            self._save_undo(widget); np = pos + 1
            widget.value = val[:np] + self.register + val[np:]
            widget.cursor_position = np + len(self.register) - 1; return True
        if key == "u":
            self._pop_undo(widget); return True
        if key == "v":
            self.mode = VimMode.Visual; self.visual_anchor = pos; return True
        if key == ":":
            self.mode = VimMode.Command; self.command_buffer = ""; return True
        if key == "/":
            self.mode = VimMode.Command; self.command_buffer = "/"; return True
        if key == "escape":
            return True
        if key == "p":
            return True
        return False

    def _do_pending(self, key: str, widget: InputWidget) -> bool:
        seq, self._pending = self._pending + key, ""
        val = widget.value
        if seq == "dd":
            self._save_undo(widget); self.register = val
            widget.value = ""; widget.cursor_position = 0; return True
        if seq == "yy":
            self.register = val; return True
        if seq == "gg":
            widget.cursor_position = 0; return True
        if seq[0] in ("d", "y"):
            return self._op_motion(seq[0], key, widget)
        return True

    def _op_motion(self, op: str, motion: str, widget: InputWidget) -> bool:
        val, pos = widget.value, widget.cursor_position
        target = self._motion_target(motion, val, pos)
        if target is None:
            return True
        start, end = (min(pos, target), max(pos, target))
        self.register = val[start:end]
        if op == "d":
            self._save_undo(widget)
            widget.value = val[:start] + val[end:]
            widget.cursor_position = start
        return True

    def _motion_target(self, m: str, val: str, pos: int) -> int | None:
        return {"w": self._next_word, "b": self._prev_word, "e": self._end_word}.get(m, lambda v, p: {"$": len(v), "0": 0}.get(m))(val, pos)

    # -- Insert mode --

    def _insert(self, key: str, widget: InputWidget) -> bool | str:
        if key == "escape":
            self.mode = VimMode.Normal
            if widget.cursor_position > 0:
                widget.cursor_position -= 1
            return True
        return False

    # -- Visual mode --

    def _visual(self, key: str, widget: InputWidget) -> bool | str:
        val, pos = widget.value, widget.cursor_position
        if key == "escape":
            self.mode = VimMode.Normal; return True
        if key == "h":
            widget.cursor_position = max(0, pos - 1); return True
        if key == "l":
            widget.cursor_position = min(len(val), pos + 1); return True
        if key in ("y", "d"):
            start, end = min(self.visual_anchor, pos), max(self.visual_anchor, pos) + 1
            self.register = val[start:end]
            if key == "d":
                self._save_undo(widget)
                widget.value = val[:start] + val[end:]
                widget.cursor_position = start
            self.mode = VimMode.Normal; return True
        return True

    # -- Command mode --

    def _command(self, key: str, widget: InputWidget) -> bool | str:
        if key == "escape":
            self.mode = VimMode.Normal; self.command_buffer = ""; return True
        if key == "enter":
            cmd = self.command_buffer; self.mode = VimMode.Normal
            self.command_buffer = ""; return cmd if cmd else True
        if key == "backspace":
            if self.command_buffer:
                self.command_buffer = self.command_buffer[:-1]
            else:
                self.mode = VimMode.Normal
            return True
        if len(key) == 1:
            self.command_buffer += key
        return True

    # -- Word motion helpers --

    @staticmethod
    def _next_word(val: str, pos: int) -> int:
        n, i = len(val), pos
        while i < n and not val[i].isspace(): i += 1
        while i < n and val[i].isspace(): i += 1
        return i

    @staticmethod
    def _prev_word(val: str, pos: int) -> int:
        if pos <= 0: return 0
        i = pos - 1
        while i > 0 and val[i].isspace(): i -= 1
        while i > 0 and not val[i - 1].isspace(): i -= 1
        return i

    @staticmethod
    def _end_word(val: str, pos: int) -> int:
        n = len(val)
        if pos >= n - 1: return max(0, n - 1)
        i = pos + 1
        while i < n and val[i].isspace(): i += 1
        while i < n - 1 and not val[i + 1].isspace(): i += 1
        return i

    # -- Undo --

    def _save_undo(self, w: InputWidget) -> None:
        self._undo_stack.append((w.value, w.cursor_position))

    def _pop_undo(self, w: InputWidget) -> None:
        if self._undo_stack:
            v, p = self._undo_stack.pop(); w.value = v; w.cursor_position = p
