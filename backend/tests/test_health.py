from unittest.mock import MagicMock
from app.db.session import get_db
from app.main import app
from app.services.health_service import HealthService


def test_root_endpoint(client):
    """Test root endpoint returns application metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "DayFlow"
    assert "version" in data
    assert data["status"] == "online"
    assert data["documentation"] == "/docs"


def test_health_liveness_endpoint(client):
    """Test health liveness endpoint returns ok."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend"
    assert "timestamp" in data


def test_health_readiness_endpoint_success(client):
    """Test health readiness endpoint when database is connected."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_health_readiness_endpoint_db_failure(client, monkeypatch):
    """Test health readiness endpoint returns 503 when database connectivity fails."""
    # Mock HealthService to simulate database failure
    monkeypatch.setattr(HealthService, "check_database_readiness", lambda db: False)

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["service"] == "backend"
    assert data["database"] == "disconnected"
    assert "Could not establish connection" in data["details"]


def test_health_service_exception_handling():
    """Directly test HealthService handles exceptions gracefully."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("DB Connection timeout")
    
    result = HealthService.check_database_readiness(mock_db)
    assert result is False

