"""Tests for SSE chunking and decoding in hanzoai._streaming."""
from __future__ import annotations

import sys
import asyncio
from typing import Iterator, AsyncIterator
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "pkg" / "hanzoai"))

from hanzoai._streaming import SSEDecoder, ServerSentEvent


def make_sync_iterator(chunks: list[bytes]) -> Iterator[bytes]:
    yield from chunks


async def make_async_iterator(chunks: list[bytes]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


class TestIterChunks:
    """Test that _iter_chunks correctly splits SSE frames."""

    def _collect_chunks(self, raw_chunks: list[bytes]) -> list[bytes]:
        decoder = SSEDecoder()
        return list(decoder._iter_chunks(make_sync_iterator(raw_chunks)))

    def test_simple_frame_lf(self):
        """Single frame terminated by \\n\\n."""
        raw = [b"data: hello\n\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\n\n"]

    def test_simple_frame_crlf(self):
        """Single frame terminated by \\r\\n\\r\\n."""
        raw = [b"data: hello\r\n\r\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\r\n\r\n"]

    def test_simple_frame_cr(self):
        """Single frame terminated by \\r\\r."""
        raw = [b"data: hello\r\r"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\r\r"]

    def test_multiple_frames(self):
        """Multiple frames in one byte chunk."""
        raw = [b"data: one\n\ndata: two\n\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: one\n\n", b"data: two\n\n"]

    def test_split_across_chunks(self):
        """Frame split across multiple byte chunks."""
        raw = [b"data: hel", b"lo\n\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\n\n"]

    def test_separator_split_across_chunks_lf(self):
        """\\n\\n separator split across chunk boundary."""
        raw = [b"data: hello\n", b"\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\n\n"]

    def test_separator_split_across_chunks_crlf(self):
        """\\r\\n\\r\\n separator split across chunk boundary at various points."""
        # Split between \r\n and \r\n
        raw = [b"data: hello\r\n", b"\r\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\r\n\r\n"]

    def test_crlf_split_mid_separator(self):
        """The critical bug case: \\r\\n\\r\\n split so \\r and \\n land in different chunks."""
        # This is the case splitlines(keepends=True) gets wrong:
        # chunk1 ends with \r, chunk2 starts with \n\r\n
        raw = [b"data: hello\r", b"\n\r\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\r\n\r\n"]

    def test_crlf_split_three_ways(self):
        """\\r\\n\\r\\n split across three chunks."""
        raw = [b"data: hello\r\n", b"\r", b"\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello\r\n\r\n"]

    def test_trailing_data_no_terminator(self):
        """Data without a trailing separator is yielded on stream end."""
        raw = [b"data: hello"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: hello"]

    def test_empty_input(self):
        """No data yields nothing."""
        chunks = self._collect_chunks([])
        assert chunks == []

    def test_only_separator(self):
        """Just a separator yields it as a chunk."""
        raw = [b"\n\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"\n\n"]

    def test_multiple_frames_split(self):
        """Two frames, each split across chunks."""
        raw = [b"data: one\n", b"\ndata: tw", b"o\n\n"]
        chunks = self._collect_chunks(raw)
        assert chunks == [b"data: one\n\n", b"data: two\n\n"]


class TestAiterChunks:
    """Test that _aiter_chunks matches _iter_chunks behavior."""

    async def _collect_chunks(self, raw_chunks: list[bytes]) -> list[bytes]:
        decoder = SSEDecoder()
        result = []
        async for chunk in decoder._aiter_chunks(make_async_iterator(raw_chunks)):
            result.append(chunk)
        return result

    @pytest.mark.asyncio
    async def test_simple_frame(self):
        chunks = await self._collect_chunks([b"data: hello\n\n"])
        assert chunks == [b"data: hello\n\n"]

    @pytest.mark.asyncio
    async def test_crlf_split_mid_separator(self):
        """The critical bug case for async path."""
        raw = [b"data: hello\r", b"\n\r\n"]
        chunks = await self._collect_chunks(raw)
        assert chunks == [b"data: hello\r\n\r\n"]

    @pytest.mark.asyncio
    async def test_multiple_frames_split(self):
        raw = [b"data: one\n", b"\ndata: tw", b"o\n\n"]
        chunks = await self._collect_chunks(raw)
        assert chunks == [b"data: one\n\n", b"data: two\n\n"]


class TestDoneAndPingSentinel:
    """Test that [DONE] and event: ping are skipped."""

    def _collect_events(self, raw_chunks: list[bytes]) -> list[ServerSentEvent]:
        decoder = SSEDecoder()
        return list(decoder.iter_bytes(make_sync_iterator(raw_chunks)))

    def test_done_sentinel_skipped(self):
        """data: [DONE] should not produce an event."""
        raw = [b"data: {\"text\": \"hi\"}\n\n", b"data: [DONE]\n\n"]
        events = self._collect_events(raw)
        assert len(events) == 1
        assert events[0].data == '{"text": "hi"}'

    def test_ping_event_skipped(self):
        """event: ping should not produce an event."""
        raw = [b"event: ping\ndata: \n\n", b"data: {\"text\": \"hi\"}\n\n"]
        events = self._collect_events(raw)
        assert len(events) == 1
        assert events[0].data == '{"text": "hi"}'

    def test_normal_events_pass_through(self):
        """Normal events should still work."""
        raw = [b"data: {\"a\": 1}\n\n", b"data: {\"b\": 2}\n\n"]
        events = self._collect_events(raw)
        assert len(events) == 2
        assert events[0].json() == {"a": 1}
        assert events[1].json() == {"b": 2}

    @pytest.mark.asyncio
    async def test_done_sentinel_skipped_async(self):
        """data: [DONE] should not produce an event in async path."""
        decoder = SSEDecoder()
        raw = [b"data: {\"text\": \"hi\"}\n\n", b"data: [DONE]\n\n"]
        events = []
        async for sse in decoder.aiter_bytes(make_async_iterator(raw)):
            events.append(sse)
        assert len(events) == 1
        assert events[0].data == '{"text": "hi"}'
