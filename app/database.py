"""
DayFlow backend – SQLAlchemy 2 database setup.

The database URL is always read from settings (environment variable) so
production can point at a persistent Render disk path without any
source-code change.

The engine is created lazily on first access so tests can override
DATABASE_URL via environment before any import triggers engine creation.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


def _make_engine(url: str):
    """
    Build a SQLAlchemy engine for the given URL.

    For SQLite we:
    - Enable WAL mode for better concurrent read performance.
    - Enable foreign-key enforcement (off by default in SQLite).
    - Ensure the data directory exists before returning the engine.
    """
    # Create the data directory if the URL points at a file-based SQLite DB.
    if url.startswith("sqlite:///"):
        db_path_str = url[len("sqlite:///"):]
        if db_path_str:  # skip in-memory databases
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)

    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        url,
        connect_args=connect_args,
        echo=os.getenv("APP_ENV", "development") == "development",
    )

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Lazy singletons – created on first access, not at import time.
# This allows tests to override DATABASE_URL before any engine is built.
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = _make_engine(settings.database_url)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            class_=Session,
        )
    return _SessionLocal


# Convenience alias used by Alembic env.py and tests that need the engine
# directly (they call get_engine() after setting the env var)
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and guarantee cleanup on exit.

    Usage in route handlers::

        def my_route(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
