import logging
import asyncio
from typing import List, Dict, Any
from app.github_analysis.schemas import GitHubRepoInfo
from app.github_analysis.github_api import fetch_github_graphql, fetch_file_content, fetch_repo_file_tree
from app.utils.llm_factory import get_groq_model
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Models ---
class RepoAnalysisResult(BaseModel):
    summary: str = Field(description="A brief summary of what the repository does.")
    coding_behavior: str = Field(description="An analysis of the user's coding behavior in this repo (e.g. hardcoded values, architecture patterns, code quality).")
    inferred_skills: List[str] = Field(description="A list of skills/technologies inferred from the codebase.")

class ProfileAnalysisResult(BaseModel):
    overall_summary: str = Field(description="An overall summary of the user's GitHub profile based on all repositories.")
    overall_coding_behavior: str = Field(description="An overall assessment of their coding behavior, highlighting strengths and weaknesses.")
    all_inferred_skills: List[str] = Field(description="A deduplicated list of all skills inferred.")

# --- Prompts ---
REPO_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """You are an expert Senior Software Engineer reviewing a candidate's repository.

    Repository Name: {repo_name}
    Description: {description}
    Language: {language}

    Here is a selection of the file tree and contents of key files from the repository:
    {file_contents}

    Based on this information, perform an in-depth analysis.
    1. Summarize what the repository is about.
    2. Analyze the coding behavior. Look for:
       - Code organization and architecture patterns.
       - Presence of hardcoded values or lack of configuration management.
       - Best practices (or lack thereof) like error handling, documentation, modularity.
    3. Infer technical skills, frameworks, and tools used.

    Be objective and highlight both strengths and weaknesses.
    """
)

PROFILE_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """You are an expert Senior Software Engineer evaluating a candidate's overall GitHub profile.

    Here are the individual analyses of their repositories:
    {repo_analyses}

    Provide an aggregated overview:
    1. A single cohesive summary of their overall technical profile.
    2. A comprehensive analysis of their coding behavior across all projects.
    3. A merged, deduplicated list of all their technical skills.
    """
)

async def fetch_top_repositories(access_token: str) -> List[GitHubRepoInfo]:
    query = """
    query {
      viewer {
        login
        repositories(first: 10, orderBy: {field: PUSHED_AT, direction: DESC}, isFork: false) {
          nodes {
            name
            nameWithOwner
            url
            description
            stargazerCount
            pushedAt
            primaryLanguage {
              name
            }
            owner {
              login
            }
          }
        }
        repositoriesContributedTo(first: 5, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            nameWithOwner
            url
            description
            stargazerCount
            pushedAt
            primaryLanguage {
              name
            }
            owner {
              login
            }
          }
        }
      }
    }
    """

    data = await fetch_github_graphql(query, {}, access_token)

    repos_map = {}

    owned_repos = data.get("viewer", {}).get("repositories", {}).get("nodes", []) or []
    for repo in owned_repos:
        full_name = repo.get("nameWithOwner")
        if full_name and full_name not in repos_map:
            repos_map[full_name] = GitHubRepoInfo(
                name=full_name,
                owner=repo.get("owner", {}).get("login", ""),
                url=repo.get("url", ""),
                description=repo.get("description"),
                stargazerCount=repo.get("stargazerCount", 0),
                pushedAt=repo.get("pushedAt"),
                primaryLanguage=repo.get("primaryLanguage", {}).get("name") if repo.get("primaryLanguage") else None,
                isOwner=True
            )

    contributed_repos = data.get("viewer", {}).get("repositoriesContributedTo", {}).get("nodes", []) or []
    for repo in contributed_repos:
        full_name = repo.get("nameWithOwner")
        if full_name and full_name not in repos_map:
            repos_map[full_name] = GitHubRepoInfo(
                name=full_name,
                owner=repo.get("owner", {}).get("login", ""),
                url=repo.get("url", ""),
                description=repo.get("description"),
                stargazerCount=repo.get("stargazerCount", 0),
                pushedAt=repo.get("pushedAt"),
                primaryLanguage=repo.get("primaryLanguage", {}).get("name") if repo.get("primaryLanguage") else None,
                isOwner=False
            )

    return list(repos_map.values())[:10]

def is_high_value_file(path: str) -> bool:
    high_value_names = {"readme.md", "package.json", "requirements.txt", "pom.xml", "dockerfile", "docker-compose.yml"}
    high_value_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".h", ".cs"}

    lower_path = path.lower()
    file_name = lower_path.split("/")[-1]

    if file_name in high_value_names:
        return True

    if any(lower_path.endswith(ext) for ext in high_value_extensions):
        # Filter out deeply nested files or test files to save context
        parts = lower_path.split("/")
        if "node_modules" in parts or "venv" in parts or ".git" in parts or "dist" in parts or "build" in parts:
            return False
        # Limit depth to top level or one/two folders deep, and ignore tests
        if len(parts) <= 3 and "test" not in file_name and "spec" not in file_name:
            return True

    return False

async def analyze_repository(repo: GitHubRepoInfo, access_token: str) -> Dict[str, Any]:
    file_tree = await fetch_repo_file_tree(repo.owner, repo.name.split("/")[-1], access_token)

    high_value_files = [f for f in file_tree if is_high_value_file(f)][:10] # Cap at 10 files

    file_contents = ""
    file_contents += f"--- FILE TREE (Partial) ---\n"
    file_contents += "\n".join(file_tree[:50]) + ("\n...(truncated)\n" if len(file_tree) > 50 else "\n")

    for file_path in high_value_files:
        content = await fetch_file_content(repo.owner, repo.name.split("/")[-1], file_path, access_token)
        if content:
            # truncate content if too large
            if len(content) > 5000:
                content = content[:5000] + "\n...(truncated)"
            file_contents += f"\n\n--- FILE: {file_path} ---\n{content}\n"

    model = get_groq_model(temperature=0.1)
    structured_llm = model.with_structured_output(RepoAnalysisResult)

    chain = REPO_ANALYSIS_PROMPT | structured_llm

    try:
        result: RepoAnalysisResult = await chain.ainvoke({
            "repo_name": repo.name,
            "description": repo.description or "No description",
            "language": repo.primaryLanguage or "Unknown",
            "file_contents": file_contents
        })
        return {
            "summary": result.summary,
            "coding_behavior": result.coding_behavior,
            "inferred_skills": result.inferred_skills
        }
    except Exception as e:
        logger.error(f"Failed to analyze repo {repo.name}: {e}")
        return {
            "summary": "Analysis failed",
            "coding_behavior": "Analysis failed",
            "inferred_skills": []
        }

async def analyze_selected_repositories(user_id: str, repos: List[str], access_token: str) -> Dict[str, Any]:
    all_repos = await fetch_top_repositories(access_token)
    selected_repos_info = [r for r in all_repos if r.name in repos]

    if not selected_repos_info:
        raise ValueError("No matching repositories found")

    tasks = []
    for repo in selected_repos_info:
        tasks.append(analyze_repository(repo, access_token))

    analyses = await asyncio.gather(*tasks)

    # Format for overall analysis
    repo_analyses_text = ""
    for repo, analysis in zip(selected_repos_info, analyses):
        repo_analyses_text += f"\n\n### Repository: {repo.name}\n"
        repo_analyses_text += f"Summary: {analysis['summary']}\n"
        repo_analyses_text += f"Coding Behavior: {analysis['coding_behavior']}\n"
        repo_analyses_text += f"Skills: {', '.join(analysis['inferred_skills'])}\n"

    model = get_groq_model(temperature=0.1)
    structured_llm = model.with_structured_output(ProfileAnalysisResult)
    chain = PROFILE_ANALYSIS_PROMPT | structured_llm

    overall_result: ProfileAnalysisResult = await chain.ainvoke({
        "repo_analyses": repo_analyses_text
    })

    return {
        "repo_analyses": {r.name: a for r, a in zip(selected_repos_info, analyses)},
        "profile": {
            "summary": overall_result.overall_summary,
            "coding_behavior": overall_result.overall_coding_behavior,
            "skills": overall_result.all_inferred_skills
        }
    }
