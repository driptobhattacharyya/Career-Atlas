from pydantic import BaseModel, Field
from typing import List

class GapSchema(BaseModel):
    skill: str = Field(description="Name of the missing skill (e.g. Docker, PyTorch)")
    category: str = Field(description="Category of the skill (e.g. Cloud & DevOps, Languages)")
    relevance: int = Field(description="Relevance percentage to the target role (0-100)")
    difficulty: str = Field(description="One of: Easy, Medium, Hard")
    prerequisites: List[str] = Field(description="List of skills required to learn this")
    why: str = Field(description="1 sentence explaining why this skill is a crucial gap")

class GapAnalysisResponse(BaseModel):
    gaps: List[GapSchema] = Field(description="Top 6 skill gaps for the user")
