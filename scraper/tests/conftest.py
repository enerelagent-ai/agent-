"""Shared pytest fixtures for scraper tests."""

import os

import psycopg2
import psycopg2.extras
import pytest

from scraper.save import normalize_dsn

DSN = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/postgres")


@pytest.fixture()
def cur():
    """Cursor in a transaction that is rolled back after each test, so
    integration tests run against the real local Postgres without persisting."""
    try:
        conn = psycopg2.connect(normalize_dsn(DSN))
    except psycopg2.OperationalError:
        pytest.skip("local Postgres not available")
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    yield cursor
    conn.rollback()
    conn.close()
