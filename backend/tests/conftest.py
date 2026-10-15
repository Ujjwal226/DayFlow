"""
DayFlow tests – shared pytest fixtures.

Key design decisions
--------------------
* DATABASE_URL is set to a temp SQLite file BEFORE importing app modules, so
  the lazy engine singleton picks up the right URL.
* The app's get_db dependency is overridden so route handlers use the same
  transactional session as each test, enabling rollback-based isolation.
* The HTTPX TestClient is synchronous – no async test setup needed.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# ------------------------------------------------------------------ #
# Set the test database URL BEFORE any app module is imported.
# The lazy engine in database.py will pick this up on first call.
# ------------------------------------------------------------------ #
_tmp_dir = tempfile.mkdtemp(prefix="dayflow_test_")
_TEST_DB_PATH = os.path.join(_tmp_dir, "test_dayflow.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["APP_ENV"] = "testing"

# Now safe to import app modules
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.auth import get_current_user  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


# ------------------------------------------------------------------ #
# Session-scoped engine – schema created once for the whole test run
# ------------------------------------------------------------------ #

@pytest.fixture(scope="session")
def test_engine():
    """Create engine + schema once for the whole test session."""
    url = f"sqlite:///{_TEST_DB_PATH}"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def TestSessionLocal(test_engine):
    return sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False, class_=Session
    )


# ------------------------------------------------------------------ #
# Function-scoped session – rolls back after every test
# ------------------------------------------------------------------ #

@pytest.fixture()
def db_session(TestSessionLocal) -> Generator[Session, None, None]:
    """
    Provide a transactional session that rolls back after each test.
    This gives each test a clean slate without recreating the schema.
    """
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def default_user(db_session: Session) -> models.User:
    """Create or retrieve the default authenticated test user."""
    from sqlalchemy import select
    stmt = select(models.User).where(models.User.email == "testuser@example.com")
    user = db_session.scalars(stmt).first()
    if user is None:
        user = models.User(
            email="testuser@example.com",
            hashed_password="$2b$12$e7kY7UqZc00N5lGk06RjCe9J2m7E8L2Qd4gJ0qF6yC9DayFlow2026",
            full_name="Default Test User",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


# ------------------------------------------------------------------ #
# TestClient with overridden dependency
# ------------------------------------------------------------------ #

@pytest.fixture()
def client(db_session: Session, default_user: models.User) -> Generator[TestClient, None, None]:
    """
    Return a TestClient whose database dependency uses the isolated
    test session and defaults to an authenticated user for existing test suites.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # rollback handled by db_session fixture

    def _override_get_current_user():
        return default_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def unauth_client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Return a TestClient with only DB overridden, requiring real JWT authentication.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

