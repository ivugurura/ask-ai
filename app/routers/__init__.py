from fastapi import APIRouter

from app.routers.ask import router as ask_router
from app.routers.ingest import router as ingest_router

api_router = APIRouter()

api_router.include_router(ingest_router)
api_router.include_router(ask_router)
