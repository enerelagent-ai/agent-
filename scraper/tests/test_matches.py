"""Integration tests for duplicate-match recording, run against the local
Postgres inside a transaction that is always rolled back (nothing persists)."""

import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
import pytest

from scraper.matches import (
    fetch_listing,
    find_matches_for_listing,
    record_matches,
    superseded_listing_ids,
)
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


def test_superseded_ids_keep_one_listing_per_group(cur) -> None:
    id_a, id_b = _insert_pair(cur)
    record_matches(cur, [(min(id_a, id_b), max(id_a, id_b), 0.9)])

    superseded = superseded_listing_ids(cur)
    ours = superseded & {id_a, id_b}
    assert len(ours) == 1  # exactly one of the pair is dropped
    # Equal completeness -> the more recently posted one is kept.
    kept = ({id_a, id_b} - ours).pop()
    row_kept = [r for r in
                (fetch_listing(cur, "test://dup-a"), fetch_listing(cur, "test://dup-b"))
                if r["id"] == kept][0]
    row_dropped = [r for r in
                   (fetch_listing(cur, "test://dup-a"), fetch_listing(cur, "test://dup-b"))
                   if r["id"] != kept][0]
    assert (row_kept["posted_at"] or "") >= (row_dropped["posted_at"] or "")
