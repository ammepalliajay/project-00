"""Structured logging configuration for microservice and Celery workers."""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict


def scrub_secrets(text: str) -> str:
    """Mask credentials and sensitive strings from log messages."""
    if not isinstance(text, str):
        return text
    scrubbed = text
    # Mask password/secret/tokens
    scrubbed = re.sub(
        r"(?i)(password|secret|access_key|api_key|token)[\s:=]+['\"]?([^'\"&\s,]+)['\"]?",
        r"\1: [REDACTED]",
        scrubbed,
    )
    # Mask AMQP passwords
    scrubbed = re.sub(r"(amqp://[^:]+:)[^@]+(@)", r"\1[REDACTED]\2", scrubbed)
    # Mask Redis passwords
    scrubbed = re.sub(r"redis://:[^@]+@", r"redis://:[REDACTED]@", scrubbed)
    return scrubbed


class StructuredJsonFormatter(logging.Formatter):
    """Format logs as structured JSON with execution metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub_secrets(record.getMessage()),
        }

        # Optional metadata fields
        for field in [
            "job_id",
            "celery_task_id",
            "operation",
            "status",
            "duration_sec",
            "input_size_bytes",
            "output_size_bytes",
            "retry_count",
            "error",
        ]:
            val = getattr(record, field, None)
            if val is not None:
                log_data[field] = val

        if record.exc_info:
            # Format exception safely without exposing credentials
            log_data["exception"] = scrub_secrets(self.formatException(record.exc_info))

        return json.dumps(log_data)


def configure_logging(log_level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """Configure root and application loggers."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if json_format:
            handler.setFormatter(StructuredJsonFormatter())
        else:
            fmt = "%(asctime)s [%(levelname)s] [job=%(job_id)s task=%(celery_task_id)s] %(message)s"
            formatter = logging.Formatter(fmt)

            # Custom filter to provide default values for job_id and celery_task_id
            class ContextFilter(logging.Filter):
                def filter(self, rec: logging.LogRecord) -> bool:
                    if not hasattr(rec, "job_id"):
                        rec.job_id = "-"
                    if not hasattr(rec, "celery_task_id"):
                        rec.celery_task_id = "-"
                    rec.msg = scrub_secrets(str(rec.msg))
                    return True

            handler.addFilter(ContextFilter())
            handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    # Suppress overly chatty 3rd party loggers
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    return logging.getLogger("media_service")


logger = configure_logging()
