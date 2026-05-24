from typing import List, Optional

from pydantic import BaseModel, Field


class JobMatchSchema(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    remote: Optional[bool] = None
    seniority: Optional[str] = Field(
        default=None, description="Intern, Entry, Junior, Mid, Senior"
    )
    match_pct: int = Field(description="Calculated match percentage (0-100)")
    matched: List[str] = Field(description="Keywords matched with user skills")
    missing: List[str] = Field(description="Required keywords missing from user skills")
    salary: Optional[str] = None
    posted_days: Optional[str] = Field(
        default=None,
        description="How long ago posted as free text, e.g. '3 days', '2 weeks', or null if unknown",
    )
    description: str
    external_url: str


class ScrapedJobsResponse(BaseModel):
    jobs: List[JobMatchSchema]


class ScoreBreakdown(BaseModel):
    semantic: float
    skill_overlap: float
    experience: float
    education: float
    final: float


class JobExplanation(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    reasoning: str = ""


class JobResult(BaseModel):
    job_id: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    apply_url: Optional[str] = None

    score: ScoreBreakdown
    explanation: JobExplanation

    # Transitional compatibility fields for the existing UI and persisted rows.
    remote: Optional[bool] = None
    seniority: Optional[str] = None
    match_pct: Optional[int] = None
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    salary: Optional[str] = None
    posted_days: Optional[int] = None
    description: Optional[str] = None
    external_url: Optional[str] = None


class JobSearchResponse(BaseModel):
    query_role: str
    user_location_preference: str
    total_jobs_fetched: int
    jobs: List[JobResult]
