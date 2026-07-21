from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings

# No authentication yet — single-user local dev tool. Add protection
# before any public/shared deployment.
app = FastAPI(title="Ulaanbaatar Real Estate Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
