import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
TOP_K = int(os.getenv("TOP_K", ""))
