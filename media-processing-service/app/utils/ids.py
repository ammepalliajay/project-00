"""Identifier utilities for jobs, uploads, and tasks."""

import uuid


def generate_uuid() -> str:
    """Generate a clean RFC 4122 UUID4 string."""
    return str(uuid.uuid4())


def generate_job_id() -> str:
    """Generate unique job identifier."""
    return f"job_{uuid.uuid4().hex}"


def generate_file_id() -> str:
    """Generate unique file identifier."""
    return f"file_{uuid.uuid4().hex}"
