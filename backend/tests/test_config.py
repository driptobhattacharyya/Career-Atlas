"""Unit tests for app.config Google API key discovery."""
import app.config as config


def test_get_google_api_keys_collects_main_and_numbered(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "main")
    monkeypatch.setenv("GOOGLE_API_KEY_1", "k1")
    monkeypatch.setenv("GOOGLE_API_KEY_2", "k2")
    monkeypatch.delenv("GOOGLE_API_KEY_3", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY_4", raising=False)
    assert config._get_google_api_keys() == ["main", "k1", "k2"]


def test_get_google_api_keys_dedupes_and_strips(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "  dup  ")
    monkeypatch.setenv("GOOGLE_API_KEY_1", "dup")   # duplicate -> skipped
    monkeypatch.setenv("GOOGLE_API_KEY_2", "unique")
    monkeypatch.delenv("GOOGLE_API_KEY_3", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY_4", raising=False)
    assert config._get_google_api_keys() == ["dup", "unique"]


def test_get_google_api_keys_empty_when_unset(monkeypatch):
    for name in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_1", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3", "GOOGLE_API_KEY_4"]:
        monkeypatch.delenv(name, raising=False)
    assert config._get_google_api_keys() == []
