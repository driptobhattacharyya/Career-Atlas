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

def test_build_groq_structured_chain(monkeypatch):
    calls = []

    class _MockStructuredModel:
        def __init__(self, schema):
            self.schema = schema

    class _MockModel:
        def __init__(self, model_name, temperature):
            self.model_name = model_name
            self.temperature = temperature

        def with_structured_output(self, schema):
            calls.append(("with_structured_output", schema))
            return _MockStructuredModel(schema)

    def _mock_get_groq_model(model_name, temperature):
        calls.append(("get_groq_model", model_name, temperature))
        return _MockModel(model_name, temperature)

    monkeypatch.setattr(llm_factory, "get_groq_model", _mock_get_groq_model)

    class _MockPrompt:
        def __or__(self, other):
            calls.append(("__or__", other))
            return "chain"

    prompt = _MockPrompt()
    schema = {"type": "object"}

    chain = llm_factory.build_groq_structured_chain(prompt, schema, temperature=0.5, model_name="test-model")

    assert chain == "chain"
    assert len(calls) == 3
    assert calls[0] == ("get_groq_model", "test-model", 0.5)
    assert calls[1] == ("with_structured_output", schema)
    assert calls[2][0] == "__or__"
    assert isinstance(calls[2][1], _MockStructuredModel)
