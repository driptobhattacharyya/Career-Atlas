from pydantic import BaseModel, Field
from typing import List, Optional

class SkillSchema(BaseModel):
    name: str = Field(description="Name of the skill, e.g., Python, AWS, React.")
    category: str = Field(description="One of: Languages, Frameworks, Data, Cloud & DevOps, Tools, Soft Skills")
    level: str = Field(description="One of: beginner, intermediate, advanced")
    evidence: Optional[str] = Field(None, description="Brief 1-sentence proof of skill found in the resume")

class ExperienceSchema(BaseModel):
    role: str
    company: str
    start_date: Optional[str]
    end_date: Optional[str]
    bullets: List[str]

class EducationSchema(BaseModel):
    school: str
    degree: str
    start_date: Optional[str]
    end_date: Optional[str]

class ProjectSchema(BaseModel):
    name: str
    description: Optional[str]
    tech: List[str] = Field(default_factory=list)
    link: Optional[str]

class ResumeExtractionResponse(BaseModel):
    name: str
    headline: Optional[str] = Field(None, description="A 1-line professional summary based on experience.")
    email: Optional[str]
    location: Optional[str]
    summary: Optional[str] = Field(None, description="A 2-3 sentence summary of the person's career arc.")
    skills: List[SkillSchema] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    projects: List[ProjectSchema] = Field(default_factory=list)
