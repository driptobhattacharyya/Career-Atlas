import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.resume_extraction.service import (
    extract_structured_resume_data,
    pdf_bytes_to_markdown,
)

router = APIRouter(prefix="/api/parse-resume", tags=["Resume"])
RESUME_STORAGE_DIR = Path("static/resumes")
RESUME_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    return sanitized or "resume.pdf"


def _insert_resume_row(data: dict[str, Any], user_id: str, resume_key: str) -> str:
    try:
        resp = (
            db_client.table("resumes")
            .insert(
                {
                    "user_id": user_id,
                    "resume_key": resume_key,
                    "full_name": data.get("full_name"),
                    "headline": data.get("headline"),
                    "summary": data.get("summary"),
                }
            )
            .execute()
        )
        return resp.data[0]["id"]
    except Exception:
        # Fallback to strict minimal schema.
        resp = (
            db_client.table("resumes")
            .insert(
                {
                    "full_name": data.get("full_name"),
                    "headline": data.get("headline"),
                    "summary": data.get("summary"),
                }
            )
            .execute()
        )
        return resp.data[0]["id"]


def insert_full_resume(data: dict[str, Any], user_id: str, resume_key: str) -> str:
    resume_id = _insert_resume_row(data, user_id, resume_key)

    contact = data.get("contact", {}) or {}
    try:
        db_client.table("contacts").insert({"resume_id": resume_id, **contact}).execute()
    except Exception:
        pass

    for s in data.get("skills", []) or []:
        db_client.table("skills").insert({"resume_id": resume_id, "skill": s}).execute()

    for s in data.get("programming_languages", []) or []:
        try:
            db_client.table("programming_languages").insert({"resume_id": resume_id, "language": s}).execute()
        except Exception:
            pass

    for s in data.get("spoken_languages", []) or []:
        try:
            db_client.table("spoken_languages").insert({"resume_id": resume_id, "language": s}).execute()
        except Exception:
            pass

    for k in data.get("keywords", []) or []:
        try:
            db_client.table("keywords").insert({"resume_id": resume_id, "keyword": k}).execute()
        except Exception:
            pass

    for exp in data.get("experience", []) or []:
        exp_res = db_client.table("experiences").insert(
            {
                "resume_id": resume_id,
                "company": exp.get("company"),
                "title": exp.get("title"),
                "location": exp.get("location"),
                "start_date": exp.get("start_date"),
                "end_date": exp.get("end_date"),
                "is_current": exp.get("is_current"),
            }
        ).execute()

        exp_id = exp_res.data[0]["id"]
        for b in exp.get("description_bullets", []) or []:
            db_client.table("experience_bullets").insert({"experience_id": exp_id, "bullet": b}).execute()
        for t in exp.get("technologies", []) or []:
            db_client.table("experience_technologies").insert({"experience_id": exp_id, "tech": t}).execute()

    for edu in data.get("education", []) or []:
        edu_res = db_client.table("education").insert(
            {
                "resume_id": resume_id,
                "institution": edu.get("institution"),
                "degree": edu.get("degree"),
                "field_of_study": edu.get("field_of_study"),
                "start_date": edu.get("start_date"),
                "end_date": edu.get("end_date"),
                "grade": edu.get("grade"),
            }
        ).execute()

        edu_id = edu_res.data[0]["id"]
        for n in edu.get("notes", []) or []:
            db_client.table("education_notes").insert({"education_id": edu_id, "note": n}).execute()

    for proj in data.get("projects", []) or []:
        proj_res = db_client.table("projects").insert(
            {
                "resume_id": resume_id,
                "name": proj.get("name"),
                "description": proj.get("description"),
                "link": proj.get("link"),
            }
        ).execute()

        proj_id = proj_res.data[0]["id"]
        for t in proj.get("technologies", []) or []:
            db_client.table("project_technologies").insert({"project_id": proj_id, "tech": t}).execute()

    for cert in data.get("certifications", []) or []:
        try:
            db_client.table("certifications").insert({"resume_id": resume_id, **cert}).execute()
        except Exception:
            pass

    # Optional sync for older UI paths that read profiles.
    try:
        db_client.table("profiles").upsert(
            {
                "user_id": user_id,
                "name": data.get("full_name") or "Candidate",
                "headline": data.get("headline"),
                "summary": data.get("summary"),
                "email": contact.get("email"),
                "location": contact.get("location"),
                "github": contact.get("github"),
                "resume_key": resume_key,
                "completeness": 30,
            },
            on_conflict="user_id",
        ).execute()
    except Exception:
        pass

    return resume_id


def _latest_resume_id(user_id: str) -> str | None:
    try:
        by_user = (
            db_client.table("resumes")
            .select("id")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if by_user.data:
            return by_user.data[0]["id"]
    except Exception:
        pass

    latest = db_client.table("resumes").select("id").order("created_at", desc=True).limit(1).execute()
    if latest.data:
        return latest.data[0]["id"]
    return None


def fetch_full_resume(resume_id: str) -> dict[str, Any]:
    resume = db_client.table("resumes").select("*").eq("id", resume_id).execute().data[0]

    contact_rows = db_client.table("contacts").select("*").eq("resume_id", resume_id).execute().data
    contact = contact_rows[0] if contact_rows else {}

    skills = [x["skill"] for x in db_client.table("skills").select("*").eq("resume_id", resume_id).execute().data]
    prog_langs = [x["language"] for x in db_client.table("programming_languages").select("*").eq("resume_id", resume_id).execute().data]
    spoken_langs = [x["language"] for x in db_client.table("spoken_languages").select("*").eq("resume_id", resume_id).execute().data]
    keywords = [x["keyword"] for x in db_client.table("keywords").select("*").eq("resume_id", resume_id).execute().data]

    experiences: list[dict[str, Any]] = []
    exp_rows = db_client.table("experiences").select("*").eq("resume_id", resume_id).execute().data
    for exp in exp_rows:
        exp_id = exp["id"]
        bullets = [x["bullet"] for x in db_client.table("experience_bullets").select("*").eq("experience_id", exp_id).execute().data]
        techs = [x["tech"] for x in db_client.table("experience_technologies").select("*").eq("experience_id", exp_id).execute().data]
        exp["description_bullets"] = bullets
        exp["technologies"] = techs
        experiences.append(exp)

    education: list[dict[str, Any]] = []
    edu_rows = db_client.table("education").select("*").eq("resume_id", resume_id).execute().data
    for edu in edu_rows:
        edu_id = edu["id"]
        notes = [x["note"] for x in db_client.table("education_notes").select("*").eq("education_id", edu_id).execute().data]
        edu["notes"] = notes
        education.append(edu)

    projects: list[dict[str, Any]] = []
    proj_rows = db_client.table("projects").select("*").eq("resume_id", resume_id).execute().data
    for proj in proj_rows:
        proj_id = proj["id"]
        techs = [x["tech"] for x in db_client.table("project_technologies").select("*").eq("project_id", proj_id).execute().data]
        proj["technologies"] = techs
        projects.append(proj)

    try:
        certifications = db_client.table("certifications").select("*").eq("resume_id", resume_id).execute().data
    except Exception:
        certifications = []

    return {
        "resume_id": resume_id,
        "full_name": resume.get("full_name"),
        "headline": resume.get("headline"),
        "summary": resume.get("summary"),
        "contact": contact,
        "skills": skills,
        "programming_languages": prog_langs,
        "spoken_languages": spoken_langs,
        "experience": experiences,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "keywords": keywords,
    }


@router.post("/")
async def parse_resume(
    file: UploadFile | None = File(default=None),
    resume_key: str | None = Form(default=None),
    user_id: str = Depends(get_current_user_id),
):
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        resolved_resume_key = resume_key
        pdf_bytes: bytes
        if file is not None:
            upload_bytes = await file.read()
            if not upload_bytes:
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            stored_name = f"{user_id}_{timestamp}_{_safe_filename(file.filename or 'resume.pdf')}"
            local_path = RESUME_STORAGE_DIR / stored_name
            local_path.write_bytes(upload_bytes)
            resolved_resume_key = str(local_path)
            pdf_bytes = upload_bytes
        elif resume_key:
            local_path = Path(resume_key)
            if not local_path.exists():
                raise HTTPException(status_code=404, detail="Local resume file not found.")
            resolved_resume_key = str(local_path)
            pdf_bytes = local_path.read_bytes()
        else:
            raise HTTPException(status_code=400, detail="Provide either file upload or resume_key.")

        md_text = pdf_bytes_to_markdown(pdf_bytes)
        extracted = extract_structured_resume_data(md_text)
        extracted_dict = extracted.model_dump(mode="json")
        resume_id = insert_full_resume(extracted_dict, user_id, resolved_resume_key or "")

        return {"success": True, "message": "Resume parsed and stored successfully.", "resume_id": resume_id}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/latest")
async def get_latest_resume(user_id: str = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    resume_id = _latest_resume_id(user_id)
    if not resume_id:
        return {"success": True, "resume": None}
    return {"success": True, "resume": fetch_full_resume(resume_id)}

