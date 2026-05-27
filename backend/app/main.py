from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.redis import close_redis_client, redis_client
from app.db.session import async_session_maker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await close_redis_client()


app = FastAPI(
    title="Internal Admin CRM",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def database_health_check() -> dict[str, str]:
    async with async_session_maker() as session:
        await session.execute(text("SELECT 1"))

    return {"database": "ok"}


@app.get("/health/redis")
async def redis_health_check() -> dict[str, str]:
    await redis_client.ping()

    return {"redis": "ok"}