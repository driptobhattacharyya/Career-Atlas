import logging
import re
from typing import Any
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import require_user_id
from app.dependencies.database import db_client
from app.job_hunter.agent import job_finder_agent
from app.job_hunter.schemas import JobExplanation, JobResult, JobSearchResponse, ScoreBreakdown
from app.utils.resumes import latest_resume_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research-jobs", tags=["Jobs"])


class ResearchJobsRequest(BaseModel):
    target_role_id: str


def _posted_days_to_int(v) -> int:
    """Coerce the LLM's free-text 'posted' value into a day count for the int column."""
    if v is None:
        return 0
    if isinstance(v, int):
        return v
    s = str(v).lower()
    m = re.search(r"\d+", s)
    if not m:
        return 0
    n = int(m.group())
    if "week" in s:
        return n * 7
    if "month" in s:
        return n * 30
    return n


def _safe_first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def _resolve_profile_context(user_id: str) -> tuple[str, str]:
    query_role = "Target Role"
    location = "Remote"

    try:
        profile_resp = (
            db_client.table("profiles")
            .select("location,target_role_id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        profile = _safe_first(profile_resp.data or [])
        location = profile.get("location") or location
        target_role_id = profile.get("target_role_id")
        if target_role_id:
            role_resp = (
                db_client.table("target_roles")
                .select("title")
                .eq("id", target_role_id)
                .limit(1)
                .execute()
            )
            role = _safe_first(role_resp.data or [])
            query_role = role.get("title") or query_role
    except Exception:
        logger.warning("profile/role context lookup failed for user %s", user_id, exc_info=True)

    if location == "Remote":
        try:
            resume_id = latest_resume_id(user_id)
            if resume_id:
                contact_resp = (
                    db_client.table("contacts")
                    .select("location,city,country")
                    .eq("resume_id", resume_id)
                    .limit(1)
                    .execute()
                )
                contact = _safe_first(contact_resp.data or [])
                location = (
                    contact.get("location")
                    or contact.get("city")
                    or contact.get("country")
                    or location
                )
        except Exception:
            logger.warning("contact-location lookup failed for user %s", user_id, exc_info=True)

    return query_role, location or "Remote"


def _is_effectively_empty_score(score_payload: dict[str, Any]) -> bool:
    if not score_payload:
        return True
    keys = ("semantic", "skill_overlap", "experience", "education", "final")
    try:
        return all(float(score_payload.get(key) or 0) == 0 for key in keys)
    except (TypeError, ValueError):
        logger.debug("non-numeric score payload treated as empty: %r", score_payload)
        return True


def _row_to_job_result(row: dict[str, Any]) -> JobResult:
    score_payload = row.get("score_json") or row.get("score") or {}
    explanation_payload = row.get("explanation_json") or row.get("explanation") or {}
    matched = row.get("matched") or explanation_payload.get("strengths") or []
    missing = row.get("missing") or explanation_payload.get("gaps") or []
    final_value = score_payload.get("final")
    if final_value is None:
        final_value = row.get("match_pct", 0)
    final_pct = float(final_value)
    if final_pct <= 1:
        final_pct *= 100
    if _is_effectively_empty_score(score_payload):
        matched_count = len(matched)
        missing_count = len(missing)
        base = max(matched_count + missing_count, 1)
        semantic = min(100.0, final_pct * 0.9)
        skill_overlap = min(100.0, (matched_count / base) * 100 if base else final_pct)
        experience = 70.0 if not any("experience" in str(m).lower() for m in missing) else 55.0
        education = 75.0 if not any("education" in str(m).lower() for m in missing) else 60.0
        score_payload = {
            "semantic": semantic,
            "skill_overlap": skill_overlap,
            "experience": experience,
            "education": education,
            "final": final_pct,
        }

    return JobResult(
        job_id=str(row.get("job_id") or row.get("id") or ""),
        title=row.get("title") or "Untitled role",
        company=row.get("company"),
        location=row.get("location"),
        apply_url=row.get("external_url") or row.get("apply_url"),
        score=ScoreBreakdown(
            semantic=float(score_payload.get("semantic") or 0),
            skill_overlap=float(score_payload.get("skill_overlap") or 0),
            experience=float(score_payload.get("experience") or 0),
            education=float(score_payload.get("education") or 0),
            final=round(float(final_pct), 2),
        ),
        explanation=JobExplanation(
            strengths=list(explanation_payload.get("strengths") or matched or []),
            gaps=list(explanation_payload.get("gaps") or missing or []),
            reasoning=explanation_payload.get("reasoning")
            or row.get("description")
            or "Legacy job match record.",
        ),
        remote=row.get("remote"),
        seniority=row.get("seniority"),
        match_pct=int(round(float(row.get("match_pct") or final_pct))),
        matched=list(matched or []),
        missing=list(missing or []),
        salary=row.get("salary"),
        posted_days=row.get("posted_days"),
        description=row.get("description"),
        external_url=row.get("external_url") or row.get("apply_url"),
    )


def _insert_job_match(row: dict[str, Any]) -> None:
    try:
        db_client.table("job_matches").insert(row).execute()
        return
    except Exception:
        logger.warning(
            "job_matches insert failed with structured columns; retrying legacy shape",
            exc_info=True,
        )
        legacy_row = {
            key: value
            for key, value in row.items()
            if key
            not in {
                "job_id",
                "query_role",
                "user_location_preference",
                "score_json",
                "explanation_json",
            }
        }
        db_client.table("job_matches").insert(legacy_row).execute()


@router.post("/", response_model=JobSearchResponse)
async def research_jobs(req: ResearchJobsRequest, user_id: str = Depends(require_user_id)):
    try:
        # 1) Resolve target role from Supabase.
        role_resp = (
            db_client.table("target_roles")
            .select("id,title")
            .eq("id", req.target_role_id)
            .limit(1)
            .execute()
        )
        if not role_resp.data:
            raise HTTPException(status_code=404, detail="Target role not found")
        role_info = role_resp.data[0]

        # 2) Get latest resume for user.
        resume_id = latest_resume_id(user_id)
        if not resume_id:
            raise HTTPException(status_code=400, detail="Run resume extraction first")

        # 3) Pull profile/location and resume context from normalized schema.
        resume_row_resp = (
            db_client.table("resumes")
            .select("headline,summary")
            .eq("id", resume_id)
            .limit(1)
            .execute()
        )
        resume_row = (resume_row_resp.data or [{}])[0]

        location = "Remote"
        try:
            profile_resp = (
                db_client.table("profiles")
                .select("location")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if profile_resp.data and profile_resp.data[0].get("location"):
                location = profile_resp.data[0]["location"]
        except Exception:
            logger.warning("profile location lookup failed for user %s", user_id, exc_info=True)

        if location == "Remote":
            try:
                contact_resp = (
                    db_client.table("contacts")
                    .select("location,city,country")
                    .eq("resume_id", resume_id)
                    .limit(1)
                    .execute()
                )
                if contact_resp.data:
                    contact = contact_resp.data[0]
                    location = (
                        contact.get("location")
                        or contact.get("city")
                        or contact.get("country")
                        or "Remote"
                    )
            except Exception:
                logger.warning("contact location lookup failed for resume %s", resume_id, exc_info=True)

        skills_resp = (
            db_client.table("skills")
            .select("skill")
            .eq("resume_id", resume_id)
            .execute()
        )
        langs_resp = (
            db_client.table("programming_languages")
            .select("language")
            .eq("resume_id", resume_id)
            .execute()
        )

        user_skills = [row["skill"] for row in (skills_resp.data or []) if row.get("skill")]
        user_skills.extend([row["language"] for row in (langs_resp.data or []) if row.get("language")])

        # JOB-1: confirmed GitHub skills count toward job matching too (parity with
        # gap analysis). Only confirmed=true — quarantined guesses never inflate matches.
        try:
            gh_resp = (
                db_client.table("github_skill_evidence")
                .select("skill")
                .eq("user_id", user_id)
                .eq("confirmed", True)
                .execute()
            )
            user_skills.extend([r["skill"] for r in (gh_resp.data or []) if r.get("skill")])
        except Exception:
            # github optional — never block a job search on it, but log it.
            logger.warning("github skill lookup failed for user %s", user_id, exc_info=True)

        # Dedupe (resume ∪ GitHub can overlap) while preserving order.
        user_skills = list(dict.fromkeys(user_skills))

        if not user_skills:
            raise HTTPException(status_code=400, detail="No skills found. Re-run resume extraction.")

        exp_resp = (
            db_client.table("experiences")
            .select("id,title,company,start_date,end_date")
            .eq("resume_id", resume_id)
            .execute()
        )
        exp_rows = exp_resp.data or []

        # ⚡ Bolt Optimization: Fix N+1 query performance bottleneck
        # What: Replaced sequential Supabase queries for experience bullets with a single batched .in_() query
        # Why: Iterating over exp_rows and firing a network request for each blocked the event loop and caused N+1 latency
        # Impact: Reduces DB queries from O(N) to O(1), cutting resume processing latency
        exp_ids = [e["id"] for e in exp_rows if e.get("id")]
        exp_bullets_map = defaultdict(list)

        if exp_ids:
            bullets_resp = (
                db_client.table("experience_bullets")
                .select("experience_id,bullet")
                .in_("experience_id", exp_ids)
                .execute()
            )
            for b in (bullets_resp.data or []):
                if b.get("bullet") and b.get("experience_id"):
                    exp_bullets_map[b["experience_id"]].append(b["bullet"])

        exp_items = []
        for e in exp_rows:
            exp_items.append(
                {
                    "title": e.get("title"),
                    "company": e.get("company"),
                    "start_date": e.get("start_date"),
                    "end_date": e.get("end_date"),
                    "description_bullets": exp_bullets_map.get(e.get("id"), []),
                }
            )

        proj_resp = (
            db_client.table("projects")
            .select("name,description")
            .eq("resume_id", resume_id)
            .execute()
        )
        projects = proj_resp.data or []

        edu_resp = (
            db_client.table("education")
            .select("degree,institution")
            .eq("resume_id", resume_id)
            .execute()
        )
        education = edu_resp.data or []

        # 4) Run Adzuna + Jina + Gemini pipeline.
        resume_payload = {
            "skills": [s for s in user_skills if s],
            "programming_languages": [row["language"] for row in (langs_resp.data or []) if row.get("language")],
            "headline": resume_row.get("headline") or "",
            "experience": exp_items,
            "education": education,
            "projects": projects,
            "summary": resume_row.get("summary") or "",
        }
        parsed = job_finder_agent(
            resume=resume_payload,
            target_role=role_info["title"],
            user_location_pref=location or "Remote",
            top_k=8,
        )

        # 5) Persist jobs using the legacy flat columns plus the structured payload.
        db_client.table("job_matches").delete().eq("user_id", user_id).execute()

        insert_rows = []
        for job in parsed.jobs:
            payload = job.model_dump()
            insert_rows.append({
                "user_id": user_id,
                "job_id": payload.get("job_id"),
                "query_role": parsed.query_role,
                "user_location_preference": parsed.user_location_preference,
                "title": payload.get("title"),
                "company": payload.get("company"),
                "location": payload.get("location"),
                "remote": bool(payload.get("remote") or False),
                "seniority": payload.get("seniority"),
                "match_pct": payload.get("match_pct", 0),
                "matched": payload.get("matched", []),
                "missing": payload.get("missing", []),
                "salary": payload.get("salary"),
                "posted_days": _posted_days_to_int(payload.get("posted_days")),
                "description": payload.get("description"),
                "external_url": payload.get("external_url"),
                "score_json": payload.get("score"),
                "explanation_json": payload.get("explanation"),
            })

        if insert_rows:
            # ⚡ Bolt Optimization: Fix N+1 query performance bottleneck
            # What: Replaced sequential database inserts with a single bulk insert operation
            # Why: Inserting rows one by one blocks the event loop per insertion, which adds significant latency
            # Impact: Reduces DB queries from O(N) to O(1), improving job match persistence time
            try:
                db_client.table("job_matches").insert(insert_rows).execute()
            except Exception:
                logger.warning(
                    "job_matches bulk insert failed with structured columns; retrying legacy shape one by one",
                    exc_info=True,
                )
                for row in insert_rows:
                    legacy_row = {
                        key: value
                        for key, value in row.items()
                        if key
                        not in {
                            "job_id",
                            "query_role",
                            "user_location_preference",
                            "score_json",
                            "explanation_json",
                        }
                    }
                    try:
                        db_client.table("job_matches").insert(legacy_row).execute()
                    except Exception:
                        pass

        return parsed

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("research_jobs failed for user %s", user_id)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=JobSearchResponse)
def list_job_matches(user_id: str = Depends(require_user_id)):
    """Return the current user's persisted job matches (latest search)."""
    try:
        resp = (
            db_client.table("job_matches")
            .select("*")
            .eq("user_id", user_id)
            .order("match_pct", desc=True)
            .execute()
        )
    except Exception as e:
        logger.exception("job_matches lookup failed for user %s", user_id)
        raise HTTPException(status_code=500, detail=f"Lookup failed: {e}") from e

    rows = resp.data or []
    query_role, location = _resolve_profile_context(user_id)
    if rows:
        query_role = rows[0].get("query_role") or query_role
        location = rows[0].get("user_location_preference") or location

    return JobSearchResponse(
        query_role=query_role,
        user_location_preference=location,
        total_jobs_fetched=len(rows),
        jobs=[_row_to_job_result(row) for row in rows],
    )
