from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis_client() -> Redis:
    return redis_client


async def close_redis_client() -> None:
    await redis_client.aclose()