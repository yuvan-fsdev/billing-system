"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import main as app_main
from app import models  # noqa: F401 - ensure models are imported
from app.db import session as db_session
from app.db.session import Base


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional SQLAlchemy session backed by SQLite."""
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture()
def test_client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient using an in-memory database."""
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    # Override global engine/session for application context
    db_session.engine = engine
    db_session.SessionLocal = TestingSessionLocal
    app_main.engine = engine

    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app_main.app.dependency_overrides[app_main.get_db] = override_get_db

    with TestClient(app_main.app) as client:
        client.session_local = TestingSessionLocal  # type: ignore[attr-defined]
        yield client

    app_main.app.dependency_overrides.clear()
