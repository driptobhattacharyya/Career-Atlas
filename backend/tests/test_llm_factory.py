"""Unit tests for app.utils.llm_factory Gemini key rotation + retry logic."""
import pytest

from app.utils import llm_factory


class _FakeChat:
    """Stand-in for ChatGoogleGenerativeAI; records the api key it was built with."""
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_rotating_model_cycles_through_keys(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "google_api_keys", ["a", "b", "c"])
    monkeypatch.setattr(llm_factory, "ChatGoogleGenerativeAI", _FakeChat)

    keys = [llm_factory._get_rotating_gemini_model("m", 0.2, attempt).kwargs["google_api_key"] for attempt in range(4)]
    assert keys == ["a", "b", "c", "a"]  # attempt % len(keys)


def test_rotating_model_raises_without_keys(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "google_api_keys", [])
    with pytest.raises(ValueError, match="No GOOGLE_API_KEY"):
        llm_factory._get_rotating_gemini_model("m", 0.2, 0)


def test_invoke_gemini_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    class _Flaky:
        def invoke(self, prompt):
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError("rate limited")
            return "ok"

    monkeypatch.setattr(llm_factory, "_get_rotating_gemini_model", lambda *a, **k: _Flaky())
    monkeypatch.setattr(llm_factory.time, "sleep", lambda s: None)  # no real backoff

    assert llm_factory.invoke_gemini("prompt", max_retries=5) == "ok"
    assert calls["n"] == 3


def test_invoke_gemini_raises_last_exception_after_exhausting_retries(monkeypatch):
    class _Broken:
        def invoke(self, prompt):
            raise RuntimeError("always fails")

    monkeypatch.setattr(llm_factory, "_get_rotating_gemini_model", lambda *a, **k: _Broken())
    monkeypatch.setattr(llm_factory.time, "sleep", lambda s: None)

    with pytest.raises(RuntimeError, match="always fails"):
        llm_factory.invoke_gemini("prompt", max_retries=3)


async def test_ainvoke_gemini_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    class _Flaky:
        async def ainvoke(self, prompt):
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("transient")
            return "async-ok"

    monkeypatch.setattr(llm_factory, "_get_rotating_gemini_model", lambda *a, **k: _Flaky())

    async def _no_sleep(_s):
        return None
    monkeypatch.setattr(llm_factory.asyncio, "sleep", _no_sleep)

    assert await llm_factory.ainvoke_gemini("prompt", max_retries=3) == "async-ok"
    assert calls["n"] == 2
