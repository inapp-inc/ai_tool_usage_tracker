"""Pydantic schemas for tenant organization API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class OrganizationInitialMemberRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=200)
    role_name: str = Field(
        default="team_member",
        pattern=r"^(org_admin|team_admin|team_member|finance_viewer|auditor)$",
    )


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    initial_member: OrganizationInitialMemberRequest | None = None


class OrganizationCreateResponse(BaseModel):
    organization: OrganizationResponse
    initial_user_id: UUID | None = None
    initial_user_email: EmailStr | None = None


class OrganizationListResponse(BaseModel):
    data: list[OrganizationResponse]
