from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import VerifiedClaim
from app.models.portfolio import PortfolioProject


class PortfolioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, project_id: str, user_id: str) -> PortfolioProject | None:
        result = await self.session.execute(
            select(PortfolioProject).where(
                PortfolioProject.id == project_id,
                PortfolioProject.user_id == user_id,
                PortfolioProject.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[PortfolioProject]:
        result = await self.session.execute(
            select(PortfolioProject)
            .where(
                PortfolioProject.user_id == user_id,
                PortfolioProject.is_active.is_(True),
            )
            .order_by(PortfolioProject.updated_at.desc())
        )
        return list(result.scalars())

    async def claim_ids(self, project_id: str, verified_only: bool = False) -> list[str]:
        statement = select(VerifiedClaim.id).where(
            VerifiedClaim.portfolio_project_id == project_id
        )
        if verified_only:
            statement = statement.where(VerifiedClaim.verification_status == "VERIFIED")
        result = await self.session.execute(statement)
        return list(result.scalars())
