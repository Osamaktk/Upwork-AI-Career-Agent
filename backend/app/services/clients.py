from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.client_analyzer import ClientAnalyzerAgent
from app.models.enums import FactClassification, VerificationStatus
from app.models.jobs import Client, ClientAnalysis, ClientFact, ClientSource
from app.repositories.clients import ClientRepository
from app.schemas.clients import (
    ClientAnalysisDraft,
    ClientAnalysisRead,
    ClientCreate,
    ClientDetail,
    ClientFactCreate,
    ClientFactRead,
    ClientFactReference,
    ClientRead,
    ClientSourceCreate,
    ClientSourceRead,
    ClientUpdate,
)


class ClientNotFoundError(Exception):
    pass


class DuplicateClientError(Exception):
    pass


class InvalidClientSourceError(Exception):
    pass


class ClientJobMismatchError(Exception):
    pass


class ClientService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ClientRepository(session)

    async def create(self, payload: ClientCreate) -> ClientRead:
        if await self.repository.get_by_source(payload.source, payload.source_client_id):
            raise DuplicateClientError
        values = payload.model_dump(mode="python")
        values["website"] = str(payload.website) if payload.website else None
        client = Client(**values)
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return ClientRead.model_validate(client)

    async def update(self, client_id: str, payload: ClientUpdate) -> ClientRead:
        client = await self._get(client_id)
        values = payload.model_dump(exclude_unset=True, mode="python")
        if "website" in values and values["website"] is not None:
            values["website"] = str(values["website"])
        for key, value in values.items():
            setattr(client, key, value)
        await self.session.commit()
        await self.session.refresh(client)
        return ClientRead.model_validate(client)

    async def list_clients(self) -> list[ClientRead]:
        return [ClientRead.model_validate(item) for item in await self.repository.list_clients()]

    async def detail(self, client_id: str) -> ClientDetail:
        client = await self._get(client_id)
        sources = await self.repository.list_sources(client_id)
        source_map = {source.id: source for source in sources}
        facts = await self.repository.list_facts(client_id)
        analyses = await self.repository.list_analyses(client_id)
        values = {column.name: getattr(client, column.name) for column in client.__table__.columns}
        return ClientDetail.model_validate(
            {
                **values,
                "sources": sources,
                "facts": [self._fact_schema(fact, source_map) for fact in facts],
                "analyses": [ClientAnalysisRead.model_validate(item) for item in analyses],
            }
        )

    async def create_source(
        self, client_id: str, payload: ClientSourceCreate
    ) -> ClientSourceRead:
        await self._get(client_id)
        values = payload.model_dump(mode="python")
        values["url"] = str(payload.url) if payload.url else None
        source = ClientSource(client_id=client_id, facts=[], **values)
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return ClientSourceRead.model_validate(source)

    async def create_fact(self, client_id: str, payload: ClientFactCreate) -> ClientFactRead:
        await self._get(client_id)
        source = None
        if payload.client_source_id:
            source = await self.repository.get_source(payload.client_source_id, client_id)
            if source is None:
                raise InvalidClientSourceError
        now = datetime.now(UTC)
        values = payload.model_dump(mode="json")
        values["first_seen"] = payload.first_seen or now
        values["last_seen"] = payload.last_seen or now
        fact = ClientFact(client_id=client_id, **values)
        self.session.add(fact)
        await self.session.commit()
        await self.session.refresh(fact)
        return self._fact_schema(fact, {source.id: source} if source else {})

    async def list_facts(self, client_id: str) -> list[ClientFactRead]:
        await self._get(client_id)
        sources = {item.id: item for item in await self.repository.list_sources(client_id)}
        return [
            self._fact_schema(item, sources)
            for item in await self.repository.list_facts(client_id)
        ]

    async def analyze(
        self, client_id: str, job_id: str, agent: ClientAnalyzerAgent
    ) -> ClientAnalysisRead:
        client = await self._get(client_id)
        job = await self.repository.get_job(job_id, client_id)
        if job is None:
            raise ClientJobMismatchError
        facts = await self.repository.list_facts(client_id)
        draft = await agent.analyze(client, job, facts)
        if not isinstance(draft, ClientAnalysisDraft):
            raise TypeError("Client analyzer returned an invalid result")
        sources = {item.id: item for item in await self.repository.list_sources(client_id)}
        verified = [
            ClientFactReference(
                id=fact.id,
                fact=fact.fact,
                fact_type=fact.fact_type,
                source_id=fact.client_source_id or "",
                source_url=(sources[fact.client_source_id].url if fact.client_source_id else None),
            )
            for fact in facts
            if fact.classification == FactClassification.FACT.value
            and fact.verification_status == VerificationStatus.VERIFIED.value
            and fact.client_source_id in sources
        ]
        values = {
            **draft.model_dump(mode="json"),
            "verified_facts": [item.model_dump(mode="json") for item in verified],
            "model_used": agent.model if agent.use_ai else None,
            "prompt_version": "client-analysis-v1",
            "analyzed_at": datetime.now(UTC),
        }
        analysis = await self.repository.get_analysis(client_id, job_id)
        if analysis is None:
            analysis = ClientAnalysis(client_id=client_id, job_id=job_id, **values)
            self.session.add(analysis)
        else:
            for key, value in values.items():
                setattr(analysis, key, value)
        await self.session.commit()
        await self.session.refresh(analysis)
        return ClientAnalysisRead.model_validate(analysis)

    async def _get(self, client_id: str) -> Client:
        client = await self.repository.get(client_id)
        if client is None:
            raise ClientNotFoundError
        return client

    @staticmethod
    def _fact_schema(
        fact: ClientFact, sources: dict[str, ClientSource]
    ) -> ClientFactRead:
        source = sources.get(fact.client_source_id or "")
        values = {column.name: getattr(fact, column.name) for column in fact.__table__.columns}
        return ClientFactRead.model_validate(
            {
                **values,
                "source_type": source.source_type if source else None,
                "source_url": source.url if source else None,
            }
        )
