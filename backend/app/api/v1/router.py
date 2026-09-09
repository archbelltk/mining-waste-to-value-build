from fastapi import APIRouter

from app.api.v1.endpoints import organizations

api_router = APIRouter()
api_router.include_router(organizations.router, tags=["organizations"])
