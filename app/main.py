from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import ALLOWED_ORIGINS
from app.routers.ingest import router as ingest_router
from app.routers.ask import router as ask_router

app = FastAPI(title="Ivugurura Chatbot Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(ask_router)