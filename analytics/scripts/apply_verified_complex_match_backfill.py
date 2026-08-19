"""Apply the Release 3 verified legacy-match pilot safely.

Eligibility is re-derived from live data using the read-only audit classifier;
the caller must provide the exact count observed in the reviewed dry-run. The
script aborts if that count changed, if an alias cannot be resolved, or if a
listing already has different current evidence.

Usage:
    python analytics/scripts/apply_verified_complex_match_backfill.py \
        --dsn "$DATABASE_URL" --expected-count 922 --dry-run
    python analytics/scripts/apply_verified_complex_match_backfill.py \
        --dsn "$DATABASE_URL" --expected-count 922 --apply
    python analytics/scripts/apply_verified_complex_match_backfill.py \
        --dsn "$DATABASE_URL" --expected-count 922 --post-check
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import normalize_complex_name
try:
    # Imported as ``scripts.*`` by the analytics test suite.
    from scripts.dry_run_verified_complex_match_backfill import audit
except ModuleNotFoundError:
    # Executed by GitHub Actions as ``python analytics/scripts/<file>.py``.
    from dry_run_verified_complex_match_backfill import audit


SCRIPT_NOTE = "legacy verified-match backfill v1: extractor + verified-location + district guard"


def eligible_rows(cur: psycopg2.extensions.cursor, expected_count: int) -> list[dict[str, Any]]:
    results, _ = audit(cur)
    eligible = [row for row in results if row["bucket"] == "eligible_approved_pilot"]
    if len(eligible) != expected_count:
        raise ValueError(
            f"eligible count changed: expected {expected_count}, live audit found {len(eligible)}; "
            "regenerate and review the dry-run before applying"
        )
    return eligible


def prepare_rows(
    cur: psycopg2.extensions.cursor, rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    """Resolve reviewed aliases and skip listings with current evidence."""
    listing_ids = [row["listing_id"] for row in rows]
    cur.execute(
        """
        SELECT listing_id
        FROM listing_complex_matches
        WHERE is_current AND listing_id = ANY(%s)
        """,
        (listing_ids,),
    )
    already_current = {row["listing_id"] for row in cur.fetchall()}

    normalized_aliases = sorted({normalize_complex_name(row["matched_alias"]) for row in rows})
    cur.execute(
        """
        SELECT id, complex_id, normalized_alias
        FROM complex_aliases
        WHERE is_active AND normalized_alias = ANY(%s)
        """,
        (normalized_aliases,),
    )
    aliases = {row["normalized_alias"]: row for row in cur.fetchall()}

    prepared = []
    for row in rows:
        if row["listing_id"] in already_current:
            continue
        normalized = normalize_complex_name(row["matched_alias"])
        alias = aliases.get(normalized)
        if alias is None:
            raise ValueError(
                f"listing {row['listing_id']} alias {row['matched_alias']!r} is not in complex_aliases"
            )
        if alias["complex_id"] != row["assigned_complex_id"]:
            raise ValueError(
                f"listing {row['listing_id']} alias resolves to complex {alias['complex_id']}, "
                f"expected {row['assigned_complex_id']}"
            )
        prepared.append({**row, "matched_alias_id": alias["id"]})
    return prepared, len(already_current)


def apply_rows(cur: psycopg2.extensions.cursor, rows: list[dict[str, Any]]) -> int:
    for row in rows:
        cur.execute(
            """
            INSERT INTO listing_complex_matches
                (listing_id, complex_id, matched_alias_id, relation, confidence,
                 evidence_text, source_field, extractor_version, review_status,
                 reviewer_note, reviewed_at, is_current)
            VALUES
                (%(listing_id)s, %(assigned_complex_id)s, %(matched_alias_id)s,
                 %(relation)s, %(confidence)s, %(evidence_text)s, 'title',
                 %(extractor_version)s, 'approved', %(script_note)s, now(), true)
            ON CONFLICT (listing_id, complex_id, extractor_version, evidence_text)
            DO UPDATE SET
                matched_alias_id = EXCLUDED.matched_alias_id,
                relation = EXCLUDED.relation,
                confidence = EXCLUDED.confidence,
                review_status = 'approved',
                reviewer_note = EXCLUDED.reviewer_note,
                reviewed_at = now(),
                is_current = true,
                updated_at = now()
            """,
            {**row, "script_note": SCRIPT_NOTE},
        )
    return len(rows)


def post_check(cur: psycopg2.extensions.cursor, expected_count: int) -> dict[str, int]:
    eligible = eligible_rows(cur, expected_count)
    eligible_ids = {row["listing_id"] for row in eligible}
    cur.execute(
        """
        SELECT m.listing_id, m.complex_id, m.relation, m.review_status,
               m.reviewed_at, m.is_current
        FROM listing_complex_matches m
        WHERE m.reviewer_note = %s
        """,
        (SCRIPT_NOTE,),
    )
    applied = list(cur.fetchall())
    applied_ids = {row["listing_id"] for row in applied}
    invalid = sum(
        row["listing_id"] not in eligible_ids
        or row["relation"] != "unit"
        or row["review_status"] != "approved"
        or row["reviewed_at"] is None
        or not row["is_current"]
        for row in applied
    )
    cur.execute(
        """
        SELECT count(*)::int AS n
        FROM (
            SELECT listing_id
            FROM listing_complex_matches
            WHERE is_current
            GROUP BY listing_id
            HAVING count(*) > 1
        ) duplicates
        """
    )
    duplicate_current = cur.fetchone()["n"]
    return {
        "eligible": len(eligible_ids),
        "applied": len(applied_ids),
        "missing": len(eligible_ids - applied_ids),
        "unexpected": len(applied_ids - eligible_ids),
        "invalid": invalid,
        "duplicate_current": duplicate_current,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--expected-count", required=True, type=int)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--post-check", action="store_true")
    args = parser.parse_args()

    with psycopg2.connect(args.dsn) as conn:
        if args.dry_run or args.post_check:
            conn.set_session(readonly=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if args.post_check:
                result = post_check(cur, args.expected_count)
                print("post-check: " + ", ".join(f"{key}={value}" for key, value in result.items()))
                if any(result[key] for key in ("missing", "unexpected", "invalid", "duplicate_current")):
                    sys.exit(1)
                return

            eligible = eligible_rows(cur, args.expected_count)
            prepared, already_current = prepare_rows(cur, eligible)
            print(
                f"eligible={len(eligible)} prepared={len(prepared)} "
                f"already_current={already_current}"
            )
            if args.dry_run:
                conn.rollback()
                print("dry-run only, nothing written")
                return

            applied = apply_rows(cur, prepared)
            conn.commit()
            print(f"applied={applied} skipped_current={already_current}; committed")


if __name__ == "__main__":
    main()
