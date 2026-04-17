from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.resume_extraction.service import pdf_bytes_to_markdown, extract_structured_resume_data

router = APIRouter(prefix="/api/parse-resume", tags=["Resume"])

class ParseResumeRequest(BaseModel):
    resume_key: str

@router.post("/")
async def parse_resume(
    req: ParseResumeRequest, 
    user_id: str = Depends(get_current_user_id)
):
    try:
        # 1. Download file from InsForge Storage bucket "resumes"
        pdf_bytes = await db_client.download_file("resumes", req.resume_key)
        
        # 2. Extract markdown
        md_text = pdf_bytes_to_markdown(pdf_bytes)
        
        # 3. Use LLM to extract JSON
        extracted = extract_structured_resume_data(md_text)
        
        # 4. Upsert into database
        # Profiles (update)
        profile_data = {
            "name": extracted.name,
            "headline": extracted.headline,
            "email": extracted.email,
            "location": extracted.location,
            "summary": extracted.summary,
            "resume_key": req.resume_key,
            "completeness": 30
        }
        await db_client.update("profiles", {"user_id": f"eq.{user_id}"}, profile_data)
        
        # Skills
        for skill in extracted.skills:
            await db_client.insert("skills", {
                "user_id": user_id, "name": skill.name, "category": skill.category, 
                "level": skill.level, "evidence": skill.evidence, "source": "resume"
            })
            
        # Experience
        for idx, exp in enumerate(extracted.experience):
            await db_client.insert("experience_items", {
                "user_id": user_id, "role": exp.role, "company": exp.company,
                "start_date": exp.start_date, "end_date": exp.end_date,
                "bullets": exp.bullets, "sort_order": idx
            })
            
        # Education
        for edu in extracted.education:
            await db_client.insert("education_items", {
                "user_id": user_id, "school": edu.school, "degree": edu.degree,
                "start_date": edu.start_date, "end_date": edu.end_date
            })
            
        # Projects
        for idx, proj in enumerate(extracted.projects):
            await db_client.insert("project_items", {
                "user_id": user_id, "name": proj.name, "description": proj.description,
                "tech": proj.tech, "link": proj.link, "sort_order": idx
            })
            
        return {"success": True, "message": "Resume parsed and profile updated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
