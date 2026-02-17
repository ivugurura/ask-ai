from fastapi import APIRouter
from app.services.ask import ask_question

router = APIRouter()

@router.post("/ask")
def ask(payload: dict):
    question = payload.get("question", "")
    language_id = payload.get("languageId")
    return ask_question(question, language_id)