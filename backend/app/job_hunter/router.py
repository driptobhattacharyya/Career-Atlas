from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.job_hunter.agent import job_hunter_agent

router = APIRouter(prefix="/api/research-jobs", tags=["Jobs"])

class ResearchJobsRequest(BaseModel):
    target_role_id: str

@router.post("/")
async def research_jobs(req: ResearchJobsRequest, user_id: str = Depends(get_current_user_id)):
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

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

        # 3) Pull profile/location and skills from normalized schema.
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
            pass

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
                pass

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
        if not user_skills:
            raise HTTPException(status_code=400, detail="No skills found. Re-run resume extraction.")

        # 4) Run agent pipeline.
        state_input = {
            "target_role": role_info["title"],
            "user_skills": user_skills,
            "location": location,
            "iterations": 0
        }

        final_state = job_hunter_agent.invoke(state_input)
        parsed_jobs = final_state.get("parsed_jobs", [])

        # 5) Persist jobs.
        db_client.table("job_matches").delete().eq("user_id", user_id).execute()

        for job in parsed_jobs:
            payload = job.model_dump() if hasattr(job, "model_dump") else job
            db_client.table("job_matches").insert({
                "user_id": user_id,
                "title": payload.get("title"),
                "company": payload.get("company"),
                "location": payload.get("location"),
                "remote": payload.get("remote", False),
                "seniority": payload.get("seniority"),
                "match_pct": payload.get("match_pct", 0),
                "matched": payload.get("matched", []),
                "missing": payload.get("missing", []),
                "salary": payload.get("salary"),
                "posted_days": payload.get("posted_days", 0),
                "description": payload.get("description"),
                "external_url": payload.get("external_url"),
            }).execute()

        return {"success": True, "jobs": [j.model_dump() for j in parsed_jobs]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
