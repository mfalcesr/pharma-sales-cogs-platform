import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("POSTGRES_DB", "pharma_db"),
    "user":     os.getenv("POSTGRES_USER", "pharma_user"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}


def get_connection():
    """Return a new psycopg2 connection using environment-based config."""
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def db_cursor():
    """Context manager that yields a cursor, commits on success, rolls back on error."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
