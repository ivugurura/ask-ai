from fastapi import APIRouter
from app.schemas.common import CommonResponse, server_response
from app.services.ingest import ingest_unindexed_topics

router = APIRouter()

@router.post("/ingest", response_model=CommonResponse)
def ingest():
    result = ingest_unindexed_topics()
    return server_response(200, data=result, message="Ingestion complete")