import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ObjectCreate, ObjectUpdate

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "xr_objects.db"
DB_PATH: str = os.getenv("XR_DB_PATH", str(_DEFAULT_DB))
_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def configure_db(path: str | os.PathLike[str] | None) -> None:
    """設定資料庫路徑並關閉既有連線。傳 None 時回到預設路徑。"""
    global DB_PATH, _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    DB_PATH = str(path) if path is not None else str(_DEFAULT_DB)


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with _lock:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS objects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                model_url   TEXT    NOT NULL,
                position    TEXT    NOT NULL,
                rotation    TEXT    NOT NULL,
                scale       TEXT    NOT NULL,
                created_at  TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            )
            """
        )
        conn.commit()


def _to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "model_url": row["model_url"],
        "position": json.loads(row["position"]),
        "rotation": json.loads(row["rotation"]),
        "scale": json.loads(row["scale"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_objects() -> list[dict[str, Any]]:
    with _lock:
        rows = _connect().execute("SELECT * FROM objects ORDER BY id").fetchall()
    return [_to_dict(row) for row in rows]


def get_object(object_id: int) -> dict[str, Any] | None:
    with _lock:
        row = _connect().execute(
            "SELECT * FROM objects WHERE id = ?", (object_id,)
        ).fetchone()
    return _to_dict(row) if row is not None else None


def create_object(payload: ObjectCreate) -> dict[str, Any]:
    data = payload.model_dump(mode="json")
    now = _now()
    with _lock:
        conn = _connect()
        cur = conn.execute(
            """
            INSERT INTO objects
                (name, model_url, position, rotation, scale, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                str(data["model_url"]),
                json.dumps(data["position"]),
                json.dumps(data["rotation"]),
                json.dumps(data["scale"]),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM objects WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return _to_dict(row)


def update_object(object_id: int, payload: ObjectUpdate) -> dict[str, Any] | None:
    changes = payload.model_dump(mode="json", exclude_unset=True)
    if not changes:
        return get_object(object_id)

    columns: list[str] = []
    values: list[Any] = []
    for key, value in changes.items():
        if key in {"position", "rotation", "scale"}:
            value = json.dumps(value)
        elif key == "model_url":
            value = str(value)
        columns.append(f"{key} = ?")
        values.append(value)

    values.append(_now())
    values.append(object_id)

    with _lock:
        conn = _connect()
        cur = conn.execute(
            f"UPDATE objects SET {', '.join(columns)}, updated_at = ? WHERE id = ?",
            values,
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        row = conn.execute(
            "SELECT * FROM objects WHERE id = ?", (object_id,)
        ).fetchone()
    return _to_dict(row)


def delete_object(object_id: int) -> bool:
    with _lock:
        conn = _connect()
        cur = conn.execute("DELETE FROM objects WHERE id = ?", (object_id,))
        conn.commit()
    return cur.rowcount > 0
