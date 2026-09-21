from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VerificationStatus


class PortfolioProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolio_projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    problem: Mapped[str | None] = mapped_column(Text)
    solution: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(Text)
    assets: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    github_url: Mapped[str | None] = mapped_column(String(2048))
    demo_url: Mapped[str | None] = mapped_column(String(2048))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(
        String(24), default=VerificationStatus.UNVERIFIED.value, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
