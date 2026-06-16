"""007_role_permissions

Revision ID: 007_role_permissions
Revises: 006_cursor_provider_url
Create Date: 2026-06-16
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007_role_permissions"
down_revision: Union[str, None] = "006_cursor_provider_url"
branch_labels = None
depends_on = None

CONFIGURABLE_ROLES = ["team_admin", "finance_viewer", "auditor"]

# (role, page, can_read, can_write)
DEFAULT_PERMISSIONS: list[tuple[str, str, bool, bool]] = [
    ("team_admin",     "insights",          True,  False),
    ("team_admin",     "admin:teams",       True,  False),
    ("team_admin",     "admin:groups",      True,  True),
    ("team_admin",     "admin:members",     True,  True),
    ("team_admin",     "admin:credentials", False, False),
    ("team_admin",     "alerts",            True,  True),
    ("team_admin",     "uploads",           True,  True),
    ("team_admin",     "audit",             False, False),
    ("finance_viewer", "insights",          True,  False),
    ("finance_viewer", "admin:teams",       False, False),
    ("finance_viewer", "admin:groups",      False, False),
    ("finance_viewer", "admin:members",     False, False),
    ("finance_viewer", "admin:credentials", False, False),
    ("finance_viewer", "alerts",            False, False),
    ("finance_viewer", "uploads",           False, False),
    ("finance_viewer", "audit",             False, False),
    ("auditor",        "insights",          True,  False),
    ("auditor",        "admin:teams",       False, False),
    ("auditor",        "admin:groups",      False, False),
    ("auditor",        "admin:members",     False, False),
    ("auditor",        "admin:credentials", False, False),
    ("auditor",        "alerts",            False, False),
    ("auditor",        "uploads",           False, False),
    ("auditor",        "audit",             True,  False),
]


def upgrade() -> None:
    op.create_table(
        "role_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", UUID(as_uuid=True),
                  sa.ForeignKey("auth.organizations.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("page", sa.String(100), nullable=False),
        sa.Column("can_read",  sa.Boolean, nullable=False, server_default="false"),
        sa.Column("can_write", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("updated_by", UUID(as_uuid=True),
                  sa.ForeignKey("auth.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("organization_id", "role", "page", name="uq_role_perm"),
        schema="auth",
    )
    op.create_index(
        "ix_role_permissions_org_role",
        "role_permissions", ["organization_id", "role"],
        schema="auth",
    )

    # Seed defaults for all existing orgs
    conn = op.get_bind()
    orgs = conn.execute(sa.text("SELECT id FROM auth.organizations")).fetchall()
    if orgs:
        rows = [
            {
                "organization_id": str(org[0]),
                "role": role,
                "page": page,
                "can_read": can_read,
                "can_write": can_write,
            }
            for org in orgs
            for role, page, can_read, can_write in DEFAULT_PERMISSIONS
        ]
        conn.execute(
            sa.text(
                "INSERT INTO auth.role_permissions "
                "(organization_id, role, page, can_read, can_write) "
                "VALUES (:organization_id, :role, :page, :can_read, :can_write) "
                "ON CONFLICT (organization_id, role, page) DO NOTHING"
            ),
            rows,
        )


def downgrade() -> None:
    op.drop_index("ix_role_permissions_org_role",
                  table_name="role_permissions", schema="auth")
    op.drop_table("role_permissions", schema="auth")
