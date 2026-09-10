"""Job lifecycle management and status persistence using Redis."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import redis
from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.models.jobs import JobRecord, JobStatus, OperationType
from app.utils.ids import generate_job_id


class JobService:
    """Manages job records in Redis with robust serialization and health checking."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._redis_client: Optional[redis.Redis] = None
        self._memory_store: Dict[str, str] = {}  # Fallback memory store when Redis offline

    @property
    def client(self) -> redis.Redis:
        """Lazy-loaded Redis connection client."""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                db=self.settings.REDIS_DB,
                password=self.settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
        return self._redis_client

    def is_connected(self) -> bool:
        """Ping Redis instance to check availability."""
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def _job_key(self, job_id: str) -> str:
        return f"job:{job_id}"

    def create_job(
        self,
        operation: OperationType,
        input_path: str,
        parameters: Optional[Dict[str, Any]] = None,
        input_size: Optional[int] = None,
        job_id: Optional[str] = None,
    ) -> JobRecord:
        """Create new job record in PENDING status."""
        jid = job_id or generate_job_id()
        now = datetime.now(timezone.utc).isoformat()

        record = JobRecord(
            job_id=jid,
            status=JobStatus.PENDING,
            operation=operation,
            parameters=parameters or {},
            input_path=input_path,
            created_at=now,
            input_size=input_size,
            retry_count=0,
        )

        self.save_job(record)
        logger.info(
            f"Job created: {jid} for operation {operation.value}",
            extra={"job_id": jid, "operation": operation.value, "status": JobStatus.PENDING.value},
        )
        return record

    def save_job(self, record: JobRecord) -> None:
        """Persist job record to Redis."""
        key = self._job_key(record.job_id)
        payload = record.model_dump_json()

        try:
            self.client.set(key, payload)
            # Maintain an index set of job IDs for listing/metrics
            self.client.sadd("jobs:all", record.job_id)
        except Exception as exc:
            if self.settings.ENVIRONMENT == "production":
                logger.error(f"Redis unavailable for job save in production: {exc}")
                raise RuntimeError(f"Redis is unavailable: {exc}") from exc
            logger.warning(f"Redis unavailable for job save, falling back to memory: {exc}")
            self._memory_store[key] = payload

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        """Fetch job record by ID."""
        key = self._job_key(job_id)
        raw: Optional[str] = None

        try:
            raw = self.client.get(key)
        except Exception as exc:
            if self.settings.ENVIRONMENT == "production":
                logger.error(f"Redis error getting job {job_id} in production: {exc}")
                raise RuntimeError(f"Redis is unavailable: {exc}") from exc
            logger.warning(f"Redis error getting job {job_id}: {exc}")
            raw = self._memory_store.get(key)

        if not raw and self.settings.ENVIRONMENT != "production":
            raw = self._memory_store.get(key)

        if not raw:
            return None

        data = json.loads(raw)
        return JobRecord(**data)

    def mark_started(self, job_id: str, celery_task_id: Optional[str] = None) -> Optional[JobRecord]:
        """Transition job status to PROCESSING."""
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc).isoformat()
        job.celery_task_id = celery_task_id
        self.save_job(job)

        logger.info(
            f"Job started: {job_id}",
            extra={
                "job_id": job_id,
                "celery_task_id": celery_task_id or "-",
                "status": JobStatus.PROCESSING.value,
            },
        )
        return job

    def mark_completed(
        self,
        job_id: str,
        output_path: str,
        output_size: int,
        processing_time: float,
        download_url: Optional[str] = None,
    ) -> Optional[JobRecord]:
        """Transition job status to COMPLETED."""
        job = self.get_job(job_id)
        if not job:
            return None

        now = datetime.now(timezone.utc).isoformat()
        job.status = JobStatus.COMPLETED
        job.output_path = output_path
        job.output_size = output_size
        job.processing_time = round(processing_time, 4)
        job.completed_at = now
        job.download_url = download_url
        self.save_job(job)

        logger.info(
            f"Job completed: {job_id} in {job.processing_time}s",
            extra={
                "job_id": job_id,
                "celery_task_id": job.celery_task_id or "-",
                "status": JobStatus.COMPLETED.value,
                "duration_sec": job.processing_time,
                "output_size_bytes": output_size,
            },
        )
        return job

    def mark_failed(
        self,
        job_id: str,
        error_message: str,
        retry_count: int = 0,
    ) -> Optional[JobRecord]:
        """Transition job status to FAILED."""
        job = self.get_job(job_id)
        if not job:
            return None

        now = datetime.now(timezone.utc).isoformat()
        job.status = JobStatus.FAILED
        job.error = error_message
        job.retry_count = retry_count
        job.completed_at = now
        self.save_job(job)

        logger.error(
            f"Job failed: {job_id}, error: {error_message}",
            extra={
                "job_id": job_id,
                "celery_task_id": job.celery_task_id or "-",
                "status": JobStatus.FAILED.value,
                "error": error_message,
                "retry_count": retry_count,
            },
        )
        return job


_job_service_instance: Optional[JobService] = None


def get_job_service(settings: Optional[Settings] = None) -> JobService:
    """Singleton getter for JobService."""
    global _job_service_instance
    if _job_service_instance is None:
        _job_service_instance = JobService(settings)
    return _job_service_instance
