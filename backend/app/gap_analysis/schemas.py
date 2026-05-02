"""
Pydantic schemas for the Gap Analysis Agent.

GapSchema — single skill gap with ranking metadata.
GapAnalysisResponse — LLM structured output (top 6 gaps).
GapAnalysisResult — full API response including retrieval context.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class GapSchema(BaseModel):
    """A single identified skill gap."""
    skill: str = Field(
        description="Name of the missing skill (e.g. Docker, PyTorch)"
    )
    category: str = Field(
        description="Category: framework | language | concept | tool | soft"
    )
    relevance: int = Field(
        description="Relevance percentage to the target role (0-100)"
    )
    difficulty: str = Field(
        description="One of: Easy, Medium, Hard"
    )
    level_required: str = Field(
        default="intermediate",
        description="Required proficiency: beginner | intermediate | advanced"
    )
    prerequisites: List[str] = Field(
        description="List of skills required to learn this"
    )
    why: str = Field(
        description="1 sentence explaining why this skill is a crucial gap"
    )


class GapAnalysisResponse(BaseModel):
    """LLM structured output schema."""
    gaps: List[GapSchema] = Field(
        description="Top 6 skill gaps for the user, ranked by importance"
    )


class AnalyzeGapsRequest(BaseModel):
    target_role_title: str


class GapAnalysisResult(BaseModel):
    """Full API response returned to the frontend."""
    success: bool
    target_role: str
    role_slug: str
    gaps: List[dict]
    retrieval_source: str = Field(
        default="hybrid",
        description="How gaps were retrieved: hybrid | semantic_only | fallback"
    )
