"""Admin ORM models."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Team(Base):
    """Business unit for usage attribution (admin.teams)."""

    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_teams_org_name"),
        {"schema": "admin"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_budget: Mapped[int | None] = mapped_column(BigInteger)
    cost_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    tool_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TeamTool(Base):
    """Per-team pricing override for an assigned tool (admin.team_tools)."""

    __tablename__ = "team_tools"
    __table_args__ = (
        UniqueConstraint("team_id", "tool_id", name="uq_team_tools_team_tool"),
        {"schema": "admin"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.tools.id", ondelete="CASCADE"),
        nullable=False,
    )
    pricing_model: Mapped[str | None] = mapped_column(String(32))
    token_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    output_token_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    cost_per_seat: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    seat_count: Mapped[int | None] = mapped_column(Integer)
    package_allowance: Mapped[int | None] = mapped_column(BigInteger)
    overage_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    plan_name: Mapped[str | None] = mapped_column(String(200))
    pricing_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.tool_packages.id", ondelete="SET NULL"),
        nullable=True,
    )
    subscription_start: Mapped[date | None] = mapped_column(Date)
    subscription_end: Mapped[date | None] = mapped_column(Date)
    monthly_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    alert_threshold: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ToolPackage(Base):
    """Predefined subscription package for a catalogue tool (admin.tool_packages)."""

    __tablename__ = "tool_packages"
    __table_args__ = (
        UniqueConstraint("tool_id", "package_name", name="uq_tool_packages_tool_name"),
        {"schema": "admin"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.tools.id", ondelete="CASCADE"),
        nullable=False,
    )
    package_name: Mapped[str] = mapped_column(String(128), nullable=False)
    billing_type: Mapped[str] = mapped_column(String(32), nullable=False)
    monthly_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    yearly_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    seat_limit: Mapped[int | None] = mapped_column(Integer)
    token_limit: Mapped[int | None] = mapped_column(BigInteger)
    request_limit: Mapped[int | None] = mapped_column(BigInteger)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TeamMembership(Base):
    """User ↔ team assignment (admin.team_memberships)."""

    __tablename__ = "team_memberships"
    __table_args__ = {"schema": "admin"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderParent(Base):
    """Vendor / platform company (admin.provider_parents)."""

    __tablename__ = "provider_parents"
    __table_args__ = {"schema": "admin"}

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    providers: Mapped[list["Provider"]] = relationship(back_populates="parent")


class Provider(Base):
    """Configurable AI provider lookup (admin.providers)."""

    __tablename__ = "providers"
    __table_args__ = {"schema": "admin"}

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(512))
    parent_slug: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("admin.provider_parents.slug", ondelete="SET NULL"),
        nullable=True,
    )
    adapter_key: Mapped[str | None] = mapped_column(String(64))
    requires_api_endpoint: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    built_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    parent: Mapped["ProviderParent | None"] = relationship(back_populates="providers")


class Tool(Base):
    """AI tool configuration with encrypted API credential (admin.tools)."""

    __tablename__ = "tools"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_tools_org_name"),
        {"schema": "admin"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    billing_type: Mapped[str] = mapped_column(String(32), nullable=False, default="TOKEN_BASED")
    description: Mapped[str | None] = mapped_column(String(500))
    pricing_model: Mapped[str] = mapped_column(String(32), nullable=False)
    token_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    package_allowance: Mapped[int | None] = mapped_column(BigInteger)
    overage_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    pricing_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_token_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cost_total: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    balance_tokens: Mapped[int | None] = mapped_column(BigInteger)
    member_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sync_status: Mapped[str] = mapped_column(String(16), nullable=False, default="inactive")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_error: Mapped[str | None] = mapped_column(Text)
    credential_label: Mapped[str | None] = mapped_column(String(100))
    credential_environment: Mapped[str] = mapped_column(
        String(16), nullable=False, default="production"
    )
    credential_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rotation_reminder_days: Mapped[int | None] = mapped_column(BigInteger)
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    api_endpoint: Mapped[str | None] = mapped_column(String(512))
    integration_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    catalogue_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    built_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
