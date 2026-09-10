"""Application configuration using Pydantic Settings."""

from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Microservice environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Settings
    APP_NAME: str = "Distributed Media Processing Microservice"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    MAX_UPLOAD_SIZE_MB: int = 500

    # Storage Settings
    STORAGE_BACKEND: str = "local"  # 'local' or 's3'
    LOCAL_STORAGE_BASE_DIR: str = "./storage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "media-processing-bucket"
    S3_PRESIGNED_EXPIRATION_SECONDS: int = 3600

    # Redis (Job State & Result Store)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # RabbitMQ (Celery Message Broker)
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"

    # Celery Execution
    CELERY_TASK_TIMEOUT: int = 600
    CELERY_MAX_RETRIES: int = 3
    CELERY_RETRY_BACKOFF: int = 5
    CELERY_ALWAYS_EAGER: bool = False  # For local/testing without broker

    @property
    def max_upload_size_bytes(self) -> int:
        """Calculate maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def redis_url(self) -> str:
        """Construct Redis connection string."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def rabbitmq_url(self) -> str:
        """Construct RabbitMQ connection string for Celery broker."""
        vhost = self.RABBITMQ_VHOST.lstrip("/")
        if not vhost:
            vhost_part = ""
        else:
            vhost_part = f"/{vhost}"
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{vhost_part}"


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()
