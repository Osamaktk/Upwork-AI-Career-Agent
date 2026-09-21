from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models.identity import User
from app.schemas.development import DevelopmentSeedResult
from app.services.development_seed import (
    DevelopmentSeedDisabledError,
    DevelopmentSeedService,
    InvalidDevelopmentSeedError,
)

router = APIRouter(prefix="/development", tags=["development"])


@router.post("/seed", response_model=DevelopmentSeedResult)
async def seed_development_data(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DevelopmentSeedResult:
    path = Path("sample_data/development_profile.json")
    try:
        return await DevelopmentSeedService(session, settings).seed(user.id, path)
    except DevelopmentSeedDisabledError as exc:
        raise HTTPException(status_code=404, detail="Development seed is unavailable") from exc
    except (InvalidDevelopmentSeedError, OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
