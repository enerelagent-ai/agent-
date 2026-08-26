"""Import licensed public Hotkhon Intelligence map/profile data.

Only robots-allowed public pages are fetched. The importer is idempotent,
records source URLs and cutoff dates, and never touches our verified registry.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html as html_module
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


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _number_before_label(html: str, label: str) -> float | None:
    value_then_label = (
        r'<div class="v[^"]*">\s*([\d.]+)[^<]*(?:<small>[^<]*</small>)?\s*</div>\s*'
        r'<div class="k">' + re.escape(label) + r'</div>'
    )
    label_then_value = (
        r'<div class="k">' + re.escape(label) + r'</div>\s*'
        r'<div class="v[^"]*">\s*([\d.]+)'
    )
    match = re.search(value_then_label, html, re.DOTALL) or re.search(label_then_value, html, re.DOTALL)
    return float(match.group(1)) if match else None


def extract_profile_metrics(html: str) -> dict:
    """Extract factual public metrics without copying authored UI/verdict text."""
    sub = re.search(r'<div class="sub">(.*?)</div>', html, re.DOTALL)
    price_range = re.search(r'<div class="v">\s*([\d.,]+)\s*[–-]\s*([\d.,]+).*?<div class="k">Үнийн хүрээ', html, re.DOTALL)
    history = re.search(r'<span class="rng">(\d{4}-\d{2}-\d{2})\s*[—-]+\s*(\d{4}-\d{2}-\d{2})</span>', html)
    profile: dict = {
        "building_summary": _text(sub.group(1)) if sub else None,
        "price_range_million": [float(price_range.group(1).replace(",", "")), float(price_range.group(2).replace(",", ""))] if price_range else None,
        "location_score": _number_before_label(html, "Байршлын оноо"),
        "clearance_days": _number_before_label(html, "Зар цэвэрлэгдэх"),
        "likely_sold": _number_before_label(html, "Зарагдсан байж болзошгүй"),
        "price_reductions_14d": _number_before_label(html, "Үнээ бууруулсан"),
        "rental_yield_pct": _number_before_label(html, "Түрээсийн өгөөж"),
        "history_range": list(history.groups()) if history else None,
    }

    room_section = re.search(r'<h2>Өрөөний тоогоор</h2>(.*?)(?:<h2>Байршлын задаргаа</h2>|<div class="sh" style="margin-top:0">\s*<h2>Байршлын задаргаа)', html, re.DOTALL)
    if room_section:
        profile["room_price_per_sqm_million"] = [
            {"rooms": int(rooms), "value": float(value)}
            for rooms, value in re.findall(r'<td>(\d+) өрөө</td>\s*<td class="r">([\d.]+)</td>', room_section.group(1))
        ]

    location_section = re.search(r'<h2>Байршлын задаргаа</h2>(.*?)(?:<h2>Зах зээлийн байдал</h2>|<div class="sh">\s*<h2>Зах зээлийн байдал)', html, re.DOTALL)
    if location_section:
        profile["location_breakdown"] = [
            {"label": _text(label), "score": float(score)}
            for label, score in re.findall(r'<div class="lab">\s*<span>(.*?)</span>\s*<span class="num">([\d.]+)</span>', location_section.group(1), re.DOTALL)
        ]

    drivers_section = re.search(r'<h2>Үнэд нөлөөлж буй хүчин зүйл</h2>(.*?)<h2>Байрны бүтэц</h2>', html, re.DOTALL)
    if drivers_section:
        profile["price_drivers"] = [
            {"label": _text(label), "impact_pct": float(value.replace("−", "-"))}
            for label, value in re.findall(r'<span class="lab">(.*?)</span>.*?<span class="val [^"]+">([+−-]?[\d.]+)%</span>', drivers_section.group(1), re.DOTALL)
        ]
    return {key: value for key, value in profile.items() if value not in (None, [], "")}


def fetch_profile_metrics(profiles: list[dict], *, workers: int = 12) -> dict[str, dict]:
    def fetch_one(item: dict) -> tuple[str, dict]:
        slug = item["s"]
        try:
            return slug, extract_profile_metrics(fetch_text(f"https://hotkhon.mn/hotkhon/{slug}/"))
        except Exception as exc:  # one changed/missing profile must not stop the daily feed
            return slug, {"import_error": str(exc)[:200]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        return dict(executor.map(fetch_one, profiles))


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


def import_map_data(dsn: str, data: PublicMapData, *, dry_run: bool, profile_metrics: dict[str, dict] | None = None) -> dict:
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
            "metrics": Json((profile_metrics or {}).get(slug, {})),
        })
    if dry_run:
        return {"profiles": len(profiles), "contours": len(data.contours), "cutoff": data.cutoff}

    with psycopg2.connect(normalize_dsn(dsn)) as connection:
        with connection.cursor() as cursor:
            execute_batch(cursor, """
                INSERT INTO public_complex_profiles
                    (source, source_slug, source_url, canonical_name, district,
                     median_price_per_sqm, active_listings, lat, lng, photo_url,
                     has_contour, location_kind, data_as_of, profile_metrics, scraped_at)
                VALUES (%(source)s, %(slug)s, %(url)s, %(name)s, %(district)s,
                        %(price)s, %(listings)s, %(lat)s, %(lng)s, %(photo)s,
                        %(has_contour)s, %(location_kind)s, %(cutoff)s, %(metrics)s, now())
                ON CONFLICT (source, source_slug) DO UPDATE SET
                    source_url=EXCLUDED.source_url, canonical_name=EXCLUDED.canonical_name,
                    district=EXCLUDED.district, median_price_per_sqm=EXCLUDED.median_price_per_sqm,
                    active_listings=EXCLUDED.active_listings, lat=EXCLUDED.lat, lng=EXCLUDED.lng,
                    photo_url=EXCLUDED.photo_url, has_contour=EXCLUDED.has_contour,
                    location_kind=EXCLUDED.location_kind, data_as_of=EXCLUDED.data_as_of,
                    profile_metrics=CASE WHEN EXCLUDED.profile_metrics = '{}'::jsonb
                        OR EXCLUDED.profile_metrics ? 'import_error'
                        THEN public_complex_profiles.profile_metrics ELSE EXCLUDED.profile_metrics END,
                    scraped_at=now()
            """, profiles, page_size=200)
            metric_updates = [
                (Json(metrics), SOURCE, slug)
                for slug, metrics in (profile_metrics or {}).items()
                if metrics and "import_error" not in metrics
            ]
            execute_batch(cursor, """
                UPDATE public_complex_profiles
                SET profile_metrics=%s, scraped_at=now()
                WHERE source=%s AND source_slug=%s
            """, metric_updates, page_size=200)
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
    parser.add_argument("--skip-profile-metrics", action="store_true")
    args = parser.parse_args()
    html = open(args.input_html, encoding="utf-8").read() if args.input_html else fetch_text(MAP_URL)
    data = extract_map_data(html)
    metrics = None if args.skip_profile_metrics else fetch_profile_metrics(data.profiles)
    result = import_map_data(args.database_url, data, dry_run=args.dry_run, profile_metrics=metrics)
    if metrics is not None:
        result["profile_metrics"] = sum(1 for item in metrics.values() if item and "import_error" not in item)
        result["profile_metric_errors"] = sum(1 for item in metrics.values() if "import_error" in item)
    result["imported_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
