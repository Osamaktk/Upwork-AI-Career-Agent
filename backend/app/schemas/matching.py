from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RelationshipKind(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    RELATED_MATCH = "RELATED_MATCH"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class RelatedMatch(BaseModel):
    required_skill: str
    evidence: str


class SemanticRelationship(BaseModel):
    required_skill: str
    capability: str | None = None
    relationship: RelationshipKind
    reason: str


class SemanticRelationshipResult(BaseModel):
    relationships: list[SemanticRelationship] = Field(default_factory=list)


class MatchNarrative(BaseModel):
    explanation: str = Field(min_length=1, max_length=5000)
    concerns: list[str] = Field(default_factory=list, max_length=50)
    supporting_claim_ids: list[str] = Field(default_factory=list, max_length=100)


class JobMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    user_id: str
    compatibility_score: Decimal
    exact_matches: list[str]
    related_matches: list[RelatedMatch]
    missing_skills: list[str]
    portfolio_project_ids: list[str]
    relevant_claim_ids: list[str]
    concerns: list[str]
    explanation: str
    model_used: str | None
    formula_version: str
    analysis_timestamp: datetime
    created_at: datetime
    updated_at: datetime
