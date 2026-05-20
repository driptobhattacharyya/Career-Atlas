"""
Deep Researcher Agent — Pydantic schemas.

Ported from Notebooks/03_deep_researcher.ipynb (cells 5ca47aa0, 1cd195b9,
ddfa3614, ec317ddb). The Pathway tree (Pathway -> Milestone[] -> Resource[])
is emitted in a single structured-output call by the structurer node.
"""
from typing import List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field


# ── Output tree ──────────────────────────────────────────────────────────────

class Resource(BaseModel):
    title: str
    kind: str = Field(
        description="Resource type: course, doc, video, article, project, blog, tutorial, book"
    )
    provider: str = Field(description="e.g. Coursera, YouTube, official docs, fast.ai")
    url: str
    why: str = Field(description="1 sentence — why this resource for this milestone")


class Milestone(BaseModel):
    phase: Literal["Foundations", "Intermediate", "Advanced"]
    skill: str = Field(description="Gap skill being closed")
    estimated_weeks: int
    objective: str = Field(description="What the learner will be able to do after this milestone")
    resources: List[Resource] = Field(default_factory=list)
    checklist: List[str] = Field(description="3-5 concrete, checkable items")
    mini_project: Optional[str] = Field(None, description="Hands-on project suggestion")


class Pathway(BaseModel):
    target_role: str
    milestones: List[Milestone]
    rationale: str = Field(description="2-3 sentence reasoning on why the ordering works")


# ── Input gap shape (mirrors gap_analysis.schemas.GapSchema) ─────────────────

class GapIn(BaseModel):
    skill: str
    category: str
    relevance: int
    difficulty: str
    prerequisites: List[str] = Field(default_factory=list)
    why: str = ""
    level_required: str = "intermediate"


# ── Intermediate LLM outputs ─────────────────────────────────────────────────

class NextQuery(BaseModel):
    query: str = Field(description="The single best next search query — concise, 6-15 words")
    rationale: str = Field(description="Why this query, 1 sentence")


class CriticOut(BaseModel):
    decision: Literal["continue", "structure"]
    rationale: str


# ── Evaluation: LLM-as-judge ─────────────────────────────────────────────────

JudgeCriterion = Literal[
    "coverage",          # every gap addressed with a concrete milestone
    "ordering",          # milestones respect prerequisite logic
    "resource_quality",  # resources real, relevant, role-aligned
    "actionability",     # checklist + project concrete and doable
    "personalization",   # plan reflects the target role + user gaps
    "grounding",         # claims/links backed by the research notes
    "recency",           # resources current, not deprecated/expired
]


class JudgeScore(BaseModel):
    criterion: JudgeCriterion
    score: int = Field(ge=1, le=5)
    rationale: str = Field(description="One concise reason with evidence")


class JudgeVerdict(BaseModel):
    overall_score: float = Field(ge=1, le=5)
    pass_fail: Literal["pass", "fail"]
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_actions: List[str] = Field(
        default_factory=list,
        description="Concrete fixes the structurer should apply on a retry",
    )
    rubric_scores: List[JudgeScore] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


# ── Validation: link grounding + liveness ────────────────────────────────────

class DroppedResource(BaseModel):
    milestone_skill: str
    title: str
    url: str
    reason: Literal["ungrounded", "dead_link"]


class ValidationResult(BaseModel):
    checked: int = 0
    kept: int = 0
    dropped: List[DroppedResource] = Field(default_factory=list)


# ── LangGraph state ──────────────────────────────────────────────────────────

class ResearcherState(TypedDict, total=False):
    gaps: List[GapIn]
    target_role: str
    notes: List[str]
    last_query: str
    iteration: int
    max_iter: int
    pathway: Pathway
    # Evaluation / validation
    valid_urls: List[str]          # URLs actually seen in the research notes
    validation: dict               # ValidationResult dump
    judge_verdict: dict            # JudgeVerdict dump
    retry_count: int               # structure re-runs triggered by the judge
    max_retry: int


# ── API request / response ───────────────────────────────────────────────────

class DeepResearchRequest(BaseModel):
    target_role_id: str
    max_iter: int = 3


class DeepResearchResponse(BaseModel):
    success: bool
    target_role: str
    role_slug: str
    pathway: Pathway
    iterations_used: int
    sources: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = None
    quality_passed: Optional[bool] = None
    verdict: Optional[JudgeVerdict] = None
    validation: Optional[ValidationResult] = None
