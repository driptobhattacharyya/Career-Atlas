"""Unit tests for app.dependencies.auth.get_current_user_id.

The dev auth bypass must fail closed: it may only fire when
settings.environment is explicitly one of "development" / "dev" / "local".
Since `settings` is a module-level singleton built at import time (see
app/config.py), tests patch attributes on that singleton directly rather
than setting environment variables (which would have no effect after
import).
"""
import pytest
from fastapi import HTTPException

from app.dependencies import auth


def test_verified_token_short_circuits_dev_bypass_check(monkeypatch):
    """A valid token's user id is returned regardless of environment/bypass config."""
    monkeypatch.setattr(auth.settings, "environment", "production")
    monkeypatch.setattr(auth.settings, "dev_bypass_auth", False)
    monkeypatch.setattr(auth.settings, "dev_user_id", "")

    assert auth.get_current_user_id(user_id="real-user-123") == "real-user-123"


@pytest.mark.parametrize("environment", ["production", "staging", "", "PRODUCTION"])
def test_dev_bypass_refused_when_not_dev_environment(monkeypatch, environment):
    monkeypatch.setattr(auth.settings, "environment", environment)
    monkeypatch.setattr(auth.settings, "dev_bypass_auth", True)
    monkeypatch.setattr(auth.settings, "dev_user_id", "dev-user-1")

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user_id(user_id=None)
    assert exc_info.value.status_code == 401


@pytest.mark.parametrize("environment", ["development", "dev", "local", "DEVELOPMENT", "Local"])
def test_dev_bypass_allowed_in_dev_environments(monkeypatch, environment):
    monkeypatch.setattr(auth.settings, "environment", environment)
    monkeypatch.setattr(auth.settings, "dev_bypass_auth", True)
    monkeypatch.setattr(auth.settings, "dev_user_id", "dev-user-1")

    assert auth.get_current_user_id(user_id=None) == "dev-user-1"


def test_dev_bypass_requires_flag_even_in_dev_environment(monkeypatch):
    monkeypatch.setattr(auth.settings, "environment", "development")
    monkeypatch.setattr(auth.settings, "dev_bypass_auth", False)
    monkeypatch.setattr(auth.settings, "dev_user_id", "dev-user-1")

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user_id(user_id=None)
    assert exc_info.value.status_code == 401


def test_dev_bypass_requires_dev_user_id_even_in_dev_environment(monkeypatch):
    monkeypatch.setattr(auth.settings, "environment", "development")
    monkeypatch.setattr(auth.settings, "dev_bypass_auth", True)
    monkeypatch.setattr(auth.settings, "dev_user_id", "")

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user_id(user_id=None)
    assert exc_info.value.status_code == 401


def test_no_token_and_no_bypass_is_rejected(monkeypatch):
    monkeypatch.setattr(auth.settings, "environment", "development")
    monkeypatch.setattr(auth.settings, "dev_bypass_auth", False)
    monkeypatch.setattr(auth.settings, "dev_user_id", "")

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user_id(user_id=None)
    assert exc_info.value.status_code == 401
