"""Map parsed ad dicts onto the listings table and upsert them into Postgres."""

import hashlib
import re
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import COMPLEX_ALIASES, extract_complex, normalize_complex_name

AREA_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
LEADING_INT_RE = re.compile(r"^(\d+)")
NEGOTIABLE_MARKER = "үнэ тохирно"

# Coarse duplicate-candidate key: same unit re-posted should collide, price
# edits should not. Week 4 dedup logic refines matching beyond this hash.
_DEDUP_FIELDS = ("listing_type", "property_type", "district", "address", "rooms", "area_sqm")

_UPSERT_SQL = """
    INSERT INTO listings (
        source, source_url, title, description, price, price_raw, price_negotiable,
        area_sqm, rooms, floor, total_floors, complex_id,
        district, address, lat, lng, contact_phone, photo_urls,
        view_count,
        dedup_hash, listing_type, property_type, property_subtype,
        posted_at, posted_raw, specs
    )
    VALUES (
        %(source)s, %(source_url)s, %(title)s, %(description)s, %(price)s, %(price_raw)s,
        %(price_negotiable)s, %(area_sqm)s, %(rooms)s, %(floor)s, %(total_floors)s,
        %(complex_id)s,
        %(district)s, %(address)s, %(lat)s, %(lng)s, %(contact_phone)s, %(photo_urls)s,
        %(view_count)s,
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
        floor = EXCLUDED.floor,
        total_floors = EXCLUDED.total_floors,
        complex_id = EXCLUDED.complex_id,
        district = EXCLUDED.district,
        address = EXCLUDED.address,
        lat = EXCLUDED.lat,
        lng = EXCLUDED.lng,
        contact_phone = EXCLUDED.contact_phone,
        photo_urls = EXCLUDED.photo_urls,
        view_count = EXCLUDED.view_count,
        dedup_hash = EXCLUDED.dedup_hash,
        listing_type = EXCLUDED.listing_type,
        property_type = EXCLUDED.property_type,
        property_subtype = EXCLUDED.property_subtype,
        posted_at = EXCLUDED.posted_at,
        posted_raw = EXCLUDED.posted_raw,
        specs = EXCLUDED.specs,
        is_active = true,
        delisted_at = NULL,
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


def parse_floor(raw: str | None) -> int | None:
    """Leading floor number from specs values such as "4" or "25+"."""
    if not raw:
        return None
    match = LEADING_INT_RE.match(raw.strip())
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
    complex_match = extract_complex(parsed["title"])
    # Only reviewed aliases are persisted automatically. Unknown trigger-only
    # candidates remain available to the audit layer, but do not create noisy
    # production complex rows without validation. Landmark mentions are never
    # assigned to the listing itself.
    complex_name = (
        complex_match.canonical_name
        if complex_match
        and complex_match.matched_alias is not None
        and complex_match.relation == "unit"
        else None
    )
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
        "floor": parse_floor(specs.get("Хэдэн давхарт")),
        "total_floors": parse_floor(specs.get("Барилгын давхар")),
        "complex_id": None,
        "complex_name": complex_name,
        "district": parsed.get("district"),
        "address": parsed.get("location_raw"),
        "lat": parsed.get("latitude"),
        "lng": parsed.get("longitude"),
        "contact_phone": phones[0] if phones else None,
        "photo_urls": parsed.get("photo_urls") or [],
        "view_count": parsed.get("view_count"),
        "listing_type": parsed.get("listing_type"),
        "property_type": parsed.get("property_category"),
        "property_subtype": parsed.get("property_subcategory"),
        "posted_at": parsed.get("posted_at"),
        "posted_raw": parsed.get("posted_raw"),
        "specs": psycopg2.extras.Json(specs),
    }
    row["dedup_hash"] = compute_dedup_hash(row)
    return row


def _resolve_complex_ids(
    cur: psycopg2.extensions.cursor, rows: list[dict[str, Any]]
) -> None:
    """Upsert reviewed complex names and attach their IDs to listing rows."""
    names = sorted({row["complex_name"] for row in rows if row.get("complex_name")})
    if not names:
        return
    ids: dict[str, int] = {}
    for name in names:
        cur.execute(
            """
            INSERT INTO complexes (canonical_name, normalized_name, aliases)
            VALUES (%s, %s, %s)
            ON CONFLICT (canonical_name) DO UPDATE SET
                normalized_name = EXCLUDED.normalized_name,
                aliases = EXCLUDED.aliases,
                updated_at = now()
            RETURNING id
            """,
            (name, normalize_complex_name(name), list(COMPLEX_ALIASES.get(name, ()))),
        )
        returned = cur.fetchone()
        ids[name] = returned["id"] if isinstance(returned, dict) else returned[0]
    for row in rows:
        row["complex_id"] = ids.get(row.get("complex_name"))


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


def known_urls(cur: psycopg2.extensions.cursor, urls: list[str]) -> set[str]:
    """Subset of urls that already exist in listings, at any scraped_at.

    Unlike recently_scraped (a time window, for the detail-page fetch skip),
    this is plain existence — it powers list_pages.collect_ad_urls' early
    stop for incremental runs, where walking further pages that are entirely
    already-known ads wastes requests without finding anything new. Expects
    a RealDictCursor (the convention for cursor-taking helpers here).
    """
    if not urls:
        return set()
    cur.execute("SELECT source_url FROM listings WHERE source_url = ANY(%s)", (urls,))
    return {row["source_url"] for row in cur.fetchall()}


def known_urls_conn(dsn: str, urls: list[str]) -> set[str]:
    """Connection-owning wrapper around known_urls() for the pipeline."""
    if not urls:
        return set()
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            result = known_urls(cur, urls)
    conn.close()
    return result


def reconcile_category_inventory(
    cur: psycopg2.extensions.cursor,
    listing_type: str,
    seen_urls: list[str],
) -> dict[str, int]:
    """Apply one verified-complete Unegui category inventory atomically.

    Seen URLs are (re)activated; currently-active URLs of the same transaction
    type that are absent are soft-deleted. An empty inventory is rejected as a
    final guard against a bot challenge or selector regression being mistaken
    for a category with no ads.
    """
    if listing_type not in {"sale", "rent"}:
        raise ValueError(f"unsupported listing_type: {listing_type}")
    if not seen_urls:
        raise ValueError("refusing to reconcile an empty category inventory")

    cur.execute(
        """
        UPDATE listings
        SET is_active = true, delisted_at = NULL
        WHERE source = 'unegui'
          AND listing_type = %s
          AND source_url = ANY(%s)
          AND NOT is_active
        """,
        (listing_type, seen_urls),
    )
    reactivated = cur.rowcount
    cur.execute(
        """
        UPDATE listings
        SET is_active = false, delisted_at = now()
        WHERE source = 'unegui'
          AND listing_type = %s
          AND is_active
          AND NOT (source_url = ANY(%s))
        """,
        (listing_type, seen_urls),
    )
    return {"reactivated": reactivated, "delisted": cur.rowcount}


def reconcile_category_inventory_conn(
    dsn: str, listing_type: str, seen_urls: list[str]
) -> dict[str, int]:
    """Connection-owning wrapper for reconcile_category_inventory()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor() as cur:
            return reconcile_category_inventory(cur, listing_type, seen_urls)


def upsert_listings(dsn: str, rows: list[dict[str, Any]]) -> int:
    """Upsert mapped rows on (source, source_url); returns rows actually saved.

    Re-scraping the same ad updates the existing row (and refreshes
    scraped_at) instead of duplicating it. Normally one transaction; if the
    batch fails on bad data (e.g. an absurd seller-entered price), it falls
    back to row-by-row so the one bad ad is skipped with a warning instead
    of losing the whole batch — vital on long unattended runs.
    """
    if not rows:
        return 0
    conn = psycopg2.connect(normalize_dsn(dsn))
    try:
        try:
            with conn:
                with conn.cursor() as cur:
                    _resolve_complex_ids(cur, rows)
                    psycopg2.extras.execute_batch(cur, _UPSERT_SQL, rows)
            return len(rows)
        except psycopg2.DataError:
            conn.rollback()
            saved = 0
            for row in rows:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            _resolve_complex_ids(cur, [row])
                            cur.execute(_UPSERT_SQL, row)
                    saved += 1
                except psycopg2.DataError as exc:
                    reason = str(exc).splitlines()[0]
                    print(f"    skipped bad row {row.get('source_url')}: {reason}", flush=True)
            return saved
    finally:
        conn.close()
