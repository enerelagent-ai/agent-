from fastapi import APIRouter

from app.api.routes import health, listings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(listings.router)
