import httpx
from typing import Dict, Any

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
