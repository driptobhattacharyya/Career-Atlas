import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Body
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import db_client
from app.config import settings
from app.github_analysis.schemas import GitHubOAuthCallback, RepoSelection, GitHubReposResponse
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

        # Save token to database
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

        # Save profile
        db_client.table("github_profiles").upsert({
            "user_id": user_id,
            "analysis_summary": profile["summary"],
            "coding_behavior": profile["coding_behavior"],
            "inferred_skills": profile["skills"]
        }, on_conflict="user_id").execute()

        # Save individual repos
        for repo_name, analysis in repo_analyses.items():
            db_client.table("github_repositories").upsert({
                "user_id": user_id,
                "repo_name": repo_name,
                "analysis_summary": analysis["summary"],
                "coding_behavior": analysis["coding_behavior"]
            }, on_conflict="user_id, repo_name").execute()

        # Append inferred skills to the user's latest resume skills list
        # We find the latest resume first
        resume_resp = db_client.table("resumes").select("id").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if resume_resp.data:
            resume_id = resume_resp.data[0]["id"]

            # Add skills (ignore conflicts if constraint exists, though we're inserting line by line)
            for skill in profile["skills"]:
                try:
                    existing = db_client.table("skills").select("skill").eq("resume_id", resume_id).eq("skill", skill).execute()
                    if not existing.data:
                        db_client.table("skills").insert({
                            "resume_id": resume_id,
                            "skill": skill,
                            "source": "github"
                        }).execute()
                except Exception as e:
                    logger.warning(f"Failed to add skill {skill}: {e}")

        return {
            "success": True,
            "summary": profile["summary"],
            "coding_behavior": profile["coding_behavior"],
            "skills": profile["skills"]
        }

    except Exception as e:
        logger.exception("Failed to analyze github repos")
        raise HTTPException(status_code=500, detail=f"Failed to analyze repositories: {e}")

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
