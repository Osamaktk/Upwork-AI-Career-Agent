from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.job_analyzer import JobAnalyzerAgent
from app.api.dependencies import get_ai_provider, get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models.enums import CompatibilityStatus, JobStatus
from app.models.identity import User
from app.schemas.jobs import (
    BatchAnalysisResult,
    JobAnalysis,
    JobCreate,
    JobDetail,
    JobPage,
    JobRead,
    JobUpdate,
    SampleImportResult,
)
from app.schemas.matching import JobMatchRead
from app.services.ai_provider import AIProvider, AIProviderError
from app.services.batch_analysis import BatchAnalysisService
from app.services.jobs import DuplicateJobError, JobNotFoundError, JobService
from app.services.matching import (
    MatchingService,
    MatchNotReadyError,
    UnsupportedClaimError,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/import/sample", response_model=SampleImportResult)
async def import_sample_jobs(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SampleImportResult:
    del user
    return await JobService(session).import_samples(settings.sample_jobs_dir)


@router.post("/analyze/batch", response_model=BatchAnalysisResult)
async def analyze_sample_batch(
    use_ai: bool = Query(default=False),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    provider: AIProvider = Depends(get_ai_provider),
) -> BatchAnalysisResult:
    analyzer = JobAnalyzerAgent(
        provider=provider,
        model=settings.ai_fast_model,
        use_ai=use_ai,
    )
    matcher = MatchingService(
        session,
        provider=provider,
        model=settings.ai_primary_model,
        use_ai=use_ai,
    )
    return await BatchAnalysisService(session, analyzer, matcher).run(user.id)


@router.get("", response_model=JobPage)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    skill: str | None = None,
    job_status: JobStatus | None = Query(default=None, alias="status"),
    source: str | None = None,
    min_budget: Decimal | None = Query(default=None, ge=0),
    max_budget: Decimal | None = Query(default=None, ge=0),
    posted_after: datetime | None = None,
    posted_before: datetime | None = None,
    compatibility_status: CompatibilityStatus | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobPage:
    del user
    return await JobService(session).list(
        page=page,
        page_size=page_size,
        skill=skill,
        status=job_status.value if job_status else None,
        source=source,
        min_budget=min_budget,
        max_budget=max_budget,
        posted_after=posted_after,
        posted_before=posted_before,
        compatibility_status=(compatibility_status.value if compatibility_status else None),
    )


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    del user
    try:
        return JobRead.model_validate(await JobService(session).create(payload))
    except (DuplicateJobError, IntegrityError) as exc:
        raise HTTPException(status_code=409, detail="Job already exists") from exc


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobDetail:
    try:
        return await JobService(session).get_detail(job_id, user.id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: str,
    payload: JobUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    del user
    try:
        return JobRead.model_validate(await JobService(session).update(job_id, payload))
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/{job_id}/analyze", response_model=JobAnalysis)
async def analyze_job(
    job_id: str,
    use_ai: bool = Query(default=False),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    provider: AIProvider = Depends(get_ai_provider),
) -> JobAnalysis:
    del user
    agent = JobAnalyzerAgent(
        provider=provider,
        model=settings.ai_fast_model,
        use_ai=use_ai,
    )
    try:
        return await JobService(session).analyze(job_id, agent)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{job_id}/match", response_model=JobMatchRead)
async def match_job(
    job_id: str,
    use_ai: bool = Query(default=False),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    provider: AIProvider = Depends(get_ai_provider),
) -> JobMatchRead:
    service = MatchingService(
        session,
        provider=provider,
        model=settings.ai_primary_model,
        use_ai=use_ai,
    )
    try:
        return await service.match(job_id, user.id)
    except MatchNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnsupportedClaimError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
