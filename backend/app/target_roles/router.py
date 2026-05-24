"""
Target Roles — read-only catalog API.

Backend endpoint so the frontend can stop reading the table directly,
and so RLS / column changes stay invisible to the UI layer.
"""
from fastapi import APIRouter, HTTPException

from app.dependencies.database import db_client

router = APIRouter(prefix="/api/target-roles", tags=["TargetRoles"])


@router.get("/")
def list_target_roles():
    try:
        resp = (
            db_client.table("target_roles")
            .select("id,title,category,blurb,emoji,popular_skills")
            .order("title")
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"target_roles fetch failed: {e}")
    return {"success": True, "roles": resp.data or []}
