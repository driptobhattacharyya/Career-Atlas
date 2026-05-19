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


def _load_user_resume_id(user_id: str) -> str | None:
    try:
        resp = (
            db_client.table("resumes")
            .select("id")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        resp = (
            db_client.table("resumes")
            .select("id")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    if not resp.data:
        return None
    return resp.data[0]["id"]


def _load_gaps(resume_id: str, role_title: str) -> List[GapIn]:
    resp = (
        db_client.table("skill_gaps")
        .select("skill,category,relevance,difficulty,level_required,prerequisites,why")
        .eq("resume_id", resume_id)
        .eq("target_role", role_title)
        .order("relevance", desc=True)
        .execute()
    )
    rows = resp.data or []
    gaps: List[GapIn] = []
    for r in rows:
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
    role_title = role_resp.data[0]["title"]
    role_slug = resolve_role_slug(role_title)

    resume_id = _load_user_resume_id(user_id)
    if not resume_id:
        raise HTTPException(status_code=400, detail="Run resume extraction first")

    gaps = _load_gaps(resume_id, role_title)
    if not gaps:
        raise HTTPException(
            status_code=400,
            detail="No gaps found for this role. Run gap analysis first.",
        )

    state_input = {
        "gaps": gaps,
        "target_role": role_title,
        "notes": [],
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
    try:
        db_client.table("learning_pathways").delete()\
            .eq("user_id", user_id).eq("role_slug", role_slug).execute()
        db_client.table("learning_pathways").insert({
            "user_id": user_id,
            "role_slug": role_slug,
            "target_role": role_title,
            "pathway": pathway_json,
            "sources": sources,
            "iterations_used": iterations_used,
            "quality_score": quality_score,
            "quality_verdict": verdict.model_dump(mode="json") if verdict else None,
            "validation": validation.model_dump(mode="json") if validation else None,
        }).execute()
    except Exception as e:
        logger.warning("learning_pathways persistence failed (table may not exist yet): %s", e)

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
    role_slug: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    q = (
        db_client.table("learning_pathways")
        .select(
            "role_slug,target_role,pathway,sources,iterations_used,"
            "quality_score,quality_verdict,validation,created_at"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
    )
    if role_slug:
        q = q.eq("role_slug", role_slug)
    try:
        resp = q.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup failed: {e}")
    if not resp.data:
        raise HTTPException(status_code=404, detail="No pathway found")
    return {"success": True, **resp.data[0]}
