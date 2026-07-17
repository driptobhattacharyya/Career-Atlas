"""Unit tests for app.resume_extraction.service (pure normalization / parsing)."""
import json

import pytest
from pydantic import ValidationError

from app.resume_extraction import service
from app.resume_extraction.schemas import ResumeExtraction


# ── phone normalization ─────────────────────────────────────────────────────

def test_normalize_phone_none():
    assert service.normalize_phone(None) == {
        "phone_raw": None, "country_code": None,
        "national_number": None, "e164_phone": None,
    }


def test_normalize_phone_valid_indian():
    out = service.normalize_phone("9876543210", default_region="IN")
    assert out["phone_raw"] == "9876543210"
    assert out["country_code"] == "+91"
    assert out["national_number"] == "9876543210"
    assert out["e164_phone"] == "+919876543210"


def test_normalize_phone_valid_e164():
    out = service.normalize_phone("+16502530000")
    assert out["country_code"] == "+1"
    assert out["e164_phone"] == "+16502530000"


def test_normalize_phone_invalid_keeps_raw_only():
    out = service.normalize_phone("not-a-number")
    assert out["phone_raw"] == "not-a-number"
    assert out["country_code"] is None
    assert out["e164_phone"] is None


# ── text normalization ───────────────────────────────────────────────────────

def test_normalize_text_collapses_whitespace_and_newlines():
    raw = "line1  \r\n\r\n\r\n\r\nline2    with     spaces\r"
    out = service.normalize_text(raw)
    assert "\r" not in out
    assert "\n\n\n" not in out
    assert "     " not in out
    assert out.startswith("line1")


# ── URL handling ─────────────────────────────────────────────────────────────

def test_strip_trailing_punctuation():
    assert service.strip_trailing_punctuation("http://x.com).,") == "http://x.com"
    assert service.strip_trailing_punctuation("  http://x.com  ") == "http://x.com"


def test_normalize_url_valid_http():
    assert service.normalize_url("https://linkedin.com/in/foo") == "https://linkedin.com/in/foo"


def test_normalize_url_adds_scheme_for_bare_domain():
    assert service.normalize_url("github.com/foo") == "https://github.com/foo"
    assert service.normalize_url("www.example.io") == "https://www.example.io"


def test_normalize_url_trailing_angle_bracket_is_stripped_as_punctuation():
    # ">" is in the trailing-punctuation set, so "<url>" loses its closing
    # bracket first and no longer parses as a valid URL.
    assert service.normalize_url("<https://example.dev>") is None


def test_normalize_url_rejects_mailto_and_none():
    assert service.normalize_url("mailto:me@x.com") is None
    assert service.normalize_url(None) is None
    assert service.normalize_url("") is None


def test_normalize_url_rejects_unknown_tld():
    assert service.normalize_url("foo.zzz") is None


def test_normalize_url_rejects_version_like_tokens():
    assert service.normalize_url("v2.0") is None
    assert service.normalize_url("2024.01") is None


def test_extract_urls_from_text_dedupes_and_normalizes():
    text = "Visit https://github.com/foo and https://github.com/foo or www.example.com."
    urls = service.extract_urls_from_text(text)
    assert urls == ["https://github.com/foo", "https://www.example.com"]


def test_extract_urls_ignores_emails():
    urls = service.extract_urls_from_text("contact me at jane@company.com please")
    assert urls == []


# ── URL classification / manifest ────────────────────────────────────────────

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.linkedin.com/in/x", "contact.linkedin"),
        ("https://github.com/x", "contact.github"),
        ("https://x.com/x", "contact.twitter"),
        ("https://twitter.com/x", "contact.twitter"),
        ("https://instagram.com/x", "contact.instagram"),
        ("https://leetcode.com/x", "contact.leetcode"),
        ("https://kaggle.com/x", "contact.kaggle"),
        ("https://example.com", "other"),
    ],
)
def test_classify_url(url, expected):
    assert service.classify_url(url) == expected


def test_build_url_manifest_is_valid_json():
    manifest = service.build_url_manifest(["https://github.com/foo"])
    parsed = json.loads(manifest)
    assert parsed == [{"kind": "contact.github", "url": "https://github.com/foo", "domain": "github.com"}]


# ── misc helpers ─────────────────────────────────────────────────────────────

def test_strip_code_fences():
    assert service._strip_code_fences('```json\n{"a":1}\n```') == '{"a":1}'


def test_dedupe_strings_preserves_order():
    assert service._dedupe_strings([" a ", "b", "a", "", None, "b"]) == ["a", "b"]


def test_infer_skills_from_text_orders_by_position():
    text = "Experienced with Docker and Python; also uses AWS."
    inferred = service._infer_skills_from_text(text)
    # Ordered by first occurrence in the text.
    assert inferred.index("Docker") < inferred.index("Python") < inferred.index("AWS")


def test_infer_skills_empty_when_none_present():
    assert service._infer_skills_from_text("None of those keywords appear.") == []


# ── prompt builders ──────────────────────────────────────────────────────────

def test_build_extraction_prompt_includes_text_and_schema():
    prompt = service.build_extraction_prompt("Jane Doe resume")
    assert "Jane Doe resume" in prompt
    assert "TARGET JSON SCHEMA" in prompt


def test_build_repair_prompt_includes_error_and_draft():
    prompt = service.build_repair_prompt("resume", '{"bad": 1}', "field required")
    assert "field required" in prompt
    assert '{"bad": 1}' in prompt


# ── stringify_list ──────────────────────────────────────────────────────────

def test_stringify_list_splits_delimited_string():
    assert service._stringify_list("Python, Java; Go/Rust") == ["Python", "Java", "Go", "Rust"]


def test_stringify_list_dict_with_label_and_keywords():
    out = service._stringify_list({"name": "Cloud", "keywords": ["AWS", "GCP"]})
    assert "Cloud" in out
    # The combined "label: values" string is re-split on commas by add().
    assert "Cloud: AWS" in out
    assert "GCP" in out


def test_stringify_list_nested_and_scalars():
    assert service._stringify_list([["Python"], 42, True, None]) == ["Python", "42", "True"]


# ── block normalizers ────────────────────────────────────────────────────────

def test_normalize_blocks_aliases_bullets_and_tech():
    blocks = [{"achievements": ["did x"], "tools": ["Docker"]}, "ignored"]
    out = service._normalize_blocks(blocks)
    assert len(out) == 1
    assert out[0]["description_bullets"] == ["did x"]
    assert out[0]["technologies"] == ["Docker"]


def test_normalize_education_aliases_coursework():
    out = service._normalize_education([{"coursework": "Algorithms, OS"}])
    assert out[0]["notes"] == ["Algorithms", "OS"]


def test_normalize_projects_backfills_name_and_link():
    out = service._normalize_projects([{"title": "Atlas", "url": "https://x.dev", "skills": ["Python"]}])
    assert out[0]["name"] == "Atlas"
    assert out[0]["link"] == "https://x.dev"
    assert out[0]["technologies"] == ["Python"]


# ── parse_resume_json ────────────────────────────────────────────────────────

def test_parse_resume_json_normalizes_fields():
    raw = json.dumps({
        "contact": {},
        "skills": "Python, SQL",
        "programming_languages": ["Go"],
        "experience": [{"company": "Acme", "achievements": ["shipped"], "tech": ["Docker"]}],
    })
    parsed = service.parse_resume_json(raw)
    assert isinstance(parsed, ResumeExtraction)
    assert parsed.skills == ["Python", "SQL"]
    assert parsed.experience[0].description_bullets == ["shipped"]
    assert parsed.experience[0].technologies == ["Docker"]


def test_parse_resume_json_rejects_non_dict():
    with pytest.raises(ValidationError):
        service.parse_resume_json("[1, 2, 3]")


# ── post processing ──────────────────────────────────────────────────────────

def test_enforce_post_processing_normalizes_contact():
    parsed = ResumeExtraction.model_validate({
        "contact": {"phone_raw": "9876543210", "linkedin": "linkedin.com/in/foo", "github": "mailto:x@y.com"},
    })
    out = service._enforce_post_processing(parsed)
    assert out.contact.e164_phone == "+919876543210"
    assert out.contact.linkedin == "https://linkedin.com/in/foo"
    assert out.contact.github is None  # mailto rejected


def test_backfill_skills_from_sources():
    parsed = ResumeExtraction.model_validate({
        "contact": {},
        "programming_languages": ["Python"],
        "experience": [{"technologies": ["Airflow"]}],
        "projects": [{"technologies": ["Docker"]}],
    })
    out = service._backfill_skills(parsed, "irrelevant text")
    assert set(out.skills) == {"Python", "Airflow", "Docker"}


def test_backfill_skills_infers_from_text_when_empty():
    parsed = ResumeExtraction.model_validate({"contact": {}})
    out = service._backfill_skills(parsed, "Built services in Python and deployed on AWS")
    assert "Python" in out.skills
    assert "AWS" in out.skills


def test_extraction_to_json_roundtrips():
    parsed = ResumeExtraction.model_validate({"contact": {}, "full_name": "Jane"})
    data = service.extraction_to_json(parsed)
    assert data["full_name"] == "Jane"
    assert isinstance(data, dict)
