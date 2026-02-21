import psycopg2
from pgvector.psycopg2 import register_vector
from app.settings import DATABASE_URL

def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn
