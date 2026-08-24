from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.api.routes import complexes, dashboard, health, listings

api_router = APIRouter()
# /health stays open (unauthenticated) so uptime checks don't need
# credentials -- it exposes nothing beyond a static "ok".
api_router.include_router(health.router)
api_router.include_router(listings.router, dependencies=[Depends(require_admin)])
api_router.include_router(complexes.router, dependencies=[Depends(require_admin)])
api_router.include_router(dashboard.router, dependencies=[Depends(require_admin)])
