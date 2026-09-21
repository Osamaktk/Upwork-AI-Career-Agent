from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.identity import User
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.services.profiles import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfileService,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    try:
        return await ProfileService(session).create(user.id, payload)
    except ProfileAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Profile already exists") from exc


@router.get("", response_model=ProfileRead)
async def get_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    try:
        return await ProfileService(session).get(user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc


@router.patch("", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    try:
        return await ProfileService(session).update(user.id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Profile not found") from exc
