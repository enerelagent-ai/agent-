"""Shared pytest fixtures for backend tests.

First test suite this backend has (see app/database.py's engine/SessionLocal
for what production wiring looks like) -- mirrors analytics/scraper's own
pattern of running integration tests against the real local Postgres inside
a transaction that's always rolled back, rather than mocking the DB.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.main import app

_engine = create_engine(settings.database_url)


@pytest.fixture()
def db_session():
    """A Session bound to a connection whose outer transaction is always
    rolled back after the test. Never call session.commit() in a test that
    uses this -- that would end the outer transaction early and persist
    the data. Use .flush() to make inserts visible to later queries on the
    same session (autoflush is on by default here, unlike production's
    SessionLocal, so this is rarely needed explicitly)."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """TestClient wired to reuse db_session for every request's `db`
    dependency, so data a test inserts via db_session is visible to the
    API calls it makes -- both go through the exact same transaction,
    which is rolled back when the test ends either way."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
