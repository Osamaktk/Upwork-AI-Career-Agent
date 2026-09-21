from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReviewStatus, VerificationStatus
from app.models.identity import Profile, VerifiedClaim
from app.models.portfolio import PortfolioProject
from app.models.system import AuditLog
from app.repositories.claims import ClaimRepository
from app.schemas.claims import ClaimCreate, ClaimUpdate


class ClaimNotFoundError(Exception):
    pass


class InvalidClaimReferenceError(Exception):
    pass


class ClaimMustStartUnverifiedError(Exception):
    pass


class ClaimService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ClaimRepository(session)

    async def create(self, user_id: str, payload: ClaimCreate) -> VerifiedClaim:
        if payload.verification_status != VerificationStatus.UNVERIFIED:
            raise ClaimMustStartUnverifiedError
        await self._validate_references(user_id, payload.profile_id, payload.portfolio_project_id)
        claim = VerifiedClaim(
            user_id=user_id,
            **payload.model_dump(exclude={"verification_status"}, mode="json"),
            verification_status=VerificationStatus.UNVERIFIED.value,
        )
        self.session.add(claim)
        await self.session.commit()
        await self.session.refresh(claim)
        return claim

    async def update(
        self, claim_id: str, user_id: str, payload: ClaimUpdate
    ) -> VerifiedClaim:
        claim = await self._get(claim_id, user_id)
        values = payload.model_dump(exclude_unset=True, mode="json")
        profile_id = values.get("profile_id", claim.profile_id)
        project_id = values.get("portfolio_project_id", claim.portfolio_project_id)
        await self._validate_references(user_id, profile_id, project_id)
        for key, value in values.items():
            setattr(claim, key, value)
        await self.session.commit()
        await self.session.refresh(claim)
        return claim

    async def list(
        self, user_id: str, status: str | None = None, category: str | None = None
    ) -> list[VerifiedClaim]:
        return await self.repository.list_for_user(user_id, status, category)

    async def transition(
        self, claim_id: str, user_id: str, target: VerificationStatus
    ) -> VerifiedClaim:
        claim = await self._get(claim_id, user_id)
        previous = claim.verification_status
        claim.verification_status = target.value
        self.session.add(
            AuditLog(
                user_id=user_id,
                action="claim.verification_status_changed",
                input_reference=claim.id,
                output={"from": previous, "to": target.value},
                approval_status=ReviewStatus.APPROVED.value,
                result="success",
            )
        )
        if claim.portfolio_project_id:
            await self.session.flush()
            await self._refresh_project_status(claim.portfolio_project_id)
        await self.session.commit()
        await self.session.refresh(claim)
        return claim

    async def _get(self, claim_id: str, user_id: str) -> VerifiedClaim:
        claim = await self.repository.get_for_user(claim_id, user_id)
        if claim is None:
            raise ClaimNotFoundError
        return claim

    async def _validate_references(
        self, user_id: str, profile_id: str | None, project_id: str | None
    ) -> None:
        if profile_id:
            profile = await self.session.get(Profile, profile_id)
            if profile is None or profile.user_id != user_id:
                raise InvalidClaimReferenceError
        if project_id:
            project = await self.session.get(PortfolioProject, project_id)
            if project is None or project.user_id != user_id or not project.is_active:
                raise InvalidClaimReferenceError

    async def _refresh_project_status(self, project_id: str) -> None:
        project = await self.session.get(PortfolioProject, project_id)
        if project is None:
            return
        count = await self.session.scalar(
            select(func.count())
            .select_from(VerifiedClaim)
            .where(
                VerifiedClaim.portfolio_project_id == project_id,
                VerifiedClaim.verification_status == VerificationStatus.VERIFIED.value,
            )
        )
        project.verification_status = (
            VerificationStatus.VERIFIED.value
            if count
            else VerificationStatus.UNVERIFIED.value
        )
