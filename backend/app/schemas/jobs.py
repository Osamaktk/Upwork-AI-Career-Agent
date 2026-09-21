from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import AnalysisState, CompatibilityStatus, JobStatus
from app.schemas.matching import JobMatchRead


class SampleClient(BaseModel):
    source_client_id: str = Field(min_length=1, max_length=240)
    name: str | None = Field(default=None, max_length=240)
    facts: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


class JobFields(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    source_job_id: str = Field(min_length=1, max_length=240)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=50_000)
    budget_type: Literal["fixed", "hourly"] | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default="USD", min_length=3, max_length=8)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    posted_at: datetime | None = None
    source_url: HttpUrl | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_budget_and_skills(self):
        if self.budget_min is not None and self.budget_max is not None:
            if self.budget_min > self.budget_max:
                raise ValueError("budget_min cannot exceed budget_max")
        normalized: list[str] = []
        seen: set[str] = set()
        for skill in self.required_skills:
            clean = skill.strip()
            if not clean or len(clean) > 240:
                raise ValueError("Skills must contain 1 to 240 characters")
            if clean.casefold() not in seen:
                seen.add(clean.casefold())
                normalized.append(clean)
        self.required_skills = normalized
        if self.currency:
            self.currency = self.currency.upper()
        return self


class SampleJob(JobFields):
    source: Literal["sample"]
    posted_at: datetime
    client: SampleClient


class JobCreate(JobFields):
    source: str = "manual"


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1, max_length=50_000)
    budget_type: Literal["fixed", "hourly"] | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    required_skills: list[str] | None = Field(default=None, max_length=100)
    posted_at: datetime | None = None
    source_url: HttpUrl | None = None
    status: JobStatus | None = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.budget_min is not None and self.budget_max is not None:
            if self.budget_min > self.budget_max:
                raise ValueError("budget_min cannot exceed budget_max")
        if self.required_skills is not None:
            self.required_skills = JobFields(
                source="validation",
                source_job_id="validation",
                title="validation",
                description="validation",
                required_skills=self.required_skills,
            ).required_skills
        if self.currency:
            self.currency = self.currency.upper()
        return self


class JobAnalysis(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    experience_requirement: str | None = None
    timeline: str | None = None
    budget: str | None = None
    project_type: str | None = None
    complexity_indicators: list[str] = Field(default_factory=list)
    unclear_requirements: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str | None
    source: str
    source_job_id: str
    title: str
    description: str
    budget_type: str | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    currency: str | None
    required_skills: list[str]
    posted_at: datetime | None
    source_url: str | None
    status: JobStatus
    analysis_state: AnalysisState
    compatibility_status: CompatibilityStatus
    created_at: datetime
    updated_at: datetime


class JobDetail(JobRead):
    analysis: JobAnalysis | None = None
    match: JobMatchRead | None = None


class JobPage(BaseModel):
    items: list[JobRead]
    page: int
    page_size: int
    total: int
    pages: int


class ImportErrorDetail(BaseModel):
    file: str
    message: str


class SampleImportResult(BaseModel):
    imported_count: int = 0
    skipped_count: int = 0
    duplicate_count: int = 0
    validation_errors: list[ImportErrorDetail] = Field(default_factory=list)


class BatchAnalysisResult(BaseModel):
    analyzed_count: int
    matched_count: int
    failed_count: int
    ranked_matches: list[JobMatchRead]
    errors: list[str] = Field(default_factory=list)
