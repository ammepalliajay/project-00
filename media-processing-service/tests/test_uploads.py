"""Tests for media file uploads, MIME checks, size limits, and corruption prevention."""

import io
from fastapi.testclient import TestClient


def test_upload_valid_jpeg(client: TestClient, sample_media):
    """Test successful JPEG upload."""
    jpg_path = sample_media["jpg"]
    with open(jpg_path, "rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("test_photo.jpg", f, "image/jpeg")},
        )
    assert response.status_code == 201
    data = response.json()
    assert "file_id" in data
    assert data["original_name"] == "test_photo.jpg"
    assert data["media_type"] == "image"
    assert data["size_bytes"] > 0
    assert data["storage_path"].startswith("uploads/")


def test_upload_valid_png(client: TestClient, sample_media):
    """Test successful PNG upload."""
    png_path = sample_media["png"]
    with open(png_path, "rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("graphic.png", f, "image/png")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["media_type"] == "image"
    assert data["original_name"] == "graphic.png"


def test_upload_valid_webp(client: TestClient, sample_media):
    """Test successful WEBP upload."""
    webp_path = sample_media["webp"]
    with open(webp_path, "rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("sample.webp", f, "image/webp")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["media_type"] == "image"


def test_upload_valid_mp4(client: TestClient, sample_media):
    """Test successful MP4 upload."""
    if "mp4" not in sample_media:
        return
    mp4_path = sample_media["mp4"]
    with open(mp4_path, "rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("clip.mp4", f, "video/mp4")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["media_type"] == "video"


def test_upload_unsupported_extension(client: TestClient):
    """Test rejection of unsupported file types."""
    response = client.post(
        "/uploads",
        files={"file": ("malicious.exe", io.BytesIO(b"binary data"), "application/x-msdownload")},
    )
    assert response.status_code == 400
    assert "unsupported file extension" in response.json()["detail"].lower()


def test_upload_invalid_mime_type(client: TestClient, sample_media):
    """Test rejection when MIME type is mismatched or disallowed."""
    jpg_path = sample_media["jpg"]
    with open(jpg_path, "rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("test.jpg", f, "application/pdf")},
        )
    assert response.status_code == 400
    assert "unsupported media mime type" in response.json()["detail"].lower()


def test_upload_corrupted_image(client: TestClient, sample_media):
    """Test corruption detection rejecting malformed image bytes."""
    corrupt_path = sample_media["corrupt"]
    with open(corrupt_path, "rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("broken.jpg", f, "image/jpeg")},
        )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()


def test_upload_empty_file(client: TestClient):
    """Test rejection of empty 0-byte file."""
    response = client.post(
        "/uploads",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_exceeds_max_size(client: TestClient, monkeypatch):
    """Test rejection of oversized upload (413 payload too large)."""
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0.001)  # ~1 KB limit

    big_data = b"X" * (50 * 1024)  # 50 KB
    response = client.post(
        "/uploads",
        files={"file": ("big.jpg", io.BytesIO(big_data), "image/jpeg")},
    )
    assert response.status_code == 413
