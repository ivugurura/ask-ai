from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from app.db import get_conn
from app.settings import EMBEDDING_MODEL

model = SentenceTransformer(EMBEDDING_MODEL)

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(" ", strip=True)

def chunk_text(text, chunk_size=350, overlap=60):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks

def ingest_unindexed_topics():
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, slug, content, "languageId"
            FROM topics
            WHERE "isPublished" = true AND "hasIndexed" = false
        """)
        topics = cur.fetchall()

    for topic_id, slug, content, language_id in topics:
        text = html_to_text(content)
        chunks = chunk_text(text)

        if not chunks:
            continue

        embeddings = model.encode(chunks).tolist()

        with conn.cursor() as cur:
            cur.execute("""DELETE FROM topic_chunks WHERE "topicId" = %s""", (topic_id,))

            cur.executemany("""
                INSERT INTO topic_chunks
                  ("topicId", slug, "languageId", "chunkIndex", text, embedding, "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, [
                (topic_id, slug, language_id, idx, chunk, emb)
                for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))
            ])

            cur.execute("""
                UPDATE topics
                SET "hasIndexed" = true
                WHERE id = %s
            """, (topic_id,))

        conn.commit()

    conn.close()
    return {"indexed_topics": len(topics)}