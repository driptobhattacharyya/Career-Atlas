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
        # 1. Fetch user skills and location
        profile_data = await db_client.select("profiles", {"user_id": f"eq.{user_id}"})
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        location = profile_data[0].get("location", "Remote")
            
        skills_raw = await db_client.select("skills", {"user_id": f"eq.{user_id}", "select": "name"})
        user_skills = [s["name"] for s in skills_raw]
        
        # 2. Fetch role
        role_data = await db_client.select("target_roles", {"id": f"eq.{req.target_role_id}"})
        role_info = role_data[0]
        
        # 3. Run Agent
        state_input = {
            "target_role": role_info["title"],
            "user_skills": user_skills,
            "location": location,
            "iterations": 0
        }
        
        final_state = job_hunter_agent.invoke(state_input)
        parsed_jobs = final_state.get("parsed_jobs", [])
        
        # 4. Insert into DB
        await db_client.delete("job_matches", {"user_id": f"eq.{user_id}"})
        
        for job in parsed_jobs:
            await db_client.insert("job_matches", {
                "user_id": user_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote": job.remote,
                "seniority": job.seniority,
                "match_pct": job.match_pct,
                "matched": job.matched,
                "missing": job.missing,
                "salary": job.salary,
                "posted_days": job.posted_days,
                "description": job.description,
                "external_url": job.external_url
            })
            
        return {"success": True, "jobs": [j.model_dump() for j in parsed_jobs]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
