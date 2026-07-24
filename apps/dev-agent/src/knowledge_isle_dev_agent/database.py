import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(UTC).isoformat()


class AgentDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_number INTEGER NOT NULL UNIQUE,
                    issue_title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    branch TEXT,
                    pr_url TEXT,
                    pr_number INTEGER,
                    quality_passed INTEGER NOT NULL DEFAULT 0,
                    merge_approved INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                """
            )

    def create_run(self, issue_number: int, title: str) -> int:
        timestamp = now()
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO runs(issue_number, issue_title, status, created_at, updated_at) "
                "VALUES (?, ?, 'queued', ?, ?)",
                (issue_number, title, timestamp, timestamp),
            )
            return int(cursor.lastrowid)

    def update_run(self, run_id: int, **values: Any) -> None:
        values["updated_at"] = now()
        columns = ", ".join(f"{name} = ?" for name in values)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE runs SET {columns} WHERE id = ?",  # noqa: S608
                (*values.values(), run_id),
            )

    def add_event(
        self, run_id: int, message: str, *, level: str = "info", details: Any = None
    ) -> None:
        encoded = json.dumps(details, ensure_ascii=False) if details is not None else None
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO events(run_id, level, message, details, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (run_id, level, message, encoded, now()),
            )

    def list_runs(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(row) for row in rows]

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            run = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if run is None:
                return None
            events = connection.execute(
                "SELECT * FROM events WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
        result = dict(run)
        result["events"] = [dict(event) for event in events]
        return result

    def issue_seen(self, issue_number: int) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM runs WHERE issue_number = ?", (issue_number,)
            ).fetchone()
        return row is not None
