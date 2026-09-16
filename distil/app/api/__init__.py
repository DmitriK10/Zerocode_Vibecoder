"""HTTP API package.

Exposes a single :data:`api_router` that includes every sub-router.
"""

from fastapi import APIRouter

from app.api.routers import actions, audit, extract, health, texts

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(texts.router, prefix="/api", tags=["texts"])
api_router.include_router(extract.router, prefix="/api", tags=["extraction"])
api_router.include_router(actions.router, prefix="/api", tags=["actions"])
api_router.include_router(audit.router, prefix="/api", tags=["audit"])

__all__ = ["api_router"]