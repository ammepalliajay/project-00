"""Tests for root and health check endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify root endpoint provides discovery and architecture metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "architecture" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"
    assert data["metrics"] == "/metrics"


def test_health_check_structure(client: TestClient):
    """Verify health endpoint checks all four critical services."""
    response = client.get("/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "services" in data
    services = data["services"]

    # Verify each required dependency check
    assert "application" in services
    assert "redis" in services
    assert "rabbitmq" in services
    assert "ffmpeg" in services

    # Application should always be healthy
    assert services["application"]["status"] == "healthy"
    # FFmpeg should be healthy since it is installed in container
    assert services["ffmpeg"]["status"] == "healthy"
    assert "version" in services["ffmpeg"]["message"].lower() or "ffmpeg" in services["ffmpeg"]["message"].lower()


def test_health_accurate_reporting_when_dependency_down(client: TestClient, monkeypatch):
    """Verify health check accurately flags unavailable Redis / RabbitMQ as unhealthy."""
    from app.api import routes_health

    # Mock Redis failure
    monkeypatch.setattr(routes_health, "check_redis", lambda: routes_health.ServiceHealthItem(
        status="unhealthy", message="Connection refused"
    ))

    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["services"]["redis"]["status"] == "unhealthy"


def test_health_check_all_healthy(client: TestClient, monkeypatch):
    """Verify 200 response when all services report healthy."""
    from app.api import routes_health

    monkeypatch.setattr(routes_health, "check_redis", lambda: routes_health.ServiceHealthItem(
        status="healthy", message="Redis PING ok"
    ))
    monkeypatch.setattr(routes_health, "check_rabbitmq", lambda h, p: routes_health.ServiceHealthItem(
        status="healthy", message="RabbitMQ socket ok"
    ))

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
