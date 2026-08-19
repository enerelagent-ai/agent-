"""Backfill non-approved legacy complex evidence into the review queue.

Only the two explicitly reviewed dry-run buckets are accepted:
``unit_unregistered_manual_review`` and ``landmark_manual_review``. Nothing
here approves a match or changes ``listings.complex_id``.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import normalize_complex_name
from scripts.dry_run_verified_complex_match_backfill import audit


PENDING_BUCKETS = {
    "unit_unregistered_manual_review",
    "landmark_manual_review",
}
SCRIPT_NOTE_PREFIX = "legacy pending-match backfill v1: "


def pending_rows(
    cur: psycopg2.extensions.cursor,
    expected_unit_unregistered: int,
    expected_landmark: int,
) -> list[dict[str, Any]]:
    results, _ = audit(cur)
    counts = Counter(row["bucket"] for row in results)
    expected = {
        "unit_unregistered_manual_review": expected_unit_unregistered,
        "landmark_manual_review": expected_landmark,
    }
    actual = {bucket: counts.get(bucket, 0) for bucket in PENDING_BUCKETS}
    if actual != expected:
        raise ValueError(
            f"pending bucket counts changed: expected {expected}, live audit found {actual}; "
            "regenerate and review the dry-run before applying"
        )
    return [row for row in results if row["bucket"] in PENDING_BUCKETS]


def prepare_rows(
    cur: psycopg2.extensions.cursor, rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    listing_ids = [row["listing_id"] for row in rows]
    cur.execute(
        "SELECT listing_id FROM listing_complex_matches WHERE is_current AND listing_id = ANY(%s)",
        (listing_ids,),
    )
    already_current = {row["listing_id"] for row in cur.fetchall()}
    normalized = sorted({normalize_complex_name(row["matched_alias"]) for row in rows})
    cur.execute(
        """
        SELECT id, complex_id, normalized_alias
        FROM complex_aliases
        WHERE is_active AND normalized_alias = ANY(%s)
        """,
        (normalized,),
    )
    aliases = {row["normalized_alias"]: row for row in cur.fetchall()}

    prepared = []
    for row in rows:
        if row["listing_id"] in already_current:
            continue
        alias = aliases.get(normalize_complex_name(row["matched_alias"]))
        if alias is None:
            raise ValueError(
                f"listing {row['listing_id']} alias {row['matched_alias']!r} is not in complex_aliases"
            )
        if alias["complex_id"] != row["assigned_complex_id"]:
            raise ValueError(
                f"listing {row['listing_id']} alias maps to complex {alias['complex_id']}, "
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
                 %(extractor_version)s, 'pending', %(reviewer_note)s, NULL, true)
            ON CONFLICT (listing_id, complex_id, extractor_version, evidence_text)
            DO UPDATE SET
                matched_alias_id = EXCLUDED.matched_alias_id,
                relation = EXCLUDED.relation,
                confidence = EXCLUDED.confidence,
                review_status = 'pending',
                reviewer_note = EXCLUDED.reviewer_note,
                reviewed_at = NULL,
                is_current = true,
                updated_at = now()
            """,
            {
                **row,
                "reviewer_note": SCRIPT_NOTE_PREFIX + row["bucket"],
            },
        )
    return len(rows)


def post_check(
    cur: psycopg2.extensions.cursor,
    expected_unit_unregistered: int,
    expected_landmark: int,
) -> dict[str, int]:
    expected_rows = pending_rows(cur, expected_unit_unregistered, expected_landmark)
    expected_by_id = {row["listing_id"]: row for row in expected_rows}
    cur.execute(
        """
        SELECT listing_id, complex_id, relation, review_status, reviewed_at, is_current
        FROM listing_complex_matches
        WHERE reviewer_note LIKE %s
        """,
        (SCRIPT_NOTE_PREFIX + "%",),
    )
    applied = list(cur.fetchall())
    applied_ids = {row["listing_id"] for row in applied}
    invalid = sum(
        row["listing_id"] not in expected_by_id
        or row["complex_id"] != expected_by_id[row["listing_id"]]["assigned_complex_id"]
        or row["relation"] != expected_by_id[row["listing_id"]]["relation"]
        or row["review_status"] != "pending"
        or row["reviewed_at"] is not None
        or not row["is_current"]
        for row in applied
    )
    expected_ids = set(expected_by_id)
    return {
        "expected": len(expected_ids),
        "applied": len(applied_ids),
        "missing": len(expected_ids - applied_ids),
        "unexpected": len(applied_ids - expected_ids),
        "invalid": invalid,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--expected-unit-unregistered", required=True, type=int)
    parser.add_argument("--expected-landmark", required=True, type=int)
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
                result = post_check(
                    cur, args.expected_unit_unregistered, args.expected_landmark
                )
                print("post-check: " + ", ".join(f"{key}={value}" for key, value in result.items()))
                if any(result[key] for key in ("missing", "unexpected", "invalid")):
                    sys.exit(1)
                return

            rows = pending_rows(
                cur, args.expected_unit_unregistered, args.expected_landmark
            )
            prepared, already_current = prepare_rows(cur, rows)
            print(
                f"pending={len(rows)} prepared={len(prepared)} "
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

