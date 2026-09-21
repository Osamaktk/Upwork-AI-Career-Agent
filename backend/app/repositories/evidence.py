from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import EvidenceLink, JobRequirement
from app.models.portfolio import PortfolioSelection


class EvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_requirements(self, job_id: str) -> list[JobRequirement]:
        result = await self.session.execute(
            select(JobRequirement)
            .where(JobRequirement.job_id == job_id, JobRequirement.is_required.is_(True))
            .order_by(JobRequirement.created_at)
        )
        return list(result.scalars())

    async def list_links(self, job_id: str, user_id: str) -> list[EvidenceLink]:
        result = await self.session.execute(
            select(EvidenceLink)
            .where(EvidenceLink.job_id == job_id, EvidenceLink.user_id == user_id)
            .order_by(EvidenceLink.requirement_id, EvidenceLink.created_at)
        )
        return list(result.scalars())

    async def get_selection(self, job_id: str, user_id: str) -> PortfolioSelection | None:
        result = await self.session.execute(
            select(PortfolioSelection).where(
                PortfolioSelection.job_id == job_id,
                PortfolioSelection.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
