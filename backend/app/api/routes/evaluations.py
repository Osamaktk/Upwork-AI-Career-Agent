from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.models.identity import User
from app.schemas.evidence import Phase3EvaluationMetrics
from app.services.evaluations import Phase3EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/phase3", response_model=Phase3EvaluationMetrics)
async def run_phase3_evaluation(
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Phase3EvaluationMetrics:
    del user
    return await Phase3EvaluationService().run(settings.phase3_evaluation_file)
