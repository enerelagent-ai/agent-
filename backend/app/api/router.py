from fastapi import APIRouter

from app.api.routes import dashboard, health, listings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(listings.router)
api_router.include_router(dashboard.router)
