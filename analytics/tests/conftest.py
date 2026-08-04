"""Shared pytest fixtures for analytics tests."""

import os

import psycopg2
import psycopg2.extras
import pytest

from analytics.db import normalize_dsn
from analytics.matches import reset_superseded_ids_cache

DSN = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/postgres")


@pytest.fixture()
def cur():
    """Cursor in a transaction that is rolled back after each test, so
    integration tests run against the real local Postgres without persisting.

    Also resets superseded_listing_ids()'s in-process cache before every
    test: that cache is a module-level global, and pytest runs the whole
    suite in one process, so without this reset one test's cached result
    (computed from its own synthetic, about-to-be-rolled-back data) would
    leak into the next test's assertions.
    """
    reset_superseded_ids_cache()
    try:
        conn = psycopg2.connect(normalize_dsn(DSN))
    except psycopg2.OperationalError:
        pytest.skip("local Postgres not available")
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    yield cursor
    conn.rollback()
    conn.close()
