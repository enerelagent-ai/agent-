"""Backfill reviewed complex IDs after migration 010.

Usage:
    python analytics/scripts/backfill_complexes.py --dsn "$DATABASE_URL" --apply

Without --apply it performs a read-only coverage preview.
"""

from __future__ import annotations

import argparse
from collections import Counter

import psycopg2
import psycopg2.extras

from analytics.complexes import COMPLEX_ALIASES, extract_complex, normalize_complex_name


def candidates(cur: psycopg2.extensions.cursor) -> list[tuple[int, str]]:
    """Return listing IDs and reviewed unit-level canonical matches."""
    cur.execute("SELECT id, title FROM listings")
    result: list[tuple[int, str]] = []
    for listing_id, title in cur.fetchall():
        match = extract_complex(title)
        if match and match.matched_alias is not None and match.relation == "unit":
            result.append((listing_id, match.canonical_name))
    return result


def apply_backfill(cur: psycopg2.extensions.cursor, rows: list[tuple[int, str]]) -> int:
    """Upsert canonical complexes and attach IDs to candidate listings."""
    names = sorted({name for _, name in rows})
    ids: dict[str, int] = {}
    for name in names:
        cur.execute(
            """
            INSERT INTO complexes (canonical_name, normalized_name, aliases)
            VALUES (%s, %s, %s)
            ON CONFLICT (canonical_name) DO UPDATE SET
                normalized_name = EXCLUDED.normalized_name,
                aliases = EXCLUDED.aliases,
                updated_at = now()
            RETURNING id
            """,
            (name, normalize_complex_name(name), list(COMPLEX_ALIASES.get(name, ()))),
        )
        returned = cur.fetchone()
        ids[name] = returned["id"] if isinstance(returned, dict) else returned[0]
    psycopg2.extras.execute_batch(
        cur,
        "UPDATE listings SET complex_id = %s WHERE id = %s",
        [(ids[name], listing_id) for listing_id, name in rows],
    )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with psycopg2.connect(args.dsn) as conn:
        if not args.apply:
            conn.set_session(readonly=True)
        with conn.cursor() as cur:
            rows = candidates(cur)
            counts = Counter(name for _, name in rows)
            print(f"candidate_listings={len(rows)} canonical_complexes={len(counts)}")
            for name, count in counts.most_common(20):
                print(f"{count:>5}  {name}")
            if args.apply:
                print(f"updated={apply_backfill(cur, rows)}")


if __name__ == "__main__":
    main()
