"""Security validations, MIME/extension verification, and path traversal guards."""

import os
from pathlib import Path
from typing import Set
from fastapi import HTTPException, status
from app.utils.file_utils import is_safe_path


# Whitelisted extensions and MIME types
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {"jpg", "jpeg", "png", "webp"}
ALLOWED_VIDEO_EXTENSIONS: Set[str] = {"mp4", "mov", "avi"}
ALLOWED_EXTENSIONS: Set[str] = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

ALLOWED_IMAGE_MIMES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_VIDEO_MIMES: Set[str] = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/avi",
}
ALLOWED_MIMES: Set[str] = ALLOWED_IMAGE_MIMES | ALLOWED_VIDEO_MIMES


def validate_extension(filename: str) -> str:
    """Validate and return normalized lowercase extension without dot."""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: '.{ext}'. Supported extensions: {sorted(list(ALLOWED_EXTENSIONS))}",
        )
    return ext


def validate_mime(mime_type: str) -> str:
    """Validate Content-Type MIME."""
    normalized = mime_type.lower().split(";")[0].strip() if mime_type else ""
    if not normalized or normalized not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media MIME type: '{normalized}'. Supported types: {sorted(list(ALLOWED_MIMES))}",
        )
    return normalized


def validate_path_traversal(base_dir: str | Path, candidate_path: str | Path) -> Path:
    """Ensure candidate path is inside base_dir, raising 403 / 400 on traversal attempt."""
    base = Path(base_dir).resolve()
    candidate = Path(candidate_path).resolve()

    if not is_safe_path(base, candidate):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path or path traversal detected.",
        )
    return candidate


def sanitize_error_detail(exc: Exception, debug: bool = False) -> str:
    """Return user-safe error messages without leaking internal stack traces or paths."""
    if isinstance(exc, HTTPException):
        return exc.detail
    if debug:
        return str(exc)
    return "An internal server error occurred while processing the request."
