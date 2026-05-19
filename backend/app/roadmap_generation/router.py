"""
Roadmap Generation Agent — API Router.

Endpoints:
  POST  /api/generate-roadmap/                  regenerate milestones for a role,
                                                preserving prior progress state.
  GET   /api/generate-roadmap/                  list milestones (optionally scoped
                                                to a role_id) for the current user.
  PATCH /api/generate-roadmap/milestones/{id}   update milestone status.

Regenerate uses a role-scoped merge: identical (user, role, skill) rows keep
their existing status + completed_at; new skills get inserted; skills that
disappear from the new generation get deleted (scoped to that role only).
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.roadmap_generation.schemas import (
    MilestoneRowOut,
    MilestoneStatusUpdate,
)
from app.roadmap_generation.service import create_roadmap_for_gaps

router = APIRouter(prefix="/api/generate-roadmap", tags=["Roadmap"])


class GenerateRoadmapRequest(BaseModel):
    target_role_id: str


def _latest_resume_id(user_id: str) -> Optional[str]:
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
    return resp.data[0]["id"] if resp.data else None


@router.post("/")
async def generate_roadmap(
    req: GenerateRoadmapRequest,
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

    resume_id = _latest_resume_id(user_id)
    if not resume_id:
        raise HTTPException(status_code=400, detail="Run resume extraction first")

    gaps_resp = (
        db_client.table("skill_gaps")
        .select("*")
        .eq("resume_id", resume_id)
        .eq("target_role", role_title)
        .execute()
    )
    skill_gaps = gaps_resp.data or []
    if not skill_gaps:
        raise HTTPException(status_code=400, detail="Run Gap Analysis first")

    generated_milestones = create_roadmap_for_gaps(skill_gaps, role_title)

    persisted = True
    persist_error = None
    persisted_rows: List[dict] = []

    try:
        # Load prior milestones for THIS role only — preserve their progress.
        existing_resp = (
            db_client.table("milestones")
            .select("id,skill,status,completed_at")
            .eq("user_id", user_id)
            .eq("target_role_id", role_id)
            .execute()
        )
        prior_by_skill = {
            (row.get("skill") or "").strip().lower(): row
            for row in (existing_resp.data or [])
            if row.get("skill")
        }

        seen_skills: set[str] = set()
        rows_to_upsert: List[dict] = []
        for idx, ms in enumerate(generated_milestones):
            key = (ms.skill or "").strip().lower()
            seen_skills.add(key)
            prior = prior_by_skill.get(key)

            if prior:
                status = prior.get("status") or "locked"
                completed_at = prior.get("completed_at")
            else:
                status = "in_progress" if idx == 0 else "locked"
                completed_at = None

            row = {
                "user_id": user_id,
                "target_role": role_title,
                "target_role_id": role_id,
                "resume_id": resume_id,
                "phase": ms.phase,
                "title": ms.title,
                "skill": ms.skill,
                "status": status,
                "estimated_weeks": ms.estimated_weeks,
                "description": ms.description,
                "courses": [c.model_dump() for c in ms.courses],
                "project": ms.project.model_dump(),
                "checklist": ms.checklist,
                "sort_order": idx,
                "completed_at": completed_at,
            }
            if prior and prior.get("id"):
                row["id"] = prior["id"]
            rows_to_upsert.append(row)

        # Stale = same (user, role) but skill not in new generation. Scoped delete.
        stale_ids = [
            row["id"]
            for skill_key, row in prior_by_skill.items()
            if skill_key not in seen_skills and row.get("id")
        ]
        if stale_ids:
            db_client.table("milestones").delete().in_("id", stale_ids).execute()

        if rows_to_upsert:
            upsert_resp = (
                db_client.table("milestones")
                .upsert(rows_to_upsert, on_conflict="id")
                .execute()
            )
            persisted_rows = upsert_resp.data or []

    except Exception as exc:
        persisted = False
        persist_error = str(exc)
        print(f"[roadmap_generation] milestones persistence failed: {persist_error}")

    return {
        "success": True,
        "target_role": role_title,
        "target_role_id": role_id,
        "milestones": [m.model_dump() for m in generated_milestones],
        "persisted": persisted,
        "persist_error": persist_error,
        "rows": persisted_rows,
    }


@router.get("/")
async def list_milestones(
    target_role_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    q = (
        db_client.table("milestones")
        .select("*")
        .eq("user_id", user_id)
        .order("target_role_id")
        .order("sort_order")
    )
    if target_role_id:
        q = q.eq("target_role_id", target_role_id)
    resp = q.execute()
    return {"success": True, "milestones": resp.data or []}


@router.patch("/milestones/{milestone_id}", response_model=MilestoneRowOut)
async def update_milestone_status(
    milestone_id: str,
    body: MilestoneStatusUpdate,
    user_id: str = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    cur = (
        db_client.table("milestones")
        .select("id,user_id")
        .eq("id", milestone_id)
        .limit(1)
        .execute()
    )
    if not cur.data:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if cur.data[0].get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Milestone not found")

    completed_at = (
        datetime.now(timezone.utc).isoformat() if body.status == "completed" else None
    )
    upd = (
        db_client.table("milestones")
        .update({
            "status": body.status,
            "completed_at": completed_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", milestone_id)
        .execute()
    )
    if not upd.data:
        raise HTTPException(status_code=500, detail="Update returned no row")
    return MilestoneRowOut(**upd.data[0])
