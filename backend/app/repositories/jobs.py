import math
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Client, Job, JobMatch


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: str) -> Job | None:
        return await self.session.get(Job, job_id)

    async def get_by_source_id(self, source: str, source_job_id: str) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.source == source, Job.source_job_id == source_job_id)
        )
        return result.scalar_one_or_none()

    async def get_client(self, source: str, source_client_id: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(
                Client.source == source, Client.source_client_id == source_client_id
            )
        )
        return result.scalar_one_or_none()

    async def get_match(self, job_id: str, user_id: str) -> JobMatch | None:
        result = await self.session.execute(
            select(JobMatch).where(JobMatch.job_id == job_id, JobMatch.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        skill: str | None = None,
        status: str | None = None,
        source: str | None = None,
        min_budget: Decimal | None = None,
        max_budget: Decimal | None = None,
        posted_after: datetime | None = None,
        posted_before: datetime | None = None,
        compatibility_status: str | None = None,
    ) -> tuple[list[Job], int, int]:
        filters = []
        if skill:
            filters.append(cast(Job.required_skills, String).ilike(f"%{skill}%"))
        if status:
            filters.append(Job.status == status)
        if source:
            filters.append(Job.source == source)
        if min_budget is not None:
            filters.append(or_(Job.budget_max.is_(None), Job.budget_max >= min_budget))
        if max_budget is not None:
            filters.append(or_(Job.budget_min.is_(None), Job.budget_min <= max_budget))
        if posted_after:
            filters.append(Job.posted_at >= posted_after)
        if posted_before:
            filters.append(Job.posted_at <= posted_before)
        if compatibility_status:
            filters.append(Job.compatibility_status == compatibility_status)

        count_statement = select(func.count()).select_from(Job).where(*filters)
        total = int((await self.session.execute(count_statement)).scalar_one())
        statement = (
            select(Job)
            .where(*filters)
            .order_by(Job.posted_at.desc().nullslast(), Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars()), total, math.ceil(total / page_size) if total else 0
