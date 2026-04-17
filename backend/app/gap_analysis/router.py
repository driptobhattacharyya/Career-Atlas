from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.gap_analysis.service import generate_gaps_for_user

router = APIRouter(prefix="/api/analyze-gaps", tags=["Gaps"])

class AnalyzeGapsRequest(BaseModel):
    target_role_id: str

@router.post("/")
async def analyze_gaps(req: AnalyzeGapsRequest, user_id: str = Depends(get_current_user_id)):
    try:
        # 1. Fetch user skills
        user_skills_raw = await db_client.select("skills", {"user_id": f"eq.{user_id}", "select": "name"})
        user_skills = [s["name"] for s in user_skills_raw]
        
        # 2. Fetch target role popular skills
        role_data = await db_client.select("target_roles", {"id": f"eq.{req.target_role_id}"})
        if not role_data:
            raise HTTPException(status_code=404, detail="Target role not found")
        role_info = role_data[0]
        
        # 3. Call Groq service
        identified_gaps = generate_gaps_for_user(user_skills, role_info["popular_skills"], role_info["title"])
        
        # 4. DB cleanup & insertion
        await db_client.delete("skill_gaps", {"user_id": f"eq.{user_id}"})
        
        for gap in identified_gaps:
            await db_client.insert("skill_gaps", {
                "user_id": user_id,
                "skill": gap.skill,
                "category": gap.category,
                "relevance": gap.relevance,
                "difficulty": gap.difficulty,
                "prerequisites": gap.prerequisites,
                "why": gap.why
            })
            
        return {"success": True, "gaps": [g.model_dump() for g in identified_gaps]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
