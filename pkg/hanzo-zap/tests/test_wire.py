"""Tests for luxfi/zap binary wire protocol compatibility."""
import asyncio
import struct

import pytest

from hanzo_zap.wire import (
    ZAP_MAGIC,
    HEADER_SIZE,
    VERSION,
    MSG_TYPE_CLOUD,
    REQ_FLAG_REQ,
    REQ_FLAG_RESP,
    CLOUD_REQ_METHOD,
    CLOUD_REQ_AUTH,
    CLOUD_REQ_BODY,
    CLOUD_RESP_STATUS,
    CLOUD_RESP_BODY,
    CLOUD_RESP_ERROR,
    MAX_MESSAGE_SIZE,
    Message,
    Builder,
    ObjectBuilder,
    build_cloud_request,
    build_cloud_response,
    parse_cloud_request,
    parse_cloud_response,
    build_handshake,
    parse_handshake,
    obj_uint32,
    obj_bytes,
    obj_text,
    read_frame,
    write_frame,
)


# ── constants ──────────────────────────────────────────────────────────────

def test_zap_magic():
    assert ZAP_MAGIC == b"ZAP\x00"
    assert HEADER_SIZE == 16


def test_version():
    assert VERSION == 1


def test_msg_type_cloud():
    assert MSG_TYPE_CLOUD == 100


def test_req_flags():
    assert REQ_FLAG_REQ == 1
    assert REQ_FLAG_RESP == 2


def test_cloud_resp_offsets():
    """Cloud response layout: status(0:u32,4B) + body(4:Bytes,8B) + error(12:Text,8B)."""
    assert CLOUD_RESP_STATUS == 0
    assert CLOUD_RESP_BODY == 4
    assert CLOUD_RESP_ERROR == 12


# ── Message parsing ────────────────────────────────────────────────────────

def test_message_parse_rejects_short():
    with pytest.raises(ValueError, match="too short"):
        Message.parse(b"ZAP")


def test_message_parse_rejects_bad_magic():
    bad = b"BAD\x00" + b"\x00" * 12
    with pytest.raises(ValueError, match="Bad ZAP magic"):
        Message.parse(bad)


def test_message_parse_valid_header():
    header = bytearray(HEADER_SIZE)
    header[:4] = ZAP_MAGIC
    struct.pack_into("<H", header, 4, VERSION)
    msg = Message.parse(bytes(header))
    assert msg.version == VERSION
    assert msg.bytes == bytes(header)


def test_message_properties():
    flags = MSG_TYPE_CLOUD << 8 | 0x01
    header = bytearray(HEADER_SIZE)
    header[:4] = ZAP_MAGIC
    struct.pack_into("<H", header, 4, VERSION)
    struct.pack_into("<H", header, 6, flags)
    struct.pack_into("<I", header, 8, 0)
    struct.pack_into("<I", header, 12, 42)
    msg = Message.parse(bytes(header))
    assert msg.version == VERSION
    assert msg.msg_type == MSG_TYPE_CLOUD
    assert msg.flags == flags
    assert msg.root_offset == 0
    assert msg.total_size == 42


# ── Builder ───────────────────────────────────────────────────────────────

def test_builder_header():
    """Builder produces correct ZAP header."""
    b = Builder()
    result = b.finish(flags=MSG_TYPE_CLOUD << 8)
    assert result[:4] == ZAP_MAGIC
    version = struct.unpack_from("<H", result, 4)[0]
    assert version == VERSION
    flags = struct.unpack_from("<H", result, 6)[0]
    assert flags >> 8 == MSG_TYPE_CLOUD


def test_builder_with_object():
    """Builder + ObjectBuilder produce parseable message."""
    b = Builder()
    obj = b.start_object(4)
    obj.set_u32(0, 0xDEADBEEF)
    obj.finish_as_root()
    result = b.finish()
    msg = Message.parse(result)
    assert msg.root_offset == HEADER_SIZE  # object starts right after header
    val = obj_uint32(msg.bytes, msg.root_offset, 0)
    assert val == 0xDEADBEEF


def test_builder_text_field():
    """Text field with relative offset is readable."""
    b = Builder()
    obj = b.start_object(8)
    obj.set_text(0, "hello")
    obj.finish_as_root()
    result = b.finish()
    msg = Message.parse(result)
    text = obj_text(msg.bytes, msg.root_offset, 0)
    assert text == "hello"


def test_builder_bytes_field():
    """Bytes field with relative offset is readable."""
    b = Builder()
    obj = b.start_object(8)
    payload = b"\x01\x02\x03\x04"
    obj.set_bytes(0, payload)
    obj.finish_as_root()
    result = b.finish()
    msg = Message.parse(result)
    data = obj_bytes(msg.bytes, msg.root_offset, 0)
    assert data == payload


def test_builder_mixed_fields():
    """Object with inline u32 + variable-length fields."""
    b = Builder()
    obj = b.start_object(20)  # u32(4) + Bytes(8) + Text(8)
    obj.set_u32(0, 200)
    obj.set_bytes(4, b"body-data")
    obj.set_text(12, "error-msg")
    obj.finish_as_root()
    result = b.finish()
    msg = Message.parse(result)
    off = msg.root_offset
    assert obj_uint32(msg.bytes, off, 0) == 200
    assert obj_bytes(msg.bytes, off, 4) == b"body-data"
    assert obj_text(msg.bytes, off, 12) == "error-msg"


def test_builder_empty_bytes():
    """Empty bytes field roundtrips as empty."""
    b = Builder()
    obj = b.start_object(8)
    obj.set_bytes(0, b"")
    obj.finish_as_root()
    result = b.finish()
    msg = Message.parse(result)
    assert obj_bytes(msg.bytes, msg.root_offset, 0) == b""


# ── Handshake ─────────────────────────────────────────────────────────────

def test_build_and_parse_handshake():
    hs_bytes = build_handshake("test-node")
    msg = Message.parse(hs_bytes)
    assert msg.msg_type == 0
    peer = parse_handshake(msg)
    assert peer == "test-node"


def test_handshake_long_id_truncated():
    long_id = "x" * 100
    hs_bytes = build_handshake(long_id)
    msg = Message.parse(hs_bytes)
    peer = parse_handshake(msg)
    assert peer == "x" * 60


def test_handshake_empty_id():
    hs_bytes = build_handshake("")
    msg = Message.parse(hs_bytes)
    peer = parse_handshake(msg)
    assert peer == ""


# ── Cloud request/response ────────────────────────────────────────────────

def test_build_cloud_request():
    body = b'{"model":"test","messages":[]}'
    msg_bytes = build_cloud_request("chat.completions", "Bearer token123", body)
    msg = Message.parse(msg_bytes)
    assert msg.msg_type == MSG_TYPE_CLOUD


def test_cloud_request_roundtrip():
    """Build and parse a cloud request."""
    body = b'{"test":true}'
    msg_bytes = build_cloud_request("completions", "Bearer abc", body)
    msg = Message.parse(msg_bytes)
    method, auth, req_body = parse_cloud_request(msg)
    assert method == "completions"
    assert auth == "Bearer abc"
    assert req_body == body


def test_cloud_response_roundtrip():
    """Build and parse a cloud response."""
    resp_body = b'{"id":"test","choices":[]}'
    msg_bytes = build_cloud_response(200, resp_body, "")
    msg = Message.parse(msg_bytes)
    status, body, error = parse_cloud_response(msg)
    assert status == 200
    assert body == resp_body
    assert error == ""


def test_cloud_response_error():
    msg_bytes = build_cloud_response(500, b"", "internal server error")
    msg = Message.parse(msg_bytes)
    status, body, error = parse_cloud_response(msg)
    assert status == 500
    assert error == "internal server error"


def test_cloud_response_with_body_and_error():
    """Response with both body and error text."""
    resp_body = b'{"detail":"something"}'
    msg_bytes = build_cloud_response(400, resp_body, "bad request")
    msg = Message.parse(msg_bytes)
    status, body, error = parse_cloud_response(msg)
    assert status == 400
    assert body == resp_body
    assert error == "bad request"


# ── Frame I/O helpers ─────────────────────────────────────────────────────

async def _make_stream_pair():
    connected: asyncio.Future[tuple[asyncio.StreamReader, asyncio.StreamWriter]] = (
        asyncio.get_event_loop().create_future()
    )

    async def on_connect(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
        connected.set_result((r, w))

    server = await asyncio.start_server(on_connect, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    c_reader, c_writer = await asyncio.open_connection("127.0.0.1", port)
    s_reader, s_writer = await connected

    async def cleanup() -> None:
        for w in (c_writer, s_writer):
            w.close()
            await w.wait_closed()
        server.close()
        await server.wait_closed()

    return s_reader, c_writer, cleanup


@pytest.mark.asyncio
async def test_frame_io():
    reader, writer, cleanup = await _make_stream_pair()
    try:
        test_data = b"hello ZAP"
        await write_frame(writer, test_data)
        result = await read_frame(reader)
        assert result == test_data
    finally:
        await cleanup()


@pytest.mark.asyncio
async def test_frame_io_empty():
    reader, writer, cleanup = await _make_stream_pair()
    try:
        await write_frame(writer, b"")
        result = await read_frame(reader)
        assert result == b""
    finally:
        await cleanup()


@pytest.mark.asyncio
async def test_frame_io_large():
    reader, writer, cleanup = await _make_stream_pair()
    try:
        big_data = b"X" * 65536
        await write_frame(writer, big_data)
        result = await read_frame(reader)
        assert result == big_data
    finally:
        await cleanup()


@pytest.mark.asyncio
async def test_frame_rejects_oversized():
    reader, writer, cleanup = await _make_stream_pair()
    try:
        writer.write(struct.pack("<I", MAX_MESSAGE_SIZE + 1))
        await writer.drain()
        with pytest.raises(ValueError, match="too large"):
            await read_frame(reader)
    finally:
        await cleanup()


@pytest.mark.asyncio
async def test_full_message_through_frames():
    """Build a ZAP message, send through frame I/O, parse on the other side."""
    reader, writer, cleanup = await _make_stream_pair()
    try:
        hs = build_handshake("frame-test-node")
        await write_frame(writer, hs)
        received = await read_frame(reader)
        msg = Message.parse(received)
        peer = parse_handshake(msg)
        assert peer == "frame-test-node"
    finally:
        await cleanup()
