"""Tests for job submission, Redis status polling, downloads, and metrics."""

import time
from fastapi.testclient import TestClient


def test_create_and_poll_image_job(client: TestClient, sample_media):
    """Test full flow: upload -> create job -> verify Redis state -> download."""
    # 1. Upload sample image
    jpg_path = sample_media["jpg"]
    with open(jpg_path, "rb") as f:
        up_res = client.post(
            "/uploads",
            files={"file": ("photo.jpg", f, "image/jpeg")},
        )
    assert up_res.status_code == 201
    file_id = up_res.json()["file_id"]
    storage_path = up_res.json()["storage_path"]

    # 2. Submit resize job
    job_payload = {
        "operation": "resize_image",
        "input_path": storage_path,
        "parameters": {"width": 300, "height": 200, "quality": 85},
    }
    job_res = client.post("/jobs", json=job_payload)
    assert job_res.status_code == 201
    job_data = job_res.json()
    job_id = job_data["job_id"]
    assert job_id.startswith("job_")

    # 3. Poll status from Redis
    status_res = client.get(f"/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ("PENDING", "PROCESSING", "COMPLETED")

    # In eager test mode, job finishes immediately
    if status_data["status"] == "COMPLETED":
        assert status_data["output_path"] is not None
        assert status_data["output_size"] > 0
        assert status_data["processing_time"] >= 0

        # 4. Download result
        dl_res = client.get(f"/jobs/{job_id}/download")
        assert dl_res.status_code == 200
        assert len(dl_res.content) > 0


def test_invalid_operation(client: TestClient, sample_media):
    """Test rejection of unsupported or arbitrary operation names."""
    job_payload = {
        "operation": "arbitrary_shell_command",
        "input_path": "uploads/somefile.jpg",
        "parameters": {},
    }
    res = client.post("/jobs", json=job_payload)
    assert res.status_code == 422  # Pydantic validation error


def test_mismatched_media_type_operation(client: TestClient, sample_media):
    """Test rejection of video operations on image files."""
    jpg_path = sample_media["jpg"]
    with open(jpg_path, "rb") as f:
        up = client.post("/uploads", files={"file": ("pic.jpg", f, "image/jpeg")})
    storage_path = up.json()["storage_path"]

    # Attempt video thumbnail on image
    res = client.post(
        "/jobs",
        json={"operation": "video_thumbnail", "input_path": storage_path, "parameters": {}},
    )
    assert res.status_code == 400
    assert "cannot perform video operation" in res.json()["detail"].lower()


def test_get_nonexistent_job(client: TestClient):
    """Test 404 for unknown job ID."""
    res = client.get("/jobs/job_nonexistent_12345")
    assert res.status_code == 404


def test_download_incomplete_job_fails(client: TestClient):
    """Test downloading a pending or failed job returns 400."""
    from app.services.job_service import get_job_service
    from app.models.jobs import OperationType

    job_service = get_job_service()
    job = job_service.create_job(
        operation=OperationType.RESIZE_IMAGE,
        input_path="uploads/fake.jpg",
    )

    res = client.get(f"/jobs/{job.job_id}/download")
    assert res.status_code in (400, 404)


def test_prometheus_metrics_endpoint(client: TestClient):
    """Test /metrics returns Prometheus format lines."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    text = res.text
    assert "media_jobs_total" in text
