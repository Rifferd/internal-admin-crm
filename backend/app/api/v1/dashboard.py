from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.common.enums import UserRole
from app.core.redis import get_redis_client
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> DashboardStatsResponse:
    service = DashboardService(session, redis)
    return await service.get_stats()