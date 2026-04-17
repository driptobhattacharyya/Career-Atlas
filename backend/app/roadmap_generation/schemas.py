from pydantic import BaseModel, Field
from typing import List, Literal

class CourseSchema(BaseModel):
    title: str
    provider: str = Field(description="E.g., Coursera, Udemy, fast.ai")
    duration: str = Field(description="E.g., 20h, 5 weeks")
    url: str = Field(default="#")

class ProjectSuggestionSchema(BaseModel):
    title: str = Field(description="Name of the suggested practical project")
    description: str

class MilestoneSchema(BaseModel):
    phase: Literal["Foundations", "Intermediate", "Advanced"]
    title: str = Field(description="Title of the learning step")
    skill: str = Field(description="The underlying gap skill being learned")
    estimated_weeks: int
    description: str
    courses: List[CourseSchema]
    project: ProjectSuggestionSchema
    checklist: List[str] = Field(description="3-5 concrete action items")

class RoadmapGenerationResponse(BaseModel):
    milestones: List[MilestoneSchema] = Field(description="Ordered list of milestones matching the user's skill gaps")
