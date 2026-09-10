"""Prometheus metrics endpoint exposing real-time microservice statistics."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus-compatible performance and job metrics",
)
def get_metrics():
    """Return Prometheus text format metrics for Prometheus scraping."""
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
