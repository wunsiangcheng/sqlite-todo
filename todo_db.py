import sqlite3
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_DB = "todo_tasks.db"
STATUS_PENDING = "Pending"
STATUS_COMPLETED = "Completed"


@dataclass
class Task:
    id: int
    task: str
    status: str
    created_at: str


class TodoDB:
    def __init__(self, db_path: str = DEFAULT_DB, enable_wal: bool = True):
        self.db_path = db_path
        self.enable_wal = enable_wal

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout = 5000;")
            if self.enable_wal:
                conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.Error as e:
            logger.debug("PRAGMA setup failed: %s", e)
        return conn

    def setup(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Pending','Completed')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT
        );
        """
        try:
            with self._connect() as conn:
                conn.execute(schema)
                conn.commit()
                logger.debug("Database schema ensured.")
        except sqlite3.Error as e:
            logger.exception("Failed to setup database.")
            raise

    def add_task(self, task_content: str) -> int:
        if not task_content or not task_content.strip():
            raise ValueError("Task content cannot be empty.")
        task_content = task_content.strip()
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO todos (task, status) VALUES (?, ?)",
                    (task_content, STATUS_PENDING),
                )
                conn.commit()
                task_id = cur.lastrowid
                logger.info("Added task id=%s", task_id)
                return task_id
        except sqlite3.Error:
            logger.exception("Error inserting task.")
            raise

    def list_tasks(
        self,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Task]:
        sql = "SELECT id, task, status, created_at FROM todos"
        clauses = []
        params: List = []

        if status:
            if status not in (STATUS_PENDING, STATUS_COMPLETED):
                raise ValueError(f"Invalid status filter: {status}")
            clauses.append("status = ?")
            params.append(status)

        if query:
            # Use LIKE with wildcards and case-insensitive match
            clauses.append("task LIKE ? COLLATE NOCASE")
            params.append(f"%{query}%")

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY id DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        try:
            with self._connect() as conn:
                cur = conn.execute(sql, tuple(params))
                rows = cur.fetchall()
                tasks = [
                    Task(
                        id=row["id"],
                        task=row["task"],
                        status=row["status"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
                logger.debug("Fetched %d tasks (status=%s, query=%s, limit=%s).", len(tasks), status, query, limit)
                return tasks
        except sqlite3.Error:
            logger.exception("Error reading tasks.")
            raise

    def complete_task(self, task_id: int) -> bool:
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "UPDATE todos SET status = ?, updated_at = datetime('now') WHERE id = ? AND status != ?",
                    (STATUS_COMPLETED, task_id, STATUS_COMPLETED),
                )
                conn.commit()
                changed = cur.rowcount > 0
                logger.info("Complete task %s changed=%s", task_id, changed)
                return changed
        except sqlite3.Error:
            logger.exception("Error completing task.")
            raise

    def delete_task(self, task_id: int) -> bool:
        try:
            with self._connect() as conn:
                cur = conn.execute("DELETE FROM todos WHERE id = ?", (task_id,))
                conn.commit()
                deleted = cur.rowcount > 0
                logger.info("Delete task %s deleted=%s", task_id, deleted)
                return deleted
        except sqlite3.Error:
            logger.exception("Error deleting task.")
            raise
