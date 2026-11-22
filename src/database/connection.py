import os
import shutil
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from config.settings import settings

def get_db_path() -> Path:
    # If running on Vercel / AWS Lambda serverless, copy bundled database to /tmp
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_db = Path("/tmp/ai_pipeline.db")
        if not tmp_db.exists():
            root_dir = Path(__file__).resolve().parent.parent.parent
            bundled_db = root_dir / "data" / "ai_pipeline.db"
            if bundled_db.exists():
                shutil.copy2(bundled_db, tmp_db)
        return tmp_db

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

