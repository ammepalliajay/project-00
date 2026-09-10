"""API Request and Response Pydantic Schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.models.jobs import JobStatus, OperationType


class JobCreateRequest(BaseModel):
    """Schema for submitting a new processing job."""

    operation: OperationType
    input_file_id: Optional[str] = Field(
        default=None,
        description="File ID returned from /uploads endpoint",
    )
    input_path: Optional[str] = Field(
        default=None,
        description="Direct path or storage key (for local or s3 references)",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operation-specific arguments (e.g., width, height, quality, format, watermark_text)",
    )


class JobCreateResponse(BaseModel):
    """Immediate response after job creation."""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    operation: OperationType
    message: str = "Job created and queued for processing"


class JobDetailResponse(BaseModel):
    """Detailed job status information."""

    job_id: str
    status: JobStatus
    operation: OperationType
    input_path: str
    output_path: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    processing_time: Optional[float] = None
    celery_task_id: Optional[str] = None
    download_url: Optional[str] = None


class FileUploadResponse(BaseModel):
    """Metadata response after successful media upload."""

    file_id: str
    filename: str
    original_name: str
    size_bytes: int
    content_type: str
    media_type: str  # 'image' or 'video'
    storage_path: str


class ServiceHealthItem(BaseModel):
    """Individual service health status."""

    status: str  # 'healthy', 'degraded', 'unhealthy'
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Overall microservice health check response."""

    status: str  # 'healthy' or 'unhealthy'
    environment: str
    timestamp: str
    services: Dict[str, ServiceHealthItem]
