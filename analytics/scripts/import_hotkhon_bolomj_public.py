"""Import the licensed, public Hotkhon affordability snapshot."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

from analytics.db import normalize_dsn
SOURCE = "hotkhon.mn"
SOURCE_URL = "https://hotkhon.mn/bolomj/"
USER_AGENT = "EnerelMarket-PublicImporter/1.0 (+licensed republication)"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


@dataclass(frozen=True)
class AffordabilityData:
    data_as_of: str
    districts: list[str]
    listings: list[list[int | float]]
    rules: dict


def extract_affordability_data(html: str) -> AffordabilityData:
    payload = re.search(
        r"var L\s*=\s*(\[\[.*?\]\]),\s*D\s*=\s*(\[.*?\]),\s*CAP\s*=\s*(\d+),\s*MIN_DOWN\s*=\s*([\d.]+),\s*MAX_AREA\s*=\s*([\d.]+)",
        html,
        re.DOTALL,
    )
    if not payload:
        raise ValueError("public affordability payload was not found or its format changed")
    date_matches = re.findall(r"20\d{2}-\d{2}-\d{2}", html)
    data_as_of = max(date_matches) if date_matches else date.today().isoformat()
    listings = json.loads(payload.group(1))
    districts = json.loads(payload.group(2))
    if not all(len(item) == 3 and 0 <= item[2] < len(districts) for item in listings):
        raise ValueError("invalid affordability listing tuple")
    return AffordabilityData(
        data_as_of=data_as_of,
        districts=districts,
        listings=listings,
        rules={
            "loan_cap_mnt": int(payload.group(3)),
            "min_downpayment_ratio": float(payload.group(4)),
            "max_area_sqm": float(payload.group(5)),
            "formula_version": "hotkhon-public-v1",
        },
    )


def import_data(dsn: str, data: AffordabilityData, *, dry_run: bool) -> dict:
    result = {"listings": len(data.listings), "districts": len(data.districts), "data_as_of": data.data_as_of}
    if dry_run:
        return result
    with psycopg2.connect(normalize_dsn(dsn)) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public_affordability_snapshots
                (source, data_as_of, source_url, districts, listings, rules, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (source, data_as_of) DO UPDATE SET
                source_url=EXCLUDED.source_url, districts=EXCLUDED.districts,
                listings=EXCLUDED.listings, rules=EXCLUDED.rules, scraped_at=now()
            """,
            (SOURCE, data.data_as_of, SOURCE_URL, Json(data.districts), Json(data.listings), Json(data.rules)),
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input-html")
    args = parser.parse_args()
    html = Path(args.input_html).read_text(encoding="utf-8") if args.input_html else fetch_text(SOURCE_URL)
    result = import_data(args.database_url, extract_affordability_data(html), dry_run=args.dry_run)
    result["imported_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
