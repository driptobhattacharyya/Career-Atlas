from pydantic import BaseModel, Field
from typing import List, Optional

class JobMatchSchema(BaseModel):
    title: str
    company: str
    location: str
    remote: bool = False
    seniority: str = Field(description="Intern, Entry, Junior, Mid, Senior")
    match_pct: int = Field(description="Calculated match percentage (0-100)")
    matched: List[str] = Field(description="Keywords matched with user skills")
    missing: List[str] = Field(description="Required keywords missing from user skills")
    salary: Optional[str]
    posted_days: int = Field(default=0)
    description: str
    external_url: str

class ScrapedJobsResponse(BaseModel):
    jobs: List[JobMatchSchema]
