"""Add candidate inflow (source entry) date."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0006"
down_revision = "20260719_0005"
branch_labels = None
depends_on = None


def add_column_if_missing(table: str, column: sa.Column) -> None:
    existing = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("candidates", sa.Column("inflow_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "inflow_date")
