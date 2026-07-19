"""Role-specific company and candidate revival data."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0004"
down_revision = "20260719_0003"
branch_labels = None
depends_on = None


def add_column_if_missing(table: str, column: sa.Column) -> None:
    existing = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("companies", sa.Column("revival_status", sa.String(length=24), nullable=False, server_default="active"))
    add_column_if_missing("companies", sa.Column("last_contact_date", sa.Date(), nullable=True))
    add_column_if_missing("companies", sa.Column("last_job_date", sa.Date(), nullable=True))
    add_column_if_missing("companies", sa.Column("dormant_job_title", sa.String(length=180), nullable=True))
    add_column_if_missing("companies", sa.Column("dormancy_reason", sa.Text(), nullable=True))
    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("companies")}
    if "ix_companies_revival_status" not in indexes:
        op.create_index("ix_companies_revival_status", "companies", ["revival_status"])


def downgrade() -> None:
    op.drop_index("ix_companies_revival_status", table_name="companies")
    op.drop_column("companies", "dormancy_reason")
    op.drop_column("companies", "dormant_job_title")
    op.drop_column("companies", "last_job_date")
    op.drop_column("companies", "last_contact_date")
    op.drop_column("companies", "revival_status")
