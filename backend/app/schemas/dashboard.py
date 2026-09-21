from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_jobs: int
    analyzed_jobs: int
    matched_jobs: int
    jobs_needing_review: int
    profile_completeness: int = Field(ge=0, le=100)
    portfolio_count: int
