import re
import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.resume_extraction.service import (
    extract_structured_resume_data,
    pdf_bytes_to_markdown,
)
from app.utils.storage import upload_resume_file, download_resume_file

router = APIRouter(prefix="/api/parse-resume", tags=["Resume"])


def _safe_filename(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    return sanitized or "resume.pdf"


def _insert_resume_row(data: dict[str, Any], user_id: str, resume_key: str) -> str:
    # Always write user_id. A resume row without an owner is unusable and
    # would leak into other users' "latest resume" lookups — so never insert
    # one. Let a failure propagate instead of orphaning the row.
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


def insert_full_resume(data: dict[str, Any], user_id: str, resume_key: str) -> str:
    resume_id = _insert_resume_row(data, user_id, resume_key)

    contact = data.get("contact", {}) or {}
    skill_values: list[str] = []
    skill_values.extend([s for s in data.get("skills", []) or [] if isinstance(s, str) and s.strip()])
    skill_values.extend([s for s in data.get("programming_languages", []) or [] if isinstance(s, str) and s.strip()])
    skill_values.extend([s for s in data.get("spoken_languages", []) or [] if isinstance(s, str) and s.strip()])
    skill_values.extend([s for s in data.get("keywords", []) or [] if isinstance(s, str) and s.strip()])
    for exp in data.get("experience", []) or []:
        skill_values.extend([s for s in (exp.get("technologies") or []) if isinstance(s, str) and s.strip()])
    for proj in data.get("projects", []) or []:
        skill_values.extend([s for s in (proj.get("technologies") or []) if isinstance(s, str) and s.strip()])
    skill_values = list(dict.fromkeys(skill_values))
    try:
        db_client.table("contacts").insert({"resume_id": resume_id, **contact}).execute()
    except Exception:
        pass

    for s in skill_values:
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
            db_client.table("certifications").insert(
                {
                    "resume_id": resume_id,
                    "name": cert.get("name"),
                    "issuer": cert.get("issuer"),
                    "issue_date": cert.get("date"),
                    "expiry_date": None,
                    "credential_id": cert.get("credential_id"),
                    "credential_url": cert.get("link"),
                }
            ).execute()
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


def _delete_other_resumes(user_id: str, keep_resume_id: str) -> None:
    """Replace-on-upload: keep one resume per user.

    All child tables (skills, experiences, skill_gaps, milestones, …) FK to
    resumes with ON DELETE CASCADE, so dropping the old resume row also clears
    every stale derived row — no orphans.
    """
    try:
        db_client.table("resumes").delete()\
            .eq("user_id", user_id)\
            .neq("id", keep_resume_id)\
            .execute()
    except Exception:
        pass


def _latest_resume_id(user_id: str) -> str | None:
    """The user's most recent resume id, or None if they have none.

    Strictly scoped to user_id — never falls back to a global lookup, which
    would hand one user another user's resume.
    """
    resp = (
        db_client.table("resumes")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]["id"]
    return None


async def fetch_full_resume(resume_id: str) -> dict[str, Any]:
    # Phase 1: Fetch top-level entities concurrently
    queries = [
        asyncio.to_thread(lambda: db_client.table("resumes").select("*").eq("id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("contacts").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("skills").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("programming_languages").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("spoken_languages").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("keywords").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("experiences").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("education").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("projects").select("*").eq("resume_id", resume_id).execute()),
        asyncio.to_thread(lambda: db_client.table("certifications").select("*").eq("resume_id", resume_id).execute())
    ]

    results = await asyncio.gather(*queries, return_exceptions=True)

    # Handle exceptions (Supabase errors return standard Python exceptions)
    for res in results:
        if isinstance(res, Exception):
            pass # Or handle appropriately; here we rely on existing robust parsing

    # Map results (using list access, Supabase objects have .data)
    resume = results[0].data[0] if not isinstance(results[0], Exception) and results[0].data else {}
    contact = results[1].data[0] if not isinstance(results[1], Exception) and results[1].data else {}
    skills = [x["skill"] for x in results[2].data] if not isinstance(results[2], Exception) and results[2].data else []
    prog_langs = [x["language"] for x in results[3].data] if not isinstance(results[3], Exception) and results[3].data else []
    spoken_langs = [x["language"] for x in results[4].data] if not isinstance(results[4], Exception) and results[4].data else []
    keywords = [x["keyword"] for x in results[5].data] if not isinstance(results[5], Exception) and results[5].data else []

    experiences = results[6].data if not isinstance(results[6], Exception) and results[6].data else []
    education = results[7].data if not isinstance(results[7], Exception) and results[7].data else []
    projects = results[8].data if not isinstance(results[8], Exception) and results[8].data else []
    certifications = results[9].data if not isinstance(results[9], Exception) and results[9].data else []

    # Phase 2: Batch fetch all child entities in concurrent queries
    exp_ids = [exp["id"] for exp in experiences]
    edu_ids = [edu["id"] for edu in education]
    proj_ids = [proj["id"] for proj in projects]

    nested_queries = []

    if exp_ids:
        nested_queries.append(asyncio.to_thread(lambda: db_client.table("experience_bullets").select("*").in_("experience_id", exp_ids).execute()))
        nested_queries.append(asyncio.to_thread(lambda: db_client.table("experience_technologies").select("*").in_("experience_id", exp_ids).execute()))
    else:
        nested_queries.extend([None, None])

    if edu_ids:
        nested_queries.append(asyncio.to_thread(lambda: db_client.table("education_notes").select("*").in_("education_id", edu_ids).execute()))
    else:
        nested_queries.append(None)

    if proj_ids:
        nested_queries.append(asyncio.to_thread(lambda: db_client.table("project_technologies").select("*").in_("project_id", proj_ids).execute()))
    else:
        nested_queries.append(None)

    nested_promises = [q for q in nested_queries if q is not None]
    if nested_promises:
        nested_results_raw = await asyncio.gather(*nested_promises, return_exceptions=True)
    else:
        nested_results_raw = []

    nested_results = []
    for q in nested_queries:
        if q is None:
            nested_results.append(None)
        else:
            nested_results.append(nested_results_raw.pop(0))

    exp_bullets_res = nested_results[0]
    exp_techs_res = nested_results[1]
    edu_notes_res = nested_results[2]
    proj_techs_res = nested_results[3]

    # Process child relationships
    # Experiences
    exp_bullets = exp_bullets_res.data if exp_bullets_res and not isinstance(exp_bullets_res, Exception) else []
    exp_techs = exp_techs_res.data if exp_techs_res and not isinstance(exp_techs_res, Exception) else []

    bullets_by_exp = {}
    for b in exp_bullets:
        bullets_by_exp.setdefault(b["experience_id"], []).append(b["bullet"])

    techs_by_exp = {}
    for t in exp_techs:
        techs_by_exp.setdefault(t["experience_id"], []).append(t["tech"])

    for exp in experiences:
        exp["description_bullets"] = bullets_by_exp.get(exp["id"], [])
        exp["technologies"] = techs_by_exp.get(exp["id"], [])

    # Education
    edu_notes = edu_notes_res.data if edu_notes_res and not isinstance(edu_notes_res, Exception) else []
    notes_by_edu = {}
    for n in edu_notes:
        notes_by_edu.setdefault(n["education_id"], []).append(n["note"])

    for edu in education:
        edu["notes"] = notes_by_edu.get(edu["id"], [])

    # Projects
    proj_techs = proj_techs_res.data if proj_techs_res and not isinstance(proj_techs_res, Exception) else []
    techs_by_proj = {}
    for t in proj_techs:
        techs_by_proj.setdefault(t["project_id"], []).append(t["tech"])

    for proj in projects:
        proj["technologies"] = techs_by_proj.get(proj["id"], [])

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
            object_path = f"{user_id}/{timestamp}_{_safe_filename(file.filename or 'resume.pdf')}"
            upload_resume_file(object_path, upload_bytes)
            resolved_resume_key = object_path
            pdf_bytes = upload_bytes
        elif resume_key:
            try:
                pdf_bytes = download_resume_file(resume_key)
            except Exception:
                raise HTTPException(status_code=404, detail="Stored resume not found.")
            resolved_resume_key = resume_key
        else:
            raise HTTPException(status_code=400, detail="Provide either file upload or resume_key.")

        md_text = pdf_bytes_to_markdown(pdf_bytes)
        extracted = extract_structured_resume_data(md_text)
        extracted_dict = extracted.model_dump(mode="json")
        resume_id = insert_full_resume(extracted_dict, user_id, resolved_resume_key or "")
        _delete_other_resumes(user_id, resume_id)

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
    return {"success": True, "resume": await fetch_full_resume(resume_id)}


# ── Profile editing ─────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    target_role_id: str


class SkillIn(BaseModel):
    skill: str


class ExperienceUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None


def _user_resume_ids(user_id: str) -> list[str]:
    try:
        resp = db_client.table("resumes").select("id").eq("user_id", user_id).execute()
        return [r["id"] for r in (resp.data or []) if r.get("id")]
    except Exception:
        return []


@router.patch("/profile")
async def update_profile(body: ProfileUpdate, user_id: str = Depends(get_current_user_id)):
    """Change the user's target role (persisted in the `profiles` table)."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        db_client.table("profiles").upsert(
            {"user_id": user_id, "target_role_id": body.target_role_id},
            on_conflict="user_id",
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {e}")
    return {"success": True, "target_role_id": body.target_role_id}


@router.post("/skills")
async def add_skill(body: SkillIn, user_id: str = Depends(get_current_user_id)):
    """Add a skill to the user's latest resume."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skill = (body.skill or "").strip()
    if not skill:
        raise HTTPException(status_code=400, detail="Skill cannot be empty")
    resume_id = _latest_resume_id(user_id)
    if not resume_id:
        raise HTTPException(status_code=400, detail="No resume found")
    existing = (
        db_client.table("skills").select("skill").eq("resume_id", resume_id).execute()
    )
    if any((s.get("skill") or "").strip().lower() == skill.lower() for s in (existing.data or [])):
        return {"success": True, "skill": skill, "duplicate": True}
    db_client.table("skills").insert({"resume_id": resume_id, "skill": skill}).execute()
    return {"success": True, "skill": skill}


@router.delete("/skills")
async def delete_skill(skill: str, user_id: str = Depends(get_current_user_id)):
    """Remove a skill (by name) from the user's latest resume."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skill = (skill or "").strip()
    if not skill:
        raise HTTPException(status_code=400, detail="Skill cannot be empty")
    resume_id = _latest_resume_id(user_id)
    if not resume_id:
        raise HTTPException(status_code=400, detail="No resume found")
    db_client.table("skills").delete().eq("resume_id", resume_id).eq("skill", skill).execute()
    db_client.table("programming_languages").delete()\
        .eq("resume_id", resume_id).eq("language", skill).execute()
    return {"success": True, "skill": skill}


@router.patch("/experiences/{experience_id}")
async def update_experience(
    experience_id: str,
    body: ExperienceUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Edit an experience entry's title / company / dates."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    exp = (
        db_client.table("experiences")
        .select("id,resume_id")
        .eq("id", experience_id)
        .limit(1)
        .execute()
    )
    if not exp.data:
        raise HTTPException(status_code=404, detail="Experience not found")
    if exp.data[0]["resume_id"] not in _user_resume_ids(user_id):
        raise HTTPException(status_code=404, detail="Experience not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        db_client.table("experiences").update(updates).eq("id", experience_id).execute()
    return {"success": True, "updated": updates}

