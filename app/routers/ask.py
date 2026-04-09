from fastapi import APIRouter
from app.schemas.common import CommonResponse, server_response
from app.services.ask import ask_question

router = APIRouter()

@router.post("/ask", response_model=CommonResponse)
def ask(payload: dict):
    question = payload.get("question", "")
    language_id = payload.get("languageId")
    lang = payload.get("lang", "en")

    result = ask_question(question, language_id, lang)
    return server_response(200, data=result, message="Question answered")
