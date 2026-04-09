import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
TOP_K = int(os.getenv("TOP_K", "5"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "4000"))
RELEVANCE_MAX_DISTANCE = float(os.getenv("RELEVANCE_MAX_DISTANCE", "0.7"))
