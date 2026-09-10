"""Celery background tasks for asynchronous image and video processing."""

import os
from pathlib import Path
import time
from typing import Optional
from app.core.config import get_settings
from app.core.logging import logger
from app.core.metrics import (
    record_job_started,
    record_job_completed,
    record_job_failed,
    record_job_retry,
)
from app.models.jobs import IMAGE_OPERATIONS, VIDEO_OPERATIONS, OperationType
from app.services.image_processor import ImageProcessor
from app.services.job_service import get_job_service
from app.services.storage import get_storage_backend
from app.services.video_processor import VideoProcessor
from app.workers.celery_app import celery_app


def execute_job_synchronously(job_id: str) -> dict:
    """Helper for testing or synchronous task invocation."""
    task = process_media_job
    return task(job_id)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="app.workers.tasks.process_media_job",
)
def process_media_job(self, job_id: str) -> dict:
    """Core media processing worker task with automatic retry and structured metrics."""
    settings = get_settings()
    job_service = get_job_service(settings)
    storage = get_storage_backend(settings)
    image_processor = ImageProcessor()
    video_processor = VideoProcessor()

    job = job_service.get_job(job_id)
    if not job:
        logger.error(f"Task received non-existent job_id: {job_id}")
        return {"status": "error", "message": f"Job {job_id} not found"}

    task_id = self.request.id or "direct_task"
    job_service.mark_started(job_id, celery_task_id=task_id)
    record_job_started()

    start_time = time.time()
    op = job.operation

    try:
        # Step 1: Resolve input file on local disk
        input_local = storage.resolve_to_local_path(job.input_path)
        if not input_local.exists():
            raise FileNotFoundError(f"Input file not found at {job.input_path}")

        # Step 2: Determine output file extension and temporary processing destination
        stem = input_local.stem
        if op in IMAGE_OPERATIONS:
            if op == OperationType.CONVERT_IMAGE:
                target_ext = str(job.parameters.get("format", "jpeg")).lower().replace("jpeg", "jpg")
            else:
                target_ext = input_local.suffix.lstrip(".").lower() or "jpg"
            out_filename = f"{stem}_{op.value}.{target_ext}"
            tmp_output = Path(settings.LOCAL_STORAGE_BASE_DIR) / "tmp" / out_filename
            tmp_output.parent.mkdir(parents=True, exist_ok=True)

            image_processor.execute(
                input_path=input_local,
                output_path=tmp_output,
                operation=op,
                parameters=job.parameters,
            )
        elif op in VIDEO_OPERATIONS:
            if op == OperationType.VIDEO_THUMBNAIL:
                target_ext = "jpg"
            else:
                target_ext = "mp4"
            out_filename = f"{stem}_{op.value}.{target_ext}"
            tmp_output = Path(settings.LOCAL_STORAGE_BASE_DIR) / "tmp" / out_filename
            tmp_output.parent.mkdir(parents=True, exist_ok=True)

            video_processor.execute(
                input_path=input_local,
                output_path=tmp_output,
                operation=op,
                parameters=job.parameters,
            )
        else:
            raise ValueError(f"Unknown operation: {op}")

        # Step 3: Persist output file into configured storage backend (local or S3)
        storage_dest = f"processed/{out_filename}"
        with open(tmp_output, "rb") as f:
            saved_key = storage.save(
                data=f,
                destination_path=storage_dest,
                content_type=f"image/{target_ext}" if target_ext in ("jpg", "png", "webp") else "video/mp4",
            )

        duration = time.time() - start_time
        output_size = tmp_output.stat().st_size
        download_url = storage.get_url(saved_key)

        # Cleanup temporary file if different from final path
        if tmp_output.exists() and "tmp" in str(tmp_output):
            try:
                tmp_output.unlink()
            except Exception:
                pass

        # Step 4: Update Redis state and Prometheus metrics
        job_service.mark_completed(
            job_id=job_id,
            output_path=saved_key,
            output_size=output_size,
            processing_time=duration,
            download_url=download_url,
        )
        record_job_completed(op.value, duration)

        return {
            "status": "completed",
            "job_id": job_id,
            "output_path": saved_key,
            "duration": duration,
        }

    except Exception as exc:
        duration = time.time() - start_time
        current_retry = getattr(self.request, "retries", 0)
        logger.error(
            f"Error processing job {job_id} (attempt {current_retry + 1}): {exc}",
            extra={"job_id": job_id, "error": str(exc)},
        )

        if current_retry < self.max_retries:
            backoff = settings.CELERY_RETRY_BACKOFF * (2 ** current_retry)
            record_job_retry(op.value)
            logger.warning(f"Retrying job {job_id} in {backoff}s...")
            raise self.retry(exc=exc, countdown=backoff)
        else:
            job_service.mark_failed(job_id, error_message=str(exc), retry_count=current_retry)
            record_job_failed(op.value)
            return {"status": "failed", "job_id": job_id, "error": str(exc)}
