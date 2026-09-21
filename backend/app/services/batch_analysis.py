from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.job_analyzer import JobAnalyzerAgent
from app.models.jobs import Job
from app.schemas.jobs import BatchAnalysisResult
from app.services.jobs import JobService
from app.services.matching import MatchingService


class BatchAnalysisService:
    def __init__(
        self,
        session: AsyncSession,
        analyzer: JobAnalyzerAgent,
        matcher: MatchingService,
    ) -> None:
        self.session = session
        self.analyzer = analyzer
        self.matcher = matcher

    async def run(self, user_id: str) -> BatchAnalysisResult:
        analyzed = 0
        matched = 0
        failed = 0
        matches = []
        errors: list[str] = []
        result = await self.session.stream_scalars(
            select(Job).where(Job.source == "sample").order_by(Job.created_at)
        )
        async for job in result:
            try:
                await JobService(self.session).analyze(job.id, self.analyzer)
                analyzed += 1
                matches.append(await self.matcher.match(job.id, user_id))
                matched += 1
            except Exception as exc:
                failed += 1
                errors.append(f"{job.id}: {exc}")
        matches.sort(key=lambda item: item.compatibility_score, reverse=True)
        return BatchAnalysisResult(
            analyzed_count=analyzed,
            matched_count=matched,
            failed_count=failed,
            ranked_matches=matches,
            errors=errors,
        )
