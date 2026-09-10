"""Celery application instance and broker configuration."""

from celery import Celery
from app.core.config import get_settings


def create_celery_app() -> Celery:
    """Instantiate and configure Celery with RabbitMQ broker and Redis result backend."""
    settings = get_settings()

    app = Celery(
        "media_processor",
        broker=settings.rabbitmq_url,
        backend=settings.redis_url,
        include=["app.workers.tasks"],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_default_queue="media_processing",
        task_routes={
            "app.workers.tasks.process_media_job": {"queue": "media_processing"},
        },
        task_time_limit=settings.CELERY_TASK_TIMEOUT,
        task_soft_time_limit=settings.CELERY_TASK_TIMEOUT - 30,
        task_always_eager=settings.CELERY_ALWAYS_EAGER,
        task_eager_propagates=True,
    )

    return app


celery_app = create_celery_app()
