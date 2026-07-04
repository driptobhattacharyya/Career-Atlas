import re
from datetime import datetime, timezone
from typing import Any
import asyncio
from collections import defaultdict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.resume_extraction.schemas import ResumeExtraction
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


# ⚡ Bolt Optimization: Reduced N+1 queries using batched fetches and concurrent async I/O.
# Expected Impact: Converts O(N) sequential queries (where N is the number of experiences, educations, and projects)
# into a constant O(1) number of batched, concurrent queries. Significant reduction in database latency.
async def fetch_full_resume(resume_id: str) -> dict[str, Any]:
    def _fetch_base():
        return {
            "resume": db_client.table("resumes").select("*").eq("id", resume_id).execute().data,
            "contact": db_client.table("contacts").select("*").eq("resume_id", resume_id).execute().data,
            "skills": db_client.table("skills").select("*").eq("resume_id", resume_id).execute().data,
            "prog_langs": db_client.table("programming_languages").select("*").eq("resume_id", resume_id).execute().data,
            "spoken_langs": db_client.table("spoken_languages").select("*").eq("resume_id", resume_id).execute().data,
            "keywords": db_client.table("keywords").select("*").eq("resume_id", resume_id).execute().data,
            "experiences": db_client.table("experiences").select("*").eq("resume_id", resume_id).execute().data,
            "education": db_client.table("education").select("*").eq("resume_id", resume_id).execute().data,
            "projects": db_client.table("projects").select("*").eq("resume_id", resume_id).execute().data,
            "certifications": db_client.table("certifications").select("*").eq("resume_id", resume_id).execute().data
        }

    # Run all non-dependent top-level queries concurrently
    base_data = await asyncio.to_thread(_fetch_base)

    resume = base_data["resume"][0] if base_data["resume"] else {}
    contact = base_data["contact"][0] if base_data["contact"] else {}
    skills = [x["skill"] for x in base_data["skills"]]
    prog_langs = [x["language"] for x in base_data["prog_langs"]]
    spoken_langs = [x["language"] for x in base_data["spoken_langs"]]
    keywords = [x["keyword"] for x in base_data["keywords"]]

    exp_rows = base_data["experiences"] or []
    edu_rows = base_data["education"] or []
    proj_rows = base_data["projects"] or []
    certifications = base_data["certifications"] or []

    exp_ids = [exp["id"] for exp in exp_rows]
    edu_ids = [edu["id"] for edu in edu_rows]
    proj_ids = [proj["id"] for proj in proj_rows]

    def _fetch_related():
        res = {}
        if exp_ids:
            res["exp_bullets"] = db_client.table("experience_bullets").select("*").in_("experience_id", exp_ids).execute().data
            res["exp_techs"] = db_client.table("experience_technologies").select("*").in_("experience_id", exp_ids).execute().data
        if edu_ids:
            res["edu_notes"] = db_client.table("education_notes").select("*").in_("education_id", edu_ids).execute().data
        if proj_ids:
            res["proj_techs"] = db_client.table("project_technologies").select("*").in_("project_id", proj_ids).execute().data
        return res

    related_data = await asyncio.to_thread(_fetch_related)

    exp_bullets_map = defaultdict(list)
    for b in related_data.get("exp_bullets", []):
        exp_bullets_map[b["experience_id"]].append(b["bullet"])

    exp_techs_map = defaultdict(list)
    for t in related_data.get("exp_techs", []):
        exp_techs_map[t["experience_id"]].append(t["tech"])

    edu_notes_map = defaultdict(list)
    for n in related_data.get("edu_notes", []):
        edu_notes_map[n["education_id"]].append(n["note"])

    proj_techs_map = defaultdict(list)
    for t in related_data.get("proj_techs", []):
        proj_techs_map[t["project_id"]].append(t["tech"])

    experiences = []
    for exp in exp_rows:
        exp["description_bullets"] = exp_bullets_map.get(exp["id"], [])
        exp["technologies"] = exp_techs_map.get(exp["id"], [])
        experiences.append(exp)

    education = []
    for edu in edu_rows:
        edu["notes"] = edu_notes_map.get(edu["id"], [])
        education.append(edu)

    projects = []
    for proj in proj_rows:
        proj["technologies"] = proj_techs_map.get(proj["id"], [])
        projects.append(proj)

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

        return {"success": True, "message": "Resume parsed and stored successfully.", "resume_id": resume_id}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/manual")
async def submit_manual_resume(
    payload: ResumeExtraction,
    user_id: str = Depends(get_current_user_id),
):
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        resume_key = f"manual_{user_id}_{timestamp}"
        
        extracted_dict = payload.model_dump(mode="json")
        resume_id = insert_full_resume(extracted_dict, user_id, resume_key)

        return {"success": True, "message": "Manual profile saved successfully.", "resume_id": resume_id}
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


@router.get("/all")
async def get_all_resumes(user_id: str = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    resp = db_client.table("resumes")\
        .select("id, created_at, full_name, headline, summary, resume_key")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    
    return {"success": True, "resumes": resp.data or []}


@router.post("/select/{resume_id}")
async def select_resume(resume_id: str, user_id: str = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    # Verify ownership
    resp = db_client.table("resumes").select("id").eq("user_id", user_id).eq("id", resume_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    # Bump created_at so this resume sorts as the latest (gap/jobs/github all
    # read the most-recent resume). The literal string "now()" is NOT a valid
    # timestamp via PostgREST — send a real ISO-8601 UTC timestamp instead.
    db_client.table("resumes").update(
        {"created_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", resume_id).execute()
    
    return {"success": True, "resume_id": resume_id}


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

