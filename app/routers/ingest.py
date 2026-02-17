from fastapi import APIRouter
from app.services.ingest import ingest_unindexed_topics

router = APIRouter()

@router.post("/ingest")
def ingest():
    return ingest_unindexed_topics()