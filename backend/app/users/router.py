"""Users REST API — org member admin (/users)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.auth import User
from app.users.schemas import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.users.service import ADMIN_ROLES, UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def require_user_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(require_user_admin),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    return await service.list_users(current_user.organization_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    current_user: User = Depends(require_user_admin),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.create_user(current_user.organization_id, body)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_user_admin),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_user(current_user.organization_id, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    current_user: User = Depends(require_user_admin),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.update_user(current_user.organization_id, user_id, body)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_user_admin),
    service: UserService = Depends(get_user_service),
) -> None:
    await service.deactivate_user(current_user.organization_id, user_id)
