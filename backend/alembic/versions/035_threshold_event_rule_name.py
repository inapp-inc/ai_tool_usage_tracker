"""Preserve threshold event history when alert rules are removed."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "035_threshold_event_rule_name"
down_revision: Union[str, None] = "034_figma_billing_import"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "threshold_events",
        sa.Column("rule_name", sa.String(100), nullable=True),
        schema="notifications",
    )
    op.execute(
        """
        UPDATE notifications.threshold_events e
        SET rule_name = t.name
        FROM admin.thresholds t
        WHERE e.threshold_id = t.id
        """
    )
    op.alter_column(
        "threshold_events",
        "rule_name",
        existing_type=sa.String(100),
        nullable=False,
        schema="notifications",
    )

    op.alter_column(
        "threshold_events",
        "threshold_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
        schema="notifications",
    )

    op.drop_constraint(
        "threshold_events_threshold_id_fkey",
        "threshold_events",
        schema="notifications",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "threshold_events_threshold_id_fkey",
        "threshold_events",
        "thresholds",
        ["threshold_id"],
        ["id"],
        source_schema="notifications",
        referent_schema="admin",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "threshold_events_threshold_id_fkey",
        "threshold_events",
        schema="notifications",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "threshold_events_threshold_id_fkey",
        "threshold_events",
        "thresholds",
        ["threshold_id"],
        ["id"],
        source_schema="notifications",
        referent_schema="admin",
        ondelete="CASCADE",
    )
    op.alter_column(
        "threshold_events",
        "threshold_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
        schema="notifications",
    )
    op.drop_column("threshold_events", "rule_name", schema="notifications")
