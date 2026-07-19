"""Candidate compensation, work modes, and dashboard ball ownership."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0003"
down_revision = "20260719_0002"
branch_labels = None
depends_on = None


def add_column_if_missing(table: str, column: sa.Column) -> None:
    existing = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("candidates", sa.Column("current_salary_million", sa.Float(), nullable=True))
    add_column_if_missing("candidates", sa.Column("work_style_options", sa.JSON(), nullable=False, server_default="[]"))
    add_column_if_missing("action_items", sa.Column("ball_owner", sa.String(length=12), nullable=False, server_default="mine"))
    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("action_items")}
    if "ix_action_items_ball_owner" not in indexes:
        op.create_index("ix_action_items_ball_owner", "action_items", ["ball_owner"])


def downgrade() -> None:
    op.drop_index("ix_action_items_ball_owner", table_name="action_items")
    op.drop_column("action_items", "ball_owner")
    op.drop_column("candidates", "work_style_options")
    op.drop_column("candidates", "current_salary_million")
