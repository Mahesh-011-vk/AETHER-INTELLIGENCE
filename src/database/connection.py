import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from config.settings import settings

def get_db_path() -> Path:
    # Handle sqlite:///path/to/db
    raw_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    db_path = Path(raw_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    db_path = get_db_path()
    conn = sqlite3.connect(
        str(db_path),
        timeout=30.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    try:
        # WAL mode for reliable concurrency and atomic writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
    finally:
        conn.close()

