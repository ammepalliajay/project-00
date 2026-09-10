"""Job enumeration and internal state data structures."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job lifecycle statuses."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OperationType(str, Enum):
    """Supported image and video operations."""
    # Image Operations
    RESIZE_IMAGE = "resize_image"
    CROP_IMAGE = "crop_image"
    COMPRESS_IMAGE = "compress_image"
    CONVERT_IMAGE = "convert_image"
    WATERMARK_IMAGE = "watermark_image"

    # Video Operations
    VIDEO_THUMBNAIL = "video_thumbnail"
    VIDEO_COMPRESS = "video_compress"
    VIDEO_TRANSCODE = "video_transcode"


IMAGE_OPERATIONS = {
    OperationType.RESIZE_IMAGE,
    OperationType.CROP_IMAGE,
    OperationType.COMPRESS_IMAGE,
    OperationType.CONVERT_IMAGE,
    OperationType.WATERMARK_IMAGE,
}

VIDEO_OPERATIONS = {
    OperationType.VIDEO_THUMBNAIL,
    OperationType.VIDEO_COMPRESS,
    OperationType.VIDEO_TRANSCODE,
}


class JobRecord(BaseModel):
    """Full representation of a media processing job stored in Redis / DB."""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    operation: OperationType
    parameters: Dict[str, Any] = Field(default_factory=dict)
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
