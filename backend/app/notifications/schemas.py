"""Pydantic schemas for in-app notifications API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    severity: str | None = None
    title: str
    body: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    data: list[NotificationResponse]
    meta: dict[str, Any] = Field(default_factory=dict)


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkAllReadResponse(BaseModel):
    marked_read: int
