"""Security tests: path traversal defenses, secret scrubbing, and mocked S3 storage."""

import boto3
from moto import mock_aws
from pathlib import Path
import pytest
from fastapi import HTTPException
from app.core.logging import scrub_secrets
from app.core.security import (
    sanitize_error_detail,
    validate_extension,
    validate_mime,
    validate_path_traversal,
)
from app.services.storage import S3StorageBackend
from app.utils.file_utils import is_safe_path, sanitize_filename


def test_path_traversal_detection(tmp_path):
    """Ensure path traversal attempts are detected and rejected."""
    base = tmp_path / "sandbox"
    base.mkdir()

    # Traversal attempts
    assert not is_safe_path(base, base / "../outside.txt")
    assert not is_safe_path(base, base / "../../etc/passwd")
    assert not is_safe_path(base, "/etc/shadow")

    with pytest.raises(HTTPException) as exc_info:
        validate_path_traversal(base, base / "../escape.py")
    assert exc_info.value.status_code == 400


def test_sanitize_filename():
    """Verify filename cleaner strips traversal sequences and dangerous characters."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.exe") == "calc.exe"
    assert sanitize_filename("my file!@#$%.png") == "my_file_____.png"
    assert sanitize_filename(".hidden") == "file.hidden"


def test_secret_scrubbing_in_logs():
    """Verify secret patterns are scrubbed from log strings."""
    secret_log = "Connected with amqp://guest:superSecretPassword123@rabbitmq:5672/"
    scrubbed = scrub_secrets(secret_log)
    assert "superSecretPassword123" not in scrubbed
    assert "[REDACTED]" in scrubbed

    aws_log = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    scrubbed_aws = scrub_secrets(aws_log)
    assert "wJalrXUtnFEMI" not in scrubbed_aws


def test_safe_error_responses():
    """Ensure production error sanitizer hides internal details and traces."""
    internal_exc = FileNotFoundError("/var/secret/private_key.pem not found")
    safe_msg = sanitize_error_detail(internal_exc, debug=False)
    assert "/var/secret" not in safe_msg
    assert "internal server error" in safe_msg.lower()


@mock_aws
def test_mocked_s3_storage_operations(tmp_path):
    """Verify S3 storage backend operations using moto (zero real AWS required)."""
    bucket_name = "test-media-bucket"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)

    backend = S3StorageBackend(
        bucket_name=bucket_name,
        region="us-east-1",
        cache_dir=str(tmp_path / "cache"),
    )

    # 1. Save
    key = backend.save(b"HELLO S3 MEDIA", "uploads/test.txt", content_type="text/plain")
    assert key == "uploads/test.txt"

    # 2. Exists
    assert backend.exists(key) is True
    assert backend.exists("nonexistent.txt") is False

    # 3. Get
    content = backend.get(key)
    assert content == b"HELLO S3 MEDIA"

    # 4. Presigned URL
    url = backend.get_url(key)
    assert "https://" in url
    assert key in url

    # 5. Delete
    assert backend.delete(key) is True
    assert backend.exists(key) is False
