from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.identity import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DashboardSummary:
    return await DashboardService(session).summary(user.id)
