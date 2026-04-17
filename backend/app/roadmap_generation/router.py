from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.roadmap_generation.service import create_roadmap_for_gaps

router = APIRouter(prefix="/api/generate-roadmap", tags=["Roadmap"])

class GenerateRoadmapRequest(BaseModel):
    target_role_id: str

@router.post("/")
async def generate_roadmap(req: GenerateRoadmapRequest, user_id: str = Depends(get_current_user_id)):
    try:
        # 1. Fetch Skill Gaps and target role
        gaps_raw = await db_client.select("skill_gaps", {"user_id": f"eq.{user_id}"})
        if not gaps_raw:
            raise HTTPException(status_code=400, detail="Run Gap Analysis first")
            
        role_data = await db_client.select("target_roles", {"id": f"eq.{req.target_role_id}"})
        role_info = role_data[0]
        
        # 2. Call LLM
        generated_milestones = create_roadmap_for_gaps(gaps_raw, role_info["title"])
        
        # 3. Clean DB and insert new
        await db_client.delete("milestones", {"user_id": f"eq.{user_id}"})
        
        # Convert models to dictionaries
        for idx, ms in enumerate(generated_milestones):
            await db_client.insert("milestones", {
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
                "sort_order": idx
            })
            
        return {"success": True, "milestones": [m.model_dump() for m in generated_milestones]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
