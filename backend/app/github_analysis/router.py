import logging
import httpx
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.config import settings
from app.github_analysis.schemas import GitHubOAuthCallback, RepoSelection, GitHubReposResponse, SkillAction
from app.github_analysis.service import fetch_top_repositories, analyze_selected_repositories

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github", tags=["GitHub Analysis"])

@router.post("/oauth/callback")
async def github_oauth_callback(
    req: GitHubOAuthCallback,
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=500, detail="GitHub OAuth is not configured on the server")

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": req.code,
            },
            headers={"Accept": "application/json"}
        )

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")

        token_data = token_resp.json()
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth error"))

        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")

        # Get GitHub user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )

        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user info")

        github_user = user_resp.json()
        github_user_id = str(github_user.get("id"))
        github_username = github_user.get("login")

        # Save token to database.
        # CATRK-7 token storage review: token is never returned by any endpoint
        # (status->username, /profile->no token) nor logged (errors carry response
        # bodies, token lives only in request headers). RLS + service-key-only access
        # + Supabase at-rest disk encryption is the baseline. App-layer column
        # encryption (pgcrypto/Vault) deferred — defense-in-depth, not a missing
        # control; add if tokens ever need to survive a DB-read compromise.
        db_client.table("github_tokens").upsert({
            "user_id": user_id,
            "access_token": access_token,
            "github_user_id": github_user_id,
            "github_username": github_username
        }, on_conflict="user_id").execute()

        return {"success": True, "github_username": github_username}

@router.get("/repos", response_model=GitHubReposResponse)
async def get_github_repos(user_id: str = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token_resp = db_client.table("github_tokens").select("access_token").eq("user_id", user_id).execute()
        if not token_resp.data:
            raise HTTPException(status_code=400, detail="GitHub not connected")

        access_token = token_resp.data[0]["access_token"]
        repos = await fetch_top_repositories(access_token)

        return {"success": True, "repos": repos}
    except Exception as e:
        logger.exception("Failed to fetch github repos")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {e}")

@router.post("/analyze", response_model=dict)
async def analyze_github_repos(
    req: RepoSelection,
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token_resp = db_client.table("github_tokens").select("access_token").eq("user_id", user_id).execute()
        if not token_resp.data:
            raise HTTPException(status_code=400, detail="GitHub not connected")

        access_token = token_resp.data[0]["access_token"]

        # Analyze selected repos
        analysis_data = await analyze_selected_repositories(user_id, req.repos, access_token)

        profile = analysis_data["profile"]
        repo_analyses = analysis_data["repo_analyses"]

        # Save profile (display summary + flat skill-name list for the headline).
        db_client.table("github_profiles").upsert({
            "user_id": user_id,
            "analysis_summary": profile["summary"],
            "coding_behavior": profile["coding_behavior"],
            "inferred_skills": profile["skills"]
        }, on_conflict="user_id").execute()

        # Save per-repo structured facts (languages%, commit activity) for the panel.
        for repo_name, analysis in repo_analyses.items():
            db_client.table("github_repositories").upsert({
                "user_id": user_id,
                "repo_name": repo_name,
                "analysis_summary": analysis["summary"],
                "coding_behavior": analysis["coding_behavior"],
                "languages": analysis.get("languages"),
                "commit_count": analysis.get("commit_count"),
                "first_commit_at": analysis.get("first_commit_at"),
                "last_commit_at": analysis.get("last_commit_at"),
            }, on_conflict="user_id, repo_name").execute()

        # CATRK-10 + UX-3: inferred skills land in github_skill_evidence.
        # HIGH-confidence (manifest/language-backed) auto-confirm so the user
        # isn't ticking 15 boxes; medium/low stay quarantined for explicit review
        # — the human gate stays where misrepresentation risk is real. Nothing
        # touches the resume `skills` table.
        # ignore_duplicates: never clobber a prior user confirm/reject decision on
        # re-analyze. ponytail: full re-sync (re-score changed repos) is a later task.
        for repo_name, analysis in repo_analyses.items():
            for ev in analysis["inferred_skills"]:
                try:
                    db_client.table("github_skill_evidence").upsert({
                        "user_id": user_id,
                        "skill": ev.skill,
                        "evidence": ev.evidence,
                        "confidence": ev.confidence,
                        "source_repo": repo_name,
                        "confirmed": ev.confidence == "high",
                    }, on_conflict="user_id, skill, source_repo", ignore_duplicates=True).execute()
                except Exception as e:
                    logger.warning(f"Failed to store evidence for {ev.skill}: {e}")

        return {
            "success": True,
            "summary": profile["summary"],
            "coding_behavior": profile["coding_behavior"],
            "skills": profile["skills"],
        }

    except Exception as e:
        logger.exception("Failed to analyze github repos")
        raise HTTPException(status_code=500, detail=f"Failed to analyze repositories: {e}")

@router.get("/profile")
async def get_github_insights(user_id: str = Depends(get_current_user_id)):
    """Powers the insights panel: stored profile + per-repo facts + quarantined
    skill suggestions (with evidence/confidence/confirmed)."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # ⚡ Bolt Optimization: Fix N+1 query performance bottleneck
    # What: Replaced sequential, synchronous Supabase queries with concurrent batch fetching via asyncio.to_thread.
    # Why: The Supabase Python client is synchronous and blocks the FastAPI event loop. Doing these sequentially was adding significant latency.
    profile_resp, repos_resp, evidence_resp = await asyncio.gather(
        asyncio.to_thread(lambda: db_client.table("github_profiles").select("*").eq("user_id", user_id).execute()),
        asyncio.to_thread(lambda: db_client.table("github_repositories").select("*").eq("user_id", user_id).execute()),
        asyncio.to_thread(lambda: db_client.table("github_skill_evidence").select("*").eq("user_id", user_id).order("confidence", desc=True).execute())
    )

    return {
        "success": True,
        "profile": profile_resp.data[0] if profile_resp.data else None,
        "repositories": repos_resp.data or [],
        "skill_evidence": evidence_resp.data or [],
    }


@router.post("/skills/confirm")
async def confirm_github_skills(req: SkillAction, user_id: str = Depends(get_current_user_id)):
    """Promote suggested skills into the verified profile (confirmed=true). Gap
    analysis only counts confirmed GitHub skills."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not req.evidence_ids:
        return {"success": True, "updated": 0}

    resp = db_client.table("github_skill_evidence").update({"confirmed": True})\
        .eq("user_id", user_id).in_("id", req.evidence_ids).execute()
    return {"success": True, "updated": len(resp.data or [])}


@router.post("/skills/reject")
async def reject_github_skills(req: SkillAction, user_id: str = Depends(get_current_user_id)):
    """Discard suggested skills. ponytail: reject = delete the row; re-analyze
    re-suggests it if the evidence is still there."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not req.evidence_ids:
        return {"success": True, "deleted": 0}

    resp = db_client.table("github_skill_evidence").delete()\
        .eq("user_id", user_id).in_("id", req.evidence_ids).execute()
    return {"success": True, "deleted": len(resp.data or [])}


@router.get("/status")
async def get_github_status(user_id: str = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        resp = db_client.table("github_tokens").select("github_username").eq("user_id", user_id).execute()
        if resp.data:
            return {"success": True, "connected": True, "github_username": resp.data[0]["github_username"]}
        return {"success": True, "connected": False}
    except Exception as e:
        logger.error(f"Failed to get github status: {e}")
        return {"success": True, "connected": False}
