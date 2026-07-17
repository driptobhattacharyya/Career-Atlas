"""Unit tests for app.job_hunter.agent (pure scoring / parsing logic)."""
import numpy as np
import pytest

from app.job_hunter import agent
from app.job_hunter.schemas import JobResult


# ── text / json helpers ──────────────────────────────────────────────────

def test_strip_code_fences_removes_json_fence():
    assert agent._strip_code_fences('```json\n[{"a": 1}]\n```') == '[{"a": 1}]'


def test_strip_code_fences_plain_text():
    assert agent._strip_code_fences("  hello  ") == "hello"
    assert agent._strip_code_fences(None) == ""


def test_safe_json_parse_list():
    assert agent.safe_json_parse('[{"x": 1}]') == [{"x": 1}]


def test_safe_json_parse_dict_wrapped_in_list():
    assert agent.safe_json_parse('{"x": 1}') == [{"x": 1}]


def test_safe_json_parse_double_encoded_string():
    assert agent.safe_json_parse('"[{\\"x\\": 1}]"') == [{"x": 1}]


def test_safe_json_parse_fenced():
    assert agent.safe_json_parse('```json\n[{"x": 1}]\n```') == [{"x": 1}]


def test_safe_json_parse_invalid_returns_empty():
    assert agent.safe_json_parse("not json") == []
    assert agent.safe_json_parse(None) == []


def test_tokenize_lowercases_and_keeps_symbols():
    assert agent.tokenize("Python, C++ and C#.NET") == {"python", "c++", "c#.net", "and"}
    assert agent.tokenize(None) == set()


# ── location filtering ─────────────────────────────────────────────────────

def test_location_filter_empty_job_location_passes():
    assert agent.location_filter("", "pune") is True


def test_location_filter_remote():
    assert agent.location_filter("Remote - India", "remote") is True
    assert agent.location_filter("Pune, India", "remote") is False


def test_location_filter_hybrid_matches_remote_too():
    assert agent.location_filter("Hybrid role", "hybrid") is True
    assert agent.location_filter("Fully Remote", "hybrid") is True
    assert agent.location_filter("On-site Pune", "hybrid") is False


def test_location_filter_city_aliases():
    assert agent.location_filter("Bengaluru, KA", "bangalore") is True
    assert agent.location_filter("Bombay office", "mumbai") is True
    assert agent.location_filter("Chennai", "mumbai") is False


def test_location_filter_unknown_city_uses_literal_match():
    assert agent.location_filter("Kolkata, WB", "kolkata") is True
    assert agent.location_filter("Delhi", "kolkata") is False


# ── fallback listings ──────────────────────────────────────────────────────

def test_search_url_encodes_query_and_location():
    url = agent._search_url("Data Scientist", "New York")
    assert "keywords=Data%20Scientist" in url
    assert "location=New%20York" in url
    assert url.startswith("https://www.linkedin.com/jobs/search/")


def test_fallback_jobs_count_and_company_cycling():
    jobs = agent._fallback_jobs("Backend Engineer", "Pune", count=5)
    assert len(jobs) == 5
    assert jobs[0]["company"] == agent.FALLBACK_COMPANIES[0]
    assert all(j["location"] == "Pune" for j in jobs)
    assert all(j["job_id"].startswith("fallback-") for j in jobs)


def test_fallback_jobs_defaults_location_to_remote():
    jobs = agent._fallback_jobs("QA", "", count=2)
    assert len(jobs) == 2
    assert jobs[0]["location"] == "Remote"


# ── vector math ─────────────────────────────────────────────────────────────

def test_cosine_sim_identical_vectors():
    v = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert agent.cosine_sim(v, v) == pytest.approx(1.0, abs=1e-4)


def test_cosine_sim_orthogonal_vectors():
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0], dtype=np.float32)
    assert agent.cosine_sim(a, b) == pytest.approx(0.0, abs=1e-6)


# ── resume representation ───────────────────────────────────────────────────

def test_build_resume_representation_aggregates_skills():
    resume = {
        "skills": ["Python", "SQL"],
        "programming_languages": ["Go"],
        "spoken_languages": ["English"],
        "keywords": ["ETL"],
        "experience": [{"technologies": ["Airflow"], "description_bullets": ["Built pipelines"]}],
        "projects": [{"technologies": ["Docker"], "description": "A project"}],
        "summary": "Data engineer",
    }
    structured, semantic = agent.build_resume_representation(resume)
    assert structured["skills"] == {"python", "sql", "go", "english", "etl", "airflow", "docker"}
    assert structured["has_experience"] is True
    assert structured["has_education"] is False
    assert "data engineer" in semantic.lower()
    assert "airflow" in semantic.lower()


def test_build_resume_representation_handles_empty_resume():
    structured, semantic = agent.build_resume_representation({})
    assert structured["skills"] == set()
    assert structured["has_experience"] is False
    assert structured["has_education"] is False
    assert semantic == ""


# ── scoring (no external embeddings -> deterministic fallback path) ─────────

def test_score_jobs_uses_semantic_fallback_when_embeddings_unavailable(monkeypatch):
    # Force the embedding call to fail so score_jobs takes the deterministic path.
    monkeypatch.setattr(agent, "embed_batch", lambda texts: (_ for _ in ()).throw(RuntimeError("no key")))
    resume = {"skills": ["Python", "SQL"], "experience": [{"title": "Eng"}], "education": [{"degree": "BS"}]}
    jobs = [
        {"title": "Python Developer", "description": "We love python and sql"},
        {"title": "Marketing Lead", "description": "brand campaigns"},
    ]
    scored = agent.score_jobs(resume, jobs)
    assert len(scored) == 2
    py = scored[0]["_scores"]
    mk = scored[1]["_scores"]
    # Python job overlaps both skills -> skill_overlap 1.0; marketing job -> 0.0
    assert py["skill_overlap"] == pytest.approx(1.0)
    assert mk["skill_overlap"] == pytest.approx(0.0)
    assert py["final"] > mk["final"]
    assert scored[0]["_matched_tokens"] == ["python", "sql"]
    # experience + education present -> full sub-scores
    assert py["experience"] == 1.0
    assert py["education"] == 1.0


def test_score_jobs_experience_education_defaults():
    # No experience / education -> reduced sub-scores, embeddings absent (no jina key).
    resume = {"skills": ["python"]}
    jobs = [{"title": "Dev", "description": "python role"}]
    scored = agent.score_jobs(resume, jobs)
    s = scored[0]["_scores"]
    assert s["experience"] == 0.4
    assert s["education"] == 0.5


# ── compact resume + prompt building ────────────────────────────────────────

def test_build_compact_resume_for_llm():
    resume = {
        "skills": ["Python"],
        "experience": [{"title": "Eng", "company": "Acme", "start_date": "2020", "end_date": "2022", "technologies": ["Go", ""]}],
        "education": [{"degree": "BS", "institution": "MIT"}],
        "projects": [{"name": "Atlas", "technologies": ["Docker"]}],
    }
    compact = agent.build_compact_resume_for_llm(resume)
    assert compact["experience_titles"] == ["Eng at Acme (2020–2022)"]
    assert compact["experience_technologies"] == ["Go"]  # blank filtered out
    assert compact["education"] == ["BS from MIT"]
    assert compact["projects"] == ["Atlas"]
    assert compact["project_technologies"] == ["Docker"]


def test_build_bulk_explanation_prompt_contains_ids():
    resume = {"skills": ["Python"]}
    jobs = [{"job_id": "abc", "title": "Dev", "company": "Acme", "description": "x" * 1000, "_scores": {"final": 0.5}}]
    prompt = agent.build_bulk_explanation_prompt(resume, jobs)
    assert "abc" in prompt
    assert "JSON array" in prompt
    # description is truncated to 800 chars in the compact job payload
    assert "x" * 801 not in prompt


# ── gemini content flattening ───────────────────────────────────────────────

class _Resp:
    def __init__(self, content):
        self.content = content


def test_gemini_generate_json_string_content(monkeypatch):
    monkeypatch.setattr(agent, "invoke_gemini", lambda *a, **k: _Resp("hello"))
    assert agent.gemini_generate_json("p") == "hello"


def test_gemini_generate_json_list_content(monkeypatch):
    content = ["a", {"text": "b"}, {"notext": 1}]
    monkeypatch.setattr(agent, "invoke_gemini", lambda *a, **k: _Resp(content))
    assert agent.gemini_generate_json("p") == "a\nb"


# ── fallback explanations ────────────────────────────────────────────────────

def test_fallback_explanations_matches_skills_and_gaps():
    resume = {"skills": ["Python", "Testing"]}
    jobs = [{"job_id": "1", "title": "Python Engineer", "description": "python testing role"}]
    out = agent._fallback_explanations(resume, jobs)
    assert "python" in out["1"]["strengths"]
    assert "testing" in out["1"]["strengths"]
    # "testing" is matched, so it is excluded from the canned gap list
    assert "testing" not in out["1"]["gaps"]


# ── result builder ───────────────────────────────────────────────────────────

def test_build_job_result_maps_scores_and_explanation():
    job = {
        "job_id": "j1", "title": "Dev", "company": "Acme", "location": "Remote",
        "apply_url": "https://apply", "description": "desc", "_matched_tokens": ["python"],
    }
    scores = {"semantic": 0.812345, "skill_overlap": 0.5, "experience": 1.0, "education": 0.5, "final": 0.6789}
    explanation = {"strengths": ["python"], "gaps": ["cloud"], "reasoning": "good fit"}
    result = agent._build_job_result(job, scores, explanation)
    assert isinstance(result, JobResult)
    assert result.job_id == "j1"
    assert result.score.final == pytest.approx(67.89)
    assert result.match_pct == 68
    assert result.remote is True
    assert result.matched == ["python"]
    assert result.missing == ["cloud"]
    assert result.explanation.reasoning == "good fit"


# ── end-to-end agent (hermetic: no adzuna/jina/gemini keys) ─────────────────

def test_job_finder_agent_uses_fallbacks(monkeypatch):
    # No Adzuna key -> fetch returns [] -> fallback jobs; force LLM explanation to fail.
    monkeypatch.setattr(agent, "gemini_generate_json", lambda prompt: (_ for _ in ()).throw(RuntimeError("no llm")))
    resume = {"skills": ["python"], "experience": [{"title": "eng"}]}
    resp = agent.job_finder_agent(resume, "Backend Engineer", "Pune", top_k=3)
    assert resp.query_role == "Backend Engineer"
    assert resp.user_location_preference == "Pune"
    assert len(resp.jobs) == 3
    assert all(isinstance(j, JobResult) for j in resp.jobs)
    # Explanations fell back, so every job still has non-empty reasoning.
    assert all(j.explanation.reasoning for j in resp.jobs)
