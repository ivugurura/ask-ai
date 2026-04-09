from sentence_transformers import SentenceTransformer
from pgvector import Vector
import requests

from app.db import get_conn
from app.settings import (
    EMBEDDING_MODEL,
    TOP_K,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    SUMMARY_MAX_CHARS,
    RELEVANCE_MAX_DISTANCE,
)

model = SentenceTransformer(EMBEDDING_MODEL)

PROMPT_BY_LANGUAGE = {
    "en": {
        "intro": (
            "You are a helpful assistant. Summarize the content below in 2-3 sentences. "
            "Focus on answering the question directly."
        ),
        "question_label": "Question",
        "content_label": "Content",
    },
    "fr": {
        "intro": (
            "Vous etes un assistant utile. Resumez le contenu ci-dessous en 2 a 3 phrases. "
            "Concentrez-vous sur une reponse directe a la question."
        ),
        "question_label": "Question",
        "content_label": "Contenu",
    },
    "kn": {
        "intro": (
            "Nk umu assistant. Mu nteruro 2-3, sobanura ibi bikurikira. "
            "Wite cyane ku gusubiza ikibazo neza."
        ),
        "question_label": "Ikibazo",
        "content_label": "Ibikubiye mu nyandiko",
    },
    "sw": {
        "intro": (
            "Wewe ni msaidizi mwenye msaada. Fupisha maudhui yafuatayo kwa sentensi 2 hadi 3. "
            "Lenga kujibu swali moja kwa moja."
        ),
        "question_label": "Swali",
        "content_label": "Maudhui",
    },
}


def _summarize_with_ollama(question: str, context: str, lang: str = "en") -> str:
    if not context.strip():
        return ""

    language_key = (lang or "en").lower()
    prompt_config = PROMPT_BY_LANGUAGE.get(language_key, PROMPT_BY_LANGUAGE["en"])

    prompt = (
        f"{prompt_config['intro']}\n\n"
        f"{prompt_config['question_label']}: {question}\n\n"
        f"{prompt_config['content_label']}:\n{context}\n"
    )

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.RequestException as e:
        print(f"Error occurred while summarizing with Ollama: {e}")
        return ""

def ask_question(
    question: str,
    language_id: int | None = None,
    lan: str = "en",
):
    query_emb = Vector(model.encode([question])[0].tolist())
    conn = get_conn()

    with conn.cursor() as cur:
        if language_id:
            cur.execute("""
                SELECT tc.text, t.title, t.slug, tc.embedding <=> %s AS distance
                FROM topic_chunks tc
                JOIN topics t ON tc."topicId" = t.id
                WHERE tc."languageId" = %s
                ORDER BY distance
                LIMIT %s
            """, (query_emb, language_id, TOP_K))
        else:
            cur.execute("""
                SELECT tc.text, t.title, t.slug, tc.embedding <=> %s AS distance
                FROM topic_chunks tc
                JOIN topics t ON tc."topicId" = t.id
                ORDER BY distance
                LIMIT %s
            """, (query_emb, TOP_K))

        rows = cur.fetchall()

    conn.close()

    filtered_rows = [r for r in rows if r[3] <= RELEVANCE_MAX_DISTANCE]
    chunks = [r[0] for r in filtered_rows]
    raw_context = "\n\n".join(chunks)
    context = raw_context[:SUMMARY_MAX_CHARS]
    summary = _summarize_with_ollama(question, context, lan)

    sources_by_slug = {}
    print(summary)
    for _text, title, slug, _distance in filtered_rows:
        if slug not in sources_by_slug:
            sources_by_slug[slug] = {"title": title, "slug": slug}

    return {
        "answer": summary or raw_context,
        "sources": list(sources_by_slug.values()),
    }