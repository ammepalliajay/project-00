"""Video processing service using FFmpeg: thumbnails, compression, transcoding."""

import os
from pathlib import Path
import subprocess
from typing import Any, Dict, Optional, Tuple
from app.core.logging import logger
from app.models.jobs import OperationType


class VideoProcessor:
    """Safe wrapper around FFmpeg binary for video manipulation."""

    ALLOWED_PRESETS = {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"}
    ALLOWED_RESOLUTIONS = {"1920x1080", "1280x720", "854x480", "640x360", "426x240"}

    @staticmethod
    def check_ffmpeg() -> Tuple[bool, str]:
        """Verify FFmpeg installation and report version."""
        try:
            res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                first_line = res.stdout.splitlines()[0] if res.stdout else "FFmpeg available"
                return True, first_line
            return False, f"FFmpeg returned code {res.returncode}"
        except Exception as e:
            return False, str(e)

    def generate_thumbnail(
        self,
        input_path: Path,
        output_path: Path,
        timestamp_sec: float = 1.0,
        width: Optional[int] = None,
    ) -> Path:
        """Extract a single frame thumbnail at given timestamp."""
        ts = max(0.0, float(timestamp_sec))
        vf_filter = f"scale={int(width)}:-2" if width and width > 0 else "null"

        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(ts),
            "-i",
            str(input_path),
            "-vf",
            vf_filter,
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ]

        logger.info(f"Generating video thumbnail: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            logger.error(f"FFmpeg thumbnail error: {res.stderr}")
            raise RuntimeError(f"FFmpeg thumbnail extraction failed: {res.stderr[-200:] if res.stderr else 'Unknown error'}")

        return output_path

    def compress(
        self,
        input_path: Path,
        output_path: Path,
        crf: int = 28,
        preset: str = "medium",
        audio_bitrate: str = "128k",
    ) -> Path:
        """Compress video using H.264 (libx264) and AAC with constant rate factor (CRF)."""
        safe_crf = max(18, min(45, int(crf)))
        safe_preset = preset if preset in self.ALLOWED_PRESETS else "medium"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "libx264",
            "-crf",
            str(safe_crf),
            "-preset",
            safe_preset,
            "-c:a",
            "aac",
            "-b:a",
            audio_bitrate,
            "-movflags",
            "+faststart",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]

        logger.info(f"Compressing video: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            logger.error(f"FFmpeg compression error: {res.stderr}")
            raise RuntimeError(f"FFmpeg video compression failed: {res.stderr[-200:] if res.stderr else 'Unknown error'}")

        return output_path

    def transcode(
        self,
        input_path: Path,
        output_path: Path,
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        video_bitrate: Optional[str] = None,
    ) -> Path:
        """Transcode video to MP4 container (H.264/AAC) with optional scaling and fps."""
        cmd = ["ffmpeg", "-y", "-i", str(input_path)]

        vf_filters = []
        if resolution and resolution in self.ALLOWED_RESOLUTIONS:
            w, h = resolution.split("x")
            vf_filters.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2")

        if fps and 1 <= int(fps) <= 60:
            cmd.extend(["-r", str(int(fps))])

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        cmd.extend([
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            "-pix_fmt",
            "yuv420p",
        ])

        if video_bitrate:
            cmd.extend(["-b:v", str(video_bitrate)])

        cmd.append(str(output_path))

        logger.info(f"Transcoding video: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            logger.error(f"FFmpeg transcoding error: {res.stderr}")
            raise RuntimeError(f"FFmpeg video transcoding failed: {res.stderr[-200:] if res.stderr else 'Unknown error'}")

        return output_path

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        operation: OperationType,
        parameters: Dict[str, Any],
    ) -> Path:
        """Dispatch video operations to FFmpeg."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if operation == OperationType.VIDEO_THUMBNAIL:
            ts = float(parameters.get("timestamp_sec", 1.0))
            w = parameters.get("width")
            return self.generate_thumbnail(input_path, output_path, timestamp_sec=ts, width=w)

        elif operation == OperationType.VIDEO_COMPRESS:
            crf = int(parameters.get("crf", 28))
            preset = str(parameters.get("preset", "medium"))
            audio_b = str(parameters.get("audio_bitrate", "128k"))
            return self.compress(input_path, output_path, crf=crf, preset=preset, audio_bitrate=audio_b)

        elif operation == OperationType.VIDEO_TRANSCODE:
            res = parameters.get("resolution")
            fps = parameters.get("fps")
            v_b = parameters.get("video_bitrate")
            return self.transcode(input_path, output_path, resolution=res, fps=fps, video_bitrate=v_b)

        else:
            raise ValueError(f"Unsupported video operation: {operation}")
