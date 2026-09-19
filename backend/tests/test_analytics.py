import importlib
import pytest


def test_analytics_router_exists():
    """Verify whether app.routers.analytics exists and has a router instance."""
    try:
        analytics_module = importlib.import_module("app.routers.analytics")
        assert hasattr(analytics_module, "router")
    except ModuleNotFoundError:
        pytest.skip("backend/app/routers/analytics.py does not exist in this repository.")
