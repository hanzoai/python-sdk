"""Tests for vim keybinding support."""

import pytest

from hanzo_dev.vim_mode import VimMode, VimState


class FakeWidget:
    """Minimal InputWidget implementation for testing."""

    def __init__(self, value: str = "", cursor_position: int = 0):
        self._value = value
        self._cursor_position = cursor_position

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        self._value = v

    @property
    def cursor_position(self) -> int:
        return self._cursor_position

    @cursor_position.setter
    def cursor_position(self, v: int) -> None:
        self._cursor_position = v


# -- Mode transitions --

class TestModeTransitions:
    def test_starts_in_normal(self):
        s = VimState()
        assert s.mode == VimMode.Normal

    def test_i_enters_insert(self):
        s = VimState()
        w = FakeWidget("hello")
        s.handle_key("i", w)
        assert s.mode == VimMode.Insert

    def test_a_enters_insert_after(self):
        s = VimState()
        w = FakeWidget("hello", 2)
        s.handle_key("a", w)
        assert s.mode == VimMode.Insert
        assert w.cursor_position == 3

    def test_I_enters_insert_at_start(self):
        s = VimState()
        w = FakeWidget("hello", 3)
        s.handle_key("I", w)
        assert s.mode == VimMode.Insert
        assert w.cursor_position == 0

    def test_A_enters_insert_at_end(self):
        s = VimState()
        w = FakeWidget("hello", 0)
        s.handle_key("A", w)
        assert s.mode == VimMode.Insert
        assert w.cursor_position == 5

    def test_o_enters_insert_at_end(self):
        s = VimState()
        w = FakeWidget("hello", 0)
        s.handle_key("o", w)
        assert s.mode == VimMode.Insert
        assert w.cursor_position == 5

    def test_O_enters_insert_at_start(self):
        s = VimState()
        w = FakeWidget("hello", 3)
        s.handle_key("O", w)
        assert s.mode == VimMode.Insert
        assert w.cursor_position == 0

    def test_escape_from_insert(self):
        s = VimState(mode=VimMode.Insert)
        w = FakeWidget("hello", 3)
        s.handle_key("escape", w)
        assert s.mode == VimMode.Normal
        assert w.cursor_position == 2  # backs up one

    def test_escape_from_insert_at_zero(self):
        s = VimState(mode=VimMode.Insert)
        w = FakeWidget("hello", 0)
        s.handle_key("escape", w)
        assert s.mode == VimMode.Normal
        assert w.cursor_position == 0

    def test_v_enters_visual(self):
        s = VimState()
        w = FakeWidget("hello", 2)
        s.handle_key("v", w)
        assert s.mode == VimMode.Visual
        assert s.visual_anchor == 2

    def test_escape_from_visual(self):
        s = VimState(mode=VimMode.Visual)
        w = FakeWidget("hello")
        s.handle_key("escape", w)
        assert s.mode == VimMode.Normal

    def test_colon_enters_command(self):
        s = VimState()
        w = FakeWidget("hello")
        s.handle_key(":", w)
        assert s.mode == VimMode.Command

    def test_escape_from_command(self):
        s = VimState(mode=VimMode.Command)
        w = FakeWidget("hello")
        s.handle_key("escape", w)
        assert s.mode == VimMode.Normal


# -- Cursor movement --

class TestCursorMovement:
    def test_h_moves_left(self):
        s = VimState()
        w = FakeWidget("hello", 3)
        s.handle_key("h", w)
        assert w.cursor_position == 2

    def test_h_clamps_at_zero(self):
        s = VimState()
        w = FakeWidget("hello", 0)
        s.handle_key("h", w)
        assert w.cursor_position == 0

    def test_l_moves_right(self):
        s = VimState()
        w = FakeWidget("hello", 2)
        s.handle_key("l", w)
        assert w.cursor_position == 3

    def test_l_clamps_at_end(self):
        s = VimState()
        w = FakeWidget("hello", 5)
        s.handle_key("l", w)
        assert w.cursor_position == 5

    def test_0_goes_to_start(self):
        s = VimState()
        w = FakeWidget("hello", 4)
        s.handle_key("0", w)
        assert w.cursor_position == 0

    def test_dollar_goes_to_end(self):
        s = VimState()
        w = FakeWidget("hello", 0)
        s.handle_key("$", w)
        assert w.cursor_position == 5

    def test_w_next_word(self):
        s = VimState()
        w = FakeWidget("hello world", 0)
        s.handle_key("w", w)
        assert w.cursor_position == 6

    def test_b_prev_word(self):
        s = VimState()
        w = FakeWidget("hello world", 8)
        s.handle_key("b", w)
        assert w.cursor_position == 6

    def test_gg_goes_to_start(self):
        s = VimState()
        w = FakeWidget("hello", 4)
        s.handle_key("g", w)
        s.handle_key("g", w)
        assert w.cursor_position == 0

    def test_j_k_consumed(self):
        s = VimState()
        w = FakeWidget("hello", 2)
        assert s.handle_key("j", w) is True
        assert w.cursor_position == 2
        assert s.handle_key("k", w) is True
        assert w.cursor_position == 2


# -- Delete / Yank / Paste --

class TestEditOperations:
    def test_x_deletes_char(self):
        s = VimState()
        w = FakeWidget("hello", 1)
        s.handle_key("x", w)
        assert w.value == "hllo"
        assert s.register == "e"

    def test_x_at_end_noop(self):
        s = VimState()
        w = FakeWidget("hi", 2)
        s.handle_key("x", w)
        assert w.value == "hi"

    def test_dd_deletes_line(self):
        s = VimState()
        w = FakeWidget("hello world", 3)
        s.handle_key("d", w)
        s.handle_key("d", w)
        assert w.value == ""
        assert s.register == "hello world"

    def test_yy_yanks_line(self):
        s = VimState()
        w = FakeWidget("hello", 2)
        s.handle_key("y", w)
        s.handle_key("y", w)
        assert s.register == "hello"
        assert w.value == "hello"  # unchanged

    def test_p_pastes_after(self):
        s = VimState()
        s.register = "XY"
        w = FakeWidget("abc", 1)
        s.handle_key("p", w)
        assert w.value == "abXYc"

    def test_dw_deletes_word(self):
        s = VimState()
        w = FakeWidget("hello world", 0)
        s.handle_key("d", w)
        s.handle_key("w", w)
        assert w.value == "world"
        assert s.register == "hello "


# -- Undo --

class TestUndo:
    def test_undo_restores(self):
        s = VimState()
        w = FakeWidget("hello", 2)
        s.handle_key("x", w)
        assert w.value == "helo"
        s.handle_key("u", w)
        assert w.value == "hello"
        assert w.cursor_position == 2

    def test_undo_empty_stack(self):
        s = VimState()
        w = FakeWidget("hello", 0)
        s.handle_key("u", w)  # should not crash
        assert w.value == "hello"


# -- Visual mode --

class TestVisualMode:
    def test_visual_yank(self):
        s = VimState()
        w = FakeWidget("hello", 1)
        s.handle_key("v", w)
        s.handle_key("l", w)
        s.handle_key("l", w)
        s.handle_key("y", w)
        assert s.register == "ell"
        assert s.mode == VimMode.Normal

    def test_visual_delete(self):
        s = VimState()
        w = FakeWidget("hello", 1)
        s.handle_key("v", w)
        s.handle_key("l", w)
        s.handle_key("d", w)
        assert w.value == "hlo"
        assert s.register == "el"
        assert s.mode == VimMode.Normal


# -- Command mode --

class TestCommandMode:
    def test_accumulate_and_return(self):
        s = VimState()
        w = FakeWidget()
        s.handle_key(":", w)
        s.handle_key("w", w)
        s.handle_key("q", w)
        result = s.handle_key("enter", w)
        assert result == "wq"
        assert s.mode == VimMode.Normal

    def test_backspace_in_command(self):
        s = VimState()
        w = FakeWidget()
        s.handle_key(":", w)
        s.handle_key("a", w)
        s.handle_key("b", w)
        s.handle_key("backspace", w)
        result = s.handle_key("enter", w)
        assert result == "a"

    def test_search_prefix(self):
        s = VimState()
        w = FakeWidget("hello")
        s.handle_key("/", w)
        assert s.mode == VimMode.Command
        assert s.command_buffer == "/"
        s.handle_key("h", w)
        result = s.handle_key("enter", w)
        assert result == "/h"


# -- Insert passthrough --

class TestInsertMode:
    def test_regular_key_returns_false(self):
        s = VimState(mode=VimMode.Insert)
        w = FakeWidget("hello")
        result = s.handle_key("a", w)
        assert result is False  # not consumed, widget handles it
