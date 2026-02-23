from sentence_transformers import SentenceTransformer
from pgvector import Vector
from app.db import get_conn
from app.settings import EMBEDDING_MODEL, TOP_K

model = SentenceTransformer(EMBEDDING_MODEL)

def ask_question(question: str, language_id: int | None = None):
    query_emb = Vector(model.encode([question])[0].tolist())
    conn = get_conn()

    with conn.cursor() as cur:
        if language_id:
            cur.execute("""
                SELECT tc.text, t.title, t.slug
                FROM topic_chunks tc
                JOIN topics t ON tc."topicId" = t.id
                WHERE tc."languageId" = %s
                ORDER BY tc.embedding <=> %s
                LIMIT %s
            """, (language_id, query_emb, TOP_K))
        else:
            cur.execute("""
                SELECT tc.text, t.title, t.slug
                FROM topic_chunks tc
                JOIN topics t ON tc."topicId" = t.id
                ORDER BY tc.embedding <=> %s
                LIMIT %s
            """, (query_emb, TOP_K))

        rows = cur.fetchall()

    conn.close()

    return {
        "answer": "\n\n".join([r[0] for r in rows]),
        "sources": [{"title": r[1], "slug": r[2]} for r in rows],
    }