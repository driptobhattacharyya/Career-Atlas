"""
Deep Researcher Agent — API Router.

POST /api/deep-research/         run the plan-search-critic-structure loop
GET  /api/deep-research/latest   return last persisted pathway for current user

Input: target_role_id (UUID from target_roles), optional max_iter.
Pipeline: lookup role → fetch latest resume → load gaps from skill_gaps
(populated by gap_analysis) → invoke LangGraph → persist pathway JSONB
into learning_pathways (one row per user+role).
"""
import logging
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.deep_researcher.agent import deep_researcher_agent
from app.deep_researcher.schemas import (
    DeepResearchRequest,
    DeepResearchResponse,
    GapIn,
    JudgeVerdict,
    Pathway,
    ValidationResult,
)
from app.gap_analysis.hybrid_retrieval import resolve_role_slug
from app.roadmap_generation.service import upsert_role_milestones

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deep-research", tags=["DeepResearch"])

_URL_RE = re.compile(r"https?://[^\s]+")


def _extract_sources(notes: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for n in notes or []:
        for url in _URL_RE.findall(n):
            url = url.rstrip(".,);:]")
            if url not in seen:
                seen.add(url)
                out.append(url)
    return out


def _persist_learning_pathway(
    *,
    user_id: str,
    role_id: str,
    role_slug: str,
    role_title: str,
    pathway_json: dict,
    sources: list[str],
    iterations_used: int,
    quality_score: float | None,
    verdict: dict | None,
    validation: dict | None,
) -> None:
    import json
    
    # Map the deep research output to the actual database columns 
    # to avoid the PGRST204 Schema Cache error.
    # We serialize the debug info into the 'description' field since the table lacks those columns.
    debug_info = {
        "sources": sources,
        "iterations_used": iterations_used,
        "quality_score": quality_score,
        "quality_verdict": verdict,
        "validation": validation,
    }
    
    full_row = {
        "user_id": user_id,
        "target_role_id": role_id,
        "role_slug": role_slug,
        "title": role_title,
        "estimated_weeks": pathway_json.get("estimated_weeks", 0),
        "milestones": pathway_json.get("milestones", []),
        "resources": [], 
        "description": json.dumps(debug_info)
    }

    try:
        db_client.table("learning_pathways").delete()\
            .eq("user_id", user_id).eq("role_slug", role_slug).execute()
        db_client.table("learning_pathways").insert(full_row).execute()
        return
    except Exception as e:
        logger.warning("learning_pathways persistence failed: %s", e)


def _load_user_resume_ids(user_id: str) -> List[str]:
    """All of the user's resume ids, newest first. Strictly scoped to user_id."""
    resp = (
        db_client.table("resumes")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [r["id"] for r in (resp.data or []) if r.get("id")]


def _load_user_resume_id(user_id: str) -> str | None:
    ids = _load_user_resume_ids(user_id)
    return ids[0] if ids else None


def _normalize_learning_pathway_row(row: dict) -> dict:
    import json
    
    # Reconstruct the Pathway object from the DB columns
    pathway = {
        "target_role": row.get("title") or "Unknown",
        "estimated_weeks": row.get("estimated_weeks") or 0,
        "milestones": row.get("milestones") or []
    }
    
    # Unpack the debug info from the description column
    debug_info = {}
    description = row.get("description")
    if description:
        try:
            debug_info = json.loads(description)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug("learning pathway description not JSON: %s", e)

    return {
        "success": True,
        "role_slug": row.get("role_slug"),
        "target_role": row.get("title") or row.get("role_slug") or "Unknown role",
        "pathway": pathway,
        "sources": debug_info.get("sources") or [],
        "iterations_used": int(debug_info.get("iterations_used") or 0),
        "quality_score": debug_info.get("quality_score"),
        "quality_verdict": debug_info.get("quality_verdict"),
        "validation": debug_info.get("validation"),
        "created_at": row.get("created_at"),
    }


def _load_gaps(user_id: str, role_title: str) -> List[GapIn]:
    """Most recent gap analysis for this role across all the user's resumes.

    skill_gaps rows are pinned to the resume_id that was current when gap
    analysis ran. A newer resume upload orphans them, so we don't bind to the
    "latest resume" — we take whichever resume has the most recent skill_gaps
    for this role (by created_at).
    """
    resume_ids = _load_user_resume_ids(user_id)
    if not resume_ids:
        return []
    resp = (
        db_client.table("skill_gaps")
        .select(
            "resume_id,skill,category,relevance,difficulty,"
            "level_required,prerequisites,why,created_at"
        )
        .in_("resume_id", resume_ids)
        .eq("target_role", role_title)
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        return []
    # Keep only the newest gap-analysis batch (one resume_id), not a mix.
    newest_resume_id = rows[0]["resume_id"]
    batch = [r for r in rows if r["resume_id"] == newest_resume_id]
    batch.sort(key=lambda r: r.get("relevance") or 0, reverse=True)
    gaps: List[GapIn] = []
    for r in batch:
        prereqs = r.get("prerequisites") or []
        if isinstance(prereqs, str):
            prereqs = [p.strip() for p in prereqs.split(",") if p.strip()]
        gaps.append(GapIn(
            skill=r.get("skill") or "",
            category=r.get("category") or "concept",
            relevance=int(r.get("relevance") or 0),
            difficulty=r.get("difficulty") or "Medium",
            prerequisites=prereqs,
            why=r.get("why") or "",
            level_required=r.get("level_required") or "intermediate",
        ))
    return gaps


@router.post("/", response_model=DeepResearchResponse)
def deep_research(
    req: DeepResearchRequest,
    user_id: str = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    role_resp = (
        db_client.table("target_roles")
        .select("id,title")
        .eq("id", req.target_role_id)
        .limit(1)
        .execute()
    )
    if not role_resp.data:
        raise HTTPException(status_code=404, detail="Target role not found")
    role_id = role_resp.data[0]["id"]
    role_title = role_resp.data[0]["title"]
    role_slug = resolve_role_slug(role_title)

    resume_id = _load_user_resume_id(user_id)
    if not resume_id:
        raise HTTPException(status_code=400, detail="Run resume extraction first")

    gaps = _load_gaps(user_id, role_title)
    if not gaps:
        raise HTTPException(
            status_code=400,
            detail="No gaps found for this role. Run gap analysis first.",
        )

    # Fetch GitHub profile to enhance the prompt notes if available
    github_notes = []
    try:
        github_resp = db_client.table("github_profiles").select("analysis_summary,coding_behavior").eq("user_id", user_id).execute()
        if github_resp.data:
            github_summary = github_resp.data[0].get("analysis_summary", "")
            github_behavior = github_resp.data[0].get("coding_behavior", "")
            if github_summary or github_behavior:
                github_notes.append(f"GitHub Profile Context:\nSummary: {github_summary}\nCoding Behavior: {github_behavior}")
    except Exception as e:
        logger.warning(f"Failed to fetch GitHub profile for deep research context: {e}")

    state_input = {
        "gaps": gaps,
        "target_role": role_title,
        "notes": github_notes,
        "iteration": 0,
        "max_iter": max(1, min(req.max_iter, 6)),
        "retry_count": 0,
        "max_retry": 1,
    }

    try:
        final_state = deep_researcher_agent.invoke(
            state_input, {"recursion_limit": 40}
        )
    except Exception as e:
        logger.exception("deep_researcher graph failure")
        raise HTTPException(status_code=500, detail=f"Deep research failed: {e}")

    pathway: Pathway = final_state.get("pathway")
    if not pathway:
        raise HTTPException(status_code=500, detail="Graph produced no pathway")

    iterations_used = int(final_state.get("iteration", 0))
    sources = _extract_sources(final_state.get("notes", []))

    verdict_raw = final_state.get("judge_verdict")
    verdict = JudgeVerdict(**verdict_raw) if verdict_raw else None
    validation_raw = final_state.get("validation")
    validation = ValidationResult(**validation_raw) if validation_raw else None
    quality_score = verdict.overall_score if verdict else None
    quality_passed = (verdict.pass_fail == "pass") if verdict else None

    pathway_json = pathway.model_dump(mode="json")
    _persist_learning_pathway(
        user_id=user_id,
        role_id=role_id,
        role_slug=role_slug,
        role_title=role_title,
        pathway_json=pathway_json,
        sources=sources,
        iterations_used=iterations_used,
        quality_score=quality_score,
        verdict=verdict.model_dump(mode="json") if verdict else None,
        validation=validation.model_dump(mode="json") if validation else None,
    )

    # Persist milestones into the `milestones` table so the roadmap page can
    # track progress. Status of surviving skills is preserved across re-runs.
    try:
        milestone_dicts = [
            {
                "phase": m.phase,
                "title": m.skill,
                "skill": m.skill,
                "estimated_weeks": m.estimated_weeks,
                "description": m.objective,
                "courses": [r.model_dump(mode="json") for r in m.resources],
                "project": {"title": "Mini project", "description": m.mini_project or ""},
                "checklist": m.checklist,
            }
            for m in pathway.milestones
        ]
        upsert_role_milestones(user_id, role_id, role_title, resume_id, milestone_dicts)
    except Exception as e:
        logger.warning("milestone persistence failed: %s", e)

    return DeepResearchResponse(
        success=True,
        target_role=role_title,
        role_slug=role_slug,
        pathway=pathway,
        iterations_used=iterations_used,
        sources=sources,
        quality_score=quality_score,
        quality_passed=quality_passed,
        verdict=verdict,
        validation=validation,
    )


@router.get("/latest")
def latest_pathway(
    target_role_id: str | None = None,
    role_slug: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Resolve the canonical slug the same way POST does, so a pathway saved
    # under ROLE_SLUG_MAP's slug is reachable. target_role_id is preferred;
    # role_slug is kept only as a legacy fallback.
    resolved_slug = role_slug
    if target_role_id:
        role_resp = (
            db_client.table("target_roles")
            .select("title")
            .eq("id", target_role_id)
            .limit(1)
            .execute()
        )
        if role_resp.data:
            resolved_slug = resolve_role_slug(role_resp.data[0]["title"])

    try:
        q = (
            db_client.table("learning_pathways")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
        )
        if resolved_slug:
            q = q.eq("role_slug", resolved_slug)
        resp = q.execute()
    except Exception as e:
        logger.warning("deep_researcher latest lookup failed: %s", e)
        raise HTTPException(status_code=404, detail="No pathway found")
    if not resp.data:
        raise HTTPException(status_code=404, detail="No pathway found")
    return _normalize_learning_pathway_row(resp.data[0])
