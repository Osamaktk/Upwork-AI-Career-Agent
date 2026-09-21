from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models.enums import VerificationStatus


class PortfolioBase(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(min_length=1, max_length=8000)
    problem: str | None = Field(default=None, max_length=8000)
    solution: str | None = Field(default=None, max_length=8000)
    result: str | None = Field(default=None, max_length=8000)
    technologies: list[str] = Field(default_factory=list, max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=100)
    github_url: HttpUrl | None = None
    demo_url: HttpUrl | None = None
    assets: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=100)
    verified_claim_ids: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("technologies", "skills", "tags")
    @classmethod
    def normalize_lists(cls, values: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for value in values:
            clean = value.strip()
            if not clean or len(clean) > 240:
                raise ValueError("List values must contain 1 to 240 characters")
            if clean.casefold() not in seen:
                seen.add(clean.casefold())
                output.append(clean)
        return output


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, min_length=1, max_length=8000)
    problem: str | None = Field(default=None, max_length=8000)
    solution: str | None = Field(default=None, max_length=8000)
    result: str | None = Field(default=None, max_length=8000)
    technologies: list[str] | None = Field(default=None, max_length=100)
    skills: list[str] | None = Field(default=None, max_length=100)
    github_url: HttpUrl | None = None
    demo_url: HttpUrl | None = None
    assets: list[dict[str, Any]] | None = Field(default=None, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=100)
    verified_claim_ids: list[str] | None = Field(default=None, max_length=100)

    @field_validator("technologies", "skills", "tags")
    @classmethod
    def normalize_optional_lists(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return PortfolioBase.normalize_lists(values)


class PortfolioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    description: str
    problem: str | None
    solution: str | None
    result: str | None
    technologies: list[str]
    skills: list[str]
    github_url: str | None
    demo_url: str | None
    assets: list[dict[str, Any]]
    tags: list[str]
    verification_status: VerificationStatus
    verified_claim_ids: list[str]
    created_at: datetime
    updated_at: datetime
