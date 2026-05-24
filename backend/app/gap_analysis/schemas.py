"""
Pydantic schemas for the Gap Analysis Agent.

GapSchema — single skill gap with ranking metadata.
GapAnalysisResponse — LLM structured output (top 6 gaps).
GapAnalysisResult — full API response including retrieval context.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union


class GapSchema(BaseModel):
    """A single identified skill gap."""
    skill: str = Field(
        description="Name of the missing skill (e.g. Docker, PyTorch)"
    )
    category: str = Field(
        description="Category: framework | language | concept | tool | soft"
    )
    # int | str so Groq's strict tool-schema validation accepts a quoted
    # number ("10") from the LLM; the validator coerces it back to int.
    relevance: Union[int, str] = Field(
        description="Relevance percentage to the target role (0-100)"
    )
    difficulty: str = Field(
        description="One of: Easy, Medium, Hard"
    )

    @field_validator("relevance", mode="before")
    @classmethod
    def _coerce_relevance(cls, v):
        # 1. Handle numeric types
        if isinstance(v, (int, float)):
            if 0.0 <= v <= 1.0:
                return int(v * 100)
            return int(v)
            
        # 2. Handle string types
        if isinstance(v, str):
            try:
                # Try parsing as float first (e.g. "0.210" -> 0.21)
                val = float(v)
                if 0.0 <= val <= 1.0:
                    return int(val * 100)
                return int(val)
            except ValueError:
                # Fallback to digit extraction
                digits = "".join(c for c in v if c.isdigit())
                return int(digits) if digits else 0
        return v
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
    justifications: dict[str, str] = Field(
        description="A dictionary mapping each identified skill name to a 1-2 sentence justification of why it is important for the candidate."
    )


class AnalyzeGapsRequest(BaseModel):
    target_role_title: str
    force: Optional[bool] = False


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
