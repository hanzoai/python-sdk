"""ZAP binary wire protocol — the hanzo-zap service layer over canonical ``zap``.

The zero-copy codec is NOT reimplemented here. The object encode/decode, the
deferred out-of-line layout, 8-byte alignment, and the 16-byte header all come
from the canonical ``zap.wire`` package (the byte-faithful port of
``zap-proto/go``), the one Python copy of the wire. This module is a thin layer
that keeps hanzo-zap's small API surface (``set_u32``/``obj_uint32`` spellings,
the ``Message`` header view) and adds the hanzo *cloud service* schema
(``MsgType 100`` request/response, the handshake, and length-prefixed frame I/O)
on top of those canonical primitives.

Wire format (defined and owned by ``zap.wire``):
  Frame: [4-byte LE length][message bytes]
  Message header (16 bytes): magic(4) + version(2) + flags(2) + root_offset(4) + size(4)
  Object fields: inline primitives; (relOffset:u32 + length:u32) for text/bytes,
  the offset being relative to the field's absolute position in the buffer.
"""

from __future__ import annotations

import struct

from zap import wire as _zw

# ── Constants ────────────────────────────────────────────────────────────
# Codec constants are sourced from the canonical wire so they can never drift.
ZAP_MAGIC = _zw.MAGIC          # b"ZAP\x00"
HEADER_SIZE = _zw.HEADER_SIZE  # 16
# Both accepted versions come from the canonical wire, so the set this layer
# admits is the set ``zap.wire.parse`` admits — which is the set Go's
# ``zap.Parse`` admits. luxd emits VERSION2 by default, so a reader that
# recognises only VERSION1 cannot read the live network.
VERSION1 = _zw.VERSION1        # 1 — legacy schema
VERSION2 = _zw.VERSION2        # 2 — current; what luxd emits
VERSION = _zw.VERSION          # the version this layer emits
ALIGNMENT = _zw.ALIGNMENT      # 8
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# hanzo cloud-service schema (layered on the wire; not part of the codec).
MSG_TYPE_CLOUD = 100

# Cloud request field byte offsets (each Text/Bytes = 8 bytes: relOffset + length)
CLOUD_REQ_METHOD = 0
CLOUD_REQ_AUTH = 8
CLOUD_REQ_BODY = 16

# Cloud response field byte offsets
# Layout: status(0:u32, 4 bytes) + body(4:Bytes, 8 bytes) + error(12:Text, 8 bytes)
CLOUD_RESP_STATUS = 0   # u32 inline (4 bytes)
CLOUD_RESP_BODY = 4     # (relOffset:u32 + length:u32)
CLOUD_RESP_ERROR = 12   # (relOffset:u32 + length:u32)

# Call correlation flags
REQ_FLAG_REQ = 1
REQ_FLAG_RESP = 2

# Handshake constants
HANDSHAKE_OBJ_SIZE = 64
HANDSHAKE_ID_MAX = 60
HANDSHAKE_ID_LEN_OFFSET = 60


# ── Message ──────────────────────────────────────────────────────────────

class Message:
    """A parsed ZAP message — a header view over the full buffer.

    The object body is read with the canonical :class:`zap.wire.Object` (via the
    ``obj_*`` helpers below). This wrapper only exposes the 16-byte header fields
    in hanzo-zap's vocabulary (``msg_type``, ``root_offset``, ``total_size``).
    """

    __slots__ = ("_data",)

    def __init__(self, data: bytes | bytearray) -> None:
        self._data = bytes(data)

    @classmethod
    def parse(cls, data: bytes | bytearray) -> "Message":
        if len(data) < HEADER_SIZE:
            raise ValueError(f"ZAP message too short: {len(data)} < {HEADER_SIZE}")
        if data[:4] != ZAP_MAGIC:
            raise ValueError(f"Bad ZAP magic: {data[:4]!r}")
        ver = struct.unpack_from("<H", data, 4)[0]
        if ver not in (VERSION1, VERSION2):
            raise ValueError(
                f"Unsupported ZAP version: {ver} (expected {VERSION1} or {VERSION2})"
            )
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


# ── Object reader (delegates field decode to canonical zap.wire.Object) ──

def obj_uint32(data: bytes, obj_offset: int, field_offset: int) -> int:
    """Read a u32 inline field from the object at ``obj_offset``."""
    return _zw.Object(memoryview(data), obj_offset).uint32(field_offset)


def obj_bytes(data: bytes, obj_offset: int, field_offset: int) -> bytes:
    """Read a Bytes field (relOffset + length) from the object."""
    return _zw.Object(memoryview(data), obj_offset).bytes(field_offset)


def obj_text(data: bytes, obj_offset: int, field_offset: int) -> str:
    """Read a Text field from the object."""
    return _zw.Object(memoryview(data), obj_offset).text(field_offset)


# ── Builder (delegates the codec to canonical zap.wire.Builder) ──────────

class ObjectBuilder:
    """hanzo-zap object builder — wraps :class:`zap.wire.ObjectBuilder`.

    Keeps hanzo-zap's ``set_u32``/``set_u8`` spellings over the canonical
    ``set_uint32``/``set_uint8`` so existing schema code is unchanged.
    """

    __slots__ = ("_ob",)

    def __init__(self, ob: _zw.ObjectBuilder) -> None:
        self._ob = ob

    def set_u32(self, field_offset: int, v: int) -> None:
        self._ob.set_uint32(field_offset, v)

    def set_u8(self, field_offset: int, v: int) -> None:
        self._ob.set_uint8(field_offset, v)

    def set_bytes(self, field_offset: int, data: bytes) -> None:
        self._ob.set_bytes(field_offset, data)

    def set_text(self, field_offset: int, text: str) -> None:
        self._ob.set_text(field_offset, text)

    def finish_as_root(self) -> None:
        self._ob.finish_as_root()


class Builder:
    """hanzo-zap message builder — wraps :class:`zap.wire.Builder`.

    Adds the hanzo ``finish(flags)`` convenience (canonical splits this into
    ``finish`` / ``finish_with_flags``).
    """

    __slots__ = ("_b",)

    def __init__(self, capacity: int = 256) -> None:
        self._b = _zw.Builder(max(capacity, 256))

    def start_object(self, data_size: int) -> ObjectBuilder:
        return ObjectBuilder(self._b.start_object(data_size))

    def finish(self, flags: int = 0) -> bytes:
        return self._b.finish_with_flags(flags) if flags else self._b.finish()


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
