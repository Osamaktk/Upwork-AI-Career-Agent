from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.models.enums import (
    AnalysisState,
    CompatibilityStatus,
    FactClassification,
    JobStatus,
    VerificationStatus,
)


class Client(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("source", "source_client_id", name="uq_clients_source_external_id"),
    )

    name: Mapped[str | None] = mapped_column(String(240))
    company: Mapped[str | None] = mapped_column(String(240))
    website: Mapped[str | None] = mapped_column(String(2048))
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_client_id: Mapped[str | None] = mapped_column(String(240))
    summary: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ClientSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "client_sources"

    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(80))
    url: Mapped[str | None] = mapped_column(String(2048))
    facts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClientFact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "client_facts"

    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    client_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("client_sources.id", ondelete="RESTRICT"), index=True
    )
    fact: Mapped[str] = mapped_column(Text)
    fact_type: Mapped[str] = mapped_column(String(80), index=True)
    classification: Mapped[str] = mapped_column(
        String(24), default=FactClassification.UNKNOWN.value, index=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(24), default=VerificationStatus.UNVERIFIED.value, index=True
    )
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ClientAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "client_analyses"
    __table_args__ = (
        UniqueConstraint("client_id", "job_id", name="uq_client_analyses_client_job"),
    )

    client_id: Mapped[str] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    verified_facts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    inferences: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    unknowns: Mapped[list[str]] = mapped_column(JSON, default=list)
    project_goals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    concerns: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    communication_style_indicators: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    model_used: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40), default="client-analysis-v1")
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "source_job_id", name="uq_jobs_source_external_id"),
    )

    client_id: Mapped[str | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_job_id: Mapped[str] = mapped_column(String(240))
    title: Mapped[str] = mapped_column(String(500), index=True)
    description: Mapped[str] = mapped_column(Text)
    budget_type: Mapped[str | None] = mapped_column(String(40))
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(8))
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    normalized_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(
        String(40), default=JobStatus.DISCOVERED.value, index=True
    )
    analysis_state: Mapped[str] = mapped_column(
        String(40), default=AnalysisState.PENDING.value, index=True
    )
    compatibility_status: Mapped[str] = mapped_column(
        String(40), default=CompatibilityStatus.PENDING.value, index=True
    )


class JobRequirement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_requirements"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(80), index=True)
    value: Mapped[str] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(default=True)


class JobMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("job_id", "user_id", name="uq_job_matches_job_user"),)

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    compatibility_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    matching_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    exact_matches: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_matches: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    portfolio_project_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    relevant_claim_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    concerns: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_next_action: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(120))
    formula_version: Mapped[str] = mapped_column(String(40), default="v1")
    analysis_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class EvidenceLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            "requirement_id",
            "skill_id",
            "claim_id",
            "portfolio_project_id",
            name="uq_evidence_links_chain",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("job_requirements.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    claim_id: Mapped[str] = mapped_column(
        ForeignKey("verified_claims.id", ondelete="CASCADE"), index=True
    )
    portfolio_project_id: Mapped[str | None] = mapped_column(
        ForeignKey("portfolio_projects.id", ondelete="CASCADE"), index=True
    )
    relationship: Mapped[str] = mapped_column(String(24), index=True)
    explanation: Mapped[str] = mapped_column(Text)
    proposal_ready: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
