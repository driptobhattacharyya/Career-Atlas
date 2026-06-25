import httpx
from typing import Dict, Any

_REST_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "CareerAtlas-App",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def fetch_authenticated_login(access_token: str) -> str:
    """The viewer's login — needed to filter commits to owner-authored only."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={**_REST_HEADERS, "Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 200:
            return resp.json().get("login", "")
    return ""


async def fetch_languages(owner: str, repo: str, access_token: str) -> Dict[str, float]:
    """GET /languages -> bytes per language, returned as rounded percentages."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/languages",
            headers={**_REST_HEADERS, "Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            return {}
        byte_counts = resp.json() or {}
        total = sum(byte_counts.values())
        if total == 0:
            return {}
        return {lang: round(b * 100 / total, 1) for lang, b in byte_counts.items()}


async def fetch_commit_stats(owner: str, repo: str, login: str, access_token: str) -> Dict[str, Any]:
    """Owner-authored commit count + first/last date. ponytail: caps at 100 commits
    (single page); bump to pagination if commit volume ever needs to be exact."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits",
            params={"author": login, "per_page": 100},
            headers={**_REST_HEADERS, "Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            return {"commit_count": 0, "first_commit_at": None, "last_commit_at": None}
        commits = resp.json() or []
        if not commits:
            return {"commit_count": 0, "first_commit_at": None, "last_commit_at": None}
        dates = [c.get("commit", {}).get("author", {}).get("date") for c in commits]
        dates = [d for d in dates if d]
        return {
            "commit_count": len(commits),  # 100 means "100+"
            "first_commit_at": min(dates) if dates else None,
            "last_commit_at": max(dates) if dates else None,
        }


async def fetch_github_graphql(query: str, variables: dict, access_token: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "CareerAtlas-App"
            }
        )
        if resp.status_code != 200:
            raise Exception(f"GitHub GraphQL API failed: {resp.text}")

        data = resp.json()
        if "errors" in data:
            raise Exception(f"GitHub GraphQL returned errors: {data['errors']}")

        return data["data"]

async def fetch_file_content(owner: str, repo: str, path: str, access_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3.raw",
                "User-Agent": "CareerAtlas-App"
            }
        )
        if resp.status_code == 200:
            return resp.text
        return ""

async def fetch_repo_file_tree(owner: str, repo: str, access_token: str) -> list[str]:
    async with httpx.AsyncClient() as client:
        # Get the default branch first
        repo_info_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CareerAtlas-App"
            }
        )
        if repo_info_resp.status_code != 200:
            return []

        default_branch = repo_info_resp.json().get("default_branch", "main")

        # Get tree
        tree_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CareerAtlas-App"
            }
        )
        if tree_resp.status_code != 200:
            return []

        tree_data = tree_resp.json()
        return [item["path"] for item in tree_data.get("tree", []) if item["type"] == "blob"]
