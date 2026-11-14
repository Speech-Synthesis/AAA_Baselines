"""AAA Engine API v1 package."""

from fastapi import APIRouter

from .challenges import router as challenges_router
from .enroll import router as enroll_router
from .health import router as health_router
from .risk import router as risk_router
from .verify import router as verify_router

# Create v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(health_router, tags=["health"])
router.include_router(risk_router)
router.include_router(challenges_router)
router.include_router(enroll_router)
router.include_router(verify_router)
