from app.db.base import Base

EXPECTED_TABLES = {
    "users",
    "profiles",
    "skills",
    "portfolio_projects",
    "verified_claims",
    "jobs",
    "job_requirements",
    "clients",
    "client_sources",
    "client_facts",
    "client_analyses",
    "job_matches",
    "evidence_links",
    "portfolio_selections",
    "proposals",
    "proposal_versions",
    "applications",
    "application_events",
    "messages",
    "interviews",
    "contracts",
    "agent_tasks",
    "agent_runs",
    "notifications",
    "settings",
    "audit_logs",
}


def test_metadata_contains_the_planned_schema():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_jobs_have_source_scoped_deduplication():
    constraints = Base.metadata.tables["jobs"].constraints
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("source", "source_job_id") in unique_columns
