"""SQLite engine with WAL, foreign keys and a busy timeout."""

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, event
from sqlmodel import SQLModel, create_engine

from app.store import models  # noqa: F401  (registers tables on SQLModel.metadata)

BUSY_TIMEOUT_MS = 5000


def _apply_pragmas(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


def create_db_engine(path: Path) -> Engine:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _apply_pragmas)
    return engine


def init_db(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)
