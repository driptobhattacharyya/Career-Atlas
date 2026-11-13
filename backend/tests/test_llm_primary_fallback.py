"""OpenAI-compatible primary with Gemini/Groq fallback in app.utils.llm_factory (model layer mocked)."""
import pytest
from langchain_core.runnables import RunnableLambda

from app.utils import llm_factory


class _Msg:
    def __init__(self, content):
        self.content = content


class _Model:
    """Fake chat model; `result` may be an Exception to raise."""
    def __init__(self, result, log=None, tag=""):
        self.result, self.log, self.tag = result, log, tag

    def _run(self, *_):
        if self.log is not None:
            self.log.append(self.tag)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    def invoke(self, prompt):
        return self._run()

    async def ainvoke(self, prompt):
        return self._run()

    def with_structured_output(self, schema, **_):
        return RunnableLambda(self._run)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "use_self_hosted_llm", True)
    monkeypatch.setattr(llm_factory.settings, "google_api_keys", ["g"])
    monkeypatch.setattr(llm_factory.settings, "groq_api_key", "")
    monkeypatch.setattr(llm_factory.time, "sleep", lambda s: None)
    llm_factory.get_groq_model.cache_clear()


def _wire(monkeypatch, primary, gemini, log):
    monkeypatch.setattr(llm_factory, "get_groq_model", lambda *a, **k: _Model(primary, log, "openai"))
    monkeypatch.setattr(llm_factory, "_get_rotating_gemini_model", lambda *a, **k: _Model(gemini, log, "gemini"))


def test_primary_success_skips_gemini(monkeypatch):
    log = []
    _wire(monkeypatch, "oa", "gem", log)
    assert llm_factory.invoke_gemini("p") == "oa"
    assert log == ["openai"]


def test_primary_failure_falls_back_to_gemini_sync(monkeypatch, caplog):
    log = []
    _wire(monkeypatch, RuntimeError("sk-secret"), "gem", log)
    assert llm_factory.invoke_gemini("p") == "gem"
    assert log == ["openai", "gemini"]
    assert "RuntimeError" in caplog.text and "sk-secret" not in caplog.text


async def test_primary_failure_falls_back_to_gemini_async(monkeypatch):
    log = []
    _wire(monkeypatch, RuntimeError("down"), "gem", log)
    assert await llm_factory.ainvoke_gemini("p") == "gem"
    assert log == ["openai", "gemini"]


def test_primary_failure_without_google_key_reraises(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "google_api_keys", [])
    log = []
    err = RuntimeError("local server down")
    _wire(monkeypatch, err, "gem", log)
    with pytest.raises(RuntimeError) as exc:
        llm_factory.invoke_gemini("p")
    assert exc.value is err and log == ["openai"]


async def test_async_primary_failure_without_google_key_reraises(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "google_api_keys", [])
    _wire(monkeypatch, ValueError("x"), "gem", [])
    with pytest.raises(ValueError, match="x"):
        await llm_factory.ainvoke_gemini("p")


def test_structured_chain_falls_back_to_groq(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "groq_api_key", "gq")
    monkeypatch.setattr(llm_factory, "get_groq_model", lambda *a, **k: _Model(RuntimeError("quota")))
    monkeypatch.setattr(llm_factory, "_get_groq_fallback_model", lambda *a, **k: _Model("groq-result"))
    chain = llm_factory.build_groq_structured_chain(RunnableLambda(lambda x: x), dict)
    assert chain.invoke({}) == "groq-result"


def test_structured_chain_without_groq_key_propagates(monkeypatch):
    monkeypatch.setattr(llm_factory, "get_groq_model", lambda *a, **k: _Model(RuntimeError("quota")))
    chain = llm_factory.build_groq_structured_chain(RunnableLambda(lambda x: x), dict)
    with pytest.raises(RuntimeError, match="quota"):
        chain.invoke({})


def test_flag_off_never_builds_primary(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "use_self_hosted_llm", False)
    monkeypatch.setattr(llm_factory.settings, "groq_api_key", "gq")

    def _boom(**k):
        raise AssertionError("ChatOpenAI constructed with flag off")

    monkeypatch.setattr(llm_factory, "ChatOpenAI", _boom)
    monkeypatch.setattr(llm_factory, "_get_rotating_gemini_model", lambda *a, **k: _Model("gem"))
    monkeypatch.setattr(llm_factory, "ChatGroq", lambda **k: _Model("groq"))
    assert llm_factory.invoke_gemini("p") == "gem"
    chain = llm_factory.get_structured_model(dict)
    assert not hasattr(chain, "fallbacks") and chain.invoke({}) == "groq"


@pytest.mark.parametrize("omit,expected", [(True, False), (False, True)])
def test_omit_temperature_setting(monkeypatch, omit, expected):
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_omit_temperature", omit)
    seen = {}
    monkeypatch.setattr(llm_factory, "ChatOpenAI", lambda **k: seen.update(k) or object())
    llm_factory.get_groq_model(None, 0.2)
    assert ("temperature" in seen) is expected


# ── Real ChatOpenAI over a mocked transport: what the OpenAI API actually receives ──

import json  # noqa: E402

import httpx  # noqa: E402

from app.deep_researcher.schemas import JudgeVerdict  # noqa: E402
from app.gap_analysis.schemas import GapAnalysisResponse  # noqa: E402

_GAPS_JSON = {
    "gaps": [{"skill": "Docker", "category": "tool", "relevance": "80", "difficulty": "Medium",
              "prerequisites": [], "why": "Ships services."}],
    "justifications": {"Docker": "Needed to deploy."},
}
_VERDICT_JSON = {"overall_score": 4, "pass_fail": "pass"}


def _openai_transport(monkeypatch, content: dict):
    """Point ChatOpenAI at a fake OpenAI server; returns the list of request bodies."""
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 0, "model": "gpt-test",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": json.dumps(content)}}],
        })

    transport = httpx.MockTransport(handler)
    real = llm_factory.ChatOpenAI
    monkeypatch.setattr(llm_factory, "ChatOpenAI", lambda **k: real(
        **k, http_client=httpx.Client(transport=transport),
        http_async_client=httpx.AsyncClient(transport=transport)))
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_model", "gpt-test")
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_base_url", "https://api.openai.com/v1")
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_api_key", "sk-test")
    monkeypatch.setattr(llm_factory, "_get_rotating_gemini_model",
                        lambda *a, **k: pytest.fail("fell back to Gemini"))
    return bodies


def _assert_non_strict(body, name):
    rf = body["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["name"] == name
    # Strict mode 400s on dict fields / defaults, which silently routed to the fallback.
    assert rf["json_schema"]["strict"] is False
    assert body["model"] == "gpt-test"


async def test_gap_analysis_schema_served_by_openai_non_strict(monkeypatch):
    bodies = _openai_transport(monkeypatch, _GAPS_JSON)
    result = await llm_factory.ainvoke_gemini("p", temperature=0.0, schema=GapAnalysisResponse)
    assert isinstance(result, GapAnalysisResponse)
    assert result.gaps[0].relevance == 80 and result.justifications == {"Docker": "Needed to deploy."}
    _assert_non_strict(bodies[0], "GapAnalysisResponse")
    assert "justifications" in bodies[0]["response_format"]["json_schema"]["schema"]["properties"]


def test_structured_chain_schema_served_by_openai_non_strict(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "groq_api_key", "gq")
    monkeypatch.setattr(llm_factory, "_get_groq_fallback_model",
                        lambda *a, **k: _Model(AssertionError("fell back to Groq")))
    bodies = _openai_transport(monkeypatch, _VERDICT_JSON)
    verdict = llm_factory.get_structured_model(JudgeVerdict, temperature=0.0).invoke("p")
    assert isinstance(verdict, JudgeVerdict) and verdict.confidence == "medium"
    _assert_non_strict(bodies[0], "JudgeVerdict")


def test_groq_fallback_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(llm_factory.settings, "groq_api_key", "gq")
    monkeypatch.setattr(llm_factory, "get_groq_model", lambda *a, **k: _Model(RuntimeError("bad model")))
    monkeypatch.setattr(llm_factory, "_get_groq_fallback_model", lambda *a, **k: _Model("groq-result"))
    assert llm_factory.get_structured_model(dict).invoke("p") == "groq-result"
    assert "Groq fallback" in caplog.text


def test_describe_llm_routing_flag_on_hides_secrets(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_model", "gpt-test")
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_base_url", "https://user:pw@api.openai.com/v1")
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_api_key", "sk-secret")
    monkeypatch.setattr(llm_factory.settings, "groq_api_key", "gq")
    info = llm_factory.describe_llm_routing()
    assert info["primary"] == "openai-compatible" and info["model"] == "gpt-test"
    assert info["host"] == "api.openai.com" and info["api_key_set"] is True
    assert info["fallbacks"]["gaps_resume_jobs"] == llm_factory.GEMINI_DEFAULT_MODEL
    assert "sk-secret" not in json.dumps(info) and "pw" not in json.dumps(info)


def test_describe_llm_routing_placeholder_key_and_flag_off(monkeypatch):
    monkeypatch.setattr(llm_factory.settings, "self_hosted_llm_api_key", "sk-no-key-required")
    assert llm_factory.describe_llm_routing()["api_key_set"] is False
    monkeypatch.setattr(llm_factory.settings, "use_self_hosted_llm", False)
    assert llm_factory.describe_llm_routing()["primary"] == "groq+gemini"
