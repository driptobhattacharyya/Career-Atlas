import json
import re
import tempfile
import time
import os
from typing import Any
from urllib.parse import urlparse

import fitz
import phonenumbers
import pymupdf4llm
from pydantic import ValidationError
from phonenumbers import PhoneNumberFormat

from app.resume_extraction.schemas import ResumeExtraction
from app.utils.llm_factory import get_gemini_model

URL_TRAILING_PUNCT = ".,;:!?)]}>'\""
KNOWN_RESUME_TLDS = {
    "com", "in", "io", "dev", "net", "org", "ai", "co",
    "me", "app", "tech", "info", "edu", "gov",
}

COMMON_SKILL_TERMS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C", "Go", "Rust", "SQL",
    "HTML", "CSS", "React", "Next.js", "Node.js", "FastAPI", "Django", "Flask",
    "Pandas", "NumPy", "scikit-learn", "TensorFlow", "PyTorch", "XGBoost", "OpenCV",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Git", "Linux", "Bash", "Figma",
    "PostgreSQL", "MongoDB", "MySQL", "Tableau", "Power BI", "Jira", "Airflow", "Spark",
]


def normalize_phone(raw_phone: str | None, default_region: str = "IN") -> dict[str, str | None]:
    if not raw_phone:
        return {
            "phone_raw": None,
            "country_code": None,
            "national_number": None,
            "e164_phone": None,
        }
    try:
        parsed = phonenumbers.parse(raw_phone, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return {
                "phone_raw": raw_phone,
                "country_code": None,
                "national_number": None,
                "e164_phone": None,
            }
        return {
            "phone_raw": raw_phone,
            "country_code": f"+{parsed.country_code}",
            "national_number": str(parsed.national_number),
            "e164_phone": phonenumbers.format_number(parsed, PhoneNumberFormat.E164),
        }
    except Exception:
        return {
            "phone_raw": raw_phone,
            "country_code": None,
            "national_number": None,
            "e164_phone": None,
        }


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def strip_trailing_punctuation(url: str) -> str:
    url = url.strip()
    while url and url[-1] in URL_TRAILING_PUNCT:
        url = url[:-1]
    return url


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None

    url = strip_trailing_punctuation(url.strip())
    if url.startswith("<") and url.endswith(">"):
        url = url[1:-1].strip()
    if url.lower().startswith("mailto:"):
        return None

    parsed = urlparse(url)
    candidate = None
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        candidate = url
    elif re.match(r"^(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/.*)?$", url):
        candidate = "https://" + url
    if not candidate:
        return None

    parsed_candidate = urlparse(candidate)
    host = (parsed_candidate.netloc or "").split(":")[0]
    if "." not in host:
        return None
    tld = host.rsplit(".", 1)[-1].lower()
    if tld not in KNOWN_RESUME_TLDS:
        return None
    return candidate


def extract_urls_from_text(text: str) -> list[str]:
    text = text or ""
    pattern = re.compile(
        r"""(?ix)
        (?<!@)
        \b(
            https?://[^\s<>()\[\]{}"']+
            |
            www\.[^\s<>()\[\]{}"']+
            |
            (?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s<>()\[\]{}"']+)?
        )
        """
    )
    found: list[str] = []
    for match in pattern.finditer(text):
        url = normalize_url(match.group(1))
        if url:
            found.append(url)
    return list(dict.fromkeys(found))


def extract_embedded_urls(pdf_path: str) -> list[str]:
    doc = fitz.open(pdf_path)
    urls: list[str] = []
    for page in doc:
        for link in page.get_links():
            uri = normalize_url(link.get("uri"))
            if uri:
                urls.append(uri)
    return list(dict.fromkeys(urls))


def classify_url(url: str) -> str:
    u = url.lower()
    if "linkedin.com" in u:
        return "contact.linkedin"
    if "github.com" in u:
        return "contact.github"
    if "twitter.com" in u or "x.com" in u:
        return "contact.twitter"
    if "instagram.com" in u:
        return "contact.instagram"
    if "leetcode.com" in u:
        return "contact.leetcode"
    if "kaggle.com" in u:
        return "contact.kaggle"
    return "other"


def build_url_manifest(urls: list[str]) -> str:
    manifest = []
    for url in urls:
        parsed = urlparse(url)
        manifest.append(
            {
                "kind": classify_url(url),
                "url": url,
                "domain": parsed.netloc.lower() if parsed.netloc else "",
            }
        )
    return json.dumps(manifest, ensure_ascii=False, indent=2)


def extract_pdf_text(pdf_path: str) -> str:
    try:
        text = pymupdf4llm.to_markdown(pdf_path, header=False, footer=False)
        text = normalize_text(text) if text and text.strip() else ""
    except Exception:
        text = ""

    if not text:
        doc = fitz.open(pdf_path)
        parts = [page.get_text("text", sort=True) for page in doc]
        text = normalize_text("\n\n".join(parts))

    embedded_urls = extract_embedded_urls(pdf_path)
    visible_urls = extract_urls_from_text(text)
    all_urls: list[str] = []
    seen: set[str] = set()
    for url in embedded_urls + visible_urls:
        normalized = normalize_url(url)
        if normalized and normalized not in seen:
            seen.add(normalized)
            all_urls.append(normalized)

    if all_urls:
        text += "\n\n[EXTRACTED_URLS_JSON]\n"
        text += build_url_manifest(all_urls)
        text += "\n[/EXTRACTED_URLS_JSON]"
    return text


def pdf_bytes_to_markdown(pdf_bytes: bytes) -> str:
    # Windows-safe tempfile handling: close file before PyMuPDF opens it.
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_path = temp_file.name
    try:
        temp_file.write(pdf_bytes)
        temp_file.close()
        return extract_pdf_text(temp_path)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = (value or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _infer_skills_from_text(resume_text: str) -> list[str]:
    text = resume_text or ""
    found: list[tuple[int, str]] = []
    lowered = text.lower()
    for term in COMMON_SKILL_TERMS:
        idx = lowered.find(term.lower())
        if idx != -1:
            found.append((idx, term))
    found.sort(key=lambda item: item[0])
    return _dedupe_strings([term for _, term in found])


def build_extraction_prompt(resume_text: str) -> str:
    schema_json = json.dumps(ResumeExtraction.model_json_schema(), indent=2)
    return f"""
You are a precise resume information extraction engine.

Return ONLY valid JSON matching the provided schema. No markdown. No prose. No code fences.
Do not invent facts.
Use null where a value is unavailable.

--- TARGET JSON SCHEMA ---
{schema_json}


--- CLASSIFICATION RULES ---
programming_languages: Python, Java, C, C++, C#, JavaScript, TypeScript, Go, Rust, SQL, Bash, R, MATLAB, Scala, Swift, Kotlin, Dart
spoken_languages: English, Hindi, Marathi, Tamil, Telugu, Kannada, Bengali, French, German, Spanish, and similar human/natural languages
skills: everything else — frameworks (FastAPI, React, Django), libraries (Pandas, NumPy), platforms (AWS, GCP, Docker, Kubernetes), tools (Git, Jira, Figma), databases (PostgreSQL, MongoDB)

--- CONTACT RULES ---
- phone_raw: copy the phone string exactly as it appears in the resume
- For URLs: prefer the EXTRACTED_URLS_JSON manifest below the resume text over inferred URLs
- Do not guess or construct URLs that are not present

--- DATE RULES ---
- Preserve dates as written: "Jan 2024", "2022–Present", "August 2023"
- For ongoing roles, set is_current=true and end_date="Present"

--- NEGATIVE EXAMPLES ---
- "B.Tech" -> NOT a URL
- "v2.0" -> NOT a URL
- "2024.01" -> NOT a URL
- "SQL" -> programming_language, not a skill

Resume text:
<<<BEGIN_RESUME_TEXT
{resume_text}
END_RESUME_TEXT>>>
""".strip()


def build_repair_prompt(resume_text: str, draft_json: str, validation_error: str) -> str:
    schema_json = json.dumps(ResumeExtraction.model_json_schema(), indent=2)
    return f"""
You produced JSON that failed schema validation.

Fix it and return ONLY valid JSON matching the schema.
Do not add markdown, prose, or code fences.
Do not invent facts.
Use null where unknown.

--- TARGET JSON SCHEMA ---
{schema_json}

Validation error:
{validation_error}

Previous JSON:
{draft_json}

Resume text:
<<<BEGIN_RESUME_TEXT
{resume_text}
END_RESUME_TEXT>>>
""".strip()


def _invoke_llm(prompt: str) -> str:
    # Resume extraction is intentionally pinned to Gemini for better parsing quality.
    model = get_gemini_model(temperature=0.0)
    response = model.invoke(prompt)
    content = getattr(response, "content", "")
    if isinstance(content, str):
        raw_text = content
    elif isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                maybe_text = item.get("text")
                if isinstance(maybe_text, str):
                    parts.append(maybe_text)
        raw_text = "\n".join(parts)
    else:
        raw_text = str(content or "")

    text = _strip_code_fences(raw_text)
    if not text:
        raise RuntimeError("Empty response received from the LLM.")
    return text


def llm_generate_resume_json(prompt: str) -> str:
    max_retries = 5
    base_wait_seconds = 3
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return _invoke_llm(prompt)
        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()
            retryable_errors = [
                "503",
                "service unavailable",
                "resource exhausted",
                "quota",
                "rate limit",
                "429",
                "deadline exceeded",
                "timeout",
                "temporarily unavailable",
                "internal error",
                "500",
            ]
            should_retry = any(token in error_text for token in retryable_errors)
            if not should_retry or attempt == max_retries:
                break
            wait_time = base_wait_seconds * (2 ** (attempt - 1))
            time.sleep(wait_time)

    raise RuntimeError(
        f"Resume extraction LLM failed after {max_retries} retries. Last error: {last_error}"
    )


def parse_resume_json(candidate_json: str) -> ResumeExtraction:
    raw = json.loads(_strip_code_fences(candidate_json))
    if not isinstance(raw, dict):
        raise ValidationError.from_exception_data(
            "ResumeExtraction",
            [
                {
                    "type": "dict_type",
                    "loc": ("root",),
                    "msg": "Resume JSON must be an object",
                    "input": raw,
                }
            ],
        )

    raw["skills"] = _stringify_list(raw.get("skills", []))
    raw["programming_languages"] = _stringify_list(raw.get("programming_languages", []))
    raw["spoken_languages"] = _stringify_list(raw.get("spoken_languages", []))
    raw["keywords"] = _stringify_list(raw.get("keywords", []))
    raw["experience"] = _normalize_blocks(raw.get("experience", []))
    raw["education"] = _normalize_education(raw.get("education", []))
    raw["projects"] = _normalize_projects(raw.get("projects", []))
    raw["certifications"] = [
        item for item in raw.get("certifications", []) if isinstance(item, dict)
    ]

    return ResumeExtraction.model_validate(raw)


def _stringify_list(value: Any) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()

    def add(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, str):
            chunks = re.split(r"[,\n;|/•·]+", item)
            if len(chunks) > 1:
                for chunk in chunks:
                    add(chunk)
                return
            text = item.strip()
            if text and text not in seen:
                seen.add(text)
                items.append(text)
            return
        if isinstance(item, (int, float, bool)):
            text = str(item).strip()
            if text and text not in seen:
                seen.add(text)
                items.append(text)
            return
        if isinstance(item, list):
            for sub in item:
                add(sub)
            return
        if isinstance(item, dict):
            priority_keys = ("name", "title", "skill", "value", "label", "text")
            label = None
            for key in priority_keys:
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    label = val.strip()
                    add(val)
                    break

            rich_values: list[str] = []
            for key in ("keywords", "technologies", "items", "tags", "values"):
                val = item.get(key)
                if isinstance(val, list):
                    for sub in val:
                        if isinstance(sub, str) and sub.strip():
                            rich_values.append(sub.strip())
                        else:
                            add(sub)

            if label and rich_values:
                add(f"{label}: {', '.join(_dedupe_strings(rich_values))}")
            return

    add(value)
    return items


def _normalize_blocks(blocks: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        item = dict(block)
        item["description_bullets"] = _stringify_list(
            item.get("description_bullets")
            or item.get("bullets")
            or item.get("achievements")
            or []
        )
        item["technologies"] = _stringify_list(
            item.get("technologies")
            or item.get("tech")
            or item.get("tools")
            or []
        )
        normalized.append(item)
    return normalized


def _normalize_education(blocks: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        item = dict(block)
        item["notes"] = _stringify_list(item.get("notes") or item.get("coursework") or [])
        normalized.append(item)
    return normalized


def _normalize_projects(blocks: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        item = dict(block)
        if not item.get("name"):
            item["name"] = item.get("title") or item.get("project_name") or item.get("label")
        item["technologies"] = _stringify_list(
            item.get("technologies")
            or item.get("tech")
            or item.get("tools")
            or item.get("skills")
            or []
        )
        if not item.get("link"):
            item["link"] = item.get("url")
        normalized.append(item)
    return normalized


def _enforce_post_processing(parsed: ResumeExtraction) -> ResumeExtraction:
    parsed_dict = parsed.model_dump(mode="json")
    contact = parsed_dict.get("contact", {}) or {}
    phone_raw = contact.get("phone_raw") or contact.get("phone")
    contact.update(normalize_phone(phone_raw))
    for field in ("linkedin", "github", "website"):
        contact[field] = normalize_url(contact.get(field))
    parsed_dict["contact"] = contact
    return ResumeExtraction.model_validate(parsed_dict)


def _backfill_skills(parsed: ResumeExtraction, resume_text: str) -> ResumeExtraction:
    data = parsed.model_dump(mode="json")
    skills = _dedupe_strings(
        list(data.get("skills") or [])
        + list(data.get("programming_languages") or [])
        + list(data.get("spoken_languages") or [])
        + list(data.get("keywords") or [])
    )
    for exp in data.get("experience", []) or []:
        if isinstance(exp, dict):
            skills.extend(_dedupe_strings(list(exp.get("technologies") or [])))
    for proj in data.get("projects", []) or []:
        if isinstance(proj, dict):
            skills.extend(_dedupe_strings(list(proj.get("technologies") or [])))
    skills = _dedupe_strings(skills)
    if not skills:
        skills = _infer_skills_from_text(resume_text)
    data["skills"] = skills
    return ResumeExtraction.model_validate(data)


def extract_structured_resume_data(md_text: str) -> ResumeExtraction:
    prompt = build_extraction_prompt(md_text)
    draft_json = llm_generate_resume_json(prompt)
    for attempt in range(2):  # 1 initial + 1 repair
        try:
            parsed = parse_resume_json(draft_json)
            parsed = _enforce_post_processing(parsed)
            parsed = _backfill_skills(parsed, md_text)
            return parsed
        except ValidationError as exc:
            if attempt == 0:
                repair_prompt = build_repair_prompt(md_text, draft_json, str(exc))
                draft_json = llm_generate_resume_json(repair_prompt)
            else:
                raise

    raise RuntimeError("Resume extraction failed after validation repair attempts.")


def extraction_to_json(extracted: ResumeExtraction) -> dict[str, Any]:
    return extracted.model_dump(mode="json")
