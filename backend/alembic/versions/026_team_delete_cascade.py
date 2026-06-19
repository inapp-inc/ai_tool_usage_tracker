"""026 — cascade-delete team-associated usage, uploads, and alert history."""

from typing import Sequence, Union

from alembic import op

revision: str = "026_team_delete_cascade"
down_revision: Union[str, None] = "025_usage_event_cache_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _replace_team_fk(
    *,
    table: str,
    schema: str,
    ondelete: str,
) -> None:
    constraint = f"{table}_team_id_fkey"
    op.drop_constraint(constraint, table, schema=schema, type_="foreignkey")
    op.create_foreign_key(
        constraint,
        table,
        "teams",
        ["team_id"],
        ["id"],
        source_schema=schema,
        referent_schema="admin",
        ondelete=ondelete,
    )


def upgrade() -> None:
    _replace_team_fk(table="usage_events", schema="usage", ondelete="CASCADE")
    _replace_team_fk(table="uploads", schema="ingestion", ondelete="CASCADE")
    _replace_team_fk(table="threshold_events", schema="notifications", ondelete="CASCADE")


def downgrade() -> None:
    _replace_team_fk(table="usage_events", schema="usage", ondelete="SET NULL")
    _replace_team_fk(table="uploads", schema="ingestion", ondelete="SET NULL")
    _replace_team_fk(table="threshold_events", schema="notifications", ondelete="SET NULL")
