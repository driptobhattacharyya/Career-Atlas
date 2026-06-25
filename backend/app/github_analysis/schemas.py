from pydantic import BaseModel
from typing import List, Optional

class GitHubOAuthCallback(BaseModel):
    code: str

class RepoSelection(BaseModel):
    repos: List[str]

class SkillAction(BaseModel):
    evidence_ids: List[str]

class GitHubRepoInfo(BaseModel):
    name: str
    owner: str
    url: str
    description: Optional[str] = None
    stargazerCount: int
    pushedAt: Optional[str] = None
    primaryLanguage: Optional[str] = None
    isOwner: bool

class GitHubReposResponse(BaseModel):
    success: bool
    repos: List[GitHubRepoInfo]

class AnalysisResponse(BaseModel):
    success: bool
    summary: str
    coding_behavior: str
    skills: List[str]
