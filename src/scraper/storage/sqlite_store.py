"""Save scraped data to a SQLite database."""

import json
import re
import sqlite3
from pathlib import Path

from scraper.config import DB_PATH
from scraper.utils import get_logger

log = get_logger(__name__)

_SAFE_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def save(data: dict, db_path: str | Path | None = None, table: str = "pages") -> None:
    """Save data dict to a SQLite table."""
    if not _SAFE_TABLE_RE.match(table):
        raise ValueError(f"Invalid table name: {table!r}")

    if db_path is None:
        db_path = DB_PATH
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS [{table}] ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  url TEXT,"
            "  raw_json TEXT,"
            "  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.execute(
            f"INSERT INTO [{table}] (url, raw_json) VALUES (?, ?)",
            (
                data.get("url", ""),
                json.dumps(data, ensure_ascii=False),
            ),
        )
        conn.commit()
        log.info("Saved to %s (table: %s)", db_path, table)
    finally:
        conn.close()
