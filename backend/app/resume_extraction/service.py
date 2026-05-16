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

from app.config import settings
from app.resume_extraction.schemas import ResumeExtraction
from app.utils.llm_factory import get_gemini_model

URL_TRAILING_PUNCT = ".,;:!?)]}>'\""


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
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    if re.match(r"^(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/.*)?$", url):
        return "https://" + url
    return None


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


def build_extraction_prompt(resume_text: str) -> str:
    return f"""
You are a resume information extraction engine.

Return ONLY valid JSON matching the provided schema.
Do not add markdown, prose, code fences, or commentary.
Do not invent facts.
Use null where a value is unavailable.

Important rules:
- Put programming languages like Python, Java, C, C++, JavaScript in programming_languages.
- Put spoken human languages like English, Hindi, Marathi in spoken_languages.
- Put all other tools, libraries, frameworks, and technologies in skills.
- For contact.phone_raw, preserve the original phone text if present.
- Do not guess missing URLs.
- If a URL is visible in the resume or present in the extracted URL manifest, include it.
- Prefer the extracted URL manifest for linkedin/github/project links when possible.
- Keep dates as strings exactly as written when possible.

Resume text:
<<<BEGIN_RESUME_TEXT
{resume_text}
END_RESUME_TEXT>>>
""".strip()


def build_repair_prompt(resume_text: str, draft_json: str, validation_error: str) -> str:
    return f"""
You produced JSON that failed schema validation.

Fix it and return ONLY valid JSON matching the schema.
Do not add markdown, prose, or code fences.
Do not invent facts.
Use null where unknown.

Validation error:
{validation_error}

Previous JSON:
{draft_json}

Resume text:
<<<BEGIN_RESUME_TEXT
{resume_text}
END_RESUME_TEXT>>>
""".strip()


def _model_name() -> str:
    return settings.gap_analysis_model or "gemini-1.5-flash"


def _invoke_gemini(prompt: str) -> str:
    model = get_gemini_model(model_name=_model_name(), temperature=0.0)
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
        raise RuntimeError("Empty response received from Gemini.")
    return text


def gemini_generate_resume_json(prompt: str) -> str:
    max_retries = 5
    base_wait_seconds = 3
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return _invoke_gemini(prompt)
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
        f"Gemini request failed after {max_retries} retries. Last error: {last_error}"
    )


def parse_resume_json(candidate_json: str) -> ResumeExtraction:
    return ResumeExtraction.model_validate_json(_strip_code_fences(candidate_json))


def _enforce_post_processing(parsed: ResumeExtraction) -> ResumeExtraction:
    parsed_dict = parsed.model_dump(mode="json")
    contact = parsed_dict.get("contact", {}) or {}
    phone_raw = contact.get("phone_raw")
    contact.update(normalize_phone(phone_raw))
    for field in ("linkedin", "github", "website"):
        contact[field] = normalize_url(contact.get(field))
    parsed_dict["contact"] = contact
    return ResumeExtraction.model_validate(parsed_dict)


def extract_structured_resume_data(md_text: str) -> ResumeExtraction:
    prompt = build_extraction_prompt(md_text)
    draft_json = gemini_generate_resume_json(prompt)
    try:
        parsed = parse_resume_json(draft_json)
        return _enforce_post_processing(parsed)
    except ValidationError as exc:
        repair_prompt = build_repair_prompt(md_text, draft_json, str(exc))
        repaired_json = gemini_generate_resume_json(repair_prompt)
        repaired = parse_resume_json(repaired_json)
        return _enforce_post_processing(repaired)


def extraction_to_json(extracted: ResumeExtraction) -> dict[str, Any]:
    return extracted.model_dump(mode="json")
