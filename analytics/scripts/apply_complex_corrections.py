"""Unified apply script for complex_id corrections (Session 0/0.5 follow-up).

Executes ONLY what is listed in an --actions JSON file -- never derives
what to do from a bulk dry-run report directly. That file is expected to
be a human-approved subset of a dry-run report's buckets (see
dry_run_complex_reextract.py); this script does not know or care which
bucket an action came from, only that a person signed off on this exact
list.

Every action and its listing update are committed in the same transaction,
so neither can survive without the other. Idempotent: re-running the same actions file is safe --
already-applied actions (matched by listing_id + action + new_complex_name
in complex_link_audit) are skipped, not re-applied or double-audited.

Actions file schema:
    {"actions": [
        {"listing_id": int, "action": "unlink"|"reassign",
         "old_complex_name": str, "new_complex_name": str|null,
         "reason": str, "evidence_text": str, "district": str},
        ...
    ]}

Usage:
    # 1. See exactly what would happen -- no writes.
    python analytics/scripts/apply_complex_corrections.py \
        --dsn "$DATABASE_URL" --actions scripts/approved_actions_batch1.json \
        --script-version v1 --dry-run

    # 2. Apply for real.
    python analytics/scripts/apply_complex_corrections.py \
        --dsn "$DATABASE_URL" --actions scripts/approved_actions_batch1.json \
        --script-version v1 --apply

    # 3. Independently re-verify the result (safe to run any time).
    python analytics/scripts/apply_complex_corrections.py \
        --dsn "$DATABASE_URL" --actions scripts/approved_actions_batch1.json \
        --script-version v1 --post-check
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import psycopg2
import psycopg2.extras


def load_actions(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    actions = data["actions"]
    if not isinstance(actions, list):
        raise ValueError("actions must be a list")
    required = {"listing_id", "action", "old_complex_name", "new_complex_name", "reason", "evidence_text", "district"}
    seen_ids: set[int] = set()
    for a in actions:
        missing = required - a.keys()
        if missing:
            raise ValueError(f"action is missing required fields: {sorted(missing)}")
        if not isinstance(a["listing_id"], int) or isinstance(a["listing_id"], bool):
            raise ValueError(f"listing_id must be an integer: {a['listing_id']!r}")
        if a["listing_id"] in seen_ids:
            raise ValueError(f"duplicate action for listing {a['listing_id']}")
        seen_ids.add(a["listing_id"])
        if a["action"] not in ("unlink", "reassign"):
            raise ValueError(f"unknown action {a['action']!r} for listing {a['listing_id']}")
        if a["action"] == "reassign" and not a.get("new_complex_name"):
            raise ValueError(f"reassign action for listing {a['listing_id']} is missing new_complex_name")
        if a["action"] == "unlink" and a.get("new_complex_name") is not None:
            raise ValueError(f"unlink action for listing {a['listing_id']} must have null new_complex_name")
        for field in ("old_complex_name", "reason", "evidence_text"):
            if not isinstance(a[field], str) or not a[field].strip():
                raise ValueError(f"{field} must be non-empty for listing {a['listing_id']}")
    return actions


def already_applied(cur: psycopg2.extensions.cursor, action: dict, script_version: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM complex_link_audit
        WHERE listing_id = %(listing_id)s AND action = %(action)s
          AND script_version = %(script_version)s
          AND new_complex_name IS NOT DISTINCT FROM %(new_complex_name)s
        """,
        {**action, "script_version": script_version},
    )
    return cur.fetchone() is not None


def current_complex(cur: psycopg2.extensions.cursor, listing_id: int) -> tuple[int | None, str | None]:
    cur.execute(
        """
        SELECT l.complex_id, c.canonical_name
        FROM listings l LEFT JOIN complexes c ON l.complex_id = c.id
        WHERE l.id = %s
        """,
        (listing_id,),
    )
    row = cur.fetchone()
    return (row["complex_id"], row["canonical_name"]) if row else (None, None)


def get_or_create_complex_id(cur: psycopg2.extensions.cursor, canonical_name: str) -> int:
    cur.execute("SELECT id FROM complexes WHERE canonical_name = %s", (canonical_name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    raise ValueError(
        f"complex {canonical_name!r} does not exist in `complexes` -- "
        "reassignment must target an existing, already-reviewed canonical "
        "complex, not silently create a new one."
    )


def apply_one(cur: psycopg2.extensions.cursor, action: dict, script_version: str, dry_run: bool) -> str:
    listing_id = action["listing_id"]
    old_complex_id, live_old_name = current_complex(cur, listing_id)

    if live_old_name != action["old_complex_name"]:
        return (
            f"SKIP id={listing_id}: expected old complex "
            f"{action['old_complex_name']!r}, DB currently has {live_old_name!r} "
            "(already changed since the dry-run -- re-audit before forcing this)"
        )

    new_complex_id = None
    if action["action"] == "reassign":
        new_complex_id = get_or_create_complex_id(cur, action["new_complex_name"])

    if dry_run:
        verb = "unlink" if action["action"] == "unlink" else f"relink -> {action['new_complex_name']}"
        return f"DRY-RUN id={listing_id}: {live_old_name} -- {verb}"

    cur.execute(
        "UPDATE listings SET complex_id = %s WHERE id = %s",
        (new_complex_id, listing_id),
    )
    cur.execute(
        """
        INSERT INTO complex_link_audit
            (listing_id, action, old_complex_id, old_complex_name,
             new_complex_id, new_complex_name, reason, evidence_text,
             district, script_version)
        VALUES (%(listing_id)s, %(action)s, %(old_complex_id)s, %(old_complex_name)s,
                %(new_complex_id)s, %(new_complex_name)s, %(reason)s, %(evidence_text)s,
                %(district)s, %(script_version)s)
        """,
        {
            **action,
            "old_complex_id": old_complex_id,
            "new_complex_id": new_complex_id,
            "script_version": script_version,
        },
    )
    return f"APPLIED id={listing_id}: {live_old_name} -> {action.get('new_complex_name') or 'NULL'}"


def post_check(cur: psycopg2.extensions.cursor, actions: list[dict], script_version: str) -> None:
    n_ok = n_bad = 0
    for action in actions:
        cur.execute(
            """
            SELECT 1 FROM complex_link_audit
            WHERE listing_id = %(listing_id)s AND action = %(action)s
              AND script_version = %(script_version)s
              AND new_complex_name IS NOT DISTINCT FROM %(new_complex_name)s
            """,
            {**action, "script_version": script_version},
        )
        audited = cur.fetchone() is not None
        _, live_name = current_complex(cur, action["listing_id"])
        expected = action["new_complex_name"] if action["action"] == "reassign" else None
        matches = live_name == expected
        if audited and matches:
            n_ok += 1
        else:
            n_bad += 1
            print(f"  MISMATCH id={action['listing_id']}: audited={audited} live_complex={live_name!r} expected={expected!r}")
    print(f"post-check: {n_ok} OK, {n_bad} mismatch, {len(actions)} total")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--actions", required=True)
    parser.add_argument("--script-version", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--post-check", action="store_true")
    args = parser.parse_args()

    actions = load_actions(args.actions)
    print(f"loaded {len(actions)} action(s) from {args.actions}")

    with psycopg2.connect(args.dsn) as conn:
        if args.dry_run or args.post_check:
            conn.set_session(readonly=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if args.post_check:
                post_check(cur, actions, args.script_version)
                conn.rollback()
                return

            skipped_already_applied = 0
            for action in actions:
                if not args.dry_run and already_applied(cur, action, args.script_version):
                    skipped_already_applied += 1
                    continue
                print(apply_one(cur, action, args.script_version, dry_run=args.dry_run))

            if args.dry_run:
                conn.rollback()
            else:
                conn.commit()
                print(f"skipped (already applied): {skipped_already_applied}")

    print("dry-run only, nothing written" if args.dry_run else "applied and committed")


if __name__ == "__main__":
    main()
