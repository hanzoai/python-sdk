"""Screen recording and AI interpretation tool for Hanzo AI.

One unified tool for capturing, recording, and sending screen data to Claude:
- capture: Single screenshot
- record: Start background recording
- stop: Stop recording and get compressed frames
- session: ONE-SHOT record → analyze → compress → return for Claude

The 'session' action is the primary interface:
1. Records screen for specified duration (default 30s)
2. Analyzes for activity (movement, scene changes)
3. Extracts only keyframes at activity points
4. Compresses heavily for minimal payload
5. Returns frames ready for Claude interpretation

Typical usage:
    screen(action="session", duration=30)  # 30s session
    # Returns ~30 compressed frames, ~500KB total
    # Claude can interpret the computer use session
"""

import os
import io
import sys
import json
import time
import base64
import asyncio
import tempfile
import subprocess
from typing import Any, Literal, Optional, Annotated, final, override
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, PermissionManager, auto_timeout

from .media_tool import (
    MediaLimits,
    MediaResult,
    ActivitySegment,
    _analyze_video_activity,
    _extract_activity_frames,
    _compress_session,
    _resize_image,
)

# Thread pool for blocking operations
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="screen_")


@dataclass
class ScreenConfig:
    """Configuration for screen capture sessions."""

    # Session defaults
    default_duration: int = 30  # seconds
    max_duration: int = 120  # seconds

    # Recording settings
    fps: int = 30
    quality: str = "medium"  # low, medium, high

    # Compression for Claude
    # IMPORTANT: Claude has 2000px max for multi-image requests
    # We use 768px for good quality while staying well under limit
    target_frames: int = 30
    max_size: int = 768  # pixels (hard capped at 1568 for safety)
    jpeg_quality: int = 60

    # Activity detection
    activity_threshold: float = 0.02
    scene_threshold: float = 0.3

    # Hard limits (Claude API constraints)
    HARD_MAX_SIZE: int = 2000  # Claude's actual limit
    HARD_MAX_FRAMES: int = 100  # Max frames per request
    HARD_MAX_PAYLOAD_MB: float = 32.0  # Max total payload

    @classmethod
    def from_env(cls) -> "ScreenConfig":
        """Load from environment variables."""
        max_size = int(os.environ.get("HANZO_SCREEN_MAX_SIZE", "768"))
        # Enforce hard cap
        max_size = min(max_size, cls.HARD_MAX_SIZE)

        return cls(
            default_duration=int(os.environ.get("HANZO_SCREEN_DURATION", "30")),
            max_duration=int(os.environ.get("HANZO_SCREEN_MAX_DURATION", "120")),
            target_frames=min(
                int(os.environ.get("HANZO_SCREEN_TARGET_FRAMES", "30")),
                cls.HARD_MAX_FRAMES,
            ),
            max_size=max_size,
            jpeg_quality=int(os.environ.get("HANZO_SCREEN_QUALITY", "60")),
            activity_threshold=float(os.environ.get("HANZO_SCREEN_ACTIVITY_THRESHOLD", "0.02")),
        )


def _capture_screenshot_native(region: Optional[list[int]] = None) -> bytes:
    """Capture screenshot using macOS screencapture."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    try:
        cmd = ["screencapture", "-x", "-t", "png"]
        if region and len(region) == 4:
            x, y, w, h = region
            cmd.extend(["-R", f"{x},{y},{w},{h}"])
        cmd.append(tmp_path)

        subprocess.run(cmd, capture_output=True, timeout=2)

        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _record_screen(
    output_path: str,
    duration: int,
    fps: int = 30,
    quality: str = "medium",
    region: Optional[list[int]] = None,
) -> str:
    """Record screen to file for specified duration.

    Returns path to recorded video file.
    """
    quality_map = {"low": "28", "medium": "23", "high": "18"}
    crf = quality_map.get(quality, "23")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "avfoundation",
        "-framerate", str(fps),
        "-i", "1:none",  # Screen capture
        "-t", str(duration),
        "-c:v", "libx264",
        "-crf", crf,
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
    ]

    if region and len(region) == 4:
        x, y, w, h = region
        cmd.extend(["-vf", f"crop={w}:{h}:{x}:{y}"])

    cmd.append(output_path)

    # Run and wait for completion
    subprocess.run(cmd, capture_output=True, timeout=duration + 30)

    return output_path


def _process_recording_for_claude(
    video_path: str,
    target_frames: int = 30,
    max_size: int = 512,
    quality: int = 60,
    activity_threshold: float = 0.02,
    scene_threshold: float = 0.3,
) -> tuple[list[dict], list[dict], dict]:
    """Process recorded video for Claude interpretation.

    Returns (frames_with_base64, activity_segments, metadata).
    """
    frames, segments, metadata = _compress_session(
        video_path,
        max_duration=120,
        target_frames=target_frames,
        activity_threshold=activity_threshold,
        scene_threshold=scene_threshold,
        max_size=max_size,
        quality=quality,
    )

    # Convert to serializable format
    frames_data = []
    for data, info in frames:
        frames_data.append({
            "timestamp_sec": info["timestamp_sec"],
            "timestamp_ms": info["timestamp_ms"],
            "size": len(data),
            "base64": base64.b64encode(data).decode(),
        })

    segments_data = [
        {
            "start_ms": s.start_ms,
            "end_ms": s.end_ms,
            "activity_score": round(s.activity_score, 4),
        }
        for s in segments
    ]

    return frames_data, segments_data, metadata


Action = Literal[
    "capture",   # Single screenshot
    "record",    # Start recording (background)
    "stop",      # Stop recording
    "status",    # Recording status
    "session",   # ONE-SHOT: record → analyze → compress → return
    "analyze",   # Analyze existing video file
    "info",      # System info
]


@final
class ScreenTool(BaseTool):
    """Screen recording and AI interpretation tool.

    Primary action: 'session' - records screen, analyzes activity,
    compresses, and returns frames ready for Claude interpretation.

    Usage:
        screen(action="session", duration=30)
        # Returns compressed keyframes from 30-second recording
        # Perfect for Claude to interpret computer use sessions
    """

    name = "screen"

    def __init__(
        self,
        permission_manager: Optional[PermissionManager] = None,
        config: Optional[ScreenConfig] = None,
    ):
        if permission_manager is None:
            permission_manager = PermissionManager()
        self.permission_manager = permission_manager
        self.config = config or ScreenConfig.from_env()

        # Recording state
        self._recording = False
        self._process: Optional[subprocess.Popen] = None
        self._output_file: Optional[str] = None
        self._start_time: float = 0

        # Capabilities
        self._has_ffmpeg: Optional[bool] = None
        self._has_screencapture: Optional[bool] = None

    def _check_ffmpeg(self) -> bool:
        if self._has_ffmpeg is None:
            try:
                subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
                self._has_ffmpeg = True
            except Exception:
                self._has_ffmpeg = False
        return self._has_ffmpeg

    def _check_screencapture(self) -> bool:
        if self._has_screencapture is None:
            self._has_screencapture = sys.platform == "darwin"
        return self._has_screencapture

    @property
    @override
    def description(self) -> str:
        return f"""Screen recording and AI interpretation for Claude.

PRIMARY ACTION - session:
  Record screen → Analyze activity → Compress → Return for Claude

  screen(action="session", duration=30)

  This one call:
  1. Records screen for {self.config.default_duration}s (configurable)
  2. Detects activity (movement, clicks, typing)
  3. Extracts ~{self.config.target_frames} keyframes at activity points
  4. Compresses to ~{self.config.max_size}px @ {self.config.jpeg_quality}% quality
  5. Returns frames + activity analysis (~500KB total)

  Perfect for Claude to interpret computer use sessions.

OTHER ACTIONS:

capture: Single screenshot
  - region: [x, y, width, height] (optional)
  - optimize: Compress for Claude (default: true)
  - Returns base64 image

record: Start background recording
  - duration: Recording duration in seconds (max {self.config.max_duration})
  - fps: Frame rate (default: 30)
  - quality: low/medium/high
  - region: Specific screen area

stop: Stop recording and process
  - Returns compressed frames like 'session'

status: Check recording state

analyze: Process existing video file
  - path: Video file path
  - Returns activity analysis + compressed frames

info: System capabilities

CONFIGURATION (env vars):
  HANZO_SCREEN_DURATION={self.config.default_duration}      # Default session duration
  HANZO_SCREEN_TARGET_FRAMES={self.config.target_frames}    # Target frames per session
  HANZO_SCREEN_MAX_SIZE={self.config.max_size}              # Max frame dimension
  HANZO_SCREEN_QUALITY={self.config.jpeg_quality}           # JPEG quality
  HANZO_SCREEN_ACTIVITY_THRESHOLD={self.config.activity_threshold}

EXAMPLES:
  screen(action="session")  # 30-second session, returns ~30 compressed frames
  screen(action="session", duration=60)  # 60-second session
  screen(action="capture")  # Single screenshot
  screen(action="capture", region=[0, 0, 1920, 1080])  # Specific area
  screen(action="analyze", path="recording.mp4")  # Process existing video
"""

    @override
    @auto_timeout("screen")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "info",
        # Session/recording options
        duration: Optional[int] = None,
        fps: int = 30,
        quality: str = "medium",
        region: Optional[list[int]] = None,
        # Processing options
        target_frames: Optional[int] = None,
        max_size: Optional[int] = None,
        jpeg_quality: Optional[int] = None,
        activity_threshold: Optional[float] = None,
        # For analyze action
        path: Optional[str] = None,
        # Capture options
        optimize: bool = True,
        **kwargs,
    ) -> str:
        """Execute screen action."""
        if sys.platform != "darwin":
            return json.dumps({"error": "screen tool currently only supports macOS"})

        loop = asyncio.get_event_loop()

        # Apply config defaults with hard caps
        duration = duration or self.config.default_duration
        duration = min(duration, self.config.max_duration)
        target_frames = target_frames or self.config.target_frames
        target_frames = min(target_frames, ScreenConfig.HARD_MAX_FRAMES)
        max_size = max_size or self.config.max_size
        max_size = min(max_size, ScreenConfig.HARD_MAX_SIZE)  # Claude 2000px limit
        jpeg_quality = jpeg_quality or self.config.jpeg_quality
        activity_threshold = activity_threshold or self.config.activity_threshold

        try:
            if action == "info":
                return json.dumps({
                    "platform": sys.platform,
                    "has_ffmpeg": self._check_ffmpeg(),
                    "has_screencapture": self._check_screencapture(),
                    "recording": self._recording,
                    "config": {
                        "default_duration": self.config.default_duration,
                        "max_duration": self.config.max_duration,
                        "target_frames": self.config.target_frames,
                        "max_size": self.config.max_size,
                        "jpeg_quality": self.config.jpeg_quality,
                    },
                })

            elif action == "capture":
                # Single screenshot
                if not self._check_screencapture():
                    return json.dumps({"error": "screencapture not available"})

                data = await loop.run_in_executor(
                    _EXECUTOR,
                    _capture_screenshot_native,
                    region,
                )

                if optimize:
                    # Compress for Claude
                    data, info = await loop.run_in_executor(
                        _EXECUTOR,
                        _resize_image,
                        data,
                        max_size,
                        jpeg_quality,
                        True,  # force JPEG
                    )
                    format_type = "jpeg"
                else:
                    format_type = "png"
                    info = {}

                return json.dumps({
                    "success": True,
                    "format": format_type,
                    "size": len(data),
                    "dimensions": info.get("new_dimensions"),
                    "base64": base64.b64encode(data).decode(),
                })

            elif action == "session":
                # ONE-SHOT: record → analyze → compress → return
                if not self._check_ffmpeg():
                    return json.dumps({"error": "FFmpeg required for screen recording"})

                # Create temp file for recording
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                    video_path = f.name

                try:
                    # Record screen
                    await loop.run_in_executor(
                        _EXECUTOR,
                        _record_screen,
                        video_path,
                        duration,
                        fps,
                        quality,
                        region,
                    )

                    # Process for Claude
                    frames_data, segments_data, metadata = await loop.run_in_executor(
                        _EXECUTOR,
                        _process_recording_for_claude,
                        video_path,
                        target_frames,
                        max_size,
                        jpeg_quality,
                        activity_threshold,
                        self.config.scene_threshold,
                    )

                    total_size = sum(f["size"] for f in frames_data)

                    return json.dumps({
                        "success": True,
                        "action": "session",
                        "duration_seconds": duration,
                        "frames": frames_data,
                        "activity_segments": segments_data,
                        "total_frames": len(frames_data),
                        "total_size_bytes": total_size,
                        "total_size_kb": round(total_size / 1024, 1),
                        "compression_settings": {
                            "target_frames": target_frames,
                            "max_size": max_size,
                            "quality": jpeg_quality,
                        },
                        "metadata": metadata,
                    })

                finally:
                    # Cleanup temp file
                    if os.path.exists(video_path):
                        os.unlink(video_path)

            elif action == "record":
                # Start background recording
                if self._recording:
                    return json.dumps({"error": "Already recording"})

                if not self._check_ffmpeg():
                    return json.dumps({"error": "FFmpeg required"})

                # Create output file
                self._output_file = tempfile.mktemp(suffix=".mp4")

                # Build command
                quality_map = {"low": "28", "medium": "23", "high": "18"}
                crf = quality_map.get(quality, "23")

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-f", "avfoundation",
                    "-framerate", str(fps),
                    "-i", "1:none",
                    "-t", str(duration),
                    "-c:v", "libx264",
                    "-crf", crf,
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                ]

                if region and len(region) == 4:
                    x, y, w, h = region
                    cmd.extend(["-vf", f"crop={w}:{h}:{x}:{y}"])

                cmd.append(self._output_file)

                # Start recording process
                self._process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self._recording = True
                self._start_time = time.time()

                return json.dumps({
                    "success": True,
                    "recording": True,
                    "duration": duration,
                    "output": self._output_file,
                })

            elif action == "stop":
                # Stop recording and process
                if not self._recording:
                    return json.dumps({"error": "Not recording"})

                # Stop the process
                if self._process:
                    try:
                        self._process.stdin.write(b"q")
                        self._process.stdin.flush()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                    self._process = None

                actual_duration = time.time() - self._start_time
                video_path = self._output_file

                self._recording = False
                self._output_file = None
                self._start_time = 0

                # Process the recording
                if video_path and os.path.exists(video_path):
                    try:
                        frames_data, segments_data, metadata = await loop.run_in_executor(
                            _EXECUTOR,
                            _process_recording_for_claude,
                            video_path,
                            target_frames,
                            max_size,
                            jpeg_quality,
                            activity_threshold,
                            self.config.scene_threshold,
                        )

                        total_size = sum(f["size"] for f in frames_data)

                        return json.dumps({
                            "success": True,
                            "duration_seconds": round(actual_duration, 2),
                            "frames": frames_data,
                            "activity_segments": segments_data,
                            "total_frames": len(frames_data),
                            "total_size_kb": round(total_size / 1024, 1),
                            "metadata": metadata,
                        })

                    finally:
                        os.unlink(video_path)
                else:
                    return json.dumps({"error": "Recording file not found"})

            elif action == "status":
                result = {
                    "recording": self._recording,
                }
                if self._recording:
                    result["duration_seconds"] = round(time.time() - self._start_time, 2)
                return json.dumps(result)

            elif action == "analyze":
                # Analyze existing video file
                if not path:
                    return json.dumps({"error": "path required"})

                if not os.path.exists(path):
                    return json.dumps({"error": f"File not found: {path}"})

                frames_data, segments_data, metadata = await loop.run_in_executor(
                    _EXECUTOR,
                    _process_recording_for_claude,
                    path,
                    target_frames,
                    max_size,
                    jpeg_quality,
                    activity_threshold,
                    self.config.scene_threshold,
                )

                total_size = sum(f["size"] for f in frames_data)

                return json.dumps({
                    "success": True,
                    "source": path,
                    "frames": frames_data,
                    "activity_segments": segments_data,
                    "total_frames": len(frames_data),
                    "total_size_kb": round(total_size / 1024, 1),
                    "metadata": metadata,
                })

            else:
                return json.dumps({"error": f"Unknown action: {action}"})

        except Exception as e:
            return json.dumps({"error": str(e)})

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def screen(
            action: Annotated[str, Field(description="Action: session, capture, record, stop, analyze, info")] = "info",
            duration: Annotated[Optional[int], Field(description="Recording duration in seconds")] = None,
            fps: Annotated[int, Field(description="Frame rate for recording")] = 30,
            quality: Annotated[str, Field(description="Recording quality: low, medium, high")] = "medium",
            region: Annotated[Optional[list[int]], Field(description="Screen region [x, y, width, height]")] = None,
            target_frames: Annotated[Optional[int], Field(description="Target number of output frames")] = None,
            max_size: Annotated[Optional[int], Field(description="Max frame dimension in pixels")] = None,
            jpeg_quality: Annotated[Optional[int], Field(description="JPEG compression quality 1-100")] = None,
            activity_threshold: Annotated[Optional[float], Field(description="Activity detection sensitivity")] = None,
            path: Annotated[Optional[str], Field(description="Video file path for analyze action")] = None,
            optimize: Annotated[bool, Field(description="Optimize capture for Claude")] = True,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                duration=duration,
                fps=fps,
                quality=quality,
                region=region,
                target_frames=target_frames,
                max_size=max_size,
                jpeg_quality=jpeg_quality,
                activity_threshold=activity_threshold,
                path=path,
                optimize=optimize,
            )


# Singleton instance
screen_tool = ScreenTool()
