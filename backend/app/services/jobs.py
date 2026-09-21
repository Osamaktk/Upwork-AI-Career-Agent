import json
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.job_analyzer import JobAnalyzerAgent
from app.models.enums import AnalysisState, CompatibilityStatus
from app.models.jobs import Client, Job, JobMatch, JobRequirement
from app.repositories.jobs import JobRepository
from app.schemas.jobs import (
    ImportErrorDetail,
    JobAnalysis,
    JobCreate,
    JobDetail,
    JobPage,
    JobRead,
    JobUpdate,
    SampleImportResult,
    SampleJob,
)


class JobNotFoundError(Exception):
    pass


class DuplicateJobError(Exception):
    pass


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = JobRepository(session)

    async def import_samples(self, directory: Path) -> SampleImportResult:
        response = SampleImportResult()
        seen: set[tuple[str, str]] = set()
        for path in sorted(directory.glob("job_*.json")):
            try:
                payload = SampleJob.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, ValidationError, json.JSONDecodeError) as exc:
                response.skipped_count += 1
                response.validation_errors.append(
                    ImportErrorDetail(file=path.name, message=str(exc))
                )
                continue
            identity = (payload.source, payload.source_job_id)
            if identity in seen or await self.repository.get_by_source_id(*identity):
                response.skipped_count += 1
                response.duplicate_count += 1
                continue
            seen.add(identity)
            client = await self.repository.get_client(
                payload.source, payload.client.source_client_id
            )
            if client is None:
                client = Client(
                    source=payload.source,
                    source_client_id=payload.client.source_client_id,
                    name=payload.client.name,
                    raw_data={"facts": payload.client.facts},
                )
                self.session.add(client)
                await self.session.flush()
            else:
                client.name = payload.client.name
                client.raw_data = {"facts": payload.client.facts}
            job_values = payload.model_dump(exclude={"client"}, mode="python")
            job_values["source_url"] = (
                str(payload.source_url) if payload.source_url is not None else None
            )
            job_values["raw_data"] = payload.model_dump(mode="json")
            job_values["normalized_data"] = self.normalize_sample(payload)
            self.session.add(Job(client_id=client.id, **job_values))
            response.imported_count += 1
        await self.session.commit()
        return response

    async def create(self, payload: JobCreate) -> Job:
        if await self.repository.get_by_source_id(payload.source, payload.source_job_id):
            raise DuplicateJobError
        values = payload.model_dump(mode="python")
        values["source_url"] = str(payload.source_url) if payload.source_url else None
        values["normalized_data"] = self.normalize_fields(payload)
        job = Job(**values)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def update(self, job_id: str, payload: JobUpdate) -> Job:
        job = await self._get(job_id)
        values = payload.model_dump(exclude_unset=True, mode="python")
        if "source_url" in values and values["source_url"] is not None:
            values["source_url"] = str(values["source_url"])
        invalidates_analysis = bool(
            {"title", "description", "required_skills", "budget_min", "budget_max"} & values.keys()
        )
        for key, value in values.items():
            setattr(job, key, value)
        if invalidates_analysis:
            job.analysis_state = AnalysisState.PENDING.value
            job.compatibility_status = CompatibilityStatus.PENDING.value
            job.normalized_data = {
                **self.normalize_model(job),
                "analysis": None,
            }
            await self.session.execute(
                delete(JobRequirement).where(JobRequirement.job_id == job.id)
            )
            await self.session.execute(delete(JobMatch).where(JobMatch.job_id == job.id))
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_detail(self, job_id: str, user_id: str) -> JobDetail:
        job = await self._get(job_id)
        analysis_data = (job.normalized_data or {}).get("analysis")
        match = await self.repository.get_match(job.id, user_id)
        return JobDetail.model_validate(
            {
                **{column.name: getattr(job, column.name) for column in job.__table__.columns},
                "analysis": JobAnalysis.model_validate(analysis_data) if analysis_data else None,
                "match": match,
            }
        )

    async def list(self, **filters) -> JobPage:
        jobs, total, pages = await self.repository.list_paginated(**filters)
        return JobPage(
            items=[JobRead.model_validate(job) for job in jobs],
            page=filters["page"],
            page_size=filters["page_size"],
            total=total,
            pages=pages,
        )

    async def analyze(self, job_id: str, agent: JobAnalyzerAgent) -> JobAnalysis:
        job = await self._get(job_id)
        try:
            analysis = await agent.analyze(job)
        except Exception:
            job.analysis_state = AnalysisState.FAILED.value
            await self.session.commit()
            raise
        await self.session.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))
        for value in analysis.required_skills:
            self.session.add(
                JobRequirement(job_id=job.id, kind="SKILL", value=value, is_required=True)
            )
        for value in analysis.preferred_skills:
            self.session.add(
                JobRequirement(job_id=job.id, kind="SKILL", value=value, is_required=False)
            )
        job.required_skills = analysis.required_skills
        job.normalized_data = {
            **self.normalize_model(job),
            "analysis": analysis.model_dump(mode="json"),
        }
        job.analysis_state = AnalysisState.ANALYZED.value
        await self.session.commit()
        return analysis

    async def _get(self, job_id: str) -> Job:
        job = await self.repository.get(job_id)
        if job is None:
            raise JobNotFoundError
        return job

    @staticmethod
    def normalize_sample(payload: SampleJob) -> dict:
        return {
            "title": payload.title.strip(),
            "description": payload.description.strip(),
            "required_skills": [skill.casefold() for skill in payload.required_skills],
            "budget_type": payload.budget_type,
            "currency": payload.currency,
        }

    @staticmethod
    def normalize_fields(payload: JobCreate) -> dict:
        return {
            "title": payload.title.strip(),
            "description": payload.description.strip(),
            "required_skills": [skill.casefold() for skill in payload.required_skills],
            "budget_type": payload.budget_type,
            "currency": payload.currency,
        }

    @staticmethod
    def normalize_model(job: Job) -> dict:
        return {
            "title": job.title.strip(),
            "description": job.description.strip(),
            "required_skills": [skill.casefold() for skill in job.required_skills],
            "budget_type": job.budget_type,
            "currency": job.currency,
        }
