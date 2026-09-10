"""Storage backend abstraction supporting Local Disk and AWS S3."""

from abc import ABC, abstractmethod
import io
import os
from pathlib import Path
from typing import BinaryIO, Optional, Union
import boto3
from botocore.exceptions import ClientError
from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.core.security import validate_path_traversal
from app.utils.file_utils import ensure_directory


class BaseStorageBackend(ABC):
    """Abstract base class for storage engines."""

    @abstractmethod
    def save(
        self,
        data: Union[bytes, BinaryIO],
        destination_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Save file content and return storage key or path."""
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        """Retrieve full byte content of file."""
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Delete file from storage backend."""
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if file exists in storage backend."""
        pass

    @abstractmethod
    def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Return access URL or download URL for file."""
        pass

    @abstractmethod
    def resolve_to_local_path(self, file_path: str) -> Path:
        """Ensure file is accessible on local disk (for Pillow/FFmpeg)."""
        pass


class LocalStorageBackend(BaseStorageBackend):
    """Local filesystem storage implementation."""

    def __init__(self, base_dir: str = "./storage"):
        self.base_dir = ensure_directory(base_dir)
        self.uploads_dir = ensure_directory(self.base_dir / "uploads")
        self.processed_dir = ensure_directory(self.base_dir / "processed")

    def _resolve(self, file_path: str) -> Path:
        """Safely resolve path within base_dir, preventing traversal."""
        clean_path = file_path.lstrip("/\\")
        candidate = self.base_dir / clean_path
        return validate_path_traversal(self.base_dir, candidate)

    def save(
        self,
        data: Union[bytes, BinaryIO],
        destination_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        target_path = self._resolve(destination_path)
        ensure_directory(target_path.parent)

        if isinstance(data, bytes):
            target_path.write_bytes(data)
        else:
            with open(target_path, "wb") as f:
                if hasattr(data, "read"):
                    data.seek(0)
                    while chunk := data.read(1024 * 1024):
                        f.write(chunk)

        # Return relative storage key from base_dir
        rel = target_path.relative_to(self.base_dir).as_posix()
        return rel

    def get(self, file_path: str) -> bytes:
        target_path = self._resolve(file_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found in local storage: {file_path}")
        return target_path.read_bytes()

    def delete(self, file_path: str) -> bool:
        target_path = self._resolve(file_path)
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    def exists(self, file_path: str) -> bool:
        try:
            target_path = self._resolve(file_path)
            return target_path.is_file()
        except Exception:
            return False

    def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        # For local storage, returns the download API endpoint
        clean = file_path.replace("\\", "/").lstrip("/")
        return f"/storage/{clean}"

    def resolve_to_local_path(self, file_path: str) -> Path:
        target_path = self._resolve(file_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Local file does not exist: {file_path}")
        return target_path


class S3StorageBackend(BaseStorageBackend):
    """AWS S3 storage implementation using boto3."""

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        cache_dir: str = "./storage/s3_cache",
    ):
        self.bucket_name = bucket_name
        self.region = region
        self.cache_dir = ensure_directory(cache_dir)

        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        self.s3_client = session.client("s3")

    def save(
        self,
        data: Union[bytes, BinaryIO],
        destination_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        key = destination_path.lstrip("/\\").replace("\\", "/")
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if isinstance(data, bytes):
            stream = io.BytesIO(data)
        else:
            stream = data
            stream.seek(0)

        self.s3_client.upload_fileobj(stream, self.bucket_name, key, ExtraArgs=extra_args)
        return key

    def get(self, file_path: str) -> bytes:
        key = file_path.lstrip("/\\").replace("\\", "/")
        out = io.BytesIO()
        try:
            self.s3_client.download_fileobj(self.bucket_name, key, out)
            return out.getvalue()
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"S3 key not found: {key}")
            raise

    def delete(self, file_path: str) -> bool:
        key = file_path.lstrip("/\\").replace("\\", "/")
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete S3 key {key}: {e}")
            return False

    def exists(self, file_path: str) -> bool:
        key = file_path.lstrip("/\\").replace("\\", "/")
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            return False

    def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        key = file_path.lstrip("/\\").replace("\\", "/")
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for S3 key {key}: {e}")
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"

    def resolve_to_local_path(self, file_path: str) -> Path:
        key = file_path.lstrip("/\\").replace("\\", "/")
        local_file = self.cache_dir / key
        ensure_directory(local_file.parent)

        # Download from S3 to cache if not already cached
        if not local_file.exists():
            data = self.get(key)
            local_file.write_bytes(data)

        return local_file


def get_storage_backend(settings: Optional[Settings] = None) -> BaseStorageBackend:
    """Factory function returning configured storage backend."""
    cfg = settings or get_settings()

    if cfg.STORAGE_BACKEND.lower() == "s3":
        return S3StorageBackend(
            bucket_name=cfg.AWS_S3_BUCKET,
            region=cfg.AWS_REGION,
            access_key=cfg.AWS_ACCESS_KEY_ID,
            secret_key=cfg.AWS_SECRET_ACCESS_KEY,
            cache_dir=os.path.join(cfg.LOCAL_STORAGE_BASE_DIR, "s3_cache"),
        )

    return LocalStorageBackend(base_dir=cfg.LOCAL_STORAGE_BASE_DIR)
