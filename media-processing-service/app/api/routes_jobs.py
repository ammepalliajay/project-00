"""Job management and result download API endpoints."""

import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from app.core.config import get_settings
from app.core.logging import logger
from app.core.metrics import record_job_created
from app.models.jobs import (
    IMAGE_OPERATIONS,
    VIDEO_OPERATIONS,
    JobRecord,
    JobStatus,
    OperationType,
)
from app.models.schemas import JobCreateRequest, JobCreateResponse, JobDetailResponse
from app.services.job_service import get_job_service
from app.services.storage import get_storage_backend
from app.workers.tasks import process_media_job

router = APIRouter(tags=["Jobs"])


def _find_input_path(
    storage,
    input_path: Optional[str],
    input_file_id: Optional[str],
) -> str:
    """Resolve input path from explicit path or file_id."""
    if input_path and storage.exists(input_path):
        return input_path

    if input_file_id:
        # Check standard upload patterns
        candidate_prefixes = [
            f"uploads/{input_file_id}",
            f"{input_file_id}",
        ]
        # Check common extensions
        for prefix in candidate_prefixes:
            for ext in ["jpg", "jpeg", "png", "webp", "mp4", "mov", "avi"]:
                cand = f"{prefix}.{ext}"
                if storage.exists(cand):
                    return cand

    # If input_path was provided but didn't exist
    if input_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Input file not found at path: '{input_path}'",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either 'input_path' or a valid 'input_file_id' must be provided.",
    )


@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an asynchronous media processing job",
)
def create_job(request: JobCreateRequest):
    """Submit a processing job to Celery & RabbitMQ.

    Validates:
    - Operation compatibility with media type
    - Input file presence in storage
    - Enqueues to Celery broker
    - Records state in Redis
    """
    settings = get_settings()
    storage = get_storage_backend(settings)
    job_service = get_job_service(settings)

    resolved_input = _find_input_path(storage, request.input_path, request.input_file_id)

    # Validate media type compatibility
    ext = os.path.splitext(resolved_input)[1].lower().lstrip(".")
    is_image = ext in ("jpg", "jpeg", "png", "webp")
    is_video = ext in ("mp4", "mov", "avi")

    if is_image and request.operation in VIDEO_OPERATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot perform video operation '{request.operation.value}' on image file '{resolved_input}'",
        )
    if is_video and request.operation in IMAGE_OPERATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot perform image operation '{request.operation.value}' on video file '{resolved_input}'",
        )

    # Calculate input size if available
    input_size = None
    try:
        local_p = storage.resolve_to_local_path(resolved_input)
        if local_p.exists():
            input_size = local_p.stat().st_size
    except Exception:
        pass

    # Create job in Redis (strict failure in production if Redis is down)
    try:
        job_record = job_service.create_job(
            operation=request.operation,
            input_path=resolved_input,
            parameters=request.parameters,
            input_size=input_size,
        )
    except RuntimeError as r_err:
        logger.error(f"Failed to persist job record to Redis: {r_err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"State storage (Redis) is unavailable: {r_err}",
        )

    # Record metrics
    record_job_created(request.operation.value, is_video=is_video)

    # Enqueue asynchronously via Celery (must NOT simulate or fallback in production)
    try:
        async_result = process_media_job.delay(job_record.job_id)
        job_record.celery_task_id = async_result.id
        job_service.save_job(job_record)
    except Exception as e:
        if settings.ENVIRONMENT == "production" and not settings.CELERY_ALWAYS_EAGER:
            logger.error(
                f"Celery broker dispatch failed in production: {e}",
                extra={"job_id": job_record.job_id},
            )
            job_service.mark_failed(job_record.job_id, f"RabbitMQ broker dispatch error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Message broker (RabbitMQ) is unavailable to queue media processing task: {e}",
            )
        logger.warning(
            f"Celery broker dispatch failed ({e}), running job in direct synchronous mode for {settings.ENVIRONMENT}",
            extra={"job_id": job_record.job_id},
        )
        try:
            process_media_job(job_record.job_id)
        except Exception as sync_err:
            logger.error(f"Synchronous fallback failed: {sync_err}")

    return JobCreateResponse(
        job_id=job_record.job_id,
        status=JobStatus.PENDING,
        operation=job_record.operation,
        message="Job successfully queued for worker processing",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job execution status and result details",
)
def get_job_status(job_id: str):
    """Retrieve full status, timing, and result of a job from Redis."""
    job_service = get_job_service()
    try:
        job = job_service.get_job(job_id)
    except RuntimeError as r_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"State storage (Redis) is unavailable: {r_err}",
        )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: '{job_id}'",
        )

    return JobDetailResponse(
        job_id=job.job_id,
        status=job.status,
        operation=job.operation,
        input_path=job.input_path,
        output_path=job.output_path,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error,
        retry_count=job.retry_count,
        input_size=job.input_size,
        output_size=job.output_size,
        processing_time=job.processing_time,
        celery_task_id=job.celery_task_id,
        download_url=f"/jobs/{job_id}/download" if job.status == JobStatus.COMPLETED else None,
    )


@router.get(
    "/jobs/{job_id}/download",
    summary="Download processed media output file",
)
def download_job_output(job_id: str):
    """Download the completed media file for the specified job."""
    job_service = get_job_service()
    try:
        job = job_service.get_job(job_id)
    except RuntimeError as r_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"State storage (Redis) is unavailable: {r_err}",
        )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed yet (current status: {job.status.value}).",
        )

    if not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processed output file path is missing from job record.",
        )

    settings = get_settings()
    storage = get_storage_backend(settings)

    if settings.STORAGE_BACKEND.lower() == "s3":
        presigned_url = storage.get_url(job.output_path)
        return RedirectResponse(url=presigned_url)

    # Local file response
    local_path = storage.resolve_to_local_path(job.output_path)
    if not local_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found on storage disk.",
        )

    filename = local_path.name
    return FileResponse(
        path=str(local_path),
        filename=filename,
        media_type="application/octet-stream",
    )
