from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ClaimCategory, VerificationStatus


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(200))
    overview: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(240))
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    education: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    primary_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    secondary_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    programming_languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    frameworks: Mapped[list[str]] = mapped_column(JSON, default=list)
    tools: Mapped[list[str]] = mapped_column(JSON, default=list)
    domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    work_experience: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    internships: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    achievements: Mapped[list[str]] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(
        String(24), default=VerificationStatus.UNVERIFIED.value
    )


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("user_id", "name", "category", name="uq_skills_user_name_category"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(40), default="PRIMARY", index=True)
    level: Mapped[str | None] = mapped_column(String(80))
    verification_status: Mapped[str] = mapped_column(
        String(24), default=VerificationStatus.UNVERIFIED.value
    )


class VerifiedClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "verified_claims"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    portfolio_project_id: Mapped[str | None] = mapped_column(
        ForeignKey("portfolio_projects.id", ondelete="CASCADE"), index=True
    )
    claim: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(
        String(40), default=ClaimCategory.OTHER.value, index=True
    )
    source: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        String(24), default=VerificationStatus.UNVERIFIED.value, index=True
    )
