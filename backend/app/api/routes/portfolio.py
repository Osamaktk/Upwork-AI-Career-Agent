from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.identity import User
from app.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioUpdate
from app.services.portfolio import (
    InvalidVerifiedClaimError,
    PortfolioNotFoundError,
    PortfolioService,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: PortfolioCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PortfolioRead:
    try:
        return await PortfolioService(session).create(user.id, payload)
    except InvalidVerifiedClaimError as exc:
        raise HTTPException(status_code=422, detail="Verified claim selection is invalid") from exc


@router.get("", response_model=list[PortfolioRead])
async def list_projects(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PortfolioRead]:
    return await PortfolioService(session).list_projects(user.id)


@router.get("/{project_id}", response_model=PortfolioRead)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PortfolioRead:
    try:
        return await PortfolioService(session).get(project_id, user.id)
    except PortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Portfolio project not found") from exc


@router.patch("/{project_id}", response_model=PortfolioRead)
async def update_project(
    project_id: str,
    payload: PortfolioUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PortfolioRead:
    try:
        return await PortfolioService(session).update(project_id, user.id, payload)
    except PortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Portfolio project not found") from exc
    except InvalidVerifiedClaimError as exc:
        raise HTTPException(status_code=422, detail="Verified claim selection is invalid") from exc


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        await PortfolioService(session).delete(project_id, user.id)
    except PortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Portfolio project not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
