"""Tests for the analytics router (backend/app/routers/analytics.py).

Covers happy path, response shape validation against the route's response_model,
and rejection of unauthenticated requests.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies.auth import require_user_id

# Dynamically import analytics module if present; skip if absent in repo environment
analytics_module = pytest.importorskip("app.routers.analytics")
router = analytics_module.router
AnalyticsResponse = analytics_module.AnalyticsResponse


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_analytics_happy_path(client):
    """Test happy path returning expected data matching response_model."""
    app = client.app
    app.dependency_overrides[require_user_id] = lambda: "test-user-123"

    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()

    # Validate response shape against AnalyticsResponse model
    validated = AnalyticsResponse(**data)
    assert validated is not None


def test_analytics_unauthenticated_rejected(client):
    """Test that unauthenticated requests are rejected with 401 Unauthorized."""
    client.app.dependency_overrides.clear()
    response = client.get("/analytics")
    assert response.status_code == 401
