from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@dataclass(frozen=True)
class RunRecord:
    run_id: str
    created_at: str
    filename: str
    rows_in: int
    rows_out: int
    duplicates_removed: int

class RunStore:
    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    rows_in INTEGER NOT NULL,
                    rows_out INTEGER NOT NULL,
                    duplicates_removed INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def upsert(self, r: RunRecord) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO runs(run_id, created_at, filename, rows_in, rows_out, duplicates_removed)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                  created_at=excluded.created_at,
                  filename=excluded.filename,
                  rows_in=excluded.rows_in,
                  rows_out=excluded.rows_out,
                  duplicates_removed=excluded.duplicates_removed
                """,
                (r.run_id, r.created_at, r.filename, r.rows_in, r.rows_out, r.duplicates_removed),
            )
            conn.commit()

    def list_recent(self, limit: int = 30) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT run_id, created_at, filename, rows_in, rows_out, duplicates_removed FROM runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, run_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT run_id, created_at, filename, rows_in, rows_out, duplicates_removed FROM runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
        return dict(row) if row else None
