from pydantic import BaseModel, Field
from typing import Optional


class ContactInfo(BaseModel):
    email: Optional[str] = Field(
        default=None, description="Primary email address.")
    phone_raw: Optional[str] = Field(
        default=None, description="Raw phone number as extracted.")
    country_code: Optional[str] = Field(
        default=None, description="Country code (e.g., +91).")
    national_number: Optional[str] = Field(
        default=None, description="National number without country code.")
    e164_phone: Optional[str] = Field(
        default=None, description="E.164 formatted phone number.")
    location: Optional[str] = Field(
        default=None, description="Location such as city, state, or country.")
    linkedin: Optional[str] = Field(
        default=None, description="LinkedIn profile URL.")
    github: Optional[str] = Field(
        default=None, description="GitHub profile URL.")
    website: Optional[str] = Field(
        default=None, description="Personal website or portfolio URL.")


class ExperienceItem(BaseModel):
    company: Optional[str] = Field(
        default=None, description="Company or organization name.")
    title: Optional[str] = Field(
        default=None, description="Job title or role.")
    location: Optional[str] = Field(
        default=None, description="Job location if present.")
    start_date: Optional[str] = Field(
        default=None, description="Start date as written in the resume.")
    end_date: Optional[str] = Field(
        default=None, description="End date as written in the resume.")
    is_current: Optional[bool] = Field(
        default=None, description="True if this is the current role.")
    description_bullets: list[str] = Field(
        default_factory=list, description="Resume bullet points for the role.")
    technologies: list[str] = Field(
        default_factory=list, description="Technologies, tools, or methods mentioned for the role.")


class EducationItem(BaseModel):
    institution: Optional[str] = Field(
        default=None, description="School, college, or university name.")
    degree: Optional[str] = Field(
        default=None, description="Degree or qualification.")
    field_of_study: Optional[str] = Field(
        default=None, description="Branch, major, or specialization.")
    start_date: Optional[str] = Field(
        default=None, description="Start date if present.")
    end_date: Optional[str] = Field(
        default=None, description="End date if present.")
    grade: Optional[str] = Field(
        default=None, description="CGPA, percentage, or grade if present.")
    notes: list[str] = Field(
        default_factory=list, description="Additional notes such as honors or relevant coursework.")


class ProjectItem(BaseModel):
    name: Optional[str] = Field(default=None, description="Project name.")
    description: Optional[str] = Field(
        default=None, description="Short description of the project.")
    technologies: list[str] = Field(
        default_factory=list, description="Tools, libraries, frameworks, or languages used.")
    link: Optional[str] = Field(
        default=None, description="Project URL if present.")


class CertificationItem(BaseModel):
    name: Optional[str] = Field(
        default=None, description="Certification name.")
    issuer: Optional[str] = Field(
        default=None, description="Issuing organization.")
    date: Optional[str] = Field(default=None, description="Date if present.")
    credential_id: Optional[str] = Field(
        default=None, description="Credential ID if present.")
    link: Optional[str] = Field(
        default=None, description="Credential URL if present.")


class ResumeExtraction(BaseModel):
    full_name: Optional[str] = Field(
        default=None, description="Candidate full name.")
    headline: Optional[str] = Field(
        default=None, description="Professional headline.")
    contact: ContactInfo
    summary: Optional[str] = Field(
        default=None, description="Professional summary.")

    skills: list[str] = Field(
        default_factory=list,
        description="All professional skills, core competencies, tools, frameworks, concepts, methodologies, and technologies explicitly listed in the resume.")
    programming_languages: list[str] = Field(
        default_factory=list, description="Programming languages (Python, Java, C, etc.).")
    spoken_languages: list[str] = Field(
        default_factory=list, description="Human languages (English, Hindi, etc.).")

    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)

    keywords: list[str] = Field(
        default_factory=list, description="Important keywords for search/indexing.")
