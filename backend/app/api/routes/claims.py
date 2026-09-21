from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.enums import ClaimCategory, VerificationStatus
from app.models.identity import User, VerifiedClaim
from app.schemas.claims import ClaimCreate, ClaimRead, ClaimUpdate
from app.services.claims import (
    ClaimMustStartUnverifiedError,
    ClaimNotFoundError,
    ClaimService,
    InvalidClaimReferenceError,
)

router = APIRouter(prefix="/claims", tags=["verified claims"])


@router.post("", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VerifiedClaim:
    try:
        return await ClaimService(session).create(user.id, payload)
    except ClaimMustStartUnverifiedError as exc:
        raise HTTPException(status_code=422, detail="New claims must start UNVERIFIED") from exc
    except InvalidClaimReferenceError as exc:
        raise HTTPException(status_code=422, detail="Claim reference is invalid") from exc


@router.get("", response_model=list[ClaimRead])
async def list_claims(
    verification_status: VerificationStatus | None = Query(default=None),
    category: ClaimCategory | None = Query(default=None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[VerifiedClaim]:
    return await ClaimService(session).list(
        user.id,
        verification_status.value if verification_status else None,
        category.value if category else None,
    )


@router.patch("/{claim_id}", response_model=ClaimRead)
async def update_claim(
    claim_id: str,
    payload: ClaimUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VerifiedClaim:
    try:
        return await ClaimService(session).update(claim_id, user.id, payload)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc
    except InvalidClaimReferenceError as exc:
        raise HTTPException(status_code=422, detail="Claim reference is invalid") from exc


async def transition_claim(
    claim_id: str,
    target: VerificationStatus,
    user: User,
    session: AsyncSession,
) -> VerifiedClaim:
    try:
        return await ClaimService(session).transition(claim_id, user.id, target)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc


@router.post("/{claim_id}/verify", response_model=ClaimRead)
async def verify_claim(
    claim_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VerifiedClaim:
    return await transition_claim(claim_id, VerificationStatus.VERIFIED, user, session)


@router.post("/{claim_id}/unverify", response_model=ClaimRead)
async def unverify_claim(
    claim_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VerifiedClaim:
    return await transition_claim(claim_id, VerificationStatus.UNVERIFIED, user, session)


@router.post("/{claim_id}/expire", response_model=ClaimRead)
async def expire_claim(
    claim_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VerifiedClaim:
    return await transition_claim(claim_id, VerificationStatus.EXPIRED, user, session)
