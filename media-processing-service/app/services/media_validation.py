"""Media validation: MIME checks, file size, corruption detection, and FFprobe verification."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from app.core.logging import logger
from app.core.security import (
    ALLOWED_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    validate_extension,
    validate_mime,
)
from app.utils.file_utils import sanitize_filename


def detect_media_type(extension: str) -> str:
    """Return 'image' or 'video' based on extension."""
    ext = extension.lower().lstrip(".")
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    raise ValueError(f"Unknown media extension: {extension}")


def verify_image_integrity(file_path: Path) -> None:
    """Verify image is not corrupted using Pillow verify()."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        # Re-open and load pixels to detect truncated files
        with Image.open(file_path) as img:
            img.load()
    except (UnidentifiedImageError, OSError, ValueError, Exception) as exc:
        logger.warning(f"Corrupted image upload detected: {file_path}, error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is corrupted or unreadable.",
        )


def verify_video_integrity(file_path: Path) -> None:
    """Verify video container and streams using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height",
        "-of",
        "default=noprint_wrappers=1",
        str(file_path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode != 0 or not res.stdout.strip():
            logger.warning(f"Corrupted video detected: {file_path}, stderr: {res.stderr}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video file is corrupted or contains no valid video stream.",
            )
    except FileNotFoundError:
        # ffprobe binary not found, fallback to basic size check
        if file_path.stat().st_size < 32:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video file is empty or corrupted.",
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video validation timed out.",
        )


def validate_uploaded_file(
    upload_file: UploadFile,
    max_size_bytes: int,
) -> Tuple[str, str, str]:
    """Validate filename, extension, and content type before reading body.

    Returns: (safe_filename, validated_extension, media_type)
    """
    raw_filename = upload_file.filename or "unnamed"
    safe_name = sanitize_filename(raw_filename)
    extension = validate_extension(safe_name)

    # Validate MIME type header
    validate_mime(upload_file.content_type or "")

    media_type = detect_media_type(extension)
    return safe_name, extension, media_type
