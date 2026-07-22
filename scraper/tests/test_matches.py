"""Integration tests for duplicate-match recording, run against the local
Postgres inside a transaction that is always rolled back (nothing persists)."""

import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
import pytest

from scraper.matches import fetch_listing, find_matches_for_listing, record_matches
from scraper.save import normalize_dsn

FIXTURE = Path(__file__).parent / "fixtures" / "labeled_pairs.json"
DSN = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/postgres")

_INSERT_SQL = """
    INSERT INTO listings (source, source_url, title, price, area_sqm, rooms,
                          district, listing_type, property_type, photo_urls,
                          posted_at, dedup_hash)
    VALUES ('unegui', %(source_url)s, %(title)s, %(price)s, %(area_sqm)s, %(rooms)s,
            %(district)s, %(listing_type)s, %(property_type)s, %(photo_urls)s,
            %(posted_at)s, 'test-hash')
    RETURNING id
"""


@pytest.fixture()
def cur():
    """Cursor in a transaction that is rolled back after each test."""
    try:
        conn = psycopg2.connect(normalize_dsn(DSN))
    except psycopg2.OperationalError:
        pytest.skip("local Postgres not available")
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    yield cursor
    conn.rollback()
    conn.close()


def _insert_pair(cur) -> tuple[int, int]:
    """Insert the labeled duplicate pair (river plaza) with test URLs;
    returns the two new listing ids."""
    pair = next(p for p in json.loads(FIXTURE.read_text()) if p["label"] == "duplicate")
    ids = []
    for ad, url in zip((pair["a"], pair["b"]), ("test://dup-a", "test://dup-b")):
        cur.execute(_INSERT_SQL, {
            **{k: ad[k] for k in ("title", "price", "area_sqm", "rooms", "district",
                                  "listing_type", "property_type", "posted_at")},
            "source_url": url,
            "photo_urls": [f"test://photo{i}" for i in range(ad["n_photos"] or 0)],
        })
        ids.append(cur.fetchone()["id"])
    return ids[0], ids[1]


def test_duplicate_pair_is_found_and_recorded(cur) -> None:
    id_a, id_b = _insert_pair(cur)
    row = fetch_listing(cur, "test://dup-a")
    assert row is not None

    # The live table may legitimately contain other duplicates of this ad
    # (it is real data); assert on the inserted pair specifically.
    matches = find_matches_for_listing(cur, row)
    pair_key = tuple(sorted((id_a, id_b)))
    ours = [m for m in matches if m[:2] == pair_key]
    assert len(ours) == 1
    assert ours[0][2] >= 0.6
    assert all(a < b for a, b, _ in matches)

    record_matches(cur, ours)
    cur.execute("SELECT count(*) AS n FROM duplicate_matches WHERE (listing_id_a, listing_id_b) = (%s, %s)",
                pair_key)
    assert cur.fetchone()["n"] == 1

    # Re-recording the same pair must update in place, not duplicate.
    record_matches(cur, ours)
    cur.execute("SELECT count(*) AS n FROM duplicate_matches WHERE (listing_id_a, listing_id_b) = (%s, %s)",
                pair_key)
    assert cur.fetchone()["n"] == 1


def test_missing_listing_yields_no_row(cur) -> None:
    assert fetch_listing(cur, "test://does-not-exist") is None
