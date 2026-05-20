from pydantic import BaseModel, Field
from typing import List, Optional

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
