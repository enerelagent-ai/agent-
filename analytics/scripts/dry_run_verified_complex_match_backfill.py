"""Read-only Release 3 pilot for legacy complex assignment evidence.

This script does not infer that an existing ``listings.complex_id`` is true.
It re-runs the versioned extractor, checks the independently reviewed district
registry, and proposes only the rows that satisfy every approval invariant.

Usage:
    python analytics/scripts/dry_run_verified_complex_match_backfill.py \
        --dsn "$DATABASE_URL" \
        --md-output docs/verified_complex_match_backfill_dry_run.md \
        --json-output analytics/scripts/verified_complex_match_backfill_dry_run.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import COMPLEX_EXTRACTOR_VERSION, extract_complex


_DISTRICT_PATTERNS = {
    "Хан-Уул": re.compile(r"(?<!\w)(?:худ|хан[ -]?уул)(?!\w)", re.IGNORECASE),
    "Баянзүрх": re.compile(r"(?<!\w)(?:бзд|баянз[үv]рх)(?!\w)", re.IGNORECASE),
    "Сүхбаатар": re.compile(r"(?<!\w)(?:сбд|с[үv]хбаатар)(?!\w)", re.IGNORECASE),
    "Баянгол": re.compile(r"(?<!\w)(?:бгд|баянгол)(?!\w)", re.IGNORECASE),
    "Сонгинохайрхан": re.compile(r"(?<!\w)(?:схд|сонгинохайрхан)(?!\w)", re.IGNORECASE),
    "Чингэлтэй": re.compile(r"(?<!\w)(?:чд|чингэлтэй)(?!\w)", re.IGNORECASE),
}


def has_explicit_district_evidence(row: dict[str, Any], district: str) -> bool:
    pattern = _DISTRICT_PATTERNS.get(district)
    text = f"{row.get('title') or ''} {row.get('description') or ''}"
    return pattern.search(text) is not None if pattern else False


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return one review bucket without treating the legacy link as truth."""
    match = extract_complex(row.get("title"))
    allowed = list(row.get("allowed_districts") or [])
    extractor_agrees = bool(
        match
        and match.matched_alias is not None
        and match.canonical_name == row["assigned_canonical"]
    )
    district_passed = bool(
        row.get("has_exact_override")
        or row.get("district") in allowed
        or any(has_explicit_district_evidence(row, district) for district in allowed)
    )

    if not extractor_agrees:
        bucket = "extractor_disagrees_manual_review"
    elif match.relation != "unit":
        bucket = "landmark_manual_review"
    elif not allowed:
        bucket = "unit_unregistered_manual_review"
    elif not district_passed:
        bucket = "district_mismatch_manual_review"
    elif not row.get("is_active", True):
        bucket = "eligible_inactive_history"
    else:
        bucket = "eligible_approved_pilot"

    return {
        "listing_id": row["listing_id"],
        "source_url": row["source_url"],
        "title": row["title"],
        "district": row.get("district"),
        "is_active": bool(row.get("is_active", True)),
        "assigned_complex_id": row["assigned_complex_id"],
        "assigned_canonical": row["assigned_canonical"],
        "allowed_districts": allowed,
        "has_exact_override": bool(row.get("has_exact_override")),
        "district_guard_passed": district_passed,
        "extractor_version": COMPLEX_EXTRACTOR_VERSION,
        "extracted_canonical": match.canonical_name if match else None,
        "matched_alias": match.matched_alias if match else None,
        "relation": match.relation if match else None,
        "confidence": match.confidence if match else None,
        "evidence_text": row["title"] if match else None,
        "proposed_review_status": (
            "approved"
            if bucket in ("eligible_approved_pilot", "eligible_inactive_history")
            else "pending"
        ),
        "bucket": bucket,
    }


def audit(cur: psycopg2.extensions.cursor) -> tuple[list[dict[str, Any]], int]:
    cur.execute(
        """
        WITH registry AS (
            SELECT complex_id,
                   array_agg(DISTINCT district ORDER BY district) AS allowed_districts
            FROM verified_complex_locations
            GROUP BY complex_id
        )
        SELECT l.id AS listing_id, l.source, l.source_url, l.title,
               l.description, l.district,
               l.is_active,
               c.id AS assigned_complex_id,
               c.canonical_name AS assigned_canonical,
               r.allowed_districts,
               EXISTS (
                   SELECT 1 FROM verified_listing_complex_overrides o
                   WHERE o.source = l.source
                     AND o.source_url = l.source_url
                     AND o.complex_id = l.complex_id
               ) AS has_exact_override
        FROM listings l
        JOIN complexes c ON c.id = l.complex_id
        LEFT JOIN registry r ON r.complex_id = l.complex_id
        ORDER BY l.id
        """
    )
    results = [classify_row(dict(row)) for row in cur.fetchall()]
    cur.execute("SELECT count(*)::int AS n FROM listing_complex_matches")
    existing_matches = cur.fetchone()["n"]
    return results, existing_matches


def render_markdown(
    results: list[dict[str, Any]], existing_matches: int, generated_at: str
) -> str:
    counts = Counter(row["bucket"] for row in results)
    order = [
        "eligible_approved_pilot",
        "eligible_inactive_history",
        "unit_unregistered_manual_review",
        "district_mismatch_manual_review",
        "landmark_manual_review",
        "extractor_disagrees_manual_review",
    ]
    lines = [
        "# Verified complex match legacy backfill — dry-run",
        "",
        f"Үүсгэсэн: {generated_at}",
        "",
        "**READ-ONLY:** DB-д ямар ч match, review эсвэл `complex_id` өөрчлөлт хийгээгүй. "
        "Хуучин assignment-ийг үнэн гэж тооцоогүй; extractor + verified registry + "
        "district guard гурвыг шинээр шалгасан.",
        "",
        f"- Legacy assignment шалгасан: {len(results)}",
        f"- Өмнө нь байгаа match evidence: {existing_matches}",
        f"- Extractor version: `{COMPLEX_EXTRACTOR_VERSION}`",
        "",
        "## Ангилал",
        "",
        "| Bucket | Тоо | Автомат apply |",
        "|---|---:|---|",
    ]
    for bucket in order:
        if bucket == "eligible_approved_pilot":
            allowed = "Тийм — active pilot"
        elif bucket == "eligible_inactive_history":
            allowed = "Pilot биш — historical backfill"
        else:
            allowed = "Үгүй — human review"
        lines.append(f"| `{bucket}` | {counts.get(bucket, 0)} | {allowed} |")

    eligible = [row for row in results if row["bucket"] == "eligible_approved_pilot"]
    eligible_by_complex = Counter(row["assigned_canonical"] for row in eligible)
    lines += [
        "",
        "## Eligible approved pilot",
        "",
        "Эдгээр мөрөнд одоогийн extractor хуучин canonical хотхонтой санал нийлж, relation "
        "нь `unit`, alias нь reviewed, хотхон registry-д бүртгэлтэй, district guard давсан. "
        "Доорх нь эхний 100 мөр; бүрэн жагсаалт JSON-д байна.",
        "",
        "### Active pilot — хотхоноор",
        "",
        "| Хотхон | Eligible active зар |",
        "|---|---:|",
    ]
    for name, count in eligible_by_complex.most_common():
        lines.append(f"| {name} | {count} |")
    lines += [
        "",
        "### Active pilot — эхний 100 мөр",
        "",
    ]
    for row in eligible[:100]:
        lines.append(
            f"- id={row['listing_id']} **{row['assigned_canonical']}** "
            f"district={row['district']!r} confidence={row['confidence']} — "
            f"\"{row['title']}\""
        )

    lines += ["", "## Manual-review жишээ", ""]
    for bucket in order[2:]:
        lines.append(f"### {bucket} ({counts.get(bucket, 0)})")
        lines.append("")
        examples = [item for item in results if item["bucket"] == bucket][:20]
        for row in examples:
            lines.append(
                f"- id={row['listing_id']} assigned={row['assigned_canonical']!r} "
                f"extracted={row['extracted_canonical']!r} relation={row['relation']!r} "
                f"district={row['district']!r} allowed={row['allowed_districts']} — "
                f"\"{row['title']}\""
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
            results, existing_matches = audit(cur)
        conn.rollback()

    payload = {
        "generated_at": generated_at,
        "read_only": True,
        "extractor_version": COMPLEX_EXTRACTOR_VERSION,
        "existing_match_count": existing_matches,
        "counts": dict(Counter(row["bucket"] for row in results)),
        "eligible_active_by_complex": dict(Counter(
            row["assigned_canonical"]
            for row in results
            if row["bucket"] == "eligible_approved_pilot"
        )),
        "results": results,
    }
    with open(args.json_output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    with open(args.md_output, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(results, existing_matches, generated_at))

    for bucket, count in payload["counts"].items():
        print(f"{bucket}: {count}")
    print(f"total: {len(results)}; existing_matches: {existing_matches}")
    print(f"wrote {args.md_output} and {args.json_output}")


if __name__ == "__main__":
    main()
