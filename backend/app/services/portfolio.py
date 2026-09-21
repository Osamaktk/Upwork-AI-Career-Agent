from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import VerificationStatus
from app.models.identity import VerifiedClaim
from app.models.portfolio import PortfolioProject
from app.repositories.portfolio import PortfolioRepository
from app.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioUpdate


class PortfolioNotFoundError(Exception):
    pass


class InvalidVerifiedClaimError(Exception):
    pass


class PortfolioService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = PortfolioRepository(session)

    async def create(self, user_id: str, payload: PortfolioCreate) -> PortfolioRead:
        values = payload.model_dump(exclude={"verified_claim_ids"}, mode="json")
        project = PortfolioProject(user_id=user_id, **values)
        self.session.add(project)
        await self.session.flush()
        await self._attach_claims(project, user_id, payload.verified_claim_ids)
        await self.session.commit()
        await self.session.refresh(project)
        return await self._to_schema(project)

    async def list_projects(self, user_id: str) -> list[PortfolioRead]:
        projects = await self.repository.list_for_user(user_id)
        return [await self._to_schema(item) for item in projects]

    async def get(self, project_id: str, user_id: str) -> PortfolioRead:
        return await self._to_schema(await self._get(project_id, user_id))

    async def update(
        self, project_id: str, user_id: str, payload: PortfolioUpdate
    ) -> PortfolioRead:
        project = await self._get(project_id, user_id)
        values = payload.model_dump(exclude_unset=True, mode="json")
        claim_ids = values.pop("verified_claim_ids", None)
        for key, value in values.items():
            setattr(project, key, value)
        if claim_ids is not None:
            await self.session.execute(
                update(VerifiedClaim)
                .where(VerifiedClaim.portfolio_project_id == project.id)
                .values(portfolio_project_id=None)
            )
            await self._attach_claims(project, user_id, claim_ids)
        await self.session.commit()
        await self.session.refresh(project)
        return await self._to_schema(project)

    async def delete(self, project_id: str, user_id: str) -> None:
        project = await self._get(project_id, user_id)
        project.is_active = False
        await self.session.commit()

    async def _get(self, project_id: str, user_id: str) -> PortfolioProject:
        project = await self.repository.get_for_user(project_id, user_id)
        if project is None:
            raise PortfolioNotFoundError
        return project

    async def _attach_claims(
        self, project: PortfolioProject, user_id: str, claim_ids: list[str]
    ) -> None:
        if not claim_ids:
            project.verification_status = VerificationStatus.UNVERIFIED.value
            return
        result = await self.session.execute(
            select(VerifiedClaim).where(
                VerifiedClaim.id.in_(claim_ids),
                VerifiedClaim.user_id == user_id,
                VerifiedClaim.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        claims = list(result.scalars())
        if len(claims) != len(set(claim_ids)):
            raise InvalidVerifiedClaimError
        for claim in claims:
            claim.portfolio_project_id = project.id
        project.verification_status = VerificationStatus.VERIFIED.value

    async def _to_schema(self, project: PortfolioProject) -> PortfolioRead:
        values = {
            column.name: getattr(project, column.name) for column in project.__table__.columns
        }
        return PortfolioRead.model_validate(
            {**values, "verified_claim_ids": await self.repository.claim_ids(project.id, True)}
        )
