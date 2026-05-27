from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.clients import router as clients_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.deals import router as deals_router
from app.api.v1.tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(clients_router)
api_router.include_router(deals_router)
api_router.include_router(tasks_router)
api_router.include_router(dashboard_router)