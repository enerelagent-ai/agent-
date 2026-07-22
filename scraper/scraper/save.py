"""Map parsed ad dicts onto the listings table and upsert them into Postgres."""

import hashlib
import re
from typing import Any

import psycopg2
import psycopg2.extras

AREA_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
LEADING_INT_RE = re.compile(r"^(\d+)")
NEGOTIABLE_MARKER = "үнэ тохирно"

# Coarse duplicate-candidate key: same unit re-posted should collide, price
# edits should not. Week 4 dedup logic refines matching beyond this hash.
_DEDUP_FIELDS = ("listing_type", "property_type", "district", "address", "rooms", "area_sqm")

_UPSERT_SQL = """
    INSERT INTO listings (
        source, source_url, title, description, price, price_raw, price_negotiable,
        area_sqm, rooms,
        district, address, lat, lng, contact_phone, photo_urls,
        dedup_hash, listing_type, property_type, property_subtype,
        posted_at, posted_raw, specs
    )
    VALUES (
        %(source)s, %(source_url)s, %(title)s, %(description)s, %(price)s, %(price_raw)s,
        %(price_negotiable)s, %(area_sqm)s, %(rooms)s,
        %(district)s, %(address)s, %(lat)s, %(lng)s, %(contact_phone)s, %(photo_urls)s,
        %(dedup_hash)s, %(listing_type)s, %(property_type)s, %(property_subtype)s,
        %(posted_at)s, %(posted_raw)s, %(specs)s
    )
    ON CONFLICT (source, source_url) DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        price = EXCLUDED.price,
        price_raw = EXCLUDED.price_raw,
        price_negotiable = EXCLUDED.price_negotiable,
        area_sqm = EXCLUDED.area_sqm,
        rooms = EXCLUDED.rooms,
        district = EXCLUDED.district,
        address = EXCLUDED.address,
        lat = EXCLUDED.lat,
        lng = EXCLUDED.lng,
        contact_phone = EXCLUDED.contact_phone,
        photo_urls = EXCLUDED.photo_urls,
        dedup_hash = EXCLUDED.dedup_hash,
        listing_type = EXCLUDED.listing_type,
        property_type = EXCLUDED.property_type,
        property_subtype = EXCLUDED.property_subtype,
        posted_at = EXCLUDED.posted_at,
        posted_raw = EXCLUDED.posted_raw,
        specs = EXCLUDED.specs,
        scraped_at = now()
"""


def normalize_dsn(dsn: str) -> str:
    """Accept both plain libpq URLs and SQLAlchemy-style postgresql+psycopg2:// URLs."""
    return dsn.replace("postgresql+psycopg2://", "postgresql://", 1)


def parse_area_sqm(raw: str | None) -> float | None:
    """Extract the numeric area from a raw 'Талбай' spec value.

    Seller-entered values are messy ('296 м²', '69.85 м²', '150 м² м²');
    the first number wins. Returns None when no number is present.
    """
    if not raw:
        return None
    match = AREA_NUMBER_RE.search(raw)
    return float(match.group().replace(",", ".")) if match else None


def parse_price_negotiable(price_raw: str | None) -> bool | None:
    """Whether the display price text carries 'Үнэ тохирно' (negotiable).

    Returns None when there is no price text to judge from.
    """
    if not price_raw:
        return None
    return NEGOTIABLE_MARKER in price_raw.lower()


def parse_rooms(subcategory: str | None) -> int | None:
    """Room count from an apartment subcategory like '3 өрөө' or '5+ өрөө'.

    Non-apartment subcategories ('Хажуу өрөө түрээслүүлнэ') carry no leading
    number and yield None.
    """
    if not subcategory:
        return None
    match = LEADING_INT_RE.match(subcategory.strip())
    return int(match.group(1)) if match else None


def compute_dedup_hash(row: dict[str, Any]) -> str:
    """Deterministic sha256 over the coarse duplicate-candidate fields.

    Floats are rounded to one decimal and text lowercased so trivial
    formatting differences don't split candidates.
    """
    parts = []
    for field in _DEDUP_FIELDS:
        value = row.get(field)
        if isinstance(value, float):
            value = round(value, 1)
        parts.append("" if value is None else str(value))
    return hashlib.sha256("|".join(parts).lower().encode("utf-8")).hexdigest()


def listing_row_from_parsed(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """Map one parse_detail_page() dict onto listings columns.

    Returns None for unusable records (missing url or title, e.g. a fetch
    that never cleared the bot challenge).
    """
    if not parsed.get("url") or not parsed.get("title"):
        return None
    specs = parsed.get("specs") or {}
    phones = parsed.get("phones") or []
    row: dict[str, Any] = {
        "source": "unegui",
        "source_url": parsed["url"],
        "title": parsed["title"],
        "description": parsed.get("description"),
        "price": parsed.get("price"),
        "price_raw": parsed.get("price_raw"),
        "price_negotiable": parse_price_negotiable(parsed.get("price_raw")),
        "area_sqm": parse_area_sqm(specs.get("Талбай")),
        "rooms": parse_rooms(parsed.get("property_subcategory")),
        "district": parsed.get("district"),
        "address": parsed.get("location_raw"),
        "lat": parsed.get("latitude"),
        "lng": parsed.get("longitude"),
        "contact_phone": phones[0] if phones else None,
        "photo_urls": parsed.get("photo_urls") or [],
        "listing_type": parsed.get("listing_type"),
        "property_type": parsed.get("property_category"),
        "property_subtype": parsed.get("property_subcategory"),
        "posted_at": parsed.get("posted_at"),
        "posted_raw": parsed.get("posted_raw"),
        "specs": psycopg2.extras.Json(specs),
    }
    row["dedup_hash"] = compute_dedup_hash(row)
    return row


def recently_scraped(
    cur: psycopg2.extensions.cursor, urls: list[str], days: float
) -> set[str]:
    """Subset of urls whose listings were already scraped within `days` days.

    Lets an interrupted full-scrape run resume without re-fetching pages it
    already processed (and without hammering the site twice). Expects a
    RealDictCursor (the convention for cursor-taking helpers here).
    """
    if not urls:
        return set()
    cur.execute(
        "SELECT source_url FROM listings"
        " WHERE source_url = ANY(%s) AND scraped_at > now() - %s * interval '1 day'",
        (urls, days),
    )
    return {row["source_url"] for row in cur.fetchall()}


def recently_scraped_urls(dsn: str, urls: list[str], days: float) -> set[str]:
    """Connection-owning wrapper around recently_scraped() for the pipeline."""
    if not urls:
        return set()
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            result = recently_scraped(cur, urls, days)
    conn.close()
    return result


def upsert_listings(dsn: str, rows: list[dict[str, Any]]) -> int:
    """Upsert mapped rows on (source, source_url) in one transaction.

    Re-scraping the same ad updates the existing row (and refreshes
    scraped_at) instead of duplicating it. Returns the number of rows sent.
    """
    if not rows:
        return 0
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, _UPSERT_SQL, rows)
    conn.close()
    return len(rows)
