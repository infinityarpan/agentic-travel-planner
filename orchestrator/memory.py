import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from orchestrator.errors import PersistenceError, ResourceNotFoundError


class Memory:
    def __init__(self, database_path: str):
        self.database_path = str(Path(database_path).resolve())
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    memory_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS planner_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    plan_json TEXT,
                    results_json TEXT,
                    feedback_json TEXT,
                    memory_before_json TEXT,
                    memory_after_json TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_planner_runs_user_created
                ON planner_runs (user_id, created_at DESC)
                """
            )
            connection.commit()

    def healthcheck(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute("SELECT 1")

    def get_user_memory(self, user_id: str) -> dict[str, Any]:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT memory_json FROM user_memory WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to load user memory for '{user_id}'.") from exc
        if not row:
            return {}
        return json.loads(row["memory_json"])

    def update_user_memory(self, user_id: str, new_data: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_user_memory(user_id)
        existing.update(new_data)
        payload = json.dumps(existing)
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    INSERT INTO user_memory (user_id, memory_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        memory_json = excluded.memory_json,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, payload),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to update user memory for '{user_id}'.") from exc
        return existing

    def create_run(self, user_id: str, user_query: str, memory_before: dict[str, Any]) -> int:
        try:
            with closing(self._connect()) as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO planner_runs (
                        user_id,
                        user_query,
                        status,
                        memory_before_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (user_id, user_query, "running", json.dumps(memory_before)),
                )
                connection.commit()
                return int(cursor.lastrowid)
        except sqlite3.Error as exc:
            raise PersistenceError("Failed to create planner run record.") from exc

    def complete_run(
        self,
        run_id: int,
        *,
        status: str,
        attempts: int,
        plan: list[dict[str, Any]],
        results: list[dict[str, Any]],
        feedback: dict[str, Any],
        memory_after: dict[str, Any],
    ) -> None:
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    UPDATE planner_runs
                    SET status = ?,
                        attempts = ?,
                        plan_json = ?,
                        results_json = ?,
                        feedback_json = ?,
                        memory_after_json = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        status,
                        attempts,
                        json.dumps(plan),
                        json.dumps(results),
                        json.dumps(feedback),
                        json.dumps(memory_after),
                        run_id,
                    ),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to complete planner run '{run_id}'.") from exc

    def fail_run(self, run_id: int, *, attempts: int, error_message: str) -> None:
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    UPDATE planner_runs
                    SET status = ?,
                        attempts = ?,
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    ("failed", attempts, error_message, run_id),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to mark planner run '{run_id}' as failed.") from exc

    def get_run(self, run_id: int) -> dict[str, Any]:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    """
                    SELECT id, user_id, user_query, status, attempts, plan_json,
                           results_json, feedback_json, memory_before_json,
                           memory_after_json, error_message, created_at, updated_at
                    FROM planner_runs
                    WHERE id = ?
                    """,
                    (run_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to load planner run '{run_id}'.") from exc
        if not row:
            raise ResourceNotFoundError(f"Planner run '{run_id}' was not found.")
        return self._deserialize_run(row)

    def list_runs(self, *, user_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        query = """
            SELECT id, user_id, user_query, status, attempts, plan_json,
                   results_json, feedback_json, memory_before_json,
                   memory_after_json, error_message, created_at, updated_at
            FROM planner_runs
        """
        params: list[Any] = []
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(query, tuple(params)).fetchall()
        except sqlite3.Error as exc:
            raise PersistenceError("Failed to list planner runs.") from exc
        return [self._deserialize_run(row) for row in rows]

    def _deserialize_run(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": row["id"],
            "user_id": row["user_id"],
            "user_query": row["user_query"],
            "status": row["status"],
            "attempts": row["attempts"],
            "plan": json.loads(row["plan_json"]) if row["plan_json"] else [],
            "results": json.loads(row["results_json"]) if row["results_json"] else [],
            "feedback": json.loads(row["feedback_json"]) if row["feedback_json"] else {},
            "memory_before": json.loads(row["memory_before_json"]) if row["memory_before_json"] else {},
            "memory_after": json.loads(row["memory_after_json"]) if row["memory_after_json"] else {},
            "error_message": row["error_message"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
