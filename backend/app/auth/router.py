"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, RefreshRequest, TokenResponse, UserProfile
from app.auth.service import AuthService, AuthenticatedUser
from app.core.rate_limit import LoginRateLimiter
from app.db.session import get_session

router = APIRouter(prefix="/auth", tags=["Auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    operation_id="login",
)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Validate credentials and return JWT access token."""
    rate_limiter = LoginRateLimiter()
    email = AuthService.normalize_login_email(str(body.email))
    client_ip = _client_ip(request)

    try:
        if await rate_limiter.is_blocked(client_ip, email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
            )

        service = AuthService(session)
        user = await service.authenticate(email, body.password)
        if user is None:
            await rate_limiter.record_failure(client_ip, email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
            )

        return await service.issue_tokens(user)
    finally:
        await rate_limiter.close()


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    operation_id="refreshToken",
)
async def refresh_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Exchange refresh token for new access and refresh tokens."""
    service = AuthService(session)
    try:
        return await service.refresh(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing, expired, or invalid.",
        ) from exc


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
    operation_id="getCurrentUser",
)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserProfile:
    """Return authenticated user profile."""
    service = AuthService(session)
    profile = await service.get_profile(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing, expired, or invalid.",
        )
    return profile
