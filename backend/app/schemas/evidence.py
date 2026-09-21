from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EvidenceRelationship
from app.schemas.matching import RelatedMatch


class EvidenceLinkRead(BaseModel):
    id: str
    requirement_id: str
    requirement: str
    skill_id: str
    skill: str
    claim_id: str
    claim: str
    portfolio_project_id: str | None
    portfolio_project: str | None
    relationship: EvidenceRelationship
    explanation: str
    proposal_ready: bool


class EvidenceGraphRead(BaseModel):
    job_id: str
    job_title: str
    links: list[EvidenceLinkRead]
    unsupported_requirements: list[str]
    proposal_ready_link_count: int


class RankedPortfolioProject(BaseModel):
    project_id: str
    title: str
    relevance_score: Decimal = Field(ge=0, le=100)
    exact_matches: list[str] = Field(default_factory=list)
    related_matches: list[RelatedMatch] = Field(default_factory=list)
    verified_claim_ids: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1, max_length=4000)


class PortfolioNarrative(BaseModel):
    project_id: str
    explanation: str = Field(min_length=1, max_length=4000)
    supporting_claim_ids: list[str] = Field(default_factory=list, max_length=100)


class PortfolioNarrativeResult(BaseModel):
    projects: list[PortfolioNarrative] = Field(default_factory=list, max_length=100)


class PortfolioSelectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    user_id: str
    ranked_projects: list[RankedPortfolioProject]
    formula_version: str
    model_used: str | None
    analyzed_at: datetime
    created_at: datetime
    updated_at: datetime


class Phase3EvaluationMetrics(BaseModel):
    case_count: int
    skill_extraction_accuracy: Decimal
    portfolio_selection_accuracy: Decimal
    unsupported_claim_rate: Decimal
    false_match_rate: Decimal
    passed: bool
