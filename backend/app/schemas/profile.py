from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import VerificationStatus


class EducationEntry(BaseModel):
    institution: str = Field(min_length=1, max_length=240)
    qualification: str | None = Field(default=None, max_length=240)
    field_of_study: str | None = Field(default=None, max_length=240)
    started_at: str | None = Field(default=None, max_length=40)
    ended_at: str | None = Field(default=None, max_length=40)


class CertificationEntry(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    issuer: str | None = Field(default=None, max_length=240)
    issued_at: str | None = Field(default=None, max_length=40)
    credential_url: str | None = Field(default=None, max_length=2048)


class ExperienceEntry(BaseModel):
    role: str = Field(min_length=1, max_length=240)
    organization: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    started_at: str | None = Field(default=None, max_length=40)
    ended_at: str | None = Field(default=None, max_length=40)


class ProfileFields(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    overview: str | None = Field(default=None, max_length=8000)
    location: str | None = Field(default=None, max_length=240)
    years_experience: Decimal | None = Field(default=None, ge=0, le=80)
    education: list[EducationEntry] = Field(default_factory=list, max_length=50)
    certifications: list[CertificationEntry] = Field(default_factory=list, max_length=100)
    primary_skills: list[str] = Field(default_factory=list, max_length=100)
    secondary_skills: list[str] = Field(default_factory=list, max_length=100)
    programming_languages: list[str] = Field(default_factory=list, max_length=100)
    frameworks: list[str] = Field(default_factory=list, max_length=100)
    tools: list[str] = Field(default_factory=list, max_length=100)
    domains: list[str] = Field(default_factory=list, max_length=100)
    work_experience: list[ExperienceEntry] = Field(default_factory=list, max_length=100)
    internships: list[ExperienceEntry] = Field(default_factory=list, max_length=100)
    achievements: list[str] = Field(default_factory=list, max_length=100)

    @field_validator(
        "primary_skills",
        "secondary_skills",
        "programming_languages",
        "frameworks",
        "tools",
        "domains",
        "achievements",
    )
    @classmethod
    def normalize_string_lists(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            clean = value.strip()
            key = clean.casefold()
            if not clean or len(clean) > 240:
                raise ValueError("List values must contain 1 to 240 characters")
            if key not in seen:
                seen.add(key)
                normalized.append(clean)
        return normalized


class ProfileCreate(ProfileFields):
    pass


class ProfileUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    overview: str | None = Field(default=None, max_length=8000)
    location: str | None = Field(default=None, max_length=240)
    years_experience: Decimal | None = Field(default=None, ge=0, le=80)
    education: list[EducationEntry] | None = Field(default=None, max_length=50)
    certifications: list[CertificationEntry] | None = Field(default=None, max_length=100)
    primary_skills: list[str] | None = Field(default=None, max_length=100)
    secondary_skills: list[str] | None = Field(default=None, max_length=100)
    programming_languages: list[str] | None = Field(default=None, max_length=100)
    frameworks: list[str] | None = Field(default=None, max_length=100)
    tools: list[str] | None = Field(default=None, max_length=100)
    domains: list[str] | None = Field(default=None, max_length=100)
    work_experience: list[ExperienceEntry] | None = Field(default=None, max_length=100)
    internships: list[ExperienceEntry] | None = Field(default=None, max_length=100)
    achievements: list[str] | None = Field(default=None, max_length=100)

    @field_validator(
        "primary_skills",
        "secondary_skills",
        "programming_languages",
        "frameworks",
        "tools",
        "domains",
        "achievements",
    )
    @classmethod
    def normalize_optional_lists(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return ProfileFields.normalize_string_lists(values)


class ProfileRead(ProfileFields):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    verification_status: VerificationStatus
    completeness: int = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
