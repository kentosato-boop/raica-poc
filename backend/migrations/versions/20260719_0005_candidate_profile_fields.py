"""Add operational candidate profile fields."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0005"
down_revision = "20260719_0004"
branch_labels = None
depends_on = None


def add_column_if_missing(table: str, column: sa.Column) -> None:
    existing = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("candidates", sa.Column("current_location", sa.String(length=120), nullable=True))
    add_column_if_missing("candidates", sa.Column("desired_locations", sa.JSON(), nullable=False, server_default="[]"))
    add_column_if_missing("candidates", sa.Column("available_from", sa.Date(), nullable=True))
    add_column_if_missing("candidates", sa.Column("work_authorization", sa.String(length=120), nullable=True))
    add_column_if_missing("candidates", sa.Column("source_channel", sa.String(length=80), nullable=True))
    add_column_if_missing("candidates", sa.Column("preferred_contact_channel", sa.String(length=40), nullable=True))
    add_column_if_missing("candidates", sa.Column("consent_status", sa.String(length=24), nullable=False, server_default="confirmed"))


def downgrade() -> None:
    op.drop_column("candidates", "consent_status")
    op.drop_column("candidates", "preferred_contact_channel")
    op.drop_column("candidates", "source_channel")
    op.drop_column("candidates", "work_authorization")
    op.drop_column("candidates", "available_from")
    op.drop_column("candidates", "desired_locations")
    op.drop_column("candidates", "current_location")
