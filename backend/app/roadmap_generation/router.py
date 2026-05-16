from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.roadmap_generation.service import create_roadmap_for_gaps

router = APIRouter(prefix="/api/generate-roadmap", tags=["Roadmap"])


class GenerateRoadmapRequest(BaseModel):
    target_role_id: str


@router.post("/")
async def generate_roadmap(
    req: GenerateRoadmapRequest, user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
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
        role_title = role_info["title"]

        try:
            resume_resp = (
                db_client.table("resumes")
                .select("id")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception:
            resume_resp = (
                db_client.table("resumes")
                .select("id")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        if not resume_resp.data:
            raise HTTPException(status_code=400, detail="Run resume extraction first")
        resume_id = resume_resp.data[0]["id"]

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

        try:
            db_client.table("milestones").delete().eq("user_id", user_id).execute()
            for idx, ms in enumerate(generated_milestones):
                db_client.table("milestones").insert(
                    {
                        "user_id": user_id,
                        "phase": ms.phase,
                        "title": ms.title,
                        "skill": ms.skill,
                        "status": "in-progress" if idx == 0 else "locked",
                        "estimated_weeks": ms.estimated_weeks,
                        "description": ms.description,
                        "courses": [c.model_dump() for c in ms.courses],
                        "project": ms.project.model_dump(),
                        "checklist": ms.checklist,
                        "sort_order": idx,
                    }
                ).execute()
        except Exception as exc:
            persisted = False
            persist_error = str(exc)
            print(f"[roadmap_generation] milestones persistence skipped: {persist_error}")

        return {
            "success": True,
            "milestones": [m.model_dump() for m in generated_milestones],
            "persisted": persisted,
            "persist_error": persist_error,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
