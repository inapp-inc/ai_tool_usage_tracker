"""GitHub Copilot productivity analytics ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotOrganization(Base):
    __tablename__ = "copilot_organizations"
    __table_args__ = {"schema": "copilot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.tools.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_name: Mapped[str | None] = mapped_column(String(255))
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    subscription_type: Mapped[str | None] = mapped_column(String(64))
    monthly_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CopilotUserUsage(Base):
    __tablename__ = "copilot_user_usage"
    __table_args__ = {"schema": "copilot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin.teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copilot.copilot_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    user_login: Mapped[str] = mapped_column(String(255), nullable=False)
    user_email: Mapped[str | None] = mapped_column(String(255))
    user_name: Mapped[str | None] = mapped_column(String(255))
    feature: Mapped[str] = mapped_column(String(64), nullable=False, default="all")
    editor: Mapped[str] = mapped_column(String(64), nullable=False, default="all")
    language: Mapped[str] = mapped_column(String(64), nullable=False, default="all")
    active_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    chat_turns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suggestions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    acceptances_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    acceptance_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    lines_suggested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lines_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CopilotSeat(Base):
    __tablename__ = "copilot_seats"
    __table_args__ = {"schema": "copilot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copilot.copilot_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_login: Mapped[str] = mapped_column(String(255), nullable=False)
    user_email: Mapped[str | None] = mapped_column(String(255))
    seat_status: Mapped[str] = mapped_column(String(32), nullable=False, default="assigned")
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    monthly_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
