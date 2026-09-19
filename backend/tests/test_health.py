from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_check_status_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data["status"] == "ok"
    assert data["environment"] == settings.environment


def test_health_check_response_shape():
    response = client.get("/health")
    data = response.json()
    assert set(data.keys()) == {"status", "environment"}
    assert data.get("checkpoint_backend") is None


def test_health_check_environment_patched():
    with patch("app.main.settings.environment", "production"):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["environment"] == "production"


def test_health_check_server_error_branch():
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    with patch("app.main.settings") as mock_settings:
        type(mock_settings).environment = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Service down"))
        )
        response = client_no_raise.get("/health")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}
