from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import VerifiedClaim


class ClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, claim_id: str, user_id: str) -> VerifiedClaim | None:
        result = await self.session.execute(
            select(VerifiedClaim).where(
                VerifiedClaim.id == claim_id, VerifiedClaim.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: str, status: str | None = None, category: str | None = None
    ) -> list[VerifiedClaim]:
        statement = select(VerifiedClaim).where(VerifiedClaim.user_id == user_id)
        if status:
            statement = statement.where(VerifiedClaim.verification_status == status)
        if category:
            statement = statement.where(VerifiedClaim.category == category)
        result = await self.session.execute(statement.order_by(VerifiedClaim.created_at.desc()))
        return list(result.scalars())
