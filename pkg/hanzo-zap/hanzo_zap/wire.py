"""
luxfi/zap binary wire protocol — Python implementation.

Compatible with the Rust `hanzo-zap` crate and Go `github.com/luxfi/zap` v0.2.0.

Wire format:
  Frame: [4-byte LE length][message bytes]
  Message header (16 bytes): magic(4) + version(2) + flags(2) + root_offset(4) + size(4)
  Object fields: inline primitives, (relOffset:i32 + length:u32) for text/bytes
  relOffset is relative to the field's absolute position in the buffer.
"""

from __future__ import annotations

import struct

# ── Constants ────────────────────────────────────────────────────────────

ZAP_MAGIC = b"ZAP\x00"
HEADER_SIZE = 16
VERSION = 1
ALIGNMENT = 8
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB

MSG_TYPE_CLOUD = 100

# Cloud request field byte offsets (each Text/Bytes = 8 bytes: relOffset + length)
CLOUD_REQ_METHOD = 0
CLOUD_REQ_AUTH = 8
CLOUD_REQ_BODY = 16

# Cloud response field byte offsets
# Layout: status(0:u32, 4 bytes) + body(4:Bytes, 8 bytes) + error(12:Text, 8 bytes)
CLOUD_RESP_STATUS = 0   # u32 inline (4 bytes)
CLOUD_RESP_BODY = 4     # (relOffset:i32 + length:u32)
CLOUD_RESP_ERROR = 12   # (relOffset:i32 + length:u32)

# Call correlation flags
REQ_FLAG_REQ = 1
REQ_FLAG_RESP = 2

# Handshake constants
HANDSHAKE_OBJ_SIZE = 64
HANDSHAKE_ID_MAX = 60
HANDSHAKE_ID_LEN_OFFSET = 60


# ── Message ──────────────────────────────────────────────────────────────

class Message:
    """Parsed ZAP binary message (owns the full buffer including header)."""

    __slots__ = ("_data",)

    def __init__(self, data: bytes | bytearray) -> None:
        self._data = bytes(data)

    @classmethod
    def parse(cls, data: bytes | bytearray) -> "Message":
        if len(data) < HEADER_SIZE:
            raise ValueError(f"ZAP message too short: {len(data)} < {HEADER_SIZE}")
        if data[:4] != ZAP_MAGIC:
            raise ValueError(f"Bad ZAP magic: {data[:4]!r}")
        return cls(data)

    @property
    def bytes(self) -> bytes:
        return self._data

    @property
    def version(self) -> int:
        return struct.unpack_from("<H", self._data, 4)[0]

    @property
    def flags(self) -> int:
        return struct.unpack_from("<H", self._data, 6)[0]

    @property
    def msg_type(self) -> int:
        return self.flags >> 8

    @property
    def root_offset(self) -> int:
        """Absolute offset of the root object in the buffer."""
        return struct.unpack_from("<I", self._data, 8)[0]

    @property
    def total_size(self) -> int:
        return struct.unpack_from("<I", self._data, 12)[0]


# ── Object reader (works on full message buffer with absolute offsets) ──

def obj_uint32(data: bytes, obj_offset: int, field_offset: int) -> int:
    """Read a u32 inline field from object at obj_offset."""
    pos = obj_offset + field_offset
    if pos + 4 > len(data):
        return 0
    return struct.unpack_from("<I", data, pos)[0]


def obj_bytes(data: bytes, obj_offset: int, field_offset: int) -> bytes:
    """Read a Bytes field (relOffset:i32 + length:u32) from object."""
    pos = obj_offset + field_offset
    if pos + 8 > len(data):
        return b""
    rel_off = struct.unpack_from("<i", data, pos)[0]  # signed i32
    length = struct.unpack_from("<I", data, pos + 4)[0]
    if length == 0 or rel_off == 0:
        return b""
    abs_off = pos + rel_off
    if abs_off + length > len(data):
        return b""
    return data[abs_off:abs_off + length]


def obj_text(data: bytes, obj_offset: int, field_offset: int) -> str:
    """Read a Text field from object."""
    b = obj_bytes(data, obj_offset, field_offset)
    return b.decode("utf-8", errors="replace") if b else ""


# ── Builder (matches Rust Builder exactly) ───────────────────────────────

def _align(pos: int) -> int:
    return (pos + ALIGNMENT - 1) & ~(ALIGNMENT - 1)


class Builder:
    """Builds a ZAP message in a single buffer, matching Rust Builder."""

    def __init__(self, capacity: int = 256) -> None:
        cap = max(capacity, 256)
        self._buf = bytearray(cap)
        self._buf[:4] = ZAP_MAGIC
        struct.pack_into("<H", self._buf, 4, VERSION)
        self._pos = HEADER_SIZE
        self._root_offset = 0

    def _grow(self, n: int) -> None:
        needed = self._pos + n
        if needed <= len(self._buf):
            return
        new_cap = max(len(self._buf) * 2, needed)
        self._buf.extend(b"\x00" * (new_cap - len(self._buf)))

    def _align_pos(self) -> None:
        padding = (ALIGNMENT - (self._pos % ALIGNMENT)) % ALIGNMENT
        self._grow(padding)
        for _ in range(padding):
            self._buf[self._pos] = 0
            self._pos += 1

    def start_object(self, data_size: int) -> "ObjectBuilder":
        self._align_pos()
        return ObjectBuilder(self, self._pos, data_size)

    def finish(self, flags: int = 0) -> bytes:
        struct.pack_into("<H", self._buf, 6, flags)
        struct.pack_into("<I", self._buf, 8, self._root_offset)
        struct.pack_into("<I", self._buf, 12, self._pos)
        return bytes(self._buf[:self._pos])


class ObjectBuilder:
    """Builds a single object within a Builder, matching Rust ObjectBuilder."""

    def __init__(self, builder: Builder, start_pos: int, data_size: int) -> None:
        self._builder = builder
        self._start = start_pos
        self._data_size = data_size
        self._deferred: list[tuple[int, bytes]] = []  # (field_offset, data)

    def _ensure_field(self, end_offset: int) -> None:
        needed = self._start + end_offset
        if needed > self._builder._pos:
            self._builder._grow(needed - self._builder._pos)
            for i in range(self._builder._pos, needed):
                self._builder._buf[i] = 0
            self._builder._pos = needed

    def set_u32(self, field_offset: int, v: int) -> None:
        self._ensure_field(field_offset + 4)
        struct.pack_into("<I", self._builder._buf, self._start + field_offset, v)

    def set_u8(self, field_offset: int, v: int) -> None:
        self._ensure_field(field_offset + 1)
        self._builder._buf[self._start + field_offset] = v & 0xFF

    def set_bytes(self, field_offset: int, data: bytes) -> None:
        self._ensure_field(field_offset + 8)
        pos = self._start + field_offset
        if not data:
            struct.pack_into("<I", self._builder._buf, pos, 0)
            struct.pack_into("<I", self._builder._buf, pos + 4, 0)
            return
        struct.pack_into("<I", self._builder._buf, pos + 4, len(data))
        self._deferred.append((field_offset, data))

    def set_text(self, field_offset: int, text: str) -> None:
        self.set_bytes(field_offset, text.encode("utf-8"))

    def finish_as_root(self) -> None:
        """Finalize and set as root object."""
        self._ensure_field(self._data_size)
        for field_offset, data in self._deferred:
            data_pos = self._builder._pos
            self._builder._grow(len(data))
            start = self._builder._pos
            self._builder._buf[start:start + len(data)] = data
            self._builder._pos += len(data)
            field_abs = self._start + field_offset
            rel_offset = data_pos - field_abs
            struct.pack_into("<i", self._builder._buf, field_abs, rel_offset)  # signed i32
        self._builder._root_offset = self._start


# ── Cloud service helpers ────────────────────────────────────────────────

def build_cloud_request(method: str, auth: str, body: bytes) -> bytes:
    """Build a MsgType 100 cloud service request message."""
    b = Builder(len(body) + len(method) + len(auth) + 128)
    obj = b.start_object(24)  # 3 * 8 bytes
    obj.set_text(CLOUD_REQ_METHOD, method)
    obj.set_text(CLOUD_REQ_AUTH, auth)
    obj.set_bytes(CLOUD_REQ_BODY, body)
    obj.finish_as_root()
    return b.finish(flags=MSG_TYPE_CLOUD << 8)


def build_cloud_response(status: int, body: bytes, error: str) -> bytes:
    """Build a MsgType 100 cloud service response message."""
    b = Builder(len(body) + len(error) + 128)
    obj = b.start_object(20)  # u32(4) + Bytes(8) + Text(8) = 20
    obj.set_u32(CLOUD_RESP_STATUS, status)
    obj.set_bytes(CLOUD_RESP_BODY, body)
    obj.set_text(CLOUD_RESP_ERROR, error)
    obj.finish_as_root()
    return b.finish(flags=MSG_TYPE_CLOUD << 8)


def parse_cloud_request(msg: Message) -> tuple[str, str, bytes]:
    """Parse a cloud request → (method, auth, body)."""
    data = msg.bytes
    off = msg.root_offset
    method = obj_text(data, off, CLOUD_REQ_METHOD)
    auth = obj_text(data, off, CLOUD_REQ_AUTH)
    body = obj_bytes(data, off, CLOUD_REQ_BODY)
    return method, auth, body


def parse_cloud_response(msg: Message) -> tuple[int, bytes, str]:
    """Parse a cloud response → (status, body, error)."""
    data = msg.bytes
    off = msg.root_offset
    status = obj_uint32(data, off, CLOUD_RESP_STATUS)
    body = obj_bytes(data, off, CLOUD_RESP_BODY)
    error = obj_text(data, off, CLOUD_RESP_ERROR)
    return status, body, error


# ── Handshake ────────────────────────────────────────────────────────────

def build_handshake(node_id: str) -> bytes:
    """Build a handshake message (msg_type=0, 64-byte fixed object)."""
    b = Builder(128)
    obj = b.start_object(HANDSHAKE_OBJ_SIZE)
    id_bytes = node_id.encode("utf-8")[:HANDSHAKE_ID_MAX]
    for i, byte in enumerate(id_bytes):
        obj.set_u8(i, byte)
    obj.set_u32(HANDSHAKE_ID_LEN_OFFSET, len(id_bytes))
    obj.finish_as_root()
    return b.finish()


def parse_handshake(msg: Message) -> str:
    """Parse a handshake message → peer node ID."""
    data = msg.bytes
    off = msg.root_offset
    id_len = obj_uint32(data, off, HANDSHAKE_ID_LEN_OFFSET)
    if id_len == 0:
        return ""
    start = off
    end = start + min(id_len, HANDSHAKE_ID_MAX)
    if end > len(data):
        return ""
    return data[start:end].decode("utf-8", errors="replace")


# ── Frame I/O ────────────────────────────────────────────────────────────

async def read_frame(reader) -> bytes:
    """Read a length-prefixed frame: [4-byte LE length][data]."""
    len_buf = await reader.readexactly(4)
    length = struct.unpack("<I", len_buf)[0]
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"ZAP frame too large: {length}")
    if length == 0:
        return b""
    return await reader.readexactly(length)


async def write_frame(writer, data: bytes) -> None:
    """Write a length-prefixed frame."""
    writer.write(struct.pack("<I", len(data)))
    writer.write(data)
    await writer.drain()
