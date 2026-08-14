"""Build a privacy-safe complex-name audit fixture from the curated CSV.

The source CSV contains phone and price data, so this script deliberately
emits only URL, current title, expected entity/name, and verification evidence.
It never treats a matching URL as proof: Unegui URLs can be reused for a new ad.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg2


NON_COMPLEX_LABELS = {
    "115-р сургуулийн хажууд": "landmark",
    "АПУ компаний хажууд": "landmark",
    "Мишээл экспо": "landmark",
    "Туул голын хойно байрлах 36-р байранд": "building",
    "Удирдлагын академийн байр": "building",
    "Хүрмэн TESCOMA-тай байр": "building",
    "Шинэ Зуун Билэг сургуулийн зүүн талд": "landmark",
    "зайсан удирдлагын академийн урд": "location",
}

# Only observed spelling/transliteration variants are listed. This is kept
# deliberately conservative: an unknown fuzzy match remains review_required.
ALIASES: dict[str, tuple[str, ...]] = {
    "Akoya Residence": ("akoya residence", "akoya tower", "akoyatower", "акояа тауэр", "акоя тауэр"),
    "Buti Town": ("buti town", "бути таун", "бүти таун"),
    "Gerlug vista": ("gerlug vista", "гэрлүг виста"),
    "Global Town": ("global town", "глобал таун"),
    "Hansvill": ("hansvill", "хансвилл"),
    "Japan Town": ("japan town", "жапан таун"),
    "Khan Hills": ("khan hills", "khan khills", "khankhills", "хан хиллс", "ханхиллс"),
    "King Tower": ("king tower", "king taur", "кинг тауэр", "кинг таур"),
    "Marshal Town": ("marshal town", "marshall town", "маршал таун", "маршилл таун", "маршил таун"),
    "Modun Town": ("modun town", "модун таун"),
    "Nobles Residence": ("nobles residence", "nobles хотхон"),
    "Ocean's 10 apartment": ("ocean's 10 apartment", "ocean 10 apartment", "ocean 10 апартмент", "оcean 10 апартмент"),
    "Park Garden": ("park garden", "парк гарден", "рark garden"),
    "Regis Place": ("regis place", "regis palace", "рэжис плэйс"),
    "River Garden": ("river garden", "ривер гарден"),
    "River Plaza": ("river plaza", "river tower", "ривер плаза", "ривер тауэр"),
    "River Villa": ("river villa", "ривер вилла"),
    "Sky Garden Residence": ("sky garden residence", "sky garden", "skygarden", "скай гарден"),
    "Sn tower": ("sn tower", "sn тауэр"),
    "Solaris Residence": ("solaris residence", "solaris plus residence", "solaris plus"),
    "Tokyo Town": ("tokyo town", "tokya town", "токио таун"),
    "Vega City": ("vega city", "вега сити"),
    "Жаргалан": ("жаргалан", "jargalan"),
    "Зайсан Green House": ("зайсан green house", "green house"),
    "Зайсан Энхжин": ("зайсан энхжин", "энхжин хотхон"),
    "Рапид": ("рапид", "хурд хороолол"),
    "Хүннү 2222": ("хүннү 2222", "хүннү-2222", "хүннү-222", "hunnu 2222", "hunnu2222"),
    "Хүннү Плюс": ("хүннү плюс", "хүннү plus", "хүннү пласт", "hunnu plus"),
}

# Manually reviewed conflicts where the current title names another property
# (or a clearly unrelated numbered neighbourhood) but that other name is not
# necessarily one of the CSV's canonical labels.
KNOWN_REUSED_URL_PATTERNS: dict[str, tuple[str, ...]] = {
    "Akoya Residence": ("aqua garden", "акуа гарден"),
    "Japan Town": ("ocean apartment", "ocean's 10", "ocean 10"),
    "KH apartment": ("home town",),
    "River Villa": ("баянмонгол хороолол", "river garden"),
    "Оргил Стар": ("3 оргил хотхон", "орчид парк", "orchid park"),
    "Цэнгэлдэх": ("1-р хороолол", "1р хороолол"),
}


def normalize(value: str) -> str:
    """Normalize text for conservative exact alias containment."""
    value = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return "".join(char for char in value if char.isalnum())


def label_aliases(label: str) -> tuple[str, ...]:
    """Return the canonical label plus its reviewed spelling variants."""
    return (label, *ALIASES.get(label, ()))


def matching_labels(title: str, labels: set[str]) -> set[str]:
    """Find canonical labels with a reviewed alias contained in title."""
    normalized_title = normalize(title)
    return {
        label
        for label in labels
        if any(normalize(alias) in normalized_title for alias in label_aliases(label))
    }


def classify_row(row: dict[str, str], title: str | None, labels: set[str]) -> dict[str, Any]:
    """Classify one CSV row without exposing its phone or price fields."""
    expected = row["Хотхон"].strip()
    result: dict[str, Any] = {
        "source_url": row["Холбоос"].strip(),
        "csv_label": expected,
        "current_title": title,
    }
    if title is None:
        result.update(entity_type="unknown", status="source_unavailable", evidence=None)
        return result

    if expected in NON_COMPLEX_LABELS:
        result.update(
            entity_type=NON_COMPLEX_LABELS[expected],
            status="confirmed_negative",
            evidence="curated_non_complex_label",
        )
        return result

    matches = matching_labels(title, labels)
    if expected in matches:
        direct = normalize(expected) in normalize(title)
        result.update(
            entity_type="complex",
            status="confirmed_positive",
            evidence="canonical_in_title" if direct else "reviewed_alias_in_title",
        )
    elif matches or any(
        normalize(pattern) in normalize(title)
        for pattern in KNOWN_REUSED_URL_PATTERNS.get(expected, ())
    ):
        result.update(
            entity_type="invalid",
            status="reused_url_mismatch",
            evidence="current_title_matches_other_complex",
            current_complex_candidates=sorted(matches),
        )
    else:
        # Manual review found no current-title evidence either way. Exclude it
        # from both positive and negative gold sets instead of inventing a label.
        result.update(
            entity_type="unknown",
            status="excluded_insufficient_evidence",
            evidence="manual_review_found_no_title_evidence",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-output", type=Path)
    args = parser.parse_args()

    with args.csv.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    required = {"Хотхон", "Холбоос"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"CSV must contain columns: {sorted(required)}")

    urls = [row["Холбоос"].strip() for row in rows]
    with psycopg2.connect(args.dsn) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_url, title FROM listings "
                "WHERE source = 'unegui' AND source_url = ANY(%s)",
                (urls,),
            )
            titles = dict(cur.fetchall())

    complex_labels = {row["Хотхон"].strip() for row in rows} - set(NON_COMPLEX_LABELS)
    audited = [classify_row(row, titles.get(row["Холбоос"].strip()), complex_labels) for row in rows]
    counts = Counter(item["status"] for item in audited)
    payload = {
        "schema_version": 1,
        "source": args.csv.name,
        "privacy": "Phone and price columns intentionally omitted.",
        "counts": dict(sorted(counts.items())),
        "rows": audited,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.fixture_output:
        gold_statuses = {"confirmed_positive", "confirmed_negative", "reused_url_mismatch"}
        fixture_rows = [item for item in audited if item["status"] in gold_statuses]
        fixture = {
            "schema_version": 1,
            "source": args.csv.name,
            "privacy": "Phone and price columns intentionally omitted.",
            "selection": "Only rows with current-title evidence; unavailable/insufficient rows excluded.",
            "counts": dict(sorted(Counter(item["status"] for item in fixture_rows).items())),
            "rows": fixture_rows,
        }
        args.fixture_output.parent.mkdir(parents=True, exist_ok=True)
        args.fixture_output.write_text(
            json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(payload["counts"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
