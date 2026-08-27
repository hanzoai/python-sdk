"""Tests for hanzo_tools.core.capture — the one way a tool returns a screenshot."""

import base64
from io import BytesIO

import pytest

from hanzo_tools.core import ToolImage, capture
from hanzo_tools.core.unified import _result_to_mcp

PIL = pytest.importorskip("PIL.Image")

#: The size that started this: a 4480x1440 desktop is ~740K base64 chars as PNG.
SCREEN = (4480, 1440)


def png(size=SCREEN) -> bytes:
    """A noisy image — a flat fill would compress away and prove nothing."""
    img = PIL.new("RGB", size)
    img.putdata([((x * 7) % 256, (x * 13) % 256, (x * 29) % 256) for x in range(size[0] * size[1])])
    buf = BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def raw():
    return png()


def test_inline_is_a_bounded_jpeg_and_the_native_capture_is_on_disk(raw, tmp_path):
    out = capture(raw, fmt="png", path=str(tmp_path / "shot.png"))
    img = out["image"]

    assert isinstance(img, ToolImage) and img.mime_type == "image/jpeg"
    assert len(base64.b64decode(img.data)) < 150_000
    assert out["preview"]["width"] == 1280
    assert (out["width"], out["height"]) == SCREEN
    # The full-resolution capture is a file read away, byte for byte.
    assert (tmp_path / "shot.png").read_bytes() == raw
    assert out["path"] == str(tmp_path / "shot.png")


def test_full_res_inlines_the_native_capture(raw):
    out = capture(raw, fmt="png", full_res=True)
    assert out["image"].mime_type == "image/png"
    assert base64.b64decode(out["image"].data) == raw
    # max_width=0 is the same door.
    assert base64.b64decode(capture(raw, fmt="png", max_width=0)["image"].data) == raw


def test_max_width_and_quality_are_the_dials(raw):
    small = capture(raw, fmt="png", max_width=320, quality=40)
    assert small["preview"]["width"] == 320
    assert len(base64.b64decode(small["image"].data)) < len(
        base64.b64decode(capture(raw, fmt="png")["image"].data)
    )


def test_a_capture_smaller_than_the_box_keeps_its_size(raw):
    out = capture(png((400, 300)), fmt="png")
    assert (out["preview"]["width"], out["preview"]["height"]) == (400, 300)


def test_a_pdf_is_saved_never_inlined(tmp_path):
    out = capture(b"%PDF-1.4\n", fmt="pdf", path=str(tmp_path / "doc.pdf"))
    assert "image" not in out
    assert (tmp_path / "doc.pdf").read_bytes() == b"%PDF-1.4\n"


def test_the_wire_carries_pixels_not_base64_text(raw):
    blocks = _result_to_mcp(capture(raw, fmt="png"))
    kinds = [b.type for b in blocks]
    assert kinds == ["text", "image"]
    assert blocks[1].mimeType == "image/jpeg"
    # The JSON text an agent reads stays a few hundred characters.
    assert len(blocks[0].text) < 1000
    assert "base64" not in blocks[0].text
