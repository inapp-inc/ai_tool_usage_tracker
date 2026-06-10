"""Initial PostgreSQL schemas per database.md (TASK-INF-004)."""

from typing import Sequence, Union

from alembic import op

revision: str = "001_initial_schemas"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMAS = (
    "auth",
    "admin",
    "ingestion",
    "usage",
    "notifications",
    "reporting",
    "audit",
)


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def downgrade() -> None:
    for schema in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
