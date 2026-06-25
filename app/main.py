from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.settings import ALLOWED_ORIGINS
from app.routers import api_router
from app.schemas.common import server_response

app = FastAPI(title="Ivugurura Chatbot Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/ai/v1")


@app.get("/ai/health")
def health_check():
    return server_response(200, message="Healthy")


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return server_response(404, message="You seem to be lost. The endpoint you are looking for does not exist.")
    return server_response(exc.status_code, message=exc.detail)


@app.exception_handler(Exception)
def unhandled_exception_handler(_request: Request, exc: Exception):
    return server_response(500, message=f"Unexpected error: {exc}")