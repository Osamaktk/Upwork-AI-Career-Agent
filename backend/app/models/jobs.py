from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AnalysisState, CompatibilityStatus, JobStatus


class Client(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("source", "source_client_id", name="uq_clients_source_external_id"),
    )

    name: Mapped[str | None] = mapped_column(String(240))
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
