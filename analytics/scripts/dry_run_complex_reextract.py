"""Session 0/0.5 dry-run: bucket every currently complex_id-assigned
listing for review. Writes nothing to the database (readonly session).

Bucketing keys off the HUMAN-LABELED fixture (tests/fixtures/
landmark_relabel_69.json), not off a fresh extractor re-run alone --
re-deriving "confirmed" status purely from extractor output collapsed the
69 audit rows into "landmark, therefore safe to unlink" without noticing
that 10 of them were only ever labeled "ambiguous" and 3 are known
extractor gaps (still resolve wrong because of a missing alias, not
because the row itself is fine). Those 13 are NOT safe to unlink on the
same footing as the 29 a human actually confirmed as pure landmark
references.

Four buckets:
    confirmed_unlink               -- label == landmark_none (29): human
                                       confirmed no other complex is named.
    other_unit_manual_review       -- label == landmark_reassign AND the
                                       fixed extractor now resolves the
                                       suggested complex as a unit match
                                       (27): reassignment candidates, still
                                       gated on human approval before apply.
    extractor_exception_manual_review -- label == landmark_reassign but the
                                       extractor does NOT yet resolve as
                                       expected (3): a missing-alias gap,
                                       needs a person, not an assumption.
    ambiguous_manual_review        -- label == ambiguous (10): never
                                       auto-unlinked or auto-reassigned.
Every other currently-assigned listing (not in the 69-row fixture) stays
"unchanged" -- but is still re-checked against the fixed extractor, not
assumed, in case the regex change had any effect this audit didn't predict.

Usage:
    python analytics/scripts/dry_run_complex_reextract.py \
        --dsn "$DATABASE_URL" \
        --md-output docs/complex_reextract_dry_run.md \
        --json-output analytics/scripts/complex_reextract_dry_run.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import extract_complex

LANDMARK_FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "landmark_relabel_69.json"


def load_human_labels() -> dict[int, dict[str, Any]]:
    fixture = json.loads(LANDMARK_FIXTURE.read_text(encoding="utf-8"))
    return {row["listing_id"]: row for row in fixture["rows"]}


def classify_all(cur: psycopg2.extensions.cursor, human_labels: dict[int, dict]) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT l.id, l.title, l.district, c.canonical_name AS assigned_canonical
        FROM listings l JOIN complexes c ON l.complex_id = c.id
        ORDER BY l.id
        """
    )
    results = []
    for row in cur.fetchall():
        match = extract_complex(row["title"])
        now_relation = match.relation if match else None
        now_canonical = match.canonical_name if match else None
        labeled = human_labels.get(row["id"])

        if labeled is None:
            # Not one of the 69 audited rows -- still re-checked, never
            # just assumed fine, but no human label exists to defer to.
            if now_canonical == row["assigned_canonical"] and now_relation == "unit":
                bucket = "unchanged"
            else:
                # A surprise the original audit didn't catch -- route to
                # the same cautious bucket as a labeled ambiguous row
                # rather than guessing.
                bucket = "ambiguous_manual_review"
        elif labeled["label"] == "landmark_none":
            bucket = "confirmed_unlink"
        elif labeled["label"] == "ambiguous":
            bucket = "ambiguous_manual_review"
        elif labeled["label"] == "landmark_reassign":
            resolved = now_relation == "unit" and now_canonical == labeled["suggested_canonical"]
            bucket = "other_unit_manual_review" if resolved else "extractor_exception_manual_review"
        else:
            bucket = "ambiguous_manual_review"

        results.append({
            "listing_id": row["id"],
            "district": row["district"],
            "assigned_canonical": row["assigned_canonical"],
            "title": row["title"],
            "now_relation": now_relation,
            "now_canonical": now_canonical,
            "human_label": labeled["label"] if labeled else None,
            "suggested_canonical": labeled["suggested_canonical"] if labeled else None,
            "bucket": bucket,
        })
    return results


def render_markdown(results: list[dict]) -> str:
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_bucket[r["bucket"]].append(r)
    counts = Counter(r["bucket"] for r in results)

    lines = [
        "# Хотхон assignment dry-run re-extract тайлан (v2 — human label-д тулгуурлав)",
        "",
        f"Vvсгэсэн: {datetime.now(timezone.utc).isoformat()}",
        "",
        "**Анхаар**: dry-run — ямар ч мөр өөрчлөгдөөгvй. Bucket нь extractor-ийн "
        "гаралт дангаараа биш, 69 мөрийн гараар баталгаажуулсан label-ийг "
        "vндэслэсэн. `confirmed_unlink`-ээс бусад бvх bucket ХVН баталгаажуулах "
        "ёстой.",
        "",
        f"## Тойм ({len(results)} нийт assignment)",
        "",
        "| Bucket | Тоо |",
        "|---|---|",
    ]
    for bucket in [
        "unchanged", "confirmed_unlink", "other_unit_manual_review",
        "ambiguous_manual_review", "extractor_exception_manual_review",
    ]:
        lines.append(f"| {bucket} | {counts.get(bucket, 0)} |")
    lines.append("")

    lines += ["## other_unit_manual_review — reassignment нэр дэвшигч (27, батлалт хvлээж байна)", ""]
    for r in by_bucket["other_unit_manual_review"]:
        lines.append(
            f"- id={r['listing_id']} district={r['district']!r} "
            f"{r['assigned_canonical']} → **{r['now_canonical']}** — \"{r['title']}\""
        )
    lines.append("")

    lines += ["## extractor_exception_manual_review — дутуу alias-аас vvдсэн (3)", ""]
    for r in by_bucket["extractor_exception_manual_review"]:
        lines.append(
            f"- id={r['listing_id']} district={r['district']!r} "
            f"assigned={r['assigned_canonical']} санал болгосон={r['suggested_canonical']} "
            f"одоогийн extractor: relation={r['now_relation']} canonical={r['now_canonical']} "
            f"— \"{r['title']}\""
        )
    lines.append("")

    lines += ["## ambiguous_manual_review — АВТОМАТААР unlink/reassign хийхгvй (10)", ""]
    for r in by_bucket["ambiguous_manual_review"]:
        lines.append(
            f"- id={r['listing_id']} district={r['district']!r} "
            f"assigned={r['assigned_canonical']} тэмдэглэл={r['suggested_canonical']!r} "
            f"— \"{r['title']}\""
        )
    lines.append("")

    lines += [
        f"## confirmed_unlink ({len(by_bucket['confirmed_unlink'])}) — batalgaажсан landmark, нэр дэвшигчгvй",
        "",
        "(бvрэн жагсаалт JSON файлд)",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--md-output", required=True)
    parser.add_argument("--json-output", required=True)
    args = parser.parse_args()

    human_labels = load_human_labels()

    with psycopg2.connect(args.dsn) as conn:
        conn.set_session(readonly=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            results = classify_all(cur, human_labels)
        conn.rollback()

    with open(args.json_output, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": datetime.now(timezone.utc).isoformat(), "results": results},
            f, ensure_ascii=False, indent=2,
        )
    with open(args.md_output, "w", encoding="utf-8") as f:
        f.write(render_markdown(results))

    counts = Counter(r["bucket"] for r in results)
    for bucket, n in counts.items():
        print(f"{bucket}: {n}")
    print(f"total: {len(results)}")
    print(f"wrote {args.md_output} and {args.json_output}")


if __name__ == "__main__":
    main()
