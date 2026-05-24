from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

MilestoneStatus = Literal["locked", "in_progress", "completed", "skipped"]


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
    milestones: List[MilestoneSchema] = Field(
        description="Ordered list of milestones matching the user's skill gaps"
    )


class MilestoneStatusUpdate(BaseModel):
    status: MilestoneStatus


class MilestoneRowOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    target_role: Optional[str] = None
    target_role_id: Optional[str] = None
    resume_id: Optional[str] = None
    phase: Optional[str] = None
    title: Optional[str] = None
    skill: Optional[str] = None
    status: MilestoneStatus
    estimated_weeks: Optional[int] = None
    description: Optional[str] = None
    courses: List[dict] = Field(default_factory=list)
    project: dict = Field(default_factory=dict)
    checklist: List[str] = Field(default_factory=list)
    sort_order: int = 0
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
