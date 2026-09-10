"""Media file upload route with strict MIME, size, and corruption validations."""

import os
from pathlib import Path
import tempfile
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import validate_path_traversal
from app.models.schemas import FileUploadResponse
from app.services.media_validation import (
    validate_uploaded_file,
    verify_image_integrity,
    verify_video_integrity,
)
from app.services.storage import get_storage_backend
from app.utils.ids import generate_file_id

router = APIRouter(tags=["Uploads"])


@router.post(
    "/uploads",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload media file for processing",
)
async def upload_file(file: UploadFile = File(...)):
    """Accept and validate media upload.

    Checks:
    - Whitelisted extension and MIME type
    - Path traversal guards
    - Maximum configured file size (streamed read)
    - Image/video corruption verification
    - UUID filename generation
    """
    settings = get_settings()
    storage = get_storage_backend(settings)

    # Validate header metadata
    safe_name, ext, media_type = validate_uploaded_file(
        file,
        max_size_bytes=settings.max_upload_size_bytes,
    )

    file_id = generate_file_id()
    unique_filename = f"{file_id}.{ext}"

    # Stream file to secure temporary file while enforcing max size
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp_path = Path(tmp.name)
        try:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Uploaded file exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB} MB",
                    )
                tmp.write(chunk)
            tmp.flush()

            if total_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty (0 bytes).",
                )

            # Integrity verification (detect corrupted uploads)
            if media_type == "image":
                verify_image_integrity(tmp_path)
            elif media_type == "video":
                verify_video_integrity(tmp_path)

            # Persist to configured storage backend (storage/uploads/{unique_filename})
            storage_dest = f"uploads/{unique_filename}"
            with open(tmp_path, "rb") as saved_f:
                saved_key = storage.save(
                    data=saved_f,
                    destination_path=storage_dest,
                    content_type=file.content_type,
                )

            logger.info(
                f"Uploaded file saved: {saved_key} ({total_bytes} bytes)",
                extra={"input_size_bytes": total_bytes},
            )

            return FileUploadResponse(
                file_id=file_id,
                filename=unique_filename,
                original_name=safe_name,
                size_bytes=total_bytes,
                content_type=file.content_type or f"{media_type}/{ext}",
                media_type=media_type,
                storage_path=saved_key,
            )

        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
