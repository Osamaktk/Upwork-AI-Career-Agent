from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.client_analyzer import (
    ClientAnalyzerAgent,
    UnsupportedClientEvidenceError,
)
from app.api.dependencies import get_ai_provider, get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models.identity import User
from app.schemas.clients import (
    ClientAnalysisRead,
    ClientCreate,
    ClientDetail,
    ClientFactCreate,
    ClientFactRead,
    ClientRead,
    ClientSourceCreate,
    ClientSourceRead,
    ClientUpdate,
)
from app.services.ai_provider import AIProvider, AIProviderError
from app.services.clients import (
    ClientJobMismatchError,
    ClientNotFoundError,
    ClientService,
    DuplicateClientError,
    InvalidClientSourceError,
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientRead:
    del user
    try:
        return await ClientService(session).create(payload)
    except (DuplicateClientError, IntegrityError) as exc:
        raise HTTPException(status_code=409, detail="Client already exists") from exc


@router.get("", response_model=list[ClientRead])
async def list_clients(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ClientRead]:
    del user
    return await ClientService(session).list_clients()


@router.get("/{client_id}", response_model=ClientDetail)
async def get_client(
    client_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientDetail:
    del user
    try:
        return await ClientService(session).detail(client_id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientRead:
    del user
    try:
        return await ClientService(session).update(client_id, payload)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc


@router.post(
    "/{client_id}/sources",
    response_model=ClientSourceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_source(
    client_id: str,
    payload: ClientSourceCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientSourceRead:
    del user
    try:
        return await ClientService(session).create_source(client_id, payload)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc


@router.post(
    "/{client_id}/facts",
    response_model=ClientFactRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_fact(
    client_id: str,
    payload: ClientFactCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientFactRead:
    del user
    try:
        return await ClientService(session).create_fact(client_id, payload)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    except InvalidClientSourceError as exc:
        raise HTTPException(status_code=422, detail="Client source is invalid") from exc


@router.get("/{client_id}/facts", response_model=list[ClientFactRead])
async def list_client_facts(
    client_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ClientFactRead]:
    del user
    try:
        return await ClientService(session).list_facts(client_id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc


@router.post("/{client_id}/analyze", response_model=ClientAnalysisRead)
async def analyze_client(
    client_id: str,
    job_id: str,
    use_ai: bool = Query(default=False),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    provider: AIProvider = Depends(get_ai_provider),
) -> ClientAnalysisRead:
    del user
    agent = ClientAnalyzerAgent(
        provider=provider,
        model=settings.ai_primary_model,
        use_ai=use_ai,
    )
    try:
        return await ClientService(session).analyze(client_id, job_id, agent)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    except ClientJobMismatchError as exc:
        raise HTTPException(status_code=422, detail="Job does not belong to this client") from exc
    except UnsupportedClientEvidenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
