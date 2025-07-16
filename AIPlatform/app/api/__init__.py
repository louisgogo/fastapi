"""
API routes package.
"""

from fastapi import APIRouter

from .v1 import api_router as v1_router

# Create main API router
api_router = APIRouter()

# Include API versions
api_router.include_router(v1_router, prefix="/v1")

__all__ = ["api_router"] 