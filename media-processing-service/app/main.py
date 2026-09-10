"""FastAPI main application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes_health import router as health_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_uploads import router as uploads_router
from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import sanitize_error_detail
from app.utils.file_utils import ensure_directory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Ensure storage directories exist
    ensure_directory(f"{settings.LOCAL_STORAGE_BASE_DIR}/uploads")
    ensure_directory(f"{settings.LOCAL_STORAGE_BASE_DIR}/processed")
    ensure_directory(f"{settings.LOCAL_STORAGE_BASE_DIR}/tmp")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Asynchronous event-driven distributed media processing service "
            "powered by FastAPI, Celery, RabbitMQ, Redis, Pillow, and FFmpeg."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(health_router)
    app.include_router(uploads_router)
    app.include_router(jobs_router)
    app.include_router(metrics_router)

    # Root endpoint
    @app.get("/", tags=["General"])
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health",
            "metrics": "/metrics",
            "architecture": {
                "api": "FastAPI",
                "broker": "RabbitMQ",
                "worker": "Celery",
                "status_backend": "Redis",
                "media_engines": ["Pillow", "FFmpeg"],
                "storage": settings.STORAGE_BACKEND,
            },
        }

    # Global safe exception handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
        safe_msg = sanitize_error_detail(exc, debug=(settings.ENVIRONMENT == "development"))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": safe_msg},
        )

    return app


app = create_app()
