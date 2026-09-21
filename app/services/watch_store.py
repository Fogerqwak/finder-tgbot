import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class WatchEntry:
    id: int
    user_id: int
    username: str


class WatchStore:
    """Persists per-user watched usernames in SQLite.

    Plain blocking sqlite3 is used deliberately: calls are infrequent (a few
    user commands plus one hourly scan) and each query takes microseconds,
    so an async driver would add a dependency without a measurable benefit.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        parent = Path(db_path).parent
        if str(parent):
            parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS watches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, username COLLATE NOCASE)
                )
                """
            )
            conn.commit()

    def count_for_user(self, user_id: int) -> int:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM watches WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row[0]

    def list_for_user(self, user_id: int) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT username FROM watches WHERE user_id = ? ORDER BY created_at",
                (user_id,),
            ).fetchall()
            return [row[0] for row in rows]

    def add(self, user_id: int, username: str) -> bool:
        """Adds a username to a user's watch list. Returns False if already watched."""
        try:
            with closing(self._connect()) as conn:
                conn.execute(
                    "INSERT INTO watches (user_id, username, created_at) VALUES (?, ?, ?)",
                    (user_id, username, datetime.now(UTC).isoformat()),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove(self, user_id: int, username: str) -> bool:
        """Removes a username from a user's watch list. Returns False if it wasn't there."""
        with closing(self._connect()) as conn:
            cursor = conn.execute(
                "DELETE FROM watches WHERE user_id = ? AND username = ? COLLATE NOCASE",
                (user_id, username),
            )
            conn.commit()
            return cursor.rowcount > 0

    def all_entries(self) -> list[WatchEntry]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT id, user_id, username FROM watches").fetchall()
            return [WatchEntry(id=r[0], user_id=r[1], username=r[2]) for r in rows]

    def remove_by_id(self, watch_id: int) -> None:
        with closing(self._connect()) as conn:
            conn.execute("DELETE FROM watches WHERE id = ?", (watch_id,))
            conn.commit()
