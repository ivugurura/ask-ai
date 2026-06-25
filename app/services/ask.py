from pgvector import Vector
import requests
from urllib.parse import urlparse, urlunparse

from app.db import get_conn
from app.settings import (
    EMBEDDING_MODEL,
    TOP_K,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    SUMMARY_MAX_CHARS,
    RELEVANCE_MAX_DISTANCE,
)

_model = None


def _get_model():
    global _model
    if _model is None:
        print("Loading embedding model...")
        # Delay heavy ML imports so app startup and CI smoke tests do not require GPU libs.
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

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


def _candidate_ollama_base_urls(base_url: str) -> list[str]:
    raw_base = (base_url or "http://localhost:11434").strip()
    if not raw_base:
        raw_base = "http://localhost:11434"

    candidates = [raw_base.rstrip("/")]

    # Some deployments expose OpenAI-compatible URLs ending in /v1 (or /api).
    # Native Ollama endpoints live at the root, so we also try stripped variants.
    for suffix in ("/v1", "/api"):
        new_candidates = []
        for candidate in candidates:
            parsed = urlparse(candidate)
            path = parsed.path.rstrip("/")
            if path.endswith(suffix):
                stripped_path = path[: -len(suffix)]
                stripped_base = urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        stripped_path,
                        "",
                        "",
                        "",
                    )
                ).rstrip("/")
                if stripped_base and stripped_base not in candidates and stripped_base not in new_candidates:
                    new_candidates.append(stripped_base)
        candidates.extend(new_candidates)

    return candidates


def _extract_ollama_text(response_json: dict) -> str:
    if "response" in response_json and isinstance(response_json["response"], str):
        return response_json["response"].strip()

    message = response_json.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()

    return ""


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

    errors = []

    for base_url in _candidate_ollama_base_urls(OLLAMA_BASE_URL):
        generate_url = f"{base_url}/api/generate"
        try:
            response = requests.post(
                generate_url,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )
            if response.status_code != 404:
                response.raise_for_status()
                text = _extract_ollama_text(response.json())
                if text:
                    return text
            else:
                errors.append(f"{generate_url} returned 404")
        except requests.RequestException as e:
            errors.append(f"{generate_url} failed: {e}")

        chat_url = f"{base_url}/api/chat"
        try:
            response = requests.post(
                chat_url,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=30,
            )
            if response.status_code != 404:
                response.raise_for_status()
                text = _extract_ollama_text(response.json())
                if text:
                    return text
            else:
                errors.append(f"{chat_url} returned 404")
        except requests.RequestException as e:
            errors.append(f"{chat_url} failed: {e}")

    print(
        "Error occurred while summarizing with Ollama: "
        f"could not get a valid response for model '{OLLAMA_MODEL}'. "
        f"Tried base URL(s): {', '.join(_candidate_ollama_base_urls(OLLAMA_BASE_URL))}. "
        f"Details: {' | '.join(errors) if errors else 'no response details'}"
    )
    return ""

def ask_question(
    question: str,
    language_id: int | None = None,
    lan: str = "en",
):
    model = _get_model()
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
    for _text, title, slug, _distance in filtered_rows:
        if slug not in sources_by_slug:
            sources_by_slug[slug] = {"title": title, "slug": slug}

    return {
        "answer": summary or raw_context,
        "sources": list(sources_by_slug.values()),
    }