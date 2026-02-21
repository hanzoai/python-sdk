"""Media processing tool for Hanzo AI.

Handles images and video with configurable limits optimized for Claude's vision API:
- Up to 100 images per invocation (configurable)
- Combined payload under 32 MB (configurable)
- Per-image resolution constraints (configurable)
- Automatic optimization for Claude vision
- INTELLIGENT VIDEO SLICING with activity detection
- Computer use session compression

Limits based on Claude API constraints:
- Max 100 images per request
- Max 32 MB total payload
- Recommended 768-1568px for best quality/speed tradeoff
- Supports PNG, JPEG, GIF, WebP

Activity Detection:
- Frame differencing for movement detection
- Scene change detection via FFmpeg
- Configurable sensitivity threshold
- Only extracts frames during activity periods

Environment configuration:
- HANZO_MEDIA_MAX_IMAGES: Max images per batch (default: 100)
- HANZO_MEDIA_MAX_PAYLOAD_MB: Max total payload in MB (default: 32)
- HANZO_MEDIA_MAX_RESOLUTION: Max image dimension (default: 1568)
- HANZO_MEDIA_JPEG_QUALITY: JPEG quality 1-100 (default: 85)
- HANZO_MEDIA_OPTIMAL_SIZE: Target size for optimization (default: 768)
- HANZO_MEDIA_ACTIVITY_THRESHOLD: Activity detection sensitivity (default: 0.02)
"""

import io
import os
import sys
import json
import base64
import asyncio
import hashlib
import mimetypes
from typing import Any, Union, Literal, Optional, Annotated, final, override
from pathlib import Path
from dataclasses import field, dataclass
from concurrent.futures import ThreadPoolExecutor

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, PermissionManager, auto_timeout

# Thread pool for blocking I/O
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="media_")


@dataclass
class MediaLimits:
    """Configurable limits for media processing."""

    # Image limits
    max_images: int = 100  # Max images per batch
    max_payload_mb: float = 32.0  # Max total payload in MB
    max_resolution: int = 1568  # Max dimension (width or height)
    min_resolution: int = 10  # Min dimension

    # Optimization settings
    optimal_size: int = 768  # Target size for optimization
    jpeg_quality: int = 85  # JPEG quality (1-100)

    # Video limits
    max_frames: int = 100  # Max video frames per extraction
    max_fps: int = 30  # Max frame rate for extraction

    # Activity detection settings
    activity_threshold: float = 0.02  # % of pixels changed to count as activity (0.01-0.10)
    min_activity_gap_ms: int = 200  # Min ms between activity frames
    scene_change_threshold: float = 0.3  # FFmpeg scene change threshold

    # Session compression settings
    session_max_duration: int = 60  # Max session duration in seconds
    session_target_frames: int = 30  # Target frames for session summary
    session_compression_quality: int = 60  # Aggressive compression for sessions

    # Hard limits (Claude API constraints for multi-image requests)
    HARD_MAX_RESOLUTION: int = 2000  # Claude's actual limit
    HARD_MAX_IMAGES: int = 100
    HARD_MAX_PAYLOAD_MB: float = 32.0

    @classmethod
    def from_env(cls) -> "MediaLimits":
        """Load limits from environment variables with hard cap enforcement."""
        return cls(
            max_images=min(
                int(os.environ.get("HANZO_MEDIA_MAX_IMAGES", "100")),
                cls.HARD_MAX_IMAGES,
            ),
            max_payload_mb=min(
                float(os.environ.get("HANZO_MEDIA_MAX_PAYLOAD_MB", "32")),
                cls.HARD_MAX_PAYLOAD_MB,
            ),
            max_resolution=min(
                int(os.environ.get("HANZO_MEDIA_MAX_RESOLUTION", "1568")),
                cls.HARD_MAX_RESOLUTION,  # Claude 2000px limit for multi-image
            ),
            optimal_size=min(
                int(os.environ.get("HANZO_MEDIA_OPTIMAL_SIZE", "768")),
                cls.HARD_MAX_RESOLUTION,
            ),
            jpeg_quality=int(os.environ.get("HANZO_MEDIA_JPEG_QUALITY", "85")),
            max_frames=min(
                int(os.environ.get("HANZO_MEDIA_MAX_FRAMES", "100")),
                cls.HARD_MAX_IMAGES,
            ),
            activity_threshold=float(os.environ.get("HANZO_MEDIA_ACTIVITY_THRESHOLD", "0.02")),
            min_activity_gap_ms=int(os.environ.get("HANZO_MEDIA_MIN_ACTIVITY_GAP_MS", "200")),
            scene_change_threshold=float(os.environ.get("HANZO_MEDIA_SCENE_THRESHOLD", "0.3")),
            session_max_duration=int(os.environ.get("HANZO_MEDIA_SESSION_MAX_DURATION", "60")),
            session_target_frames=min(
                int(os.environ.get("HANZO_MEDIA_SESSION_TARGET_FRAMES", "30")),
                cls.HARD_MAX_IMAGES,
            ),
            session_compression_quality=int(os.environ.get("HANZO_MEDIA_SESSION_QUALITY", "60")),
        )

    @property
    def max_payload_bytes(self) -> int:
        return int(self.max_payload_mb * 1024 * 1024)


@dataclass
class MediaResult:
    """Result of media processing."""

    success: bool
    images: list[dict] = field(default_factory=list)
    total_size: int = 0
    total_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "total_count": self.total_count,
            "total_size_bytes": self.total_size,
            "total_size_mb": round(self.total_size / (1024 * 1024), 2),
            "images": self.images,
            "errors": self.errors if self.errors else None,
            "warnings": self.warnings if self.warnings else None,
        }


def _get_image_info(data: bytes) -> dict:
    """Get image info without full decode."""
    info = {"size": len(data), "format": "unknown"}

    # Detect format from magic bytes
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        info["format"] = "png"
    elif data[:2] == b"\xff\xd8":
        info["format"] = "jpeg"
    elif data[:6] in (b"GIF87a", b"GIF89a"):
        info["format"] = "gif"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        info["format"] = "webp"

    return info


def _resize_image(
    data: bytes,
    max_size: int,
    quality: int = 85,
    force_jpeg: bool = False,
) -> tuple[bytes, dict]:
    """Resize image and optionally convert to JPEG.

    Returns: (processed_data, info_dict)
    """
    try:
        from PIL import Image
    except ImportError:
        return data, {"error": "PIL not available", "original_size": len(data)}

    img = Image.open(io.BytesIO(data))
    original_size = img.size
    original_mode = img.mode

    # Calculate new size maintaining aspect ratio
    width, height = img.size
    needs_resize = max(width, height) > max_size

    if needs_resize:
        ratio = max_size / max(width, height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Determine output format
    info = _get_image_info(data)
    output_format = info["format"].upper()

    # Convert to JPEG if requested or if PNG is too large
    if force_jpeg or (output_format == "PNG" and len(data) > 500_000):
        output_format = "JPEG"
        if img.mode in ("RGBA", "P", "LA"):
            # Convert transparency to white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

    # Save to buffer
    buffer = io.BytesIO()
    save_kwargs = {}

    if output_format == "JPEG":
        save_kwargs = {"quality": quality, "optimize": True}
    elif output_format == "PNG":
        save_kwargs = {"optimize": True}
    elif output_format == "WEBP":
        save_kwargs = {"quality": quality}

    try:
        img.save(buffer, format=output_format, **save_kwargs)
    except Exception:
        # Fallback to JPEG
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        output_format = "JPEG"

    result = buffer.getvalue()

    return result, {
        "original_size": len(data),
        "processed_size": len(result),
        "original_dimensions": original_size,
        "new_dimensions": img.size,
        "format": output_format.lower(),
        "resized": needs_resize,
    }


def _extract_video_frames(
    video_path: str,
    count: int = 10,
    interval_ms: int = 1000,
    max_size: int = 768,
) -> list[tuple[bytes, dict]]:
    """Extract frames from video file."""
    import tempfile
    import subprocess

    frames = []

    # Get video duration
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        duration = float(result.stdout.strip())
    except Exception:
        duration = 60.0  # Default assumption

    # Calculate frame times
    interval_sec = interval_ms / 1000
    total_time = min(duration, count * interval_sec)

    for i in range(count):
        timestamp = i * interval_sec
        if timestamp >= duration:
            break

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            tmp_path = f.name

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                video_path,
                "-frames:v",
                "1",
                "-vf",
                f"scale='min({max_size},iw)':min'({max_size},ih)':force_original_aspect_ratio=decrease",
                "-q:v",
                "2",
                tmp_path,
            ]

            subprocess.run(cmd, capture_output=True, timeout=10)

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, "rb") as f:
                    data = f.read()
                frames.append(
                    (
                        data,
                        {
                            "timestamp_ms": int(timestamp * 1000),
                            "frame_index": i,
                            "size": len(data),
                            "format": "jpeg",
                        },
                    )
                )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return frames


@dataclass
class ActivitySegment:
    """A detected activity segment in video."""

    start_ms: int
    end_ms: int
    activity_score: float  # 0-1, how much activity
    frame_count: int
    description: str = ""


def _detect_scene_changes(
    video_path: str,
    threshold: float = 0.3,
    max_duration: int = 60,
) -> list[float]:
    """Detect scene changes using FFmpeg.

    Returns list of timestamps (in seconds) where scenes change.
    """
    import subprocess

    # Use FFmpeg scene detection filter
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-show_entries",
        "frame=pts_time",
        "-select_streams",
        "v:0",
        "-of",
        "csv=p=0",
        "-f",
        "lavfi",
        f"movie={video_path},select='gt(scene,{threshold})'",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        timestamps = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    ts = float(line)
                    if ts <= max_duration:
                        timestamps.append(ts)
                except ValueError:
                    continue
        return timestamps
    except Exception:
        return []


def _compute_frame_difference(
    frame1_data: bytes,
    frame2_data: bytes,
    threshold: float = 0.02,
) -> tuple[float, bool]:
    """Compute difference between two frames.

    Returns (difference_ratio, has_significant_activity).
    difference_ratio is 0-1 representing % of pixels that changed.
    """
    try:
        import numpy as np
        from PIL import Image, ImageChops
    except ImportError:
        return 0.0, False

    try:
        img1 = Image.open(io.BytesIO(frame1_data)).convert("L")  # Grayscale
        img2 = Image.open(io.BytesIO(frame2_data)).convert("L")

        # Ensure same size
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)

        # Compute difference
        diff = ImageChops.difference(img1, img2)

        # Count pixels above threshold
        diff_array = np.array(diff)
        changed_pixels = np.sum(diff_array > 10)  # Pixel value threshold
        total_pixels = diff_array.size

        ratio = changed_pixels / total_pixels if total_pixels > 0 else 0

        return ratio, ratio > threshold

    except Exception:
        return 0.0, False


def _analyze_video_activity(
    video_path: str,
    activity_threshold: float = 0.02,
    sample_fps: float = 2.0,
    max_duration: int = 60,
    scene_threshold: float = 0.3,
) -> tuple[list[ActivitySegment], list[float]]:
    """Analyze video for activity segments.

    Returns (activity_segments, keyframe_timestamps).

    Combines:
    1. Scene change detection (FFmpeg)
    2. Frame differencing (PIL)
    3. Activity clustering
    """
    import tempfile
    import subprocess

    segments = []
    keyframe_times = []

    # Get video duration
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        duration = min(float(result.stdout.strip()), max_duration)
    except Exception:
        duration = max_duration

    # Get scene changes
    scene_changes = _detect_scene_changes(video_path, scene_threshold, max_duration)
    keyframe_times.extend(scene_changes)

    # Sample frames for activity detection
    sample_interval = 1.0 / sample_fps
    num_samples = int(duration * sample_fps)

    prev_frame = None
    activity_frames = []

    for i in range(num_samples):
        timestamp = i * sample_interval
        if timestamp > duration:
            break

        # Extract frame
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            tmp_path = f.name

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                video_path,
                "-frames:v",
                "1",
                "-vf",
                "scale=320:-1",  # Small for comparison
                "-q:v",
                "5",
                tmp_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, "rb") as f:
                    frame_data = f.read()

                if prev_frame is not None:
                    diff_ratio, has_activity = _compute_frame_difference(prev_frame, frame_data, activity_threshold)
                    if has_activity:
                        activity_frames.append(
                            {
                                "timestamp": timestamp,
                                "diff_ratio": diff_ratio,
                            }
                        )
                        if timestamp not in keyframe_times:
                            keyframe_times.append(timestamp)

                prev_frame = frame_data

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Cluster activity into segments
    if activity_frames:
        current_segment_start = activity_frames[0]["timestamp"]
        current_segment_score = activity_frames[0]["diff_ratio"]
        segment_frame_count = 1

        for frame in activity_frames[1:]:
            # If gap > 1 second, start new segment
            if frame["timestamp"] - current_segment_start > 1.0 + segment_frame_count * sample_interval:
                segments.append(
                    ActivitySegment(
                        start_ms=int(current_segment_start * 1000),
                        end_ms=int((current_segment_start + segment_frame_count * sample_interval) * 1000),
                        activity_score=current_segment_score / segment_frame_count,
                        frame_count=segment_frame_count,
                    )
                )
                current_segment_start = frame["timestamp"]
                current_segment_score = frame["diff_ratio"]
                segment_frame_count = 1
            else:
                current_segment_score += frame["diff_ratio"]
                segment_frame_count += 1

        # Last segment
        segments.append(
            ActivitySegment(
                start_ms=int(current_segment_start * 1000),
                end_ms=int((current_segment_start + segment_frame_count * sample_interval) * 1000),
                activity_score=current_segment_score / segment_frame_count,
                frame_count=segment_frame_count,
            )
        )

    # Sort and deduplicate keyframe times
    keyframe_times = sorted(set(keyframe_times))

    return segments, keyframe_times


def _extract_activity_frames(
    video_path: str,
    keyframe_times: list[float],
    max_frames: int = 30,
    max_size: int = 512,
    quality: int = 60,
) -> list[tuple[bytes, dict]]:
    """Extract frames at specified timestamps with heavy compression.

    Optimized for minimal payload size.
    """
    import tempfile
    import subprocess

    frames = []

    # Limit frames
    if len(keyframe_times) > max_frames:
        # Sample evenly
        step = len(keyframe_times) / max_frames
        keyframe_times = [keyframe_times[int(i * step)] for i in range(max_frames)]

    for timestamp in keyframe_times:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            tmp_path = f.name

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                video_path,
                "-frames:v",
                "1",
                "-vf",
                f"scale='min({max_size},iw)':'min({max_size},ih)':force_original_aspect_ratio=decrease",
                "-q:v",
                str(max(1, min(31, (100 - quality) // 3))),  # FFmpeg quality 1-31
                tmp_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=10)

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, "rb") as f:
                    data = f.read()

                frames.append(
                    (
                        data,
                        {
                            "timestamp_ms": int(timestamp * 1000),
                            "timestamp_sec": round(timestamp, 2),
                            "size": len(data),
                            "format": "jpeg",
                        },
                    )
                )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return frames


def _compress_session(
    video_path: str,
    max_duration: int = 60,
    target_frames: int = 30,
    activity_threshold: float = 0.02,
    scene_threshold: float = 0.3,
    max_size: int = 512,
    quality: int = 60,
) -> tuple[list[tuple[bytes, dict]], list[ActivitySegment], dict]:
    """Full pipeline: analyze → slice → compress a computer use session.

    Returns (frames, activity_segments, metadata).
    """
    # Analyze video
    segments, keyframe_times = _analyze_video_activity(
        video_path,
        activity_threshold=activity_threshold,
        max_duration=max_duration,
        scene_threshold=scene_threshold,
    )

    # If no activity detected, sample evenly
    if not keyframe_times:
        import subprocess

        probe_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            duration = min(float(result.stdout.strip()), max_duration)
        except Exception:
            duration = max_duration

        interval = duration / target_frames
        keyframe_times = [i * interval for i in range(target_frames)]

    # Extract frames at activity points
    frames = _extract_activity_frames(
        video_path,
        keyframe_times,
        max_frames=target_frames,
        max_size=max_size,
        quality=quality,
    )

    # Compute metadata
    total_size = sum(len(f[0]) for f in frames)
    metadata = {
        "source": video_path,
        "activity_segments": len(segments),
        "keyframes_detected": len(keyframe_times),
        "frames_extracted": len(frames),
        "total_size_bytes": total_size,
        "total_size_kb": round(total_size / 1024, 1),
        "avg_frame_size_kb": round(total_size / len(frames) / 1024, 1) if frames else 0,
        "compression_settings": {
            "max_size": max_size,
            "quality": quality,
        },
    }

    return frames, segments, metadata


Action = Literal[
    # Image operations
    "load",  # Load single image
    "load_batch",  # Load multiple images
    "optimize",  # Optimize images for Claude
    "resize",  # Resize images
    "info",  # Get image info
    # Video operations
    "extract_frames",  # Extract frames from video
    # Activity detection & slicing (NEW)
    "analyze",  # Detect activity segments in video
    "slice",  # Extract frames at activity points only
    "compress_session",  # Full pipeline for computer use sessions
    # Configuration
    "limits",  # Get/set limits
    "status",  # Get current status
]


@final
class MediaTool(BaseTool):
    """Media processing tool with configurable limits.

    Handles images and video optimized for Claude's vision API:
    - Up to 100 images per batch (configurable)
    - Max 32 MB total payload (configurable)
    - Automatic resizing and optimization
    - Video frame extraction
    """

    name = "media"

    def __init__(
        self,
        permission_manager: Optional[PermissionManager] = None,
        limits: Optional[MediaLimits] = None,
    ):
        if permission_manager is None:
            permission_manager = PermissionManager()
        self.permission_manager = permission_manager
        self.limits = limits or MediaLimits.from_env()

    @property
    @override
    def description(self) -> str:
        return f"""Media processing optimized for Claude vision API.

LIMITS (configurable via env vars):
  Max images per batch: {self.limits.max_images}
  Max payload: {self.limits.max_payload_mb} MB
  Max resolution: {self.limits.max_resolution}px
  Optimal size: {self.limits.optimal_size}px
  JPEG quality: {self.limits.jpeg_quality}%

ACTIONS:

load: Load and optimize a single image
  - path: Image file path
  - optimize: Auto-optimize for Claude (default: true)
  - max_size: Max dimension (default: {self.limits.optimal_size})

load_batch: Load multiple images with limits enforcement
  - paths: List of image file paths
  - optimize: Auto-optimize all (default: true)
  - max_size: Max dimension per image
  - Returns up to {self.limits.max_images} images, max {self.limits.max_payload_mb}MB total

optimize: Optimize images for Claude vision
  - images: List of base64 images or file paths
  - max_size: Target size (default: {self.limits.optimal_size})
  - quality: JPEG quality 1-100 (default: {self.limits.jpeg_quality})

resize: Resize images to specific dimensions
  - images: List of base64 images or file paths
  - width: Target width (or max dimension if height not set)
  - height: Target height (optional)
  - maintain_aspect: Keep aspect ratio (default: true)

extract_frames: Extract frames from video
  - path: Video file path
  - count: Number of frames (max {self.limits.max_frames})
  - interval_ms: Time between frames (default: 1000)
  - optimize: Optimize frames for Claude (default: true)

analyze: Detect activity segments in video (movement, scene changes)
  - path: Video file path
  - activity_threshold: Sensitivity 0.01-0.10 (default: {self.limits.activity_threshold})
  - scene_threshold: Scene change sensitivity (default: {self.limits.scene_change_threshold})
  - max_duration: Max seconds to analyze (default: {self.limits.session_max_duration})
  - Returns activity segments with timestamps and scores

slice: Extract frames ONLY at activity points
  - path: Video file path
  - target_frames: Max frames to extract (default: {self.limits.session_target_frames})
  - activity_threshold: Sensitivity (default: {self.limits.activity_threshold})
  - max_size: Frame dimension (default: 512 for compression)
  - quality: JPEG quality (default: {self.limits.session_compression_quality})

compress_session: FULL PIPELINE for computer use video
  - path: Video file path (e.g., 30-second screen recording)
  - target_frames: Max frames (default: {self.limits.session_target_frames})
  - max_size: Frame dimension (default: 512)
  - quality: Compression quality (default: {self.limits.session_compression_quality})
  - Returns compressed keyframes + activity analysis for Claude interpretation

info: Get image/video info without loading full data
  - path: File path

limits: Get or update processing limits
  - max_images: New max images (optional)
  - max_payload_mb: New max payload (optional)
  - max_resolution: New max resolution (optional)

status: Get current configuration and stats

ENVIRONMENT VARIABLES:
  HANZO_MEDIA_MAX_IMAGES={self.limits.max_images}
  HANZO_MEDIA_MAX_PAYLOAD_MB={self.limits.max_payload_mb}
  HANZO_MEDIA_MAX_RESOLUTION={self.limits.max_resolution}
  HANZO_MEDIA_OPTIMAL_SIZE={self.limits.optimal_size}
  HANZO_MEDIA_JPEG_QUALITY={self.limits.jpeg_quality}
  HANZO_MEDIA_ACTIVITY_THRESHOLD={self.limits.activity_threshold}
  HANZO_MEDIA_SESSION_TARGET_FRAMES={self.limits.session_target_frames}
  HANZO_MEDIA_SESSION_QUALITY={self.limits.session_compression_quality}

EXAMPLES:
  media(action="load", path="screenshot.png")
  media(action="load_batch", paths=["img1.png", "img2.jpg", "img3.webp"])
  media(action="extract_frames", path="video.mp4", count=20, interval_ms=500)
  media(action="analyze", path="session.mp4")  # Detect activity
  media(action="slice", path="session.mp4", target_frames=30)  # Activity frames only
  media(action="compress_session", path="recording.mp4")  # Full pipeline for Claude
  media(action="limits", max_images=50, max_payload_mb=16)
"""

    async def _load_image(
        self,
        path: str,
        optimize: bool = True,
        max_size: Optional[int] = None,
    ) -> tuple[Optional[bytes], dict]:
        """Load and optionally optimize a single image."""
        loop = asyncio.get_event_loop()
        max_size = max_size or self.limits.optimal_size

        if not os.path.exists(path):
            return None, {"error": f"File not found: {path}"}

        try:
            # Read file
            def read_file():
                with open(path, "rb") as f:
                    return f.read()

            data = await loop.run_in_executor(_EXECUTOR, read_file)
            info = _get_image_info(data)
            info["path"] = path
            info["original_size"] = len(data)

            if optimize:
                data, opt_info = await loop.run_in_executor(
                    _EXECUTOR,
                    _resize_image,
                    data,
                    max_size,
                    self.limits.jpeg_quality,
                    False,
                )
                info.update(opt_info)

            return data, info

        except Exception as e:
            return None, {"error": str(e), "path": path}

    async def _load_batch(
        self,
        paths: list[str],
        optimize: bool = True,
        max_size: Optional[int] = None,
    ) -> MediaResult:
        """Load multiple images with limits enforcement."""
        result = MediaResult(success=True)
        max_size = max_size or self.limits.optimal_size

        # Enforce max images limit
        if len(paths) > self.limits.max_images:
            result.warnings.append(f"Requested {len(paths)} images, limited to {self.limits.max_images}")
            paths = paths[: self.limits.max_images]

        for path in paths:
            # Check payload limit
            if result.total_size >= self.limits.max_payload_bytes:
                result.warnings.append(
                    f"Payload limit ({self.limits.max_payload_mb}MB) reached, stopped at {result.total_count} images"
                )
                break

            data, info = await self._load_image(path, optimize, max_size)

            if data is None:
                result.errors.append(info.get("error", f"Failed to load {path}"))
                continue

            # Check if this image would exceed payload
            if result.total_size + len(data) > self.limits.max_payload_bytes:
                result.warnings.append(f"Skipping {path}: would exceed payload limit")
                continue

            result.images.append(
                {
                    "path": path,
                    "size": len(data),
                    "format": info.get("format", "unknown"),
                    "dimensions": info.get("new_dimensions", info.get("original_dimensions")),
                    "base64": base64.b64encode(data).decode(),
                    **{k: v for k, v in info.items() if k not in ("path", "base64")},
                }
            )
            result.total_size += len(data)
            result.total_count += 1

        if result.errors and not result.images:
            result.success = False

        return result

    @override
    @auto_timeout("media")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "status",
        # File paths
        path: Optional[str] = None,
        paths: Optional[list[str]] = None,
        # Image data
        images: Optional[list[str]] = None,  # base64 or paths
        # Processing options
        optimize: bool = True,
        max_size: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        maintain_aspect: bool = True,
        quality: Optional[int] = None,
        # Video options
        count: int = 10,
        interval_ms: int = 1000,
        # Limit updates
        max_images: Optional[int] = None,
        max_payload_mb: Optional[float] = None,
        max_resolution: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Execute media action."""
        loop = asyncio.get_event_loop()
        quality = quality or self.limits.jpeg_quality
        max_size = max_size or self.limits.optimal_size

        try:
            if action == "status":
                return json.dumps(
                    {
                        "limits": {
                            "max_images": self.limits.max_images,
                            "max_payload_mb": self.limits.max_payload_mb,
                            "max_resolution": self.limits.max_resolution,
                            "optimal_size": self.limits.optimal_size,
                            "jpeg_quality": self.limits.jpeg_quality,
                            "max_frames": self.limits.max_frames,
                        },
                        "env_vars": {
                            "HANZO_MEDIA_MAX_IMAGES": os.environ.get("HANZO_MEDIA_MAX_IMAGES"),
                            "HANZO_MEDIA_MAX_PAYLOAD_MB": os.environ.get("HANZO_MEDIA_MAX_PAYLOAD_MB"),
                            "HANZO_MEDIA_MAX_RESOLUTION": os.environ.get("HANZO_MEDIA_MAX_RESOLUTION"),
                            "HANZO_MEDIA_OPTIMAL_SIZE": os.environ.get("HANZO_MEDIA_OPTIMAL_SIZE"),
                            "HANZO_MEDIA_JPEG_QUALITY": os.environ.get("HANZO_MEDIA_JPEG_QUALITY"),
                        },
                    }
                )

            elif action == "limits":
                # Update limits if provided
                if max_images is not None:
                    self.limits.max_images = min(max_images, 100)  # Hard cap at 100
                if max_payload_mb is not None:
                    self.limits.max_payload_mb = min(max_payload_mb, 32.0)  # Hard cap at 32MB
                if max_resolution is not None:
                    self.limits.max_resolution = min(max_resolution, 4096)  # Hard cap

                return json.dumps(
                    {
                        "success": True,
                        "limits": {
                            "max_images": self.limits.max_images,
                            "max_payload_mb": self.limits.max_payload_mb,
                            "max_resolution": self.limits.max_resolution,
                            "optimal_size": self.limits.optimal_size,
                            "jpeg_quality": self.limits.jpeg_quality,
                        },
                    }
                )

            elif action == "load":
                if not path:
                    return json.dumps({"error": "path required"})

                data, info = await self._load_image(path, optimize, max_size)

                if data is None:
                    return json.dumps({"success": False, **info})

                return json.dumps(
                    {
                        "success": True,
                        "path": path,
                        "size": len(data),
                        "format": info.get("format", "unknown"),
                        "dimensions": info.get("new_dimensions", info.get("original_dimensions")),
                        "base64": base64.b64encode(data).decode(),
                        **{k: v for k, v in info.items() if k not in ("path", "base64")},
                    }
                )

            elif action == "load_batch":
                if not paths:
                    return json.dumps({"error": "paths required (list of file paths)"})

                result = await self._load_batch(paths, optimize, max_size)
                return json.dumps(result.to_dict())

            elif action == "optimize":
                if not images:
                    return json.dumps({"error": "images required (list of base64 or paths)"})

                result = MediaResult(success=True)

                for i, img in enumerate(images):
                    if result.total_count >= self.limits.max_images:
                        result.warnings.append(f"Max images ({self.limits.max_images}) reached")
                        break

                    if result.total_size >= self.limits.max_payload_bytes:
                        result.warnings.append(f"Payload limit reached")
                        break

                    try:
                        # Determine if base64 or path
                        if os.path.exists(img):
                            with open(img, "rb") as f:
                                data = f.read()
                            source = img
                        else:
                            data = base64.b64decode(img)
                            source = f"image_{i}"

                        # Optimize
                        optimized, info = await loop.run_in_executor(
                            _EXECUTOR,
                            _resize_image,
                            data,
                            max_size,
                            quality,
                            True,  # Force JPEG for optimization
                        )

                        if result.total_size + len(optimized) > self.limits.max_payload_bytes:
                            result.warnings.append(f"Skipping {source}: would exceed limit")
                            continue

                        result.images.append(
                            {
                                "index": i,
                                "source": source,
                                "size": len(optimized),
                                "format": info.get("format", "jpeg"),
                                "dimensions": info.get("new_dimensions"),
                                "compression_ratio": round(info.get("original_size", len(data)) / len(optimized), 2),
                                "base64": base64.b64encode(optimized).decode(),
                            }
                        )
                        result.total_size += len(optimized)
                        result.total_count += 1

                    except Exception as e:
                        result.errors.append(f"Image {i}: {str(e)}")

                if result.errors and not result.images:
                    result.success = False

                return json.dumps(result.to_dict())

            elif action == "resize":
                if not images:
                    return json.dumps({"error": "images required"})

                if not width and not height:
                    return json.dumps({"error": "width or height required"})

                result = MediaResult(success=True)
                target_size = width or height or self.limits.optimal_size

                for i, img in enumerate(images):
                    try:
                        if os.path.exists(img):
                            with open(img, "rb") as f:
                                data = f.read()
                        else:
                            data = base64.b64decode(img)

                        resized, info = await loop.run_in_executor(
                            _EXECUTOR,
                            _resize_image,
                            data,
                            target_size,
                            quality,
                            False,
                        )

                        result.images.append(
                            {
                                "index": i,
                                "size": len(resized),
                                "dimensions": info.get("new_dimensions"),
                                "format": info.get("format"),
                                "base64": base64.b64encode(resized).decode(),
                            }
                        )
                        result.total_size += len(resized)
                        result.total_count += 1

                    except Exception as e:
                        result.errors.append(f"Image {i}: {str(e)}")

                return json.dumps(result.to_dict())

            elif action == "extract_frames":
                if not path:
                    return json.dumps({"error": "path required (video file)"})

                if not os.path.exists(path):
                    return json.dumps({"error": f"File not found: {path}"})

                # Enforce limits
                actual_count = min(count, self.limits.max_frames, self.limits.max_images)

                frames = await loop.run_in_executor(
                    _EXECUTOR,
                    _extract_video_frames,
                    path,
                    actual_count,
                    interval_ms,
                    max_size,
                )

                result = MediaResult(success=True)

                for data, info in frames:
                    if result.total_size + len(data) > self.limits.max_payload_bytes:
                        result.warnings.append("Payload limit reached, stopped extraction")
                        break

                    result.images.append(
                        {
                            "frame_index": info["frame_index"],
                            "timestamp_ms": info["timestamp_ms"],
                            "size": len(data),
                            "format": info["format"],
                            "base64": base64.b64encode(data).decode(),
                        }
                    )
                    result.total_size += len(data)
                    result.total_count += 1

                return json.dumps(
                    {
                        **result.to_dict(),
                        "source": path,
                        "interval_ms": interval_ms,
                        "frames_extracted": result.total_count,
                    }
                )

            elif action == "info":
                if not path:
                    return json.dumps({"error": "path required"})

                if not os.path.exists(path):
                    return json.dumps({"error": f"File not found: {path}"})

                # Get file info without loading entire file
                stat = os.stat(path)
                mime_type, _ = mimetypes.guess_type(path)

                info = {
                    "path": path,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "mime_type": mime_type,
                }

                # Get image dimensions if possible
                try:
                    from PIL import Image

                    with Image.open(path) as img:
                        info["dimensions"] = img.size
                        info["format"] = img.format
                        info["mode"] = img.mode
                except Exception:
                    pass

                # Check if video
                if mime_type and mime_type.startswith("video/"):
                    info["type"] = "video"
                    try:
                        import subprocess

                        probe = subprocess.run(
                            [
                                "ffprobe",
                                "-v",
                                "error",
                                "-show_entries",
                                "format=duration:stream=width,height,r_frame_rate",
                                "-of",
                                "json",
                                path,
                            ],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        if probe.returncode == 0:
                            probe_data = json.loads(probe.stdout)
                            if "format" in probe_data:
                                info["duration_seconds"] = float(probe_data["format"].get("duration", 0))
                            if "streams" in probe_data and probe_data["streams"]:
                                stream = probe_data["streams"][0]
                                info["dimensions"] = (stream.get("width"), stream.get("height"))
                                info["frame_rate"] = stream.get("r_frame_rate")
                    except Exception:
                        pass
                else:
                    info["type"] = "image"

                return json.dumps(info)

            elif action == "analyze":
                if not path:
                    return json.dumps({"error": "path required (video file)"})

                if not os.path.exists(path):
                    return json.dumps({"error": f"File not found: {path}"})

                # Get optional params from kwargs
                activity_threshold = kwargs.get("activity_threshold", self.limits.activity_threshold)
                scene_threshold = kwargs.get("scene_threshold", self.limits.scene_change_threshold)
                max_duration = kwargs.get("max_duration", self.limits.session_max_duration)

                segments, keyframe_times = await loop.run_in_executor(
                    _EXECUTOR,
                    _analyze_video_activity,
                    path,
                    activity_threshold,
                    2.0,  # sample_fps
                    max_duration,
                    scene_threshold,
                )

                return json.dumps(
                    {
                        "success": True,
                        "source": path,
                        "activity_segments": [
                            {
                                "start_ms": s.start_ms,
                                "end_ms": s.end_ms,
                                "duration_ms": s.end_ms - s.start_ms,
                                "activity_score": round(s.activity_score, 4),
                                "frame_count": s.frame_count,
                            }
                            for s in segments
                        ],
                        "keyframe_count": len(keyframe_times),
                        "keyframe_times_sec": [round(t, 2) for t in keyframe_times],
                        "settings": {
                            "activity_threshold": activity_threshold,
                            "scene_threshold": scene_threshold,
                            "max_duration": max_duration,
                        },
                    }
                )

            elif action == "slice":
                if not path:
                    return json.dumps({"error": "path required (video file)"})

                if not os.path.exists(path):
                    return json.dumps({"error": f"File not found: {path}"})

                # Get params
                target_frames = kwargs.get("target_frames", self.limits.session_target_frames)
                activity_threshold = kwargs.get("activity_threshold", self.limits.activity_threshold)
                scene_threshold = kwargs.get("scene_threshold", self.limits.scene_change_threshold)
                max_duration = kwargs.get("max_duration", self.limits.session_max_duration)
                slice_max_size = kwargs.get("max_size", 512)  # Smaller default for compression
                slice_quality = kwargs.get("quality", self.limits.session_compression_quality)

                # First analyze
                segments, keyframe_times = await loop.run_in_executor(
                    _EXECUTOR,
                    _analyze_video_activity,
                    path,
                    activity_threshold,
                    2.0,
                    max_duration,
                    scene_threshold,
                )

                # Then extract at activity points
                frames = await loop.run_in_executor(
                    _EXECUTOR,
                    _extract_activity_frames,
                    path,
                    keyframe_times,
                    target_frames,
                    slice_max_size,
                    slice_quality,
                )

                result = MediaResult(success=True)

                for data, info in frames:
                    if result.total_size + len(data) > self.limits.max_payload_bytes:
                        result.warnings.append("Payload limit reached")
                        break

                    result.images.append(
                        {
                            "timestamp_sec": info["timestamp_sec"],
                            "timestamp_ms": info["timestamp_ms"],
                            "size": len(data),
                            "format": info["format"],
                            "base64": base64.b64encode(data).decode(),
                        }
                    )
                    result.total_size += len(data)
                    result.total_count += 1

                return json.dumps(
                    {
                        **result.to_dict(),
                        "source": path,
                        "activity_segments": len(segments),
                        "keyframes_detected": len(keyframe_times),
                        "compression_settings": {
                            "max_size": slice_max_size,
                            "quality": slice_quality,
                        },
                    }
                )

            elif action == "compress_session":
                if not path:
                    return json.dumps({"error": "path required (video file)"})

                if not os.path.exists(path):
                    return json.dumps({"error": f"File not found: {path}"})

                # Get params
                target_frames = kwargs.get("target_frames", self.limits.session_target_frames)
                activity_threshold = kwargs.get("activity_threshold", self.limits.activity_threshold)
                scene_threshold = kwargs.get("scene_threshold", self.limits.scene_change_threshold)
                max_duration = kwargs.get("max_duration", self.limits.session_max_duration)
                session_max_size = kwargs.get("max_size", 512)
                session_quality = kwargs.get("quality", self.limits.session_compression_quality)

                # Full pipeline
                frames, segments, metadata = await loop.run_in_executor(
                    _EXECUTOR,
                    _compress_session,
                    path,
                    max_duration,
                    target_frames,
                    activity_threshold,
                    scene_threshold,
                    session_max_size,
                    session_quality,
                )

                result = MediaResult(success=True)

                for data, info in frames:
                    if result.total_size + len(data) > self.limits.max_payload_bytes:
                        result.warnings.append("Payload limit reached")
                        break

                    result.images.append(
                        {
                            "timestamp_sec": info["timestamp_sec"],
                            "timestamp_ms": info["timestamp_ms"],
                            "size": len(data),
                            "format": info["format"],
                            "base64": base64.b64encode(data).decode(),
                        }
                    )
                    result.total_size += len(data)
                    result.total_count += 1

                return json.dumps(
                    {
                        **result.to_dict(),
                        **metadata,
                        "activity_segments": [
                            {
                                "start_ms": s.start_ms,
                                "end_ms": s.end_ms,
                                "activity_score": round(s.activity_score, 4),
                            }
                            for s in segments
                        ],
                    }
                )

            else:
                return json.dumps({"error": f"Unknown action: {action}"})

        except Exception as e:
            return json.dumps({"error": str(e)})

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def media(
            action: Annotated[str, Field(description="Action to perform")] = "status",
            path: Annotated[Optional[str], Field(description="File path")] = None,
            paths: Annotated[Optional[list[str]], Field(description="List of file paths")] = None,
            images: Annotated[Optional[list[str]], Field(description="Base64 images or paths")] = None,
            optimize: Annotated[bool, Field(description="Optimize for Claude")] = True,
            max_size: Annotated[Optional[int], Field(description="Max dimension")] = None,
            width: Annotated[Optional[int], Field(description="Target width")] = None,
            height: Annotated[Optional[int], Field(description="Target height")] = None,
            maintain_aspect: Annotated[bool, Field(description="Keep aspect ratio")] = True,
            quality: Annotated[Optional[int], Field(description="JPEG quality 1-100")] = None,
            count: Annotated[int, Field(description="Frame count")] = 10,
            interval_ms: Annotated[int, Field(description="Frame interval ms")] = 1000,
            # Activity detection params
            target_frames: Annotated[Optional[int], Field(description="Target frames for activity slicing")] = None,
            activity_threshold: Annotated[Optional[float], Field(description="Activity sensitivity 0.01-0.10")] = None,
            scene_threshold: Annotated[Optional[float], Field(description="Scene change sensitivity")] = None,
            max_duration: Annotated[Optional[int], Field(description="Max seconds to analyze")] = None,
            # Limit updates
            max_images: Annotated[Optional[int], Field(description="Update max images limit")] = None,
            max_payload_mb: Annotated[Optional[float], Field(description="Update max payload MB")] = None,
            max_resolution: Annotated[Optional[int], Field(description="Update max resolution")] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                path=path,
                paths=paths,
                images=images,
                optimize=optimize,
                max_size=max_size,
                width=width,
                height=height,
                maintain_aspect=maintain_aspect,
                quality=quality,
                count=count,
                interval_ms=interval_ms,
                max_images=max_images,
                max_payload_mb=max_payload_mb,
                max_resolution=max_resolution,
                # Pass activity params as kwargs
                target_frames=target_frames,
                activity_threshold=activity_threshold,
                scene_threshold=scene_threshold,
                max_duration=max_duration,
            )


# Singleton instance
media_tool = MediaTool()
