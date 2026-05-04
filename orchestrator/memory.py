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
                CREATE TABLE IF NOT EXISTS travel_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    trip_brief_json TEXT,
                    trip_packages_json TEXT,
                    recommended_package_json TEXT,
                    cost_breakdown_json TEXT,
                    assumptions_json TEXT,
                    service_trace_json TEXT,
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
                CREATE INDEX IF NOT EXISTS idx_travel_runs_user_created
                ON travel_runs (user_id, created_at DESC)
                """
            )
            connection.commit()

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
                    INSERT INTO travel_runs (
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
            raise PersistenceError("Failed to create travel run record.") from exc

    def complete_run(
        self,
        run_id: int,
        *,
        status: str,
        trip_brief: dict[str, Any],
        trip_packages: list[dict[str, Any]],
        recommended_package: dict[str, Any],
        cost_breakdown: dict[str, Any],
        assumptions: list[str],
        service_trace: list[dict[str, Any]],
        memory_after: dict[str, Any],
    ) -> None:
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    UPDATE travel_runs
                    SET status = ?,
                        trip_brief_json = ?,
                        trip_packages_json = ?,
                        recommended_package_json = ?,
                        cost_breakdown_json = ?,
                        assumptions_json = ?,
                        service_trace_json = ?,
                        memory_after_json = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        status,
                        json.dumps(trip_brief),
                        json.dumps(trip_packages),
                        json.dumps(recommended_package),
                        json.dumps(cost_breakdown),
                        json.dumps(assumptions),
                        json.dumps(service_trace),
                        json.dumps(memory_after),
                        run_id,
                    ),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to complete travel run '{run_id}'.") from exc

    def fail_run(self, run_id: int, *, error_message: str) -> None:
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    UPDATE travel_runs
                    SET status = ?,
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    ("failed", error_message, run_id),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to mark travel run '{run_id}' as failed.") from exc

    def get_run(self, run_id: int) -> dict[str, Any]:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    """
                    SELECT id, user_id, user_query, status, trip_brief_json,
                           trip_packages_json, recommended_package_json,
                           cost_breakdown_json, assumptions_json,
                           service_trace_json, memory_before_json,
                           memory_after_json, error_message, created_at, updated_at
                    FROM travel_runs
                    WHERE id = ?
                    """,
                    (run_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to load travel run '{run_id}'.") from exc
        if not row:
            raise ResourceNotFoundError(f"Travel run '{run_id}' was not found.")
        return self._deserialize_run(row)

    def list_runs(self, *, user_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        query = """
            SELECT id, user_id, user_query, status, trip_brief_json,
                   trip_packages_json, recommended_package_json,
                   cost_breakdown_json, assumptions_json,
                   service_trace_json, memory_before_json,
                   memory_after_json, error_message, created_at, updated_at
            FROM travel_runs
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
            raise PersistenceError("Failed to list travel runs.") from exc
        return [self._deserialize_run(row) for row in rows]

    def _deserialize_run(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": row["id"],
            "user_id": row["user_id"],
            "user_query": row["user_query"],
            "status": row["status"],
            "trip_brief": json.loads(row["trip_brief_json"]) if row["trip_brief_json"] else None,
            "trip_packages": json.loads(row["trip_packages_json"]) if row["trip_packages_json"] else [],
            "recommended_package": json.loads(row["recommended_package_json"]) if row["recommended_package_json"] else None,
            "cost_breakdown": json.loads(row["cost_breakdown_json"]) if row["cost_breakdown_json"] else None,
            "assumptions": json.loads(row["assumptions_json"]) if row["assumptions_json"] else [],
            "service_trace": json.loads(row["service_trace_json"]) if row["service_trace_json"] else [],
            "memory_before": json.loads(row["memory_before_json"]) if row["memory_before_json"] else {},
            "memory_after": json.loads(row["memory_after_json"]) if row["memory_after_json"] else {},
            "error_message": row["error_message"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
