"""Native MCP ImageContent: tools return images the client can *see*.

HIP-0300 tools serialize results to JSON text. That flattened images into
useless base64-in-text. The fix: a ``ToolImage`` value type + one converter in
``BaseTool.register`` that emits a real ``mcp.types.ImageContent`` block for any
image anywhere in a result — while text-only results stay byte-for-byte JSON.

This guards the contract end to end: the converter, and the emitting tools
(fs image read; browser screenshots wire the same ``ToolImage``).
"""

import base64
import struct
import zlib

from hanzo_tools.core import ToolImage
from hanzo_tools.core.unified import _result_to_mcp


def _tiny_png() -> bytes:
    def chunk(t: bytes, d: bytes) -> bytes:
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes((255, 0, 0)) for _ in range(2))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_text_only_result_is_unchanged_json_string():
    out = _result_to_mcp({"ok": True, "data": {"x": 1}, "error": None})
    assert isinstance(out, str)
    assert '"x": 1' in out


def test_image_result_becomes_text_plus_imagecontent():
    from mcp.types import ImageContent, TextContent

    img = ToolImage.from_bytes(_tiny_png(), "image/png", alt="probe")
    out = _result_to_mcp({"ok": True, "data": {"shot": img}, "error": None})

    assert isinstance(out, list) and len(out) == 2
    text, image = out
    assert isinstance(text, TextContent)
    assert isinstance(image, ImageContent)
    assert image.mimeType == "image/png"
    # data is real base64 that decodes back to a PNG
    assert base64.b64decode(image.data)[:8] == b"\x89PNG\r\n\x1a\n"
    # the image bytes never leak into the text — only a compact placeholder
    assert "__image__" in text.text
    assert img.data not in text.text


def test_images_are_collected_recursively():
    from mcp.types import ImageContent

    img = ToolImage.from_bytes(_tiny_png(), "image/png")
    out = _result_to_mcp({"data": {"frames": [img, {"inner": img}]}})
    assert isinstance(out, list)
    assert sum(1 for b in out if isinstance(b, ImageContent)) == 2


def test_fs_read_of_image_emits_toolimage(tmp_path):
    """The fs tool returns image files as a ToolImage (native vision path)."""
    import asyncio

    from hanzo_tools.core import PermissionManager
    from hanzo_tools.fs.fs_tool import FsTool

    png = tmp_path / "probe.png"
    png.write_bytes(_tiny_png())

    pm = PermissionManager()
    pm.add_allowed_path(str(tmp_path))
    tool = FsTool(permission_manager=pm)
    result = asyncio.run(tool.call(None, action="read", uri=str(png)))

    data = result.get("data", result)
    assert isinstance(data.get("image"), ToolImage)
    assert data["mime"] == "image/png"
