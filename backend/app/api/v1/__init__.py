"""AAA Engine API v1 package."""

from fastapi import APIRouter

from .health import router as health_router
from .risk import router as risk_router

# Create v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(health_router, tags=["health"])
router.include_router(risk_router)
