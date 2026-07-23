from fastapi import APIRouter

from knowledge_isle_api.api.routes.auth import router as auth_router
from knowledge_isle_api.api.routes.dashboard import router as dashboard_router
from knowledge_isle_api.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
