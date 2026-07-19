"""Candidate workflow, parallel processes, and explainable matching axes."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0002"
down_revision = "20260719_0001"
branch_labels = None
depends_on = None


def add_column_if_missing(table: str, column: sa.Column) -> None:
    existing = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("candidates", sa.Column("email", sa.String(length=180), nullable=True))
    add_column_if_missing("candidates", sa.Column("remote_preference", sa.String(length=24), nullable=False, server_default="flexible"))
    add_column_if_missing("candidates", sa.Column("specialization", sa.String(length=100), nullable=True))
    add_column_if_missing("candidates", sa.Column("specialization_years", sa.Float(), nullable=False, server_default="0"))
    add_column_if_missing("candidates", sa.Column("recent_tenure_years", sa.Float(), nullable=False, server_default="0"))
    add_column_if_missing("candidates", sa.Column("internal_parallel_count", sa.Integer(), nullable=False, server_default="0"))
    add_column_if_missing("candidates", sa.Column("external_parallel_count", sa.Integer(), nullable=False, server_default="0"))
    add_column_if_missing("candidates", sa.Column("current_processes", sa.JSON(), nullable=False, server_default="[]"))
    add_column_if_missing("candidates", sa.Column("skill_sheet_filename", sa.String(length=240), nullable=True))
    add_column_if_missing("candidates", sa.Column("skill_sheet_path", sa.String(length=500), nullable=True))
    add_column_if_missing("candidates", sa.Column("skill_sheet_uploaded_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("candidates", sa.Column("skill_sheet_text", sa.Text(), nullable=True))
    add_column_if_missing("companies", sa.Column("ra_owner", sa.String(length=100), nullable=False, server_default="RA 太郎"))
    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("companies")}
    if "ix_companies_ra_owner" not in indexes:
        op.create_index("ix_companies_ra_owner", "companies", ["ra_owner"])
    add_column_if_missing("jobs", sa.Column("preferred_age_min", sa.Integer(), nullable=True))
    add_column_if_missing("jobs", sa.Column("preferred_age_max", sa.Integer(), nullable=True))
    add_column_if_missing("jobs", sa.Column("remote_mode", sa.String(length=24), nullable=False, server_default="onsite"))
    add_column_if_missing("jobs", sa.Column("specialization", sa.String(length=100), nullable=True))
    add_column_if_missing("jobs", sa.Column("min_specialization_years", sa.Float(), nullable=False, server_default="0"))
    add_column_if_missing("matches", sa.Column("age_score", sa.Integer(), nullable=False, server_default="0"))
    add_column_if_missing("matches", sa.Column("remote_score", sa.Integer(), nullable=False, server_default="0"))
    add_column_if_missing("matches", sa.Column("specialization_score", sa.Integer(), nullable=False, server_default="0"))
    add_column_if_missing("matches", sa.Column("stability_score", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("matches", "stability_score")
    op.drop_column("matches", "specialization_score")
    op.drop_column("matches", "remote_score")
    op.drop_column("matches", "age_score")
    op.drop_column("jobs", "min_specialization_years")
    op.drop_column("jobs", "specialization")
    op.drop_column("jobs", "remote_mode")
    op.drop_column("jobs", "preferred_age_max")
    op.drop_column("jobs", "preferred_age_min")
    op.drop_index("ix_companies_ra_owner", table_name="companies")
    op.drop_column("companies", "ra_owner")
    op.drop_column("candidates", "skill_sheet_text")
    op.drop_column("candidates", "skill_sheet_uploaded_at")
    op.drop_column("candidates", "skill_sheet_path")
    op.drop_column("candidates", "skill_sheet_filename")
    op.drop_column("candidates", "current_processes")
    op.drop_column("candidates", "external_parallel_count")
    op.drop_column("candidates", "internal_parallel_count")
    op.drop_column("candidates", "recent_tenure_years")
    op.drop_column("candidates", "specialization_years")
    op.drop_column("candidates", "specialization")
    op.drop_column("candidates", "remote_preference")
    op.drop_column("candidates", "email")
