"""
Gap Analysis Agent — API Router.

POST /api/analyze-gaps/
  - Fetches user skills from DB
  - Resolves target role
  - Runs hybrid retrieval + LLM gap analysis
  - Stores results in DB
  - Returns ranked gaps
"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.gap_analysis.service import generate_gaps_for_user
from app.gap_analysis.hybrid_retrieval import resolve_role_slug

from app.gap_analysis.schemas import AnalyzeGapsRequest

router = APIRouter(prefix="/api/analyze-gaps", tags=["Gaps"])


@router.get("/")
async def get_saved_gaps(
    user_id: str = Depends(get_current_user_id, use_cache=True),
):
    """Return the user's latest stored skill gaps so results reload on re-sign-in."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Resolve latest resume for this user — strictly scoped to user_id.
        resume_resp = db_client.table("resumes")\
            .select("id")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if not resume_resp.data:
            return {"success": True, "gaps": [], "target_role": None}

        resume_id = resume_resp.data[0]["id"]

        gaps_resp = db_client.table("skill_gaps")\
            .select("*")\
            .eq("resume_id", resume_id)\
            .execute()

        gaps = gaps_resp.data or []
        target_role = gaps[0]["target_role"] if gaps else None

        return {
            "success": True,
            "target_role": target_role,
            "gaps": gaps,
            "retrieval_source": "database",
        }
    except Exception as e:
        print(f"❌ ERROR in get_saved_gaps: {str(e)}")
        return {"success": True, "gaps": [], "target_role": None}


@router.post("/")
async def analyze_gaps(
    req: AnalyzeGapsRequest,
    user_id: str = Depends(get_current_user_id, use_cache=True),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # 1. Fetch user data from DB (using schema from Resume_Extraction_Agent.ipynb)
        user_skills = []
        user_headline = ""
        resume_id = None
        try:
            # Strictly scoped to user_id — never a global resume lookup.
            resume_resp = db_client.table("resumes")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if resume_resp.data:
                resume = resume_resp.data[0]
                resume_id = resume["id"]
                user_headline = resume.get("headline", "")

                # Fetch skills scoped to this resume only.
                skills_resp = db_client.table("skills").select("skill").eq("resume_id", resume_id).execute()
                user_skills.extend([s["skill"] for s in skills_resp.data if s.get("skill")])

                # Fetch programming languages from 'programming_languages' table
                langs_resp = db_client.table("programming_languages").select("language").eq("resume_id", resume_id).execute()
                user_skills.extend([lang_row["language"] for lang_row in langs_resp.data if lang_row.get("language")])

                # Fetch GitHub profile analysis to enhance headline/context
                github_resp = db_client.table("github_profiles").select("analysis_summary,coding_behavior").eq("user_id", user_id).execute()
                if github_resp.data:
                    github_summary = github_resp.data[0].get("analysis_summary", "")
                    github_behavior = github_resp.data[0].get("coding_behavior", "")
                    if github_summary or github_behavior:
                        user_headline += f"\n\nGitHub Profile Context:\nSummary: {github_summary}\nCoding Behavior: {github_behavior}"
        except Exception:
            # Silently fallback to empty if DB schema mismatch occurs
            pass

        # 2. Use target role title directly (Dynamic Mode)
        role_title = req.target_role_title
        role_slug = resolve_role_slug(role_title)

        # ── SMART CACHE CHECK (Linked to Resume ID) ────────────────────────
        # DESIGN IMPROVEMENT: Link gaps to resume_id. 
        # If the resume changes (new ID), the cache automatically busts.
        if resume_id and not req.force:
            try:
                existing_gaps_resp = db_client.table("skill_gaps")\
                    .select("*")\
                    .eq("resume_id", resume_id)\
                    .eq("target_role", role_title)\
                    .execute()
                
                if existing_gaps_resp.data:
                    print(f"✅ [CACHE] Found valid gaps for Resume {resume_id}. Skipping AI run.")
                    return {
                        "success": True,
                        "target_role": role_title,
                        "role_slug": role_slug,
                        "gaps": existing_gaps_resp.data,
                        "retrieval_source": "database_cache",
                        "explainability": {
                            "role_slug": role_slug,
                            "input_skill_count": len(user_skills),
                            "retrieved_requirements": [],
                            "note": "Served from cached DB gaps; retrieval trace unavailable for this run.",
                        },
                    }
            except Exception:
                pass

        # 3. Run gap analysis pipeline (Only if cache miss)
        identified_gaps, explainability = await generate_gaps_for_user(user_skills, role_title, user_headline)

        # 4. Optional: Save gaps to DB for Deep Researcher
        if resume_id:
            try:
                # Clear previous gaps for this specific resume and role
                db_client.table("skill_gaps").delete()\
                    .eq("resume_id", resume_id)\
                    .eq("target_role", role_title)\
                    .execute()
                
                gap_data = [
                    {
                        "resume_id": resume_id, # Linking solely via Resume ID
                        "target_role": role_title,
                        "skill": gap.skill,
                        "category": gap.category,
                        "relevance": gap.relevance,
                        "difficulty": gap.difficulty,
                        "level_required": gap.level_required,
                        "prerequisites": gap.prerequisites,
                        "why": gap.why,
                    }
                    for gap in identified_gaps
                ]
                if gap_data:
                    db_client.table("skill_gaps").insert(gap_data).execute()
            except Exception as e:
                print(f"⚠️ Could not save gaps to DB: {e}")
                pass

        return {
            "success": True,
            "target_role": role_title,
            "role_slug": role_slug,
            "gaps": [g.model_dump() for g in identified_gaps],
            "retrieval_source": "hybrid",
            "explainability": explainability,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in analyze_gaps: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gap Analysis Error: {str(e)}")
