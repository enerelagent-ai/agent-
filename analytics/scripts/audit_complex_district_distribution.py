"""Session 0 (v3 plan) read-only audit: per-complex district/khoroo spread,
multi-complex-mention ambiguity, and a landmark-relation consistency check.

Writes nothing to the database (opens a readonly session) and draws no
conclusions about which district is "correct" -- that would be circular
(deriving truth from data that might itself be wrong). It only reports
distributions for a human to review against an independently-built
registry (Session 0.5).

Usage:
    python analytics/scripts/audit_complex_district_distribution.py \
        --dsn "$DATABASE_URL" \
        --md-output docs/complex_district_audit_report.md \
        --json-output analytics/scripts/complex_district_audit.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import _compiled_aliases, extract_complex, normalize_complex_name

_KHOROO_RE = re.compile(
    r"(?:\bхороо\s*№?\s*(?P<after>\d+)\b|\b(?P<before>\d+)\s*-?\s*р?\s*хороо\b)",
    re.IGNORECASE,
)
_LANDMARK_CUE = re.compile(
    r"^\s*(?:(?:ын|ийн|ы|ий|ны|ний)\s+)?"
    r"(?P<cue>хажууд|ойролцоо|харалдаа|ард|урд|хойно|"
    r"баруун(?:\s+урд|\s+хойд|\s+талд)?|зүүн(?:\s+урд|\s+хойд|\s+талд)?|"
    r"эсрэг\s+талд|замын\s+эсрэг\s+талд)",
    re.IGNORECASE,
)


def _khoroo_from_address(address: str | None) -> str | None:
    """Best-effort khoroo number from the free-text address field.

    There is no structured khoroo column (listings.address is free text,
    e.g. "Хан-Уул, Хан-Уул, Хороо 15" or just "Хан-Уул, Хурд") -- this is
    a lossy heuristic for audit visibility only, never a join key.
    """
    if not address:
        return None
    match = _KHOROO_RE.search(address)
    return (match.group("after") or match.group("before")) if match else None


def _assigned_landmark_evidence(title: str, canonical_name: str) -> str | None:
    """Return a nearby-location cue following the assigned complex alias.

    This deliberately lives in the audit rather than the production
    extractor.  The extractor's relation check slices after the bare alias,
    which can leave a Mongolian genitive suffix (``-ийн``) before ``хажууд``
    and miss the cue.  The compiled alias pattern consumes that suffix, so
    checking from the full match end exposes suspicious stored assignments
    without changing any database value.
    """
    normalized = normalize_complex_name(title)
    for canonical, _alias, pattern in _compiled_aliases():
        if canonical != canonical_name:
            continue
        match = pattern.search(normalized)
        if match and (cue := _LANDMARK_CUE.match(normalized[match.end():])):
            return cue.group("cue")
    return None


def per_complex_distribution(cur: psycopg2.extensions.cursor) -> dict[str, Any]:
    """District/khoroo spread for every currently-assigned complex.

    Reports the majority district as one fact among several -- NOT as a
    verified truth. Session 0.5's registry is the actual ground truth
    source; using this report's own majority to "correct" itself would be
    circular (a systematically-wrong majority would just confirm itself).
    """
    cur.execute(
        """
        SELECT c.canonical_name, l.id, l.district, l.address, l.title
        FROM listings l JOIN complexes c ON l.complex_id = c.id
        ORDER BY c.canonical_name, l.id
        """
    )
    rows = cur.fetchall()

    by_complex: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_complex[row["canonical_name"]].append(row)

    report: dict[str, Any] = {}
    for name, items in sorted(by_complex.items()):
        district_counts = Counter(i["district"] for i in items)
        khoroo_counts = Counter(k for i in items if (k := _khoroo_from_address(i["address"])) is not None)
        total = len(items)
        majority_district, majority_n = district_counts.most_common(1)[0]
        minority = [i for i in items if i["district"] != majority_district]
        report[name] = {
            "total_listings": total,
            "district_distribution": dict(district_counts),
            "khoroo_distribution": dict(khoroo_counts),
            "khoroo_coverage": sum(khoroo_counts.values()),
            "majority_district": majority_district,
            "majority_pct": round(100 * majority_n / total, 1),
            "minority_rows": [
                {"listing_id": i["id"], "district": i["district"], "address": i["address"], "title": i["title"]}
                for i in minority
            ],
        }
    return report


def multi_complex_mentions(cur: psycopg2.extensions.cursor) -> list[dict]:
    """Titles whose text matches MORE than one canonical complex's alias --
    extract_complex() silently picks one via its unit-then-length
    tie-break; these are exactly the cases where that tie-break should be
    reviewed by a human, not trusted blind. Scans every listing, not just
    already-assigned ones, since a currently-unassigned or landmark-only
    row can still carry this ambiguity.
    """
    cur.execute("SELECT id, title, district, complex_id FROM listings WHERE title IS NOT NULL")
    aliases = _compiled_aliases()
    findings = []
    for row in cur.fetchall():
        normalized = normalize_complex_name(row["title"])
        hits = {canonical for canonical, _alias, pattern in aliases if pattern.search(normalized)}
        if len(hits) > 1:
            findings.append({
                "listing_id": row["id"],
                "title": row["title"],
                "district": row["district"],
                "candidates": sorted(hits),
                "assigned_complex_id": row["complex_id"],
            })
    return findings


def assignment_consistency_check(cur: psycopg2.extensions.cursor) -> list[dict]:
    """Compare each stored assignment with today's extractor result.

    The original backfill only stored ``complex_id``; it did not persist the
    evidence or relation that produced it.  Re-running the extractor is
    therefore an audit aid, not ground truth.  We report every assigned row
    that now resolves to a landmark, no match, or a different canonical name.
    """
    cur.execute(
        """
        SELECT l.id, l.title, c.canonical_name
        FROM listings l JOIN complexes c ON l.complex_id = c.id
        """
    )
    findings = []
    for row in cur.fetchall():
        match = extract_complex(row["title"])
        reason = None
        landmark_evidence = _assigned_landmark_evidence(row["title"], row["canonical_name"])
        if landmark_evidence:
            reason = "suspected_landmark"
        elif match is None:
            reason = "no_match"
        elif match.relation == "landmark":
            reason = "landmark"
        elif match.canonical_name != row["canonical_name"]:
            reason = "canonical_mismatch"
        if reason:
            findings.append({
                "listing_id": row["id"],
                "title": row["title"],
                "assigned_canonical": row["canonical_name"],
                "extracted_canonical": match.canonical_name if match else None,
                "extracted_relation": match.relation if match else None,
                "evidence_text": landmark_evidence,
                "reason": reason,
            })
    return findings


def render_markdown(district_report: dict, multi_mentions: list[dict], landmark_findings: list[dict]) -> str:
    lines = [
        "# Хотхон-district audit тайлан (Session 0, v3 төлөвлөгөө)",
        "",
        f"Vvсгэсэн: {datetime.now(timezone.utc).isoformat()}",
        "",
        "**Анхаар**: Энэ тайлан ЗӨВХӨН тайлагнана — ямар ч мөрийг автоматаар "
        "зассангvй, ямар ч дvvргийг \"vнэн\" гэж баталсангvй (олонхийн санал "
        "circular logic vvсгэдэг тул). Session 0.5-ийн бие даасан registry-г "
        "vvсгэхэд ашиглах баримт материал.",
        "",
        f"## 1. Дvvргийн тархалт ({len(district_report)} хотхон)",
        "",
        "| Хотхон | Нийт | Гол дvvрэг | Гол дvvргийн % | Өөр дvvргvvд | Хорооны тархалт (coverage) |",
        "|---|---|---|---|---|---|",
    ]
    n_clean = n_minor = n_major = 0
    for name, d in district_report.items():
        if d["majority_pct"] == 100.0:
            n_clean += 1
        elif d["majority_pct"] >= 95.0:
            n_minor += 1
        else:
            n_major += 1
        other = {k: v for k, v in d["district_distribution"].items() if k != d["majority_district"]}
        other_str = ", ".join(f"{k}:{v}" for k, v in sorted(other.items(), key=lambda kv: -kv[1])) or "—"
        khoroo_str = ", ".join(
            f"{k}-р:{v}" for k, v in sorted(d["khoroo_distribution"].items(), key=lambda kv: (-kv[1], int(kv[0])))
        ) or "—"
        lines.append(
            f"| {name} | {d['total_listings']} | {d['majority_district']} | "
            f"{d['majority_pct']}% | {other_str} | {khoroo_str} ({d['khoroo_coverage']}/{d['total_listings']}) |"
        )
    lines += [
        "",
        f"**Тойм**: {n_clean} хотхон 100% нэг дvvрэгтэй, {n_minor} хотхон "
        f"≥95% (цөөн зөрчилтэй), {n_major} хотхон <95% (илvv нарийвчлан "
        "vзэх шаардлагатай).",
        "",
        "## 2. Дvvрэг зөрсөн мөрvvд (гараар review хийх материал)",
        "",
    ]
    any_minority = False
    for name, d in district_report.items():
        if not d["minority_rows"]:
            continue
        any_minority = True
        lines.append(f"### {name} (гол: {d['majority_district']}, {d['majority_pct']}%)")
        lines.append("")
        for r in d["minority_rows"]:
            lines.append(f"- id={r['listing_id']} district={r['district']!r} — \"{r['title']}\" (address: {r['address']!r})")
        lines.append("")
    if not any_minority:
        lines.append("(байхгvй)")
        lines.append("")

    lines += [
        f"## 3. Олон хотхон зэрэг дурдсан мөр ({len(multi_mentions)})",
        "",
    ]
    if multi_mentions:
        for m in multi_mentions[:200]:
            lines.append(
                f"- id={m['listing_id']} district={m['district']!r} "
                f"candidates={m['candidates']} assigned_complex_id={m['assigned_complex_id']} "
                f"— \"{m['title']}\""
            )
        if len(multi_mentions) > 200:
            lines.append(f"... ({len(multi_mentions) - 200} vлдсэн, бvрэн жагсаалт JSON файлд)")
    else:
        lines.append("(байхгvй)")
    lines.append("")

    lines += [
        f"## 4. Stored assignment ба одоогийн extractor-ийн зөрүү ({len(landmark_findings)})",
        "",
        "Энэ нь автоматаар буруу гэсэн дvгнэлт биш. Хуучин backfill evidence/relation "
        "хадгалаагvй тул өнөөгийн extractor-тай landmark, no-match эсвэл canonical "
        "нэрээр зөрсөн мөрvvдийг гараар шалгах жагсаалт юм.",
        "",
    ]
    if landmark_findings:
        for f in landmark_findings:
            lines.append(
                f"- id={f['listing_id']} reason={f['reason']} "
                f"assigned={f['assigned_canonical']!r} extracted={f['extracted_canonical']!r} "
                f"relation={f['extracted_relation']!r} — \"{f['title']}\""
            )
    else:
        lines.append("(байхгvй — тогтвортой)")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--md-output", required=True)
    parser.add_argument("--json-output", required=True)
    args = parser.parse_args()

    with psycopg2.connect(args.dsn) as conn:
        conn.set_session(readonly=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            district_report = per_complex_distribution(cur)
            multi_mentions = multi_complex_mentions(cur)
            landmark_findings = assignment_consistency_check(cur)
        conn.rollback()

    with open(args.json_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "district_distribution": district_report,
                "multi_complex_mentions": multi_mentions,
                "assignment_consistency_findings": landmark_findings,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(args.md_output, "w", encoding="utf-8") as f:
        f.write(render_markdown(district_report, multi_mentions, landmark_findings))

    total_minority = sum(len(d["minority_rows"]) for d in district_report.values())
    print(f"complexes audited: {len(district_report)}")
    print(f"minority (district-mismatch) rows: {total_minority}")
    print(f"multi-complex-mention rows: {len(multi_mentions)}")
    print(f"assignment-consistency findings: {len(landmark_findings)}")
    print(f"wrote {args.md_output} and {args.json_output}")


if __name__ == "__main__":
    main()
