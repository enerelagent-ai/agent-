"""Map parsed ad dicts onto the listings table and upsert them into Postgres."""

import hashlib
import re
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.complexes import (
    COMPLEX_ALIASES,
    COMPLEX_EXTRACTOR_VERSION,
    extract_complex,
    normalize_complex_name,
)

AREA_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
LEADING_INT_RE = re.compile(r"^(\d+)")
NEGOTIABLE_MARKER = "үнэ тохирно"

_DISTRICT_TEXT_PATTERNS = {
    "Хан-Уул": re.compile(r"(?<!\w)(?:худ|хан[ -]?уул)(?!\w)", re.IGNORECASE),
    "Баянзүрх": re.compile(r"(?<!\w)(?:бзд|баянз[үv]рх)(?!\w)", re.IGNORECASE),
    "Сүхбаатар": re.compile(r"(?<!\w)(?:сбд|с[үv]хбаатар)(?!\w)", re.IGNORECASE),
    "Баянгол": re.compile(r"(?<!\w)(?:бгд|баянгол)(?!\w)", re.IGNORECASE),
    "Сонгинохайрхан": re.compile(r"(?<!\w)(?:схд|сонгинохайрхан)(?!\w)", re.IGNORECASE),
    "Чингэлтэй": re.compile(r"(?<!\w)(?:чд|чингэлтэй)(?!\w)", re.IGNORECASE),
}

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


def has_explicit_district_evidence(row: dict[str, Any], district: str) -> bool:
    """Whether seller-authored title/description explicitly names district.

    Unegui's location dropdown is occasionally wrong while both title and
    description say e.g. ``ХУД-15``.  This is a narrow override for a verified
    complex registry guard, not a general district inference mechanism.
    """
    pattern = _DISTRICT_TEXT_PATTERNS.get(district)
    if pattern is None:
        return False
    text = " ".join(str(row.get(field) or "") for field in ("title", "description"))
    return pattern.search(text) is not None


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
        # Keep evidence even when the match is a landmark and therefore must
        # never become listings.complex_id. Trigger-only unknown names are not
        # admitted to the verified tables until their alias is reviewed.
        "complex_match": (
            {
                "canonical_name": complex_match.canonical_name,
                "matched_alias": complex_match.matched_alias,
                "relation": complex_match.relation,
                "confidence": complex_match.confidence,
                "evidence_text": parsed["title"],
            }
            if complex_match and complex_match.matched_alias is not None
            else None
        ),
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
    """Upsert reviewed complex names and attach IDs with location guards.

    Release 3 only updates the fast pointer for a reviewed unit alias whose
    complex has an independently verified location and whose listing passes
    that district guard (or an exact reviewed override). All other candidates
    stay unlinked and are persisted to the review queue separately.
    """
    names = sorted({row["complex_name"] for row in rows if row.get("complex_name")})
    if not names:
        return
    cur.execute(
        """
        SELECT c.canonical_name, array_agg(DISTINCT v.district) AS districts
        FROM complexes c
        JOIN verified_complex_locations v ON v.complex_id = c.id
        WHERE c.canonical_name = ANY(%s)
        GROUP BY c.canonical_name
        """,
        (names,),
    )
    allowed_districts = {
        row["canonical_name"]: set(row["districts"])
        for row in cur.fetchall()
    }
    guarded_rows = [
        row for row in rows
        if row.get("complex_name") in allowed_districts and row.get("source_url")
    ]
    override_keys: set[tuple[str, str]] = set()
    if guarded_rows:
        cur.execute(
            """
            SELECT o.source_url, c.canonical_name
            FROM verified_listing_complex_overrides o
            JOIN complexes c ON c.id = o.complex_id
            WHERE o.source = 'unegui'
              AND o.source_url = ANY(%s)
            """,
            ([row["source_url"] for row in guarded_rows],),
        )
        override_keys = {
            (row["source_url"], row["canonical_name"])
            for row in cur.fetchall()
        }
    for row in rows:
        name = row.get("complex_name")
        allowed = allowed_districts.get(name)
        has_allowed_text_evidence = allowed is not None and any(
            has_explicit_district_evidence(row, district) for district in allowed
        )
        has_listing_override = (row.get("source_url"), name) in override_keys
        if (
            allowed is None
            or (
                row.get("district") not in allowed
                and not has_allowed_text_evidence
                and not has_listing_override
            )
        ):
            row["complex_name"] = None

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


def _persist_complex_matches(
    cur: psycopg2.extensions.cursor, rows: list[dict[str, Any]]
) -> int:
    """Persist current reviewed-alias evidence after listing upsert.

    This never creates canonical identities from trigger-only guesses. A
    district-safe unit assignment is policy-approved in the same transaction;
    landmarks and blocked/unregistered unit candidates remain pending.
    Re-scraping is idempotent and retains older extractor results as history.
    """
    if not rows:
        return 0
    candidates = [row for row in rows if row.get("complex_match")]
    urls = [row["source_url"] for row in rows]
    cur.execute(
        "SELECT source_url, id FROM listings WHERE source = 'unegui' AND source_url = ANY(%s)",
        (urls,),
    )
    listing_ids = {row["source_url"]: row["id"] for row in cur.fetchall()}
    if listing_ids:
        cur.execute(
            """
            UPDATE listing_complex_matches
            SET is_current = false, updated_at = now()
            WHERE listing_id = ANY(%s) AND is_current
            """,
            (list(listing_ids.values()),),
        )
    if not candidates:
        return 0

    names = sorted({row["complex_match"]["canonical_name"] for row in candidates})
    aliases = sorted({
        normalize_complex_name(row["complex_match"]["matched_alias"])
        for row in candidates
    })
    cur.execute(
        "SELECT canonical_name, id FROM complexes WHERE canonical_name = ANY(%s)",
        (names,),
    )
    complex_ids = {row["canonical_name"]: row["id"] for row in cur.fetchall()}
    cur.execute(
        "SELECT normalized_alias, id FROM complex_aliases WHERE normalized_alias = ANY(%s) AND is_active",
        (aliases,),
    )
    alias_ids = {row["normalized_alias"]: row["id"] for row in cur.fetchall()}

    persisted = 0
    for row in candidates:
        match = row["complex_match"]
        listing_id = listing_ids.get(row["source_url"])
        complex_id = complex_ids.get(match["canonical_name"])
        alias_id = alias_ids.get(normalize_complex_name(match["matched_alias"]))
        if listing_id is None or complex_id is None or alias_id is None:
            continue
        approved = match["relation"] == "unit" and row.get("complex_id") == complex_id
        review_status = "approved" if approved else "pending"
        reviewer_note = "district-safe verified-location policy" if approved else None
        cur.execute(
            """
            INSERT INTO listing_complex_matches
                (listing_id, complex_id, matched_alias_id, relation, confidence,
                 evidence_text, source_field, extractor_version, review_status,
                 reviewer_note, reviewed_at, is_current)
            VALUES
                (%s, %s, %s, %s, %s, %s, 'title', %s, %s, %s,
                 CASE WHEN %s = 'approved' THEN now() ELSE NULL END, true)
            ON CONFLICT (listing_id, complex_id, extractor_version, evidence_text)
            DO UPDATE SET
                matched_alias_id = EXCLUDED.matched_alias_id,
                relation = EXCLUDED.relation,
                confidence = EXCLUDED.confidence,
                review_status = EXCLUDED.review_status,
                reviewer_note = EXCLUDED.reviewer_note,
                reviewed_at = EXCLUDED.reviewed_at,
                is_current = true,
                detected_at = now(),
                updated_at = now()
            """,
            (
                listing_id, complex_id, alias_id, match["relation"], match["confidence"],
                match["evidence_text"], COMPLEX_EXTRACTOR_VERSION, review_status,
                reviewer_note, review_status,
            ),
        )
        persisted += 1
    return persisted


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
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    _resolve_complex_ids(cur, rows)
                    psycopg2.extras.execute_batch(cur, _UPSERT_SQL, rows)
                    _persist_complex_matches(cur, rows)
            return len(rows)
        except psycopg2.DataError:
            conn.rollback()
            saved = 0
            for row in rows:
                try:
                    with conn:
                        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                            _resolve_complex_ids(cur, [row])
                            cur.execute(_UPSERT_SQL, row)
                            _persist_complex_matches(cur, [row])
                    saved += 1
                except psycopg2.DataError as exc:
                    reason = str(exc).splitlines()[0]
                    print(f"    skipped bad row {row.get('source_url')}: {reason}", flush=True)
            return saved
    finally:
        conn.close()
