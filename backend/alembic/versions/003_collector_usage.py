"""Collector configs, runs, and token usage events (token collector MVP)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_collector_usage"
down_revision: Union[str, None] = "002_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collector_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("api_token_ciphertext", sa.Text(), nullable=False),
        sa.Column("pull_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "pull_interval_minutes >= 5 AND pull_interval_minutes <= 1440",
            name="ck_collector_pull_interval",
        ),
        schema="ingestion",
    )

    op.create_table(
        "collector_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "collector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ingestion.collector_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("records_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema="ingestion",
    )
    op.create_index(
        "ix_collector_runs_collector_id",
        "collector_runs",
        ["collector_id"],
        schema="ingestion",
    )

    op.create_table(
        "usage_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "collector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ingestion.collector_configs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "estimated_cost",
            sa.Numeric(18, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column("vendor_event_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("input_tokens >= 0", name="ck_usage_input_tokens"),
        sa.CheckConstraint("output_tokens >= 0", name="ck_usage_output_tokens"),
        sa.CheckConstraint("total_tokens >= 0", name="ck_usage_total_tokens"),
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_occurred_at",
        "usage_events",
        ["occurred_at"],
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_collector_id",
        "usage_events",
        ["collector_id"],
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_vendor_event",
        "usage_events",
        ["provider", "vendor_event_id"],
        unique=True,
        schema="usage",
        postgresql_where=sa.text("vendor_event_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("usage_events", schema="usage")
    op.drop_table("collector_runs", schema="ingestion")
    op.drop_table("collector_configs", schema="ingestion")
