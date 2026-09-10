"""File system utilities, safe path operations, and size formatters."""

import os
from pathlib import Path
import re


def ensure_directory(path: str | Path) -> Path:
    """Ensure directory exists and return Path object."""
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and injection.

    Removes path separators, null bytes, and non-whitelisted characters.
    """
    if not filename:
        return "unnamed_file"

    # Strip null bytes, normalize backslashes to forward slashes
    clean = filename.replace("\x00", "").replace("\\", "/").strip()

    # Extract base name only (removes directory components on all platforms)
    clean = os.path.basename(clean)

    # Keep only alphanumeric, hyphens, underscores, and dots
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", clean)

    # Avoid hidden files starting with .
    if clean.startswith("."):
        clean = f"file.{clean.lstrip('.')}"

    return clean or "unnamed_file"


def is_safe_path(base_dir: str | Path, target_path: str | Path) -> bool:
    """Validate that target_path resolves strictly within base_dir (prevent path traversal)."""
    try:
        base = Path(base_dir).resolve()
        target = Path(target_path).resolve()
        return base in target.parents or base == target
    except Exception:
        return False


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    val = float(size_bytes)
    while val >= 1024.0 and unit_index < len(units) - 1:
        val /= 1024.0
        unit_index += 1
    return f"{val:.2f} {units[unit_index]}"


def get_file_extension(filename: str) -> str:
    """Return lowercase extension without leading dot."""
    ext = os.path.splitext(filename)[1].lower()
    return ext.lstrip(".")
