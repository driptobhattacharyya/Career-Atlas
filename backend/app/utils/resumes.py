"""Shared resume-lookup helpers.

Several routers need "the user's resumes, newest first" or just "the latest
one". These lookups are always strictly scoped to `user_id` — never a global
fallback, which would hand one user another user's resume.
"""
from app.dependencies.database import db_client


def user_resume_ids(user_id: str) -> list[str]:
    """All of the user's resume ids, newest first. Strictly scoped to user_id."""
    try:
        resp = (
            db_client.table("resumes")
            .select("id")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [r["id"] for r in (resp.data or []) if r.get("id")]
    except Exception:
        return []


def latest_resume_id(user_id: str) -> str | None:
    """The user's most recent resume id, or None if they have none."""
    ids = user_resume_ids(user_id)
    return ids[0] if ids else None
