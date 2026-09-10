"""Health check route with real availability verification for Redis, RabbitMQ, and FFmpeg."""

from datetime import datetime, timezone
import socket
from typing import Dict
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.models.schemas import HealthResponse, ServiceHealthItem
from app.services.job_service import get_job_service
from app.services.video_processor import VideoProcessor

router = APIRouter(tags=["Health"])


def check_rabbitmq(host: str, port: int, timeout: float = 0.5) -> ServiceHealthItem:
    """Perform real socket check to RabbitMQ broker."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return ServiceHealthItem(status="healthy", message=f"Connected to {host}:{port}")
    except Exception as e:
        return ServiceHealthItem(status="unhealthy", message=f"Cannot reach RabbitMQ at {host}:{port}: {e}")


def check_redis() -> ServiceHealthItem:
    """Perform ping check to Redis."""
    job_service = get_job_service()
    if job_service.is_connected():
        return ServiceHealthItem(status="healthy", message="Redis PING successful")
    return ServiceHealthItem(status="unhealthy", message="Redis connection failed")


def check_ffmpeg() -> ServiceHealthItem:
    """Perform binary execution check on FFmpeg."""
    ok, details = VideoProcessor.check_ffmpeg()
    if ok:
        return ServiceHealthItem(status="healthy", message=details)
    return ServiceHealthItem(status="unhealthy", message=details)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System and dependencies health check",
)
def get_health():
    """Verify application, Redis, RabbitMQ, and FFmpeg availability.

    Never falsely reports an unavailable dependency as healthy.
    """
    settings = get_settings()

    services: Dict[str, ServiceHealthItem] = {
        "application": ServiceHealthItem(status="healthy", message=f"{settings.APP_NAME} running"),
        "redis": check_redis(),
        "rabbitmq": check_rabbitmq(settings.RABBITMQ_HOST, settings.RABBITMQ_PORT),
        "ffmpeg": check_ffmpeg(),
    }

    all_healthy = all(s.status == "healthy" for s in services.values())
    overall_status = "healthy" if all_healthy else "unhealthy"

    response_payload = HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=response_payload.model_dump())
