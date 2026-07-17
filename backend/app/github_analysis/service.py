import logging
import asyncio
from typing import List, Dict, Any
from app.github_analysis.schemas import GitHubRepoInfo
from app.github_analysis.github_api import (
    fetch_github_graphql,
    fetch_file_content,
    fetch_repo_file_tree,
    fetch_languages,
    fetch_commit_stats,
    fetch_authenticated_login,
)
from app.utils.llm_factory import build_groq_structured_chain
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Models ---
class SkillEvidence(BaseModel):
    skill: str = Field(description="The skill/technology name (e.g. Python, Docker, React).")
    evidence: str = Field(description="A direct quote of a file path from the tree OR a language from the language breakdown that proves this skill. Do not invent evidence.")
    confidence: str = Field(description="low, medium, or high — how strongly the evidence supports the skill.")

class RepoAnalysisResult(BaseModel):
    summary: str = Field(description="A brief summary of what the repository does.")
    coding_behavior: str = Field(description="An analysis of the user's coding behavior in this repo (e.g. hardcoded values, architecture patterns, code quality).")
    inferred_skills: List[SkillEvidence] = Field(description="Skills inferred from the codebase, each bound to concrete evidence.")

class ProfileAnalysisResult(BaseModel):
    overall_summary: str = Field(description="An overall summary of the user's GitHub profile based on all repositories.")
    overall_coding_behavior: str = Field(description="An overall assessment of their coding behavior, highlighting strengths and weaknesses.")

# --- Prompts ---
REPO_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """You are an expert Senior Software Engineer reviewing a candidate's repository.

    Repository Name: {repo_name}
    Description: {description}
    Primary Language: {language}

    Language breakdown (by bytes, authoritative): {languages}
    Commit activity (owner-authored): {commit_context}

    Here is a manifest-first selection of the file tree and contents of key files:
    {file_contents}

    Based ONLY on the information above, perform an in-depth analysis.
    1. Summarize what the repository is about.
    2. Analyze the coding behavior. Look for:
       - Code organization and architecture patterns.
       - Presence of hardcoded values or lack of configuration management.
       - Best practices (or lack thereof) like error handling, documentation, modularity.
    3. Infer technical skills. For EACH skill you MUST cite evidence: quote an exact
       file path shown above (e.g. "requirements.txt", "src/app.py") or a language
       from the language breakdown. Never list a skill you cannot tie to the evidence
       above. Set confidence honestly (high only when a manifest or language stat
       directly proves it).

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
            isFork
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
        if repo.get("isFork"):
            continue  # CATRK-11: forks inflate signal with code the user didn't write
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

# CATRK-12: authoritative files first. Manifests list real dependencies with zero
# guessing; README + entrypoints give intent. Only then fill with source.
MANIFEST_FILES = {
    "package.json", "requirements.txt", "pyproject.toml", "go.mod", "pom.xml",
    "cargo.toml", "build.gradle", "composer.json", "gemfile", "pubspec.yaml",
    "dockerfile", "docker-compose.yml", "setup.py", "pipfile",
}
ENTRYPOINT_FILES = {"main.py", "app.py", "index.js", "index.ts", "server.ts", "server.js", "main.go", "main.rs"}
SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".h", ".cs"}
_SKIP_DIRS = {"node_modules", "venv", ".git", "dist", "build", ".venv"}


def select_files(file_tree: List[str], cap: int = 12) -> List[str]:
    """Manifest-first ordering: manifests, then README, then entrypoints, then
    shallow non-test source — deduped, capped."""
    def name(p): return p.lower().split("/")[-1]
    def skipped(p): return any(d in p.lower().split("/") for d in _SKIP_DIRS)

    tree = [f for f in file_tree if not skipped(f)]
    manifests = [f for f in tree if name(f) in MANIFEST_FILES]
    readmes = [f for f in tree if name(f).startswith("readme")]
    entrypoints = [f for f in tree if name(f) in ENTRYPOINT_FILES]
    source = [
        f for f in tree
        if any(name(f).endswith(ext) for ext in SOURCE_EXTENSIONS)
        and len(f.split("/")) <= 3
        and "test" not in name(f) and "spec" not in name(f)
    ]

    ordered, seen = [], set()
    for bucket in (manifests, readmes, entrypoints, source):
        for f in bucket:
            if f not in seen:
                seen.add(f)
                ordered.append(f)
    return ordered[:cap]


def _filter_evidence(skills: List[SkillEvidence], fetched_paths: List[str], languages: Dict[str, float]) -> List[SkillEvidence]:
    """CATRK-13: any skill whose evidence doesn't quote a fetched path or a real
    language gets its confidence capped to low — overconfident guesses can't survive."""
    path_blob = " ".join(fetched_paths).lower()
    lang_names = {lang.lower() for lang in languages}
    out = []
    for s in skills:
        ev = (s.evidence or "").lower()
        backed = any(p and p in ev for p in path_blob.split()) or any(lang in ev or lang in s.skill.lower() for lang in lang_names)
        out.append(s if backed else SkillEvidence(skill=s.skill, evidence=s.evidence, confidence="low"))
    return out


def _commit_context(stats: Dict[str, Any]) -> str:
    n = stats.get("commit_count", 0)
    if not n:
        return "no owner-authored commits found"
    span = ""
    if stats.get("first_commit_at") and stats.get("last_commit_at"):
        span = f" between {stats['first_commit_at'][:10]} and {stats['last_commit_at'][:10]}"
    return f"{n}{'+' if n >= 100 else ''} owner-authored commits{span}"


async def analyze_repository(repo: GitHubRepoInfo, login: str, access_token: str) -> Dict[str, Any]:
    short_name = repo.name.split("/")[-1]

    file_tree, languages, commit_stats = await asyncio.gather(
        fetch_repo_file_tree(repo.owner, short_name, access_token),
        fetch_languages(repo.owner, short_name, access_token),
        fetch_commit_stats(repo.owner, short_name, login, access_token),
    )

    selected_files = select_files(file_tree)

    file_contents = "--- FILE TREE (Partial) ---\n"
    file_contents += "\n".join(file_tree[:50]) + ("\n...(truncated)\n" if len(file_tree) > 50 else "\n")

    for file_path in selected_files:
        content = await fetch_file_content(repo.owner, short_name, file_path, access_token)
        if content:
            if len(content) > 5000:
                content = content[:5000] + "\n...(truncated)"
            file_contents += f"\n\n--- FILE: {file_path} ---\n{content}\n"

    lang_str = ", ".join(f"{lang} {p}%" for lang, p in sorted(languages.items(), key=lambda x: -x[1])) or "unknown"

    chain = build_groq_structured_chain(REPO_ANALYSIS_PROMPT, RepoAnalysisResult, temperature=0.1)

    base = {
        "summary": "Analysis failed",
        "coding_behavior": "Analysis failed",
        "inferred_skills": [],
        "languages": languages,
        **commit_stats,
    }
    try:
        result: RepoAnalysisResult = await chain.ainvoke({
            "repo_name": repo.name,
            "description": repo.description or "No description",
            "language": repo.primaryLanguage or "Unknown",
            "languages": lang_str,
            "commit_context": _commit_context(commit_stats),
            "file_contents": file_contents,
        })
        skills = _filter_evidence(result.inferred_skills, selected_files, languages)
        return {**base, "summary": result.summary, "coding_behavior": result.coding_behavior, "inferred_skills": skills}
    except Exception as e:
        logger.error(f"Failed to analyze repo {repo.name}: {e}")
        return base

async def analyze_selected_repositories(user_id: str, repos: List[str], access_token: str) -> Dict[str, Any]:
    login = await fetch_authenticated_login(access_token)
    all_repos = await fetch_top_repositories(access_token)
    selected_repos_info = [r for r in all_repos if r.name in repos]

    if not selected_repos_info:
        raise ValueError("No matching repositories found")

    analyses = await asyncio.gather(*[
        analyze_repository(repo, login, access_token) for repo in selected_repos_info
    ])

    # Format for overall analysis
    repo_analyses_text = ""
    for repo, analysis in zip(selected_repos_info, analyses):
        skill_names = ", ".join(s.skill for s in analysis["inferred_skills"])
        repo_analyses_text += f"\n\n### Repository: {repo.name}\n"
        repo_analyses_text += f"Summary: {analysis['summary']}\n"
        repo_analyses_text += f"Coding Behavior: {analysis['coding_behavior']}\n"
        repo_analyses_text += f"Skills: {skill_names}\n"

    chain = build_groq_structured_chain(PROFILE_ANALYSIS_PROMPT, ProfileAnalysisResult, temperature=0.1)

    overall_result: ProfileAnalysisResult = await chain.ainvoke({
        "repo_analyses": repo_analyses_text
    })

    # Deduplicated skill-name list (display only — the source of truth is per-repo evidence).
    display_skills = sorted({s.skill for a in analyses for s in a["inferred_skills"]})

    return {
        "repo_analyses": {r.name: a for r, a in zip(selected_repos_info, analyses)},
        "profile": {
            "summary": overall_result.overall_summary,
            "coding_behavior": overall_result.overall_coding_behavior,
            "skills": display_skills,
        },
    }
