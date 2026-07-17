import json
import logging
import re
from typing import Any, Optional

import numpy as np
import requests

from app.config import settings
from app.job_hunter.schemas import (
    JobExplanation,
    JobResult,
    JobSearchResponse,
    ScoreBreakdown,
)
from app.utils.llm_factory import invoke_gemini

logger = logging.getLogger(__name__)

INDIA_CITY_ALIASES = {
    "pune": {"pune", "poona"},
    "mumbai": {"mumbai", "bombay"},
    "bangalore": {"bangalore", "bengaluru"},
    "hyderabad": {"hyderabad", "hyd"},
    "delhi": {"delhi", "new delhi", "ncr", "gurugram", "noida", "gurgaon"},
    "chennai": {"chennai", "madras"},
}

FALLBACK_COMPANIES = [
    "Atlas Labs",
    "Northstar Systems",
    "Vector Harbor",
    "Summit Works",
    "Signal Foundry",
]


def _strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()


def safe_json_parse(text: str):
    text = _strip_code_fences((text or "").strip())
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, str):
            return json.loads(parsed)
        if isinstance(parsed, dict):
            return [parsed]
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug("safe_json_parse could not decode LLM output: %s", e)
        return []
    return []


def tokenize(text: str):
    return set(re.findall(r"[a-zA-Z0-9\+\#\.]+", (text or "").lower()))


def location_filter(job_loc: str, user_pref: str) -> bool:
    if not job_loc:
        return True
    job_loc_l = job_loc.lower()
    pref = (user_pref or "").lower().strip()
    if pref == "remote":
        return "remote" in job_loc_l
    if pref == "hybrid":
        return "hybrid" in job_loc_l or "remote" in job_loc_l
    aliases = INDIA_CITY_ALIASES.get(pref, {pref})
    return any(alias in job_loc_l for alias in aliases)


def fetch_jobs(query_role: str, where: str, results: int = 20) -> list[dict[str, Any]]:
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        return []
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "what": query_role,
        "where": where if where not in {"remote", "hybrid"} else "",
        "results_per_page": results,
        "content-type": "application/json",
    }
    r = requests.get(url, params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    jobs = []
    for j in data.get("results", []):
        jobs.append(
            {
                "job_id": str(j.get("id")) if j.get("id") is not None else None,
                "title": j.get("title"),
                "company": (j.get("company") or {}).get("display_name"),
                "location": (j.get("location") or {}).get("display_name"),
                "description": j.get("description") or "",
                "apply_url": j.get("redirect_url"),
            }
        )
    return jobs


def _search_url(query_role: str, location: str) -> str:
    # Used only by fallback listings. LinkedIn's job search lands on real
    # postings, unlike a raw Google search results page.
    kw = requests.utils.quote(query_role.strip())
    loc = requests.utils.quote(location.strip())
    return f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={loc}"


def _fallback_jobs(query_role: str, user_location_pref: str, count: int = 5) -> list[dict[str, Any]]:
    location = user_location_pref if user_location_pref else "Remote"
    titles = [
        f"{query_role}",
        f"Senior {query_role}",
        f"Mid-level {query_role}",
        f"Entry-level {query_role}",
        f"Contract {query_role}",
    ]
    jobs: list[dict[str, Any]] = []
    for idx, title in enumerate(titles[:count]):
        company = FALLBACK_COMPANIES[idx % len(FALLBACK_COMPANIES)]
        jobs.append(
            {
                "job_id": f"fallback-{idx + 1}",
                "title": title,
                "company": company,
                "location": location,
                "description": (
                    f"Curated fallback listing for a {query_role} role. "
                    f"Searches for {query_role} opportunities with emphasis on {location.lower()} availability."
                ),
                "apply_url": _search_url(query_role, location),
            }
        )
    return jobs


def _fetch_jobs_with_fallback(query_role: str, user_location_pref: str, results: int = 20) -> list[dict[str, Any]]:
    search_variants = [
        query_role,
        f"{query_role} jobs",
        f"entry level {query_role}",
        f"senior {query_role}",
        f"{query_role} engineer",
    ]
    # Adzuna's `where` is a LOCATION, not the role. Passing the job title here
    # made every search return nothing and silently fall back to Google links.
    where = user_location_pref if user_location_pref.lower().strip() not in {"remote", "hybrid"} else ""

    for variant in search_variants:
        try:
            jobs = fetch_jobs(variant, where, results=results)
        except Exception:
            logger.warning("Adzuna fetch failed for variant %r", variant, exc_info=True)
            jobs = []
        if not jobs:
            continue

        strict = [j for j in jobs if location_filter(j.get("location") or "", user_location_pref)]
        if strict:
            return strict
        # If the strict location filter wipes everything out, prefer actual jobs over emptiness.
        return jobs

    return _fallback_jobs(query_role, user_location_pref, count=min(results, 5))


def embed_batch(texts: list[str]) -> np.ndarray:
    if not settings.jina_api_key:
        raise RuntimeError("JINA_API_KEY is required for job ranking embeddings.")
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.jina_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "jina-embeddings-v2-base-en",
        "input": texts,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]
    return np.array([d["embedding"] for d in data], dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def build_resume_representation(resume: dict[str, Any]):
    skill_sources: list[Any] = []
    skill_sources.extend(resume.get("skills") or [])
    skill_sources.extend(resume.get("programming_languages") or [])
    skill_sources.extend(resume.get("spoken_languages") or [])
    skill_sources.extend(resume.get("keywords") or [])
    for exp in resume.get("experience") or []:
        if isinstance(exp, dict):
            skill_sources.extend(exp.get("technologies") or [])
    for proj in resume.get("projects") or []:
        if isinstance(proj, dict):
            skill_sources.extend(proj.get("technologies") or [])
    skills = {
        s.lower()
        for s in skill_sources
        if isinstance(s, str) and s.strip()
    }
    exp_text = " ".join(
        " ".join((e.get("description_bullets", []) or []) + (e.get("technologies", []) or []))
        for e in (resume.get("experience") or [])
        if isinstance(e, dict)
    )
    proj_text = " ".join(
        " ".join(
            [
                p.get("description") or "",
                " ".join(p.get("technologies") or []),
            ]
        )
        for p in (resume.get("projects") or [])
        if isinstance(p, dict)
    )
    summary = resume.get("summary") or ""
    structured = {
        "skills": skills,
        "has_experience": len(resume.get("experience") or []) > 0,
        "has_education": len(resume.get("education") or []) > 0,
    }
    semantic_text = " ".join([summary, exp_text, proj_text]).strip()
    return structured, semantic_text


def score_jobs(resume: dict[str, Any], jobs: list[dict[str, Any]]):
    structured, resume_text = build_resume_representation(resume)
    job_texts = [f"{j.get('title') or ''} {j.get('description') or ''}".strip() for j in jobs]
    resume_skills = structured["skills"]
    headline_tokens = tokenize(resume.get("headline", ""))
    try:
        embeds = embed_batch([resume_text] + job_texts)
        r_emb = embeds[0]
        j_embs = embeds[1:]
    except Exception:
        logger.warning("Jina embedding failed; falling back to heuristic scoring", exc_info=True)
        r_emb = None
        j_embs = None
    results = []
    for i, job in enumerate(jobs):
        j_text = job_texts[i]
        job_tokens = tokenize(j_text)
        overlap_tokens = resume_skills & job_tokens
        overlap = len(overlap_tokens)
        # Fixed formula: fraction of resume skills represented in job text.
        skill_score = overlap / max(len(resume_skills), 1)
        title_text = (job.get("title") or "").lower()
        title_boost = 0.1 if any(tok in title_text for tok in headline_tokens if tok) else 0.0
        exp_score = 1.0 if structured["has_experience"] else 0.4
        edu_score = 1.0 if structured["has_education"] else 0.5
        if r_emb is not None and j_embs is not None:
            semantic = cosine_sim(r_emb, j_embs[i])
        else:
            semantic = min(1.0, 0.35 + 0.65 * skill_score + title_boost)
        final = min(
            1.0,
            (0.55 * semantic + 0.25 * skill_score + 0.10 * exp_score + 0.05 * edu_score + 0.05 * title_boost),
        )
        results.append(
            {
                **job,
                "_matched_tokens": sorted(overlap_tokens)[:15],
                "_scores": {
                    "semantic": semantic,
                    "skill_overlap": skill_score,
                    "experience": exp_score,
                    "education": edu_score,
                    "final": final,
                },
            }
        )
    return results


def build_compact_resume_for_llm(resume: dict[str, Any]) -> dict[str, Any]:
    return {
        "skills": resume.get("skills", []),
        "programming_languages": resume.get("programming_languages", []),
        "spoken_languages": resume.get("spoken_languages", []),
        "keywords": resume.get("keywords", []),
        "experience_titles": [
            f"{e.get('title')} at {e.get('company')} ({e.get('start_date')}–{e.get('end_date')})"
            for e in resume.get("experience", [])
            if isinstance(e, dict)
        ],
        "experience_technologies": [
            tech
            for e in resume.get("experience", [])
            if isinstance(e, dict)
            for tech in (e.get("technologies") or [])
            if isinstance(tech, str) and tech.strip()
        ],
        "education": [
            f"{e.get('degree')} from {e.get('institution')}"
            for e in resume.get("education", [])
            if isinstance(e, dict)
        ],
        "projects": [p.get("name") for p in resume.get("projects", []) if isinstance(p, dict)],
        "project_technologies": [
            tech
            for p in resume.get("projects", [])
            if isinstance(p, dict)
            for tech in (p.get("technologies") or [])
            if isinstance(tech, str) and tech.strip()
        ],
    }


def build_bulk_explanation_prompt(resume: dict[str, Any], jobs: list[dict[str, Any]]) -> str:
    compact_resume = build_compact_resume_for_llm(resume)
    compact_jobs = [
        {
            "job_id": j.get("job_id"),
            "title": j.get("title"),
            "company": j.get("company"),
            "description": (j.get("description") or "")[:800],
            "scores": j.get("_scores", {}),
        }
        for j in jobs
    ]
    return f"""
You are evaluating job fit for a candidate.
Return ONLY a valid JSON array — no markdown, no preamble.

Candidate profile:
{json.dumps(compact_resume)}

Jobs to evaluate:
{json.dumps(compact_jobs)}

For each job return:
[
  {{
    "job_id": "...",
    "strengths": ["specific skill or experience that matches"],
    "gaps": ["specific requirement missing from candidate profile"],
    "reasoning": "1-2 sentence overall fit summary"
  }}
]
""".strip()


def gemini_generate_json(prompt: str) -> str:
    response = invoke_gemini(prompt, temperature=0.1)
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content or "")


def _fallback_explanations(resume: dict[str, Any], jobs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    resume_skill_sources: list[Any] = []
    resume_skill_sources.extend(resume.get("skills") or [])
    resume_skill_sources.extend(resume.get("programming_languages") or [])
    resume_skill_sources.extend(resume.get("spoken_languages") or [])
    resume_skill_sources.extend(resume.get("keywords") or [])
    for exp in resume.get("experience") or []:
        if isinstance(exp, dict):
            resume_skill_sources.extend(exp.get("technologies") or [])
    for proj in resume.get("projects") or []:
        if isinstance(proj, dict):
            resume_skill_sources.extend(proj.get("technologies") or [])
    resume_skills = {
        s.lower()
        for s in resume_skill_sources
        if isinstance(s, str) and s.strip()
    }
    output: dict[str, dict[str, Any]] = {}
    for job in jobs:
        job_text = f"{job.get('title') or ''} {job.get('description') or ''}".lower()
        matched = sorted({skill for skill in resume_skills if skill and skill in job_text})[:5]
        gaps = sorted(
            [skill for skill in ["communication", "system design", "testing", "cloud", "data"] if skill not in matched]
        )[:3]
        output[str(job.get("job_id") or job.get("id") or "")] = {
            "strengths": matched or ["Relevant experience and transferable skills"],
            "gaps": gaps or ["More role-specific evidence would help"],
            "reasoning": f"This role is a reasonable fit for {job.get('title') or 'the target role'} based on the available resume signals.",
        }
    return output


def _build_job_result(job: dict[str, Any], scores: dict[str, float], explanation: dict[str, Any]) -> JobResult:
    final_pct = round(float(scores["final"]) * 100, 2)
    matched = job.get("_matched_tokens", [])
    gaps = explanation.get("gaps", [])
    reasoning = explanation.get("reasoning", "") or job.get("description") or ""
    return JobResult(
        job_id=str(job.get("job_id") or job.get("id") or ""),
        title=job.get("title") or "Untitled role",
        company=job.get("company"),
        location=job.get("location"),
        apply_url=job.get("apply_url"),
        score=ScoreBreakdown(
            semantic=round(float(scores["semantic"]), 4),
            skill_overlap=round(float(scores["skill_overlap"]), 4),
            experience=round(float(scores["experience"]), 4),
            education=round(float(scores["education"]), 4),
            final=final_pct,
        ),
        explanation=JobExplanation(
            strengths=explanation.get("strengths", []) or [],
            gaps=gaps or [],
            reasoning=reasoning,
        ),
        remote="remote" in (job.get("location") or "").lower(),
        seniority=None,
        match_pct=int(round(final_pct)),
        matched=matched or [],
        missing=gaps or [],
        salary=None,
        posted_days=0,
        description=job.get("description") or reasoning,
        external_url=job.get("apply_url"),
    )


def job_finder_agent(
    resume: dict[str, Any],
    target_role: str,
    user_location_pref: str,
    top_k: int = 5,
) -> JobSearchResponse:
    jobs = _fetch_jobs_with_fallback(target_role, user_location_pref, results=25)
    if not jobs:
        jobs = _fallback_jobs(target_role, user_location_pref, count=5)
    scored = score_jobs(resume, jobs)
    scored = sorted(scored, key=lambda x: x["_scores"]["final"], reverse=True)[: max(top_k, 7)]
    prompt = build_bulk_explanation_prompt(resume, scored)
    explanations: dict[str, dict[str, Any]] = {}
    try:
        explanations_json = gemini_generate_json(prompt)
        parsed_explanations = safe_json_parse(explanations_json)
        explanations = {
            e.get("job_id"): e
            for e in parsed_explanations
            if isinstance(e, dict) and e.get("job_id")
        }
    except Exception:
        logger.warning("LLM job explanations failed; using heuristic fallback", exc_info=True)
        explanations = {}
    if not explanations:
        explanations = _fallback_explanations(resume, scored)

    out_jobs: list[JobResult] = []
    for j in scored[:top_k]:
        s = j["_scores"]
        e = explanations.get(
            j.get("job_id"),
            {"strengths": [], "gaps": [], "reasoning": "No explanation generated."},
        )
        out_jobs.append(_build_job_result(j, s, e))

    return JobSearchResponse(
        query_role=target_role,
        user_location_preference=user_location_pref,
        total_jobs_fetched=len(jobs),
        jobs=out_jobs,
    )
