"""Find and record duplicate matches for newly saved listings.

The SQL prefilter mirrors the hard-equality half of dedup.are_candidates()
(listing_type, property_type, district) so only a small slice of the table
is pulled per listing; rooms/area refinement and soft-signal scoring then
run in Python. Matches at or above the threshold are upserted into
duplicate_matches, so re-scoring a pair updates score and matched_at in
place instead of duplicating it.
"""

from typing import Any

import psycopg2
import psycopg2.extras

from analytics.dedup import (
    AUTO_RESOLVE_THRESHOLD,
    CANDIDATE_THRESHOLD,
    are_candidates,
    group_pairs,
    pick_canonical,
    score_pair,
)
from analytics.db import normalize_dsn

Match = tuple[int, int, float]

_LISTING_FIELDS = """
    SELECT id, source_url, title, listing_type, property_type, district,
           rooms, area_sqm::float AS area_sqm, price::float AS price,
           array_length(photo_urls, 1) AS n_photos,
           to_char(posted_at, 'YYYY-MM-DD"T"HH24:MI') AS posted_at
    FROM listings
"""

_RECORD_SQL = """
    INSERT INTO duplicate_matches (listing_id_a, listing_id_b, score)
    VALUES (%s, %s, %s)
    ON CONFLICT (listing_id_a, listing_id_b)
    DO UPDATE SET score = EXCLUDED.score, matched_at = now()
"""


def fetch_listing(cur: psycopg2.extensions.cursor, source_url: str) -> dict[str, Any] | None:
    """Load one listing row (scorer field set) by source_url."""
    cur.execute(_LISTING_FIELDS + " WHERE source_url = %s", (source_url,))
    row = cur.fetchone()
    return dict(row) if row else None


def find_matches_for_listing(
    cur: psycopg2.extensions.cursor, row: dict[str, Any]
) -> list[Match]:
    """Score one listing against same-block rows already in the table.

    Returns (listing_id_a, listing_id_b, score) with a < b for every pair
    at or above DUPLICATE_THRESHOLD.
    """
    if not all(row.get(f) for f in ("listing_type", "property_type", "district")):
        return []
    cur.execute(
        _LISTING_FIELDS + """
        WHERE listing_type = %s AND property_type = %s AND district = %s AND id <> %s
        """,
        (row["listing_type"], row["property_type"], row["district"], row["id"]),
    )
    matches: list[Match] = []
    for other in (dict(r) for r in cur.fetchall()):
        if not are_candidates(row, other):
            continue
        total = score_pair(row, other)["total"]
        if total >= CANDIDATE_THRESHOLD:
            id_a, id_b = sorted((row["id"], other["id"]))
            matches.append((id_a, id_b, total))
    return matches


def record_matches(cur: psycopg2.extensions.cursor, matches: list[Match]) -> None:
    """Upsert scored pairs into duplicate_matches."""
    for id_a, id_b, score in matches:
        cur.execute(_RECORD_SQL, (id_a, id_b, score))


def superseded_listing_ids(cur: psycopg2.extensions.cursor) -> set[int]:
    """Ids analytics must EXCLUDE so duplicate groups count once.

    Only matches at or above AUTO_RESOLVE_THRESHOLD are used to build
    groups: below that (the "Possible Duplicate" tier) precision is too low
    to safely drop a listing from analytics — see dedup.match_status and
    the fixture validation it cites. Those pairs surface via
    possible_duplicate_pairs() for human review instead. Every group above
    the bar keeps its canonical listing (dedup.pick_canonical) and
    contributes the rest here. Consumers filter with e.g. WHERE id != ALL(%s).
    """
    cur.execute(
        "SELECT listing_id_a, listing_id_b FROM duplicate_matches WHERE score >= %s",
        (AUTO_RESOLVE_THRESHOLD,),
    )
    pairs = [(r["listing_id_a"], r["listing_id_b"]) for r in cur.fetchall()]
    superseded: set[int] = set()
    for group in group_pairs(pairs):
        cur.execute(_LISTING_FIELDS + " WHERE id = ANY(%s)", (list(group),))
        rows = [dict(r) for r in cur.fetchall()]
        if len(rows) < 2:
            continue
        superseded |= {row["id"] for row in rows} - {pick_canonical(rows)}
    return superseded


def possible_duplicate_pairs(cur: psycopg2.extensions.cursor) -> list[Match]:
    """Matches in the 'Possible Duplicate' review tier: recorded as
    candidates but not auto-resolved (see superseded_listing_ids). Intended
    for a human review queue; ordered by score, most confident first."""
    cur.execute(
        "SELECT listing_id_a, listing_id_b, score FROM duplicate_matches"
        " WHERE score >= %s AND score < %s ORDER BY score DESC",
        (CANDIDATE_THRESHOLD, AUTO_RESOLVE_THRESHOLD),
    )
    return [(r["listing_id_a"], r["listing_id_b"], r["score"]) for r in cur.fetchall()]


def match_new_listings(dsn: str, source_urls: list[str]) -> list[Match]:
    """Pipeline entry point: check freshly upserted listings for duplicates.

    Called after upsert_listings(), so the batch itself is already in the
    table and batch-internal duplicates are found too (each pair is stored
    once thanks to the a < b ordering and the upsert).
    """
    found: dict[tuple[int, int], Match] = {}
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            for source_url in source_urls:
                row = fetch_listing(cur, source_url)
                if row is None:
                    continue
                matches = find_matches_for_listing(cur, row)
                record_matches(cur, matches)
                for match in matches:
                    found[match[:2]] = match
    conn.close()
    return sorted(found.values())
