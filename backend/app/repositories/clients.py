from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Client, ClientAnalysis, ClientFact, ClientSource, Job


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, client_id: str) -> Client | None:
        return await self.session.get(Client, client_id)

    async def get_by_source(self, source: str, source_client_id: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(
                Client.source == source,
                Client.source_client_id == source_client_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_clients(self) -> list[Client]:
        result = await self.session.execute(select(Client).order_by(Client.updated_at.desc()))
        return list(result.scalars())

    async def list_sources(self, client_id: str) -> list[ClientSource]:
        result = await self.session.execute(
            select(ClientSource)
            .where(ClientSource.client_id == client_id)
            .order_by(ClientSource.created_at.desc())
        )
        return list(result.scalars())

    async def get_source(self, source_id: str, client_id: str) -> ClientSource | None:
        result = await self.session.execute(
            select(ClientSource).where(
                ClientSource.id == source_id,
                ClientSource.client_id == client_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_source(
        self, client_id: str, source_type: str, url: str | None
    ) -> ClientSource | None:
        result = await self.session.execute(
            select(ClientSource).where(
                ClientSource.client_id == client_id,
                ClientSource.source_type == source_type,
                ClientSource.url == url,
            )
        )
        return result.scalar_one_or_none()

    async def list_facts(self, client_id: str) -> list[ClientFact]:
        result = await self.session.execute(
            select(ClientFact)
            .where(ClientFact.client_id == client_id)
            .order_by(ClientFact.classification, ClientFact.created_at)
        )
        return list(result.scalars())

    async def find_fact(self, client_id: str, fact: str) -> ClientFact | None:
        result = await self.session.execute(
            select(ClientFact).where(
                ClientFact.client_id == client_id,
                ClientFact.fact == fact,
            )
        )
        return result.scalar_one_or_none()

    async def get_job(self, job_id: str, client_id: str) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id, Job.client_id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_analysis(self, client_id: str, job_id: str) -> ClientAnalysis | None:
        result = await self.session.execute(
            select(ClientAnalysis).where(
                ClientAnalysis.client_id == client_id,
                ClientAnalysis.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_analyses(self, client_id: str) -> list[ClientAnalysis]:
        result = await self.session.execute(
            select(ClientAnalysis)
            .where(ClientAnalysis.client_id == client_id)
            .order_by(ClientAnalysis.analyzed_at.desc())
        )
        return list(result.scalars())
