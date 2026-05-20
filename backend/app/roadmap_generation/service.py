"""
Roadmap Generation — milestone persistence.

The deep researcher is the single content engine; this module only owns the
status-preserving persistence of milestones into the `milestones` table so the
roadmap page can track progress.
"""
from typing import List

from app.dependencies.database import db_client


def upsert_role_milestones(
    user_id: str,
    role_id: str,
    role_title: str,
    resume_id: str | None,
    milestones: List[dict],
) -> List[dict]:
    """Upsert milestones for (user, role), preserving prior progress.

    Each `milestones` dict: phase, title, skill, estimated_weeks, description,
    courses(list), project(dict), checklist(list).

    Identical (user, role, skill) rows keep their existing status +
    completed_at; new skills are inserted (first = in_progress, rest locked);
    skills absent from the new set are deleted (scoped to this role).
    """
    existing_resp = (
        db_client.table("milestones")
        .select("id,skill,status,completed_at")
        .eq("user_id", user_id)
        .eq("target_role_id", role_id)
        .execute()
    )
    prior_by_skill = {
        (row.get("skill") or "").strip().lower(): row
        for row in (existing_resp.data or [])
        if row.get("skill")
    }

    seen_skills: set[str] = set()
    rows_to_upsert: List[dict] = []
    for idx, ms in enumerate(milestones):
        key = (ms.get("skill") or "").strip().lower()
        seen_skills.add(key)
        prior = prior_by_skill.get(key)

        if prior:
            status = prior.get("status") or "locked"
            completed_at = prior.get("completed_at")
        else:
            status = "in_progress" if idx == 0 else "locked"
            completed_at = None

        row = {
            "user_id": user_id,
            "target_role": role_title,
            "target_role_id": role_id,
            "resume_id": resume_id,
            "phase": ms.get("phase"),
            "title": ms.get("title"),
            "skill": ms.get("skill"),
            "status": status,
            "estimated_weeks": ms.get("estimated_weeks"),
            "description": ms.get("description"),
            "courses": ms.get("courses") or [],
            "project": ms.get("project") or {},
            "checklist": ms.get("checklist") or [],
            "sort_order": idx,
            "completed_at": completed_at,
        }
        if prior and prior.get("id"):
            row["id"] = prior["id"]
        rows_to_upsert.append(row)

    # Stale = same (user, role) but skill not in the new set. Scoped delete.
    stale_ids = [
        row["id"]
        for skill_key, row in prior_by_skill.items()
        if skill_key not in seen_skills and row.get("id")
    ]
    if stale_ids:
        db_client.table("milestones").delete().in_("id", stale_ids).execute()

    if rows_to_upsert:
        upsert_resp = (
            db_client.table("milestones")
            .upsert(rows_to_upsert, on_conflict="id")
            .execute()
        )
        return upsert_resp.data or []
    return []
