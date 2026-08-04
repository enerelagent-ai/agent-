"""Find and record duplicate matches for newly saved listings.

The SQL prefilter mirrors the hard-equality half of dedup.are_candidates()
(listing_type, property_type, district) so only a small slice of the table
is pulled per listing; rooms/area refinement and soft-signal scoring then
run in Python. Matches at or above the threshold are upserted into
duplicate_matches, so re-scoring a pair updates score and matched_at in
place instead of duplicating it.
"""

import threading
import time
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

# In-process TTL cache for superseded_listing_ids() -- see that function's
# docstring for why (it was costing ~0.7s per call, one SQL round-trip per
# duplicate group, and every /dashboard/* route calls it at least once, so
# a single dashboard page load was paying that cost 5-6 times over).
#
# TTL, not push-invalidation-on-write: the writer (the scraper pipeline,
# via record_matches()) and the reader (this backend process) are separate
# OS processes with no shared memory, so there is no in-process event to
# invalidate on -- time is the only signal available here. duplicate_matches
# only changes once a day (the scheduled scrape), so any TTL from a few
# minutes to a few hours is nowhere near stale relative to that cadence;
# 10 minutes is just a round number comfortably inside that range. A lock
# guards the compute-and-store step since FastAPI runs sync route functions
# in a threadpool -- concurrent requests really can race here, not just in
# theory.
_CACHE_TTL_SECONDS = 600
_cache_lock = threading.Lock()
_cache: tuple[float, set[int]] | None = None  # (computed_at monotonic, ids)


def reset_superseded_ids_cache() -> None:
    """Clears the cache immediately, ignoring the TTL. Test fixtures call
    this before every test (see conftest.py's `cur` fixture) -- pytest runs
    the whole suite in one process, so without this, one test's cached
    result (computed from its own synthetic, about-to-be-rolled-back data)
    would leak into the next test's assertions via this module-level cache."""
    global _cache
    with _cache_lock:
        _cache = None

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
    """Upsert scored pairs into duplicate_matches.

    Resets superseded_listing_ids()'s cache -- this is the only function
    that writes duplicate_matches, so it's the one place that can know the
    cached set might now be wrong. In production this is a no-op in
    practice (the scraper process that calls this and the backend API
    process that reads the cache are different OS processes with separate
    memory -- see that cache's own module-level comment), but it makes the
    two always-consistent within one process, which matters for anything
    (tests included) that writes a match and immediately expects the read
    side to reflect it rather than up to _CACHE_TTL_SECONDS-stale data.
    """
    for id_a, id_b, score in matches:
        cur.execute(_RECORD_SQL, (id_a, id_b, score))
    if matches:
        reset_superseded_ids_cache()


def _compute_superseded_listing_ids(cur: psycopg2.extensions.cursor) -> set[int]:
    """The real computation, unconditionally fresh (see module docstring on
    why superseded_listing_ids() itself no longer calls this directly).

    Two queries total, regardless of how many duplicate groups exist --
    not one query per group. That N+1 shape used to cost ~0.7s locally
    (one round-trip per group is cheap on a local connection), but
    diagnostic timing on the deployed Render->Neon path showed the exact
    same computation taking 16.6s: each round-trip is far more expensive
    over that network hop, and it was paying for one per group. Fetching
    every group's rows in a single WHERE id = ANY(%s) call and grouping
    them in Python removes the multiplier entirely -- this is what
    actually fixed the production latency; the TTL cache alone only
    helped requests after the first one in a 10-minute window.
    """
    cur.execute(
        "SELECT listing_id_a, listing_id_b FROM duplicate_matches WHERE score >= %s",
        (AUTO_RESOLVE_THRESHOLD,),
    )
    pairs = [(r["listing_id_a"], r["listing_id_b"]) for r in cur.fetchall()]
    groups = group_pairs(pairs)

    all_ids = [listing_id for group in groups for listing_id in group]
    if not all_ids:
        return set()
    cur.execute(_LISTING_FIELDS + " WHERE id = ANY(%s)", (all_ids,))
    rows_by_id = {row["id"]: row for row in (dict(r) for r in cur.fetchall())}

    superseded: set[int] = set()
    for group in groups:
        rows = [rows_by_id[listing_id] for listing_id in group if listing_id in rows_by_id]
        if len(rows) < 2:
            continue
        superseded |= {row["id"] for row in rows} - {pick_canonical(rows)}
    return superseded


def superseded_listing_ids(cur: psycopg2.extensions.cursor) -> set[int]:
    """Ids analytics must EXCLUDE so duplicate groups count once.

    Only matches at or above AUTO_RESOLVE_THRESHOLD are used to build
    groups: below that (the "Possible Duplicate" tier) precision is too low
    to safely drop a listing from analytics — see dedup.match_status and
    the fixture validation it cites. Those pairs surface via
    possible_duplicate_pairs() for human review instead. Every group above
    the bar keeps its canonical listing (dedup.pick_canonical) and
    contributes the rest here. Consumers filter with e.g. WHERE id != ALL(%s).

    Cached in-process for _CACHE_TTL_SECONDS (see the module-level comment
    above) -- a cache hit costs a lock acquisition and a dict lookup,
    nothing on the DB.
    """
    global _cache
    with _cache_lock:
        if _cache is not None and time.monotonic() - _cache[0] < _CACHE_TTL_SECONDS:
            return _cache[1]
        ids = _compute_superseded_listing_ids(cur)
        _cache = (time.monotonic(), ids)
        return ids


def superseded_listing_ids_conn(dsn: str) -> set[int]:
    """Connection-owning wrapper for superseded_listing_ids().

    Checks the cache before opening a connection at all -- a warm cache
    should cost nothing beyond a lock and a dict lookup, not even a trip to
    open a DB connection just to hand back a value already sitting in
    memory (Neon's serverless connections are not free/instant either).
    """
    with _cache_lock:
        if _cache is not None and time.monotonic() - _cache[0] < _CACHE_TTL_SECONDS:
            return _cache[1]
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return superseded_listing_ids(cur)


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
