from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AnalysisState, CompatibilityStatus
from app.models.jobs import Job
from app.models.portfolio import PortfolioProject
from app.repositories.profiles import ProfileRepository
from app.schemas.dashboard import DashboardSummary
from app.services.profiles import profile_completeness


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary(self, user_id: str) -> DashboardSummary:
        async def job_count(*conditions) -> int:
            value = await self.session.scalar(
                select(func.count()).select_from(Job).where(*conditions)
            )
            return int(value or 0)

        portfolio_count = await self.session.scalar(
            select(func.count())
            .select_from(PortfolioProject)
            .where(
                PortfolioProject.user_id == user_id,
                PortfolioProject.is_active.is_(True),
            )
        )
        profile = await ProfileRepository(self.session).get_for_user(user_id)
        return DashboardSummary(
            total_jobs=await job_count(),
            analyzed_jobs=await job_count(Job.analysis_state == AnalysisState.ANALYZED.value),
            matched_jobs=await job_count(
                Job.compatibility_status == CompatibilityStatus.MATCHED.value
            ),
            jobs_needing_review=await job_count(
                (Job.analysis_state == AnalysisState.NEEDS_REVIEW.value)
                | (Job.compatibility_status == CompatibilityStatus.NEEDS_REVIEW.value)
            ),
            profile_completeness=profile_completeness(profile),
            portfolio_count=int(portfolio_count or 0),
        )
