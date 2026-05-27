from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.redis import get_redis_client
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=AuthUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> AuthUserResponse:
    service = AuthService(session, redis)
    user = await service.register(data)

    return AuthUserResponse(user=user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> TokenResponse:
    service = AuthService(session, redis)

    client_ip = request.client.host if request.client else None

    return await service.login(
        data=data,
        client_ip=client_ip,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> TokenResponse:
    service = AuthService(session, redis)
    return await service.refresh(data)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: LogoutRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> MessageResponse:
    service = AuthService(session, redis)
    await service.logout(data)

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=AuthUserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> AuthUserResponse:
    return AuthUserResponse(user=current_user)