"""phase 2 profile jobs and matching

Revision ID: 858c51dd8483
Revises: 6d619e588e80
Create Date: 2026-09-21 15:28:23.903602
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "858c51dd8483"
down_revision: str | Sequence[str] | None = "6d619e588e80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMPTY_JSON = sa.text("'[]'")


def upgrade() -> None:
    op.add_column(
        "job_matches",
        sa.Column("exact_matches", sa.JSON(), server_default=EMPTY_JSON, nullable=False),
    )
    op.add_column(
        "job_matches",
        sa.Column("related_matches", sa.JSON(), server_default=EMPTY_JSON, nullable=False),
    )
    op.add_column(
        "job_matches",
        sa.Column("relevant_claim_ids", sa.JSON(), server_default=EMPTY_JSON, nullable=False),
    )
    op.add_column(
        "job_matches",
        sa.Column("concerns", sa.JSON(), server_default=EMPTY_JSON, nullable=False),
    )
    op.add_column(
        "job_matches",
        sa.Column("explanation", sa.Text(), server_default="", nullable=False),
    )
    op.add_column("job_matches", sa.Column("model_used", sa.String(length=120)))
    op.add_column(
        "job_matches",
        sa.Column("formula_version", sa.String(length=40), server_default="v1", nullable=False),
    )
    op.add_column(
        "job_matches",
        sa.Column(
            "analysis_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_job_matches_analysis_timestamp"),
        "job_matches",
        ["analysis_timestamp"],
    )

    op.add_column(
        "jobs",
        sa.Column("status", sa.String(length=40), server_default="DISCOVERED", nullable=False),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "analysis_state", sa.String(length=40), server_default="PENDING", nullable=False
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "compatibility_status",
            sa.String(length=40),
            server_default="PENDING",
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_jobs_analysis_state"), "jobs", ["analysis_state"])
    op.create_index(
        op.f("ix_jobs_compatibility_status"), "jobs", ["compatibility_status"]
    )
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"])

    op.add_column(
        "portfolio_projects",
        sa.Column("skills", sa.JSON(), server_default=EMPTY_JSON, nullable=False),
    )
    op.add_column(
        "portfolio_projects",
        sa.Column(
            "verification_status",
            sa.String(length=24),
            server_default="UNVERIFIED",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_portfolio_projects_verification_status"),
        "portfolio_projects",
        ["verification_status"],
    )

    op.add_column("profiles", sa.Column("location", sa.String(length=240)))
    op.add_column("profiles", sa.Column("years_experience", sa.Numeric(5, 2)))
    for column_name in (
        "education",
        "certifications",
        "primary_skills",
        "secondary_skills",
        "programming_languages",
        "frameworks",
        "tools",
        "domains",
        "work_experience",
        "internships",
        "achievements",
    ):
        op.add_column(
            "profiles",
            sa.Column(column_name, sa.JSON(), server_default=EMPTY_JSON, nullable=False),
        )

    with op.batch_alter_table("skills") as batch_op:
        batch_op.add_column(
            sa.Column(
                "category", sa.String(length=40), server_default="PRIMARY", nullable=False
            )
        )
        batch_op.drop_constraint("uq_skills_user_name", type_="unique")
        batch_op.create_index(op.f("ix_skills_category"), ["category"])
        batch_op.create_unique_constraint(
            "uq_skills_user_name_category", ["user_id", "name", "category"]
        )

    op.add_column(
        "verified_claims",
        sa.Column(
            "category", sa.String(length=40), server_default="OTHER", nullable=False
        ),
    )
    op.add_column("verified_claims", sa.Column("notes", sa.Text()))
    op.create_index(
        op.f("ix_verified_claims_category"), "verified_claims", ["category"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_verified_claims_category"), table_name="verified_claims")
    op.drop_column("verified_claims", "notes")
    op.drop_column("verified_claims", "category")

    with op.batch_alter_table("skills") as batch_op:
        batch_op.drop_constraint("uq_skills_user_name_category", type_="unique")
        batch_op.drop_index(op.f("ix_skills_category"))
        batch_op.create_unique_constraint("uq_skills_user_name", ["user_id", "name"])
        batch_op.drop_column("category")

    for column_name in reversed(
        (
            "education",
            "certifications",
            "primary_skills",
            "secondary_skills",
            "programming_languages",
            "frameworks",
            "tools",
            "domains",
            "work_experience",
            "internships",
            "achievements",
        )
    ):
        op.drop_column("profiles", column_name)
    op.drop_column("profiles", "years_experience")
    op.drop_column("profiles", "location")

    op.drop_index(
        op.f("ix_portfolio_projects_verification_status"),
        table_name="portfolio_projects",
    )
    op.drop_column("portfolio_projects", "verification_status")
    op.drop_column("portfolio_projects", "skills")

    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_compatibility_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_analysis_state"), table_name="jobs")
    op.drop_column("jobs", "compatibility_status")
    op.drop_column("jobs", "analysis_state")
    op.drop_column("jobs", "status")

    op.drop_index(op.f("ix_job_matches_analysis_timestamp"), table_name="job_matches")
    for column_name in (
        "analysis_timestamp",
        "formula_version",
        "model_used",
        "explanation",
        "concerns",
        "relevant_claim_ids",
        "related_matches",
        "exact_matches",
    ):
        op.drop_column("job_matches", column_name)
