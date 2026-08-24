"""Import licensed public Hotkhon Intelligence map/profile data.

Only robots-allowed public pages are fetched. The importer is idempotent,
records source URLs and cutoff dates, and never touches our verified registry.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import Json, execute_batch

from analytics.db import normalize_dsn

SOURCE = "hotkhon.mn"
MAP_URL = "https://hotkhon.mn/hotkhon/map/"
USER_AGENT = "EnerelMarket-PublicImporter/1.0 (+licensed republication)"


@dataclass(frozen=True)
class PublicMapData:
    cutoff: str
    profiles: list[dict]
    contours: list[dict]


def extract_map_data(html: str) -> PublicMapData:
    points_match = re.search(r"window\.HK=(\[.*?\]);window\.HKP=", html, re.DOTALL)
    contours_match = re.search(r"window\.HKP=(\[.*?\]);window\.HKCUT=", html, re.DOTALL)
    cutoff_match = re.search(r'window\.HKCUT="(\d{4}-\d{2}-\d{2})"', html)
    if not points_match or not contours_match or not cutoff_match:
        raise ValueError("public map payload was not found or its format changed")
    return PublicMapData(
        cutoff=cutoff_match.group(1),
        profiles=json.loads(points_match.group(1)),
        contours=json.loads(contours_match.group(1)),
    )


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def import_map_data(dsn: str, data: PublicMapData, *, dry_run: bool) -> dict:
    contour_slugs = {
        data.profiles[item["i"]]["s"]
        for item in data.contours
        if isinstance(item.get("i"), int) and item["i"] < len(data.profiles)
    }
    profiles = []
    for item in data.profiles:
        slug = item["s"]
        profiles.append({
            "source": SOURCE,
            "slug": slug,
            "url": f"https://hotkhon.mn/hotkhon/{slug}/",
            "name": item["t"],
            "district": item.get("d"),
            "price": item.get("p") * 1_000_000 if item.get("p") is not None else None,
            "listings": item.get("n", 0),
            "lat": item.get("y"),
            "lng": item.get("x"),
            "photo": item.get("u") or None,
            "has_contour": slug in contour_slugs or bool(item.get("fp")),
            "location_kind": item.get("lv") or "point",
            "cutoff": data.cutoff,
        })
    if dry_run:
        return {"profiles": len(profiles), "contours": len(data.contours), "cutoff": data.cutoff}

    with psycopg2.connect(normalize_dsn(dsn)) as connection:
        with connection.cursor() as cursor:
            execute_batch(cursor, """
                INSERT INTO public_complex_profiles
                    (source, source_slug, source_url, canonical_name, district,
                     median_price_per_sqm, active_listings, lat, lng, photo_url,
                     has_contour, location_kind, data_as_of, scraped_at)
                VALUES (%(source)s, %(slug)s, %(url)s, %(name)s, %(district)s,
                        %(price)s, %(listings)s, %(lat)s, %(lng)s, %(photo)s,
                        %(has_contour)s, %(location_kind)s, %(cutoff)s, now())
                ON CONFLICT (source, source_slug) DO UPDATE SET
                    source_url=EXCLUDED.source_url, canonical_name=EXCLUDED.canonical_name,
                    district=EXCLUDED.district, median_price_per_sqm=EXCLUDED.median_price_per_sqm,
                    active_listings=EXCLUDED.active_listings, lat=EXCLUDED.lat, lng=EXCLUDED.lng,
                    photo_url=EXCLUDED.photo_url, has_contour=EXCLUDED.has_contour,
                    location_kind=EXCLUDED.location_kind, data_as_of=EXCLUDED.data_as_of,
                    scraped_at=now()
            """, profiles, page_size=200)
            cursor.execute("DELETE FROM public_complex_contours WHERE source=%s", (SOURCE,))
            contours = []
            per_slug_index: dict[str, int] = {}
            for item in data.contours:
                point_index = item.get("i")
                if not isinstance(point_index, int) or point_index >= len(data.profiles):
                    continue
                slug = data.profiles[point_index]["s"]
                polygon_index = per_slug_index.get(slug, 0)
                per_slug_index[slug] = polygon_index + 1
                contours.append((SOURCE, slug, polygon_index, item.get("lv"), Json(item["g"]), data.cutoff))
            execute_batch(cursor, """
                INSERT INTO public_complex_contours
                    (source, source_slug, polygon_index, location_kind, geometry, data_as_of, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
            """, contours, page_size=200)
    return {"profiles": len(profiles), "contours": len(contours), "cutoff": data.cutoff}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input-html", help="Use a saved public map page instead of fetching")
    args = parser.parse_args()
    html = open(args.input_html, encoding="utf-8").read() if args.input_html else fetch_text(MAP_URL)
    result = import_map_data(args.database_url, extract_map_data(html), dry_run=args.dry_run)
    result["imported_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
