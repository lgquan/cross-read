from fastapi import APIRouter

from cross_read.api.routes import shares, status, system

api_router = APIRouter()
api_router.include_router(status.router)
api_router.include_router(shares.router)
api_router.include_router(system.router)
