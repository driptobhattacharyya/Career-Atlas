"""
Gap Analysis Agent — API Router.

POST /api/analyze-gaps/
  - Fetches user skills from DB
  - Resolves target role
  - Runs hybrid retrieval + LLM gap analysis
  - Stores results in DB
  - Returns ranked gaps
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.config import settings
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.gap_analysis.service import generate_gaps_for_user
from app.gap_analysis.hybrid_retrieval import resolve_role_slug

router = APIRouter(prefix="/api/analyze-gaps", tags=["Gaps"])


class AnalyzeGapsRequest(BaseModel):
    target_role_id: str


@router.post("/")
async def analyze_gaps(
    req: AnalyzeGapsRequest,
    user_id: str | None = Depends(get_current_user_id, use_cache=True),
    x_test_user_id: str | None = Header(default=None),
):
    # Dev bypass for Postman testing
    if settings.environment == "development" and x_test_user_id:
        user_id = x_test_user_id

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # 1. Fetch user skills from DB
        try:
            user_skills_raw = await db_client.select(
                "skills", {"user_id": f"eq.{user_id}", "select": "name"}
            )
            user_skills = [s["name"] for s in user_skills_raw]
        except Exception as e:
            print(f"⚠️ DB Select 'skills' failed: {e}. Using empty skills.")
            user_skills = []

        # 2. Fetch target role info
        try:
            role_data = await db_client.select(
                "target_roles", {"id": f"eq.{req.target_role_id}"}
            )
            if not role_data:
                raise ValueError("Role not in DB")
            role_info = role_data[0]
            role_title = role_info["title"]
        except Exception as e:
            print(f"⚠️ DB Select 'target_roles' failed: {e}. Using ID as title.")
            # Fallback to a prettified version of the ID
            role_title = req.target_role_id.replace("-", " ").title()
        
        role_slug = resolve_role_slug(role_title)

        # 3. Run gap analysis pipeline
        identified_gaps = await generate_gaps_for_user(user_skills, role_title)

        # 4. DB cleanup & insertion
        try:
            await db_client.delete("skill_gaps", {"user_id": f"eq.{user_id}"})
            for gap in identified_gaps:
                await db_client.insert("skill_gaps", {
                    "user_id": user_id,
                    "skill": gap.skill,
                    "category": gap.category,
                    "relevance": gap.relevance,
                    "difficulty": gap.difficulty,
                    "level_required": gap.level_required,
                    "prerequisites": gap.prerequisites,
                    "why": gap.why,
                })
        except Exception as e:
            print(f"⚠️ DB Write 'skill_gaps' failed: {e}. Returning results via API anyway.")

        return {
            "success": True,
            "target_role": role_title,
            "role_slug": role_slug,
            "gaps": [g.model_dump() for g in identified_gaps],
            "retrieval_source": "hybrid",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in analyze_gaps: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gap Analysis Error: {str(e)}")
