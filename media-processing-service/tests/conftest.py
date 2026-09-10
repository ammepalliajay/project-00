"""Pytest configuration, fixtures, and mock test setup."""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings, get_settings
from app.main import app
from app.services.storage import LocalStorageBackend
from app.workers.celery_app import celery_app
from scripts.generate_test_media import generate_all

# Enforce eager execution for test suite
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True


@pytest.fixture(scope="session")
def sample_media(tmp_path_factory) -> dict:
    """Generate temporary test images and videos for tests."""
    temp_media_dir = tmp_path_factory.mktemp("media_fixtures")
    return generate_all(str(temp_media_dir))


@pytest.fixture(autouse=True)
def configure_test_environment(tmp_path, monkeypatch):
    """Set test environment variables and temporary storage directories."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_BASE_DIR", str(storage_dir))
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "10")
    monkeypatch.setenv("CELERY_ALWAYS_EAGER", "True")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "mock_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "mock_secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_S3_BUCKET", "mock-test-bucket")

    # Clear cached settings
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
