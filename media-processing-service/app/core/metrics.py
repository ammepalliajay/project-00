"""Prometheus metrics collectors for microservice and worker operations."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Metrics definitions
JOBS_TOTAL = Counter(
    "media_jobs_total",
    "Total media processing jobs created",
    ["operation", "media_type"],
)

JOBS_COMPLETED = Counter(
    "media_jobs_completed_total",
    "Total media processing jobs completed successfully",
    ["operation"],
)

JOBS_FAILED = Counter(
    "media_jobs_failed_total",
    "Total media processing jobs failed",
    ["operation"],
)

JOBS_ACTIVE = Gauge(
    "media_jobs_active",
    "Number of media processing jobs currently being processed",
)

JOBS_RETRY = Counter(
    "media_jobs_retry_total",
    "Total media processing job retries executed",
    ["operation"],
)

IMAGE_JOBS_TOTAL = Counter(
    "media_image_jobs_total",
    "Total image processing jobs",
    ["operation"],
)

VIDEO_JOBS_TOTAL = Counter(
    "media_video_jobs_total",
    "Total video processing jobs",
    ["operation"],
)

PROCESSING_DURATION = Histogram(
    "media_job_processing_duration_seconds",
    "Duration of media processing jobs in seconds",
    ["operation"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)


def record_job_created(operation: str, is_video: bool) -> None:
    """Record creation of a new job."""
    m_type = "video" if is_video else "image"
    JOBS_TOTAL.labels(operation=operation, media_type=m_type).inc()
    if is_video:
        VIDEO_JOBS_TOTAL.labels(operation=operation).inc()
    else:
        IMAGE_JOBS_TOTAL.labels(operation=operation).inc()


def record_job_started() -> None:
    """Increment active job gauge."""
    JOBS_ACTIVE.inc()


def record_job_completed(operation: str, duration_sec: float) -> None:
    """Record completion and decrement active gauge."""
    JOBS_ACTIVE.dec()
    JOBS_COMPLETED.labels(operation=operation).inc()
    PROCESSING_DURATION.labels(operation=operation).observe(duration_sec)


def record_job_failed(operation: str) -> None:
    """Record job failure and decrement active gauge."""
    JOBS_ACTIVE.dec()
    JOBS_FAILED.labels(operation=operation).inc()


def record_job_retry(operation: str) -> None:
    """Record retry count."""
    JOBS_RETRY.labels(operation=operation).inc()
