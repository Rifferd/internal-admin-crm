import hashlib

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_refresh_token_blacklist_key,
    get_token_ttl_seconds,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)


class AuthService:
    LOGIN_RATE_LIMIT_ATTEMPTS = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60

    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis
        self.user_repository = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        existing_user = await self.user_repository.get_by_email(str(data.email))

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        user = User(
            email=str(data.email),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )

        user = await self.user_repository.create(user)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def login(
        self,
        data: LoginRequest,
        client_ip: str | None,
    ) -> TokenResponse:
        await self._check_login_rate_limit(
            email=str(data.email),
            client_ip=client_ip,
        )

        user = await self.user_repository.get_by_email(str(data.email))

        if user is None:
            await self._register_failed_login_attempt(
                email=str(data.email),
                client_ip=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        if not verify_password(data.password, user.password_hash):
            await self._register_failed_login_attempt(
                email=str(data.email),
                client_ip=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        await self._clear_login_rate_limit(
            email=str(data.email),
            client_ip=client_ip,
        )

        return self._create_token_pair(user)

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        payload = decode_refresh_token(data.refresh_token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if await self._is_refresh_token_blacklisted(data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        user = await self.user_repository.get_by_id(int(user_id))

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        return self._create_token_pair(user)

    async def logout(self, data: LogoutRequest) -> None:
        payload = decode_refresh_token(data.refresh_token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        await self._blacklist_refresh_token(data.refresh_token, payload)

    def _create_token_pair(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(subject=str(user.id)),
            refresh_token=create_refresh_token(subject=str(user.id)),
        )

    async def _is_refresh_token_blacklisted(self, refresh_token: str) -> bool:
        key = get_refresh_token_blacklist_key(refresh_token)
        return await self.redis.exists(key) == 1

    async def _blacklist_refresh_token(
        self,
        refresh_token: str,
        payload: dict,
    ) -> None:
        key = get_refresh_token_blacklist_key(refresh_token)
        ttl = get_token_ttl_seconds(payload)

        if ttl <= 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        await self.redis.setex(key, ttl, "1")

    async def _check_login_rate_limit(
        self,
        *,
        email: str,
        client_ip: str | None,
    ) -> None:
        key = self._get_login_rate_limit_key(email=email, client_ip=client_ip)

        attempts_raw = await self.redis.get(key)
        attempts = int(attempts_raw) if attempts_raw is not None else 0

        if attempts >= self.LOGIN_RATE_LIMIT_ATTEMPTS:
            ttl = await self.redis.ttl(key)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {ttl} seconds.",
            )

    async def _register_failed_login_attempt(
        self,
        *,
        email: str,
        client_ip: str | None,
    ) -> None:
        key = self._get_login_rate_limit_key(email=email, client_ip=client_ip)

        attempts = await self.redis.incr(key)

        if attempts == 1:
            await self.redis.expire(key, self.LOGIN_RATE_LIMIT_WINDOW_SECONDS)

    async def _clear_login_rate_limit(
        self,
        *,
        email: str,
        client_ip: str | None,
    ) -> None:
        key = self._get_login_rate_limit_key(email=email, client_ip=client_ip)
        await self.redis.delete(key)

    def _get_login_rate_limit_key(
        self,
        *,
        email: str,
        client_ip: str | None,
    ) -> str:
        normalized_email = email.lower().strip()
        normalized_ip = client_ip or "unknown"

        raw_key = f"{normalized_email}:{normalized_ip}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        return f"auth:login_rate_limit:{key_hash}"