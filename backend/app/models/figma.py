"""Figma billing CSV import ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FigmaBillingImport(Base):
    __tablename__ = "billing_imports"
    __table_args__ = {"schema": "figma"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.tools.id", ondelete="CASCADE"),
        nullable=False,
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion.uploads.id", ondelete="SET NULL"),
        nullable=True,
    )
    package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.tool_packages.id", ondelete="SET NULL"),
        nullable=True,
    )
    usage_period_start: Mapped[date | None] = mapped_column(Date)
    usage_period_end: Mapped[date | None] = mapped_column(Date)
    total_seat_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    total_paid_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    full_seat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_seat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    user_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_summary: Mapped[dict | None] = mapped_column(JSONB)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FigmaBillingImportUser(Base):
    __tablename__ = "billing_import_users"
    __table_args__ = {"schema": "figma"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("figma.billing_imports.id", ondelete="CASCADE"),
        nullable=False,
    )
    figma_user_id: Mapped[str | None] = mapped_column(String(128))
    user_email: Mapped[str | None] = mapped_column(String(255))
    user_name: Mapped[str | None] = mapped_column(String(255))
    seat_type: Mapped[str] = mapped_column(String(32), nullable=False, default="full")
    seat_credits_used: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    paid_credits_used: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    seat_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    paid_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    matched_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
