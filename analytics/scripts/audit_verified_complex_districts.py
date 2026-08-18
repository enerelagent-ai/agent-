"""Read-only audit of stored assignments against verified district registry.

The registry is an allowlist, not a majority-vote inference.  This script
never updates listings; it emits exact mismatch rows for human review.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras


_DISTRICT_PATTERNS = {
    "Хан-Уул": re.compile(r"(?<!\w)(?:худ|хан[ -]?уул)(?!\w)", re.IGNORECASE),
}


def classify_mismatch(row: dict) -> str:
    """Separate accepted seller-text evidence from unresolved conflicts."""
    text = f"{row.get('title') or ''} {row.get('description') or ''}"
    if any(
        (pattern := _DISTRICT_PATTERNS.get(district)) is not None
        and pattern.search(text)
        for district in row["allowed_districts"]
    ):
        return "source_conflict_with_explicit_verified_text"
    return "unresolved"


def audit(cur) -> tuple[list[dict], list[dict]]:
    cur.execute(
        """
        WITH registry AS (
            SELECT c.id AS complex_id, c.canonical_name,
                   array_agg(DISTINCT v.district ORDER BY v.district) AS allowed_districts,
                   array_agg(DISTINCT v.registry_version ORDER BY v.registry_version) AS registry_versions
            FROM complexes c
            JOIN verified_complex_locations v ON v.complex_id = c.id
            GROUP BY c.id, c.canonical_name
        )
        SELECT r.canonical_name, r.allowed_districts, r.registry_versions,
               count(l.id)::int AS assigned_count,
               count(l.id) FILTER (
                   WHERE (l.district IS NULL OR NOT (l.district = ANY(r.allowed_districts)))
                     AND o.id IS NULL
               )::int AS mismatch_count
        FROM registry r
        LEFT JOIN listings l ON l.complex_id = r.complex_id
        LEFT JOIN verified_listing_complex_overrides o
          ON o.source = l.source AND o.source_url = l.source_url
         AND o.complex_id = l.complex_id
        GROUP BY r.complex_id, r.canonical_name, r.allowed_districts, r.registry_versions
        ORDER BY r.canonical_name
        """
    )
    summary = [dict(row) for row in cur.fetchall()]

    cur.execute(
        """
        WITH registry AS (
            SELECT c.id AS complex_id, c.canonical_name,
                   array_agg(DISTINCT v.district ORDER BY v.district) AS allowed_districts,
                   array_agg(DISTINCT v.registry_version ORDER BY v.registry_version) AS registry_versions
            FROM complexes c
            JOIN verified_complex_locations v ON v.complex_id = c.id
            GROUP BY c.id, c.canonical_name
        )
        SELECT l.id AS listing_id, r.canonical_name AS assigned_complex,
               r.allowed_districts, r.registry_versions,
               l.district, l.address, l.title, l.description,
               l.source_url, l.is_active
        FROM listings l
        JOIN registry r ON r.complex_id = l.complex_id
        LEFT JOIN verified_listing_complex_overrides o
          ON o.source = l.source AND o.source_url = l.source_url
         AND o.complex_id = l.complex_id
        WHERE (l.district IS NULL OR NOT (l.district = ANY(r.allowed_districts)))
          AND o.id IS NULL
        ORDER BY r.canonical_name, l.id
        """
    )
    mismatches = [dict(row) for row in cur.fetchall()]
    for row in mismatches:
        row["review_status"] = classify_mismatch(row)
    return summary, mismatches


def render_markdown(summary: list[dict], mismatches: list[dict], generated_at: str) -> str:
    lines = [
        "# Verified complex district dry-run",
        "",
        f"Үүсгэсэн: {generated_at}",
        "",
        "**READ-ONLY:** Энэ тайлан DB-д ямар ч өөрчлөлт хийгээгүй. Registry нь гараар баталгаажсан allowlist; mismatch мөр бүр apply хийхээс өмнө хүнээр шалгагдана.",
        "",
        "## Тойм",
        "",
        "| Хотхон | Зөвшөөрөгдсөн дүүрэг | Нийт assignment | Mismatch |",
        "|---|---|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['canonical_name']} | {', '.join(row['allowed_districts'])} | "
            f"{row['assigned_count']} | {row['mismatch_count']} |"
        )
    unresolved = [row for row in mismatches if row["review_status"] == "unresolved"]
    accepted = [row for row in mismatches if row["review_status"] != "unresolved"]
    lines += ["", f"## Unresolved mismatch ({len(unresolved)})", ""]
    if not unresolved:
        lines.append("(байхгүй)")
    for row in unresolved:
        lines.append(
            f"- id={row['listing_id']} assigned={row['assigned_complex']!r} "
            f"district={row['district']!r} allowed={row['allowed_districts']} "
            f"active={row['is_active']} — \"{row['title']}\" "
            f"(address: {row['address']!r})"
        )
    lines += ["", f"## Accepted source-location conflict ({len(accepted)})", ""]
    if not accepted:
        lines.append("(байхгүй)")
    for row in accepted:
        lines.append(
            f"- id={row['listing_id']} assigned={row['assigned_complex']!r} "
            f"source_district={row['district']!r} seller text explicitly names "
            f"{row['allowed_districts']} — \"{row['title']}\""
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--md-output", required=True)
    parser.add_argument("--json-output", required=True)
    args = parser.parse_args()
    generated_at = datetime.now(timezone.utc).isoformat()

    with psycopg2.connect(args.dsn) as conn:
        conn.set_session(readonly=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            summary, mismatches = audit(cur)
        conn.rollback()

    payload = {
        "generated_at": generated_at,
        "read_only": True,
        "summary": summary,
        "mismatches": mismatches,
        "unresolved_count": sum(row["review_status"] == "unresolved" for row in mismatches),
        "mismatch_by_complex": dict(Counter(row["assigned_complex"] for row in mismatches)),
    }
    with open(args.json_output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    with open(args.md_output, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(summary, mismatches, generated_at))

    print(f"registered complexes: {len(summary)}")
    print(f"assignments audited: {sum(row['assigned_count'] for row in summary)}")
    print(f"district mismatches: {len(mismatches)}")
    print(f"unresolved mismatches: {sum(row['review_status'] == 'unresolved' for row in mismatches)}")
    print(f"wrote {args.md_output} and {args.json_output}")


if __name__ == "__main__":
    main()
