"""Core market calculation queries over canonical (non-duplicate) listings.

Every query excludes matches.superseded_listing_ids() first, so an
auto-resolved duplicate group is counted once, not once per repost. Every
query also filters WHERE is_active (migration 009): a sold/rented/removed
listing must never count as live inventory in a *current* market figure —
it stays in the table (soft-deleted, not dropped) purely for closure-trend
analysis over time, which is a different, deliberately separate concern
from anything in this module.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.matches import superseded_listing_ids
from analytics.db import normalize_dsn

# Below this, a comparable group is dropped entirely rather than reported —
# same discipline as investment_summary_by_district's district-level cutoff
# (_MIN_SAMPLE_SIZE, same value). Verified against the real DB: a small
# aimag like Дорноговь has only a handful of listings in some groups, and
# without this a caller asking about it would get a confident-looking
# average built from 1-2 listings. Shared by average_price_by_group,
# deal_percentages, and estimate_negotiable_price.
MIN_COMPARABLE_GROUP_SIZE = 20

# listing_type is included in the group-by even though only property_type
# and district were asked for: sale and rent prices differ by ~100x for the
# same property_type (see db/schema.sql's listing_type comment, and the
# Week 4 investigation) — blending them would make the average meaningless.
#
# price_negotiable IS NOT TRUE: a "Vнэ тохирно" placeholder is never a real
# price (same policy as deal_percentages/estimate_negotiable_price below —
# this function had fallen out of sync with that policy; 2026-08 audit).
# Real-DB impact was severe, not theoretical: a single negotiable "Газар
# зарна" land ad with a literal but absurd asking price (3.5 trillion MNT
# for one Баянзvрх plot, 2 trillion for one Сонгинохайрхан plot) inflated
# those districts' average land price 7.9x and 4.5x respectively before
# this fix.
#
# price <= _MAX_PLAUSIBLE_PRICE is defense-in-depth for the same failure on
# a future *non*-negotiable row (a typo'd extra zero or two): verified
# against the full DB that nothing legitimate is anywhere close to this
# ceiling — the highest genuine listing is ~51B MNT (a large commercial
# object), the next tier up is those same two negotiable errors at 2-3.5
# TRILLION, a >40x gap either direction, so the ceiling has wide margin and
# won't clip real high-value commercial/land listings.
_GROUP_STATS_SQL = """
    SELECT
        listing_type,
        property_type,
        district,
        count(*) AS n_listings,
        round(avg(price)::numeric, 2) AS avg_price,
        round(avg(price_per_sqm)::numeric, 2) AS avg_price_per_sqm,
        count(price_per_sqm) AS n_with_price_per_sqm
    FROM listings
    WHERE id != ALL(%(excluded_ids)s)
      AND is_active
      AND listing_type IS NOT NULL
      AND property_type IS NOT NULL
      AND district IS NOT NULL
      AND price_negotiable IS NOT TRUE
      AND price <= %(max_plausible_price)s
      AND (%(district)s IS NULL OR district = %(district)s)
    GROUP BY listing_type, property_type, district
    HAVING count(*) >= %(min_group_size)s
    ORDER BY listing_type, property_type, n_listings DESC
"""

# See _GROUP_STATS_SQL comment above for how this value and its safety
# margin were derived from the real DB.
_MAX_PLAUSIBLE_PRICE = Decimal("100000000000")  # 100 billion MNT


def average_price_by_group(
    cur: psycopg2.extensions.cursor, district: str | None = None
) -> list[dict[str, Any]]:
    """Average price and price/m² per (listing_type, property_type, district)
    group, over canonical listings only.

    district: optional exact-match filter to a single district; None
    (default) returns every district. Groups smaller than
    MIN_COMPARABLE_GROUP_SIZE are dropped entirely, same guard used by
    deal_percentages/estimate_negotiable_price — without it, a thin group
    (a small aimag like Дорноговь, or a rare property_type/district
    combination) would report a confident-looking average built from a
    handful of listings instead of coming back as unavailable.

    avg_price_per_sqm is computed over the stored generated column, so it
    only reflects listings that have both price and area_sqm; n_listings vs
    n_with_price_per_sqm shows how many of the group lack area data (common
    for land/object listings).

    Excludes price_negotiable listings (a placeholder price, never a real
    one) and anything above _MAX_PLAUSIBLE_PRICE (a data-entry-error
    ceiling) before averaging — see _GROUP_STATS_SQL's comment for why both
    guards are needed and how the ceiling was derived.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_GROUP_STATS_SQL, {
        "excluded_ids": excluded,
        "district": district,
        "min_group_size": MIN_COMPARABLE_GROUP_SIZE,
        "max_plausible_price": _MAX_PLAUSIBLE_PRICE,
    })
    return [dict(row) for row in cur.fetchall()]


def average_price_by_group_conn(dsn: str, district: str | None = None) -> list[dict[str, Any]]:
    """Connection-owning wrapper for average_price_by_group()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return average_price_by_group(cur, district)


# Unegui's breadcrumb text for the same real-world category differs between
# a sale ad and a rent ad (e.g. "Орон сууц зарна" vs "Орон сууц түрээслүүлнэ"),
# and property_subtype/rooms — the breadcrumb subcategory, e.g. "3 өрөө" — is
# only populated for this one category on either side (verified against the
# live DB: every other property_type has NULL subtype/rooms for all rows).
# That is what makes a district+subtype+room match possible here and nowhere
# else; see yield_category_coverage() for the full per-category audit.
_APARTMENT_SALE_LABEL = "Орон сууц зарна"
_APARTMENT_RENT_LABEL = "Орон сууц түрээслүүлнэ"

_RENTAL_YIELD_SQL = """
    WITH sale AS (
        SELECT district, property_subtype, rooms,
               count(*) AS n_sale,
               round(avg(price)::numeric, 2) AS avg_sale_price,
               round(avg(price_per_sqm)::numeric, 2) AS avg_sale_price_per_sqm
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND is_active
          AND listing_type = 'sale' AND property_type = %(sale_label)s
          AND district IS NOT NULL AND rooms IS NOT NULL
          AND price_negotiable IS NOT TRUE
          AND price > 0 AND price <= %(max_plausible_price)s
          AND (%(district)s IS NULL OR district = %(district)s)
        GROUP BY district, property_subtype, rooms
    ),
    rent AS (
        SELECT district, property_subtype, rooms,
               count(*) AS n_rent,
               round(avg(price)::numeric, 2) AS avg_rent_price
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND is_active
          AND listing_type = 'rent' AND property_type = %(rent_label)s
          AND district IS NOT NULL AND rooms IS NOT NULL
          AND price_negotiable IS NOT TRUE
          AND price > 0 AND price <= %(max_plausible_price)s
          AND (%(district)s IS NULL OR district = %(district)s)
        GROUP BY district, property_subtype, rooms
    )
    SELECT
        s.district, s.property_subtype, s.rooms,
        s.n_sale, s.avg_sale_price, s.avg_sale_price_per_sqm,
        r.n_rent, r.avg_rent_price,
        round(r.avg_rent_price * 12, 2) AS avg_annual_rent,
        round((r.avg_rent_price * 12 / s.avg_sale_price) * 100, 2) AS gross_rental_yield_pct,
        round(s.avg_sale_price / (r.avg_rent_price * 12), 1) AS payback_years
    FROM sale s
    JOIN rent r
      ON s.district = r.district
     AND s.property_subtype IS NOT DISTINCT FROM r.property_subtype
     AND s.rooms = r.rooms
    ORDER BY s.district, s.rooms
"""


def rental_yield_by_district_rooms(
    cur: psycopg2.extensions.cursor, district: str | None = None
) -> list[dict[str, Any]]:
    """Gross rental yield for apartments, matched sale-to-rent by (district,
    property_subtype, rooms) instead of a blunt property_type-level average,
    so a studio in one district isn't blended with a 5-room unit in another.

    district: optional exact-match filter to a single district; None
    (default) returns every district with a granular sale/rent match. Only
    narrows which (district, property_subtype, rooms) buckets are computed
    and returned — a filtered district's own buckets are built from exactly
    the same sale/rent rows as an unfiltered call, so filtering never
    changes a bucket's own numbers, only which ones come back.

    Apartments are the only property_type with this granular breakdown
    (see the module-level comment above and yield_category_coverage()), so
    this only ever returns "Орон сууц" rows. avg_annual_rent assumes the
    stored rent price is monthly, which real-DB magnitudes confirm (e.g.
    2-room: ~232M avg sale vs ~2.08M avg monthly rent -> ~10.8% yield, a
    plausible gross residential yield). payback_years is avg_sale_price
    divided by avg_annual_rent — years of rent to recoup the purchase price
    at current averages, ignoring financing, vacancy, and expenses.
    avg_sale_price_per_sqm is the sale side's price/m² for the same bucket
    (rent side has no equivalent field — nothing here needs it).
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_RENTAL_YIELD_SQL, {
        "excluded_ids": excluded,
        "sale_label": _APARTMENT_SALE_LABEL,
        "rent_label": _APARTMENT_RENT_LABEL,
        "district": district,
        "max_plausible_price": _MAX_PLAUSIBLE_PRICE,
    })
    return [dict(row) for row in cur.fetchall()]


def rental_yield_by_district_rooms_conn(dsn: str, district: str | None = None) -> list[dict[str, Any]]:
    """Connection-owning wrapper for rental_yield_by_district_rooms()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return rental_yield_by_district_rooms(cur, district)


# (canonical label, sale-side raw property_type, rent-side raw property_type)
# Raw breadcrumb text differs by transaction type, so these pairs were
# hand-matched against the live DB's distinct (listing_type, property_type)
# values — not derived by string manipulation, since one pair (houses/gers,
# see _SPECIAL_REASONS) doesn't reduce to a simple suffix swap.
_PROPERTY_TYPE_GROUPS: list[tuple[str, str | None, str | None]] = [
    ("Орон сууц (apartments)", "Орон сууц зарна", "Орон сууц түрээслүүлнэ"),
    ("00-н өрөө, В1, подвал (basement units)", "00-н өрөө, В1, подвал зарна", "00-н өрөө, В1, подвал түрээслүүлнэ"),
    ("АОС, хаус, зуслан (country houses/dachas)", "АОС, хаус, зуслан, амралтын газар зарна", "АОС, хаус, зуслан, амралтын газар түрээслүүлнэ"),
    ("Газар (land)", "Газар зарна", "Газар түрээслүүлнэ"),
    ("Гараж, контейнер, з-сууц (garage/container)", "Гараж, контейнер, з-сууц зарна", "Гараж, контейнер, з-сууц түрээслүүлнэ"),
    ("Нийтийн байр, дотуур байр (dormitory)", "Нийтийн байр, дотуур байр зарна", "Нийтийн байр, дотуур байр түрээслүүлнэ"),
    ("Оффис (office)", "Оффис зарна", "Оффис түрээслүүлнэ"),
    ("Үйлдвэр, агуулах, oбьект (industrial/warehouse)", "Үйлдвэр, агуулах, oбьект зарна", "Үйлдвэр, агуулах, oбьект түрээслүүлнэ"),
    ("Худалдаа, үйлчилгээний талбай (retail/commercial)", "Худалдаа, үйлчилгээний талбай зарна", "Худалдаа, үйлчилгээний талбай түрээслүүлнэ"),
    ("Хашаа байшин (houses)", "Хашаа байшин зарна", "Хашаа байшин, гэр түрээслүүлнэ"),
    ("Монгол гэр (traditional ger)", "Монгол гэр зарна", None),
    ("Бусад (other)", "Бусад зарна", None),
    ("Hostel/Хостел", None, "Hostel/Хостел"),
    ("Хоногоор байр, байшин (daily-rate)", None, "Хоногоор байр, байшин түрээслүүлнэ"),
    ("Хурлын өрөө, заал (meeting room/hall)", None, "Хурлын өрөө, заал түрээслүүлнэ"),
]

# Categories excluded for a semantic reason no listing count can capture:
# merging them would silently blend two different real-world property kinds.
_SPECIAL_REASONS: dict[str, str] = {
    "Монгол гэр (traditional ger)": (
        "no isolated rent-side comparable — ger rentals are folded into the "
        "'Хашаа байшин, гэр' rent category, not tracked separately"
    ),
    "Хашаа байшин (houses)": (
        "rent-side category ('Хашаа байшин, гэр') bundles gers into houses, "
        "while sale keeps 'Хашаа байшин' and 'Монгол гэр' separate — "
        "merging them would misstate yield for both"
    ),
}

_COVERAGE_COUNT_SQL = """
    SELECT count(*) AS n, count(rooms) AS n_rooms
    FROM listings
    WHERE is_active AND listing_type = %(listing_type)s AND property_type = %(label)s
"""


def _coverage_reason(
    canonical: str, sale_label: str | None, rent_label: str | None,
    n_sale: int, n_rent: int, n_rooms_sale: int, n_rooms_rent: int,
) -> str:
    if canonical in _SPECIAL_REASONS:
        return _SPECIAL_REASONS[canonical]
    if sale_label is None:
        return ("no sale-side category — this is a rent-only listing type "
                "(short-term or meeting-room rental), not a purchasable property")
    if rent_label is None:
        return "no rent-side category — cannot form a rent-price comparable"
    if n_sale == 0 or n_rent == 0:
        return f"no listings found on one side (n_sale={n_sale}, n_rent={n_rent})"
    if n_rooms_sale == 0 or n_rooms_rent == 0:
        return ("property_subtype/rooms not populated for this category — no "
                "district+subtype+room match key available (see rental_yield_by_district_rooms)")
    return ""  # unreachable when calculable is True


def yield_category_coverage(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Audit every property_type category for whether a granular sale/rent
    yield match is possible, and why not when it isn't.

    Live counts (n_sale, n_rent, and how many of those have rooms set) come
    from the DB so this stays accurate as more listings are scraped; the
    reason text is hand-annotated since "why" is a domain judgment (a label
    mismatch, a missing transaction side, or missing subtype/rooms data) that
    row counts alone can't express. Categories are never merged or
    approximated here — a category is either calculable via
    rental_yield_by_district_rooms, or excluded with a reason.
    """
    rows = []
    for canonical, sale_label, rent_label in _PROPERTY_TYPE_GROUPS:
        n_sale = n_rooms_sale = n_rent = n_rooms_rent = 0
        if sale_label:
            cur.execute(_COVERAGE_COUNT_SQL, {"listing_type": "sale", "label": sale_label})
            row = cur.fetchone()
            n_sale, n_rooms_sale = row["n"], row["n_rooms"]
        if rent_label:
            cur.execute(_COVERAGE_COUNT_SQL, {"listing_type": "rent", "label": rent_label})
            row = cur.fetchone()
            n_rent, n_rooms_rent = row["n"], row["n_rooms"]
        calculable = (
            canonical not in _SPECIAL_REASONS
            and n_sale > 0 and n_rent > 0
            and n_rooms_sale > 0 and n_rooms_rent > 0
        )
        rows.append({
            "category": canonical,
            "n_sale": n_sale,
            "n_rent": n_rent,
            "calculable": calculable,
            "reason": None if calculable else _coverage_reason(
                canonical, sale_label, rent_label, n_sale, n_rent, n_rooms_sale, n_rooms_rent
            ),
        })
    return rows


def yield_category_coverage_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for yield_category_coverage()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return yield_category_coverage(cur)


_LISTING_COUNTS_SQL = """
    SELECT
        listing_type,
        CASE WHEN property_type = ANY(%(apartment_labels)s) THEN 'apartments' ELSE 'other' END AS bucket,
        count(*) AS n
    FROM listings
    WHERE id != ALL(%(excluded_ids)s)
      AND is_active
      AND listing_type IS NOT NULL
      AND property_type IS NOT NULL
    GROUP BY listing_type, bucket
"""


def listing_counts_by_property_type(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Sale vs rent listing counts, over canonical (non-superseded) listings,
    for a donut/part-to-whole chart.

    Simplified to two buckets (apartments vs everything else) rather than
    all ~14 property_type categories: a donut reads as part-to-whole "at a
    glance" only up to a handful of segments, and apartments alone are
    already roughly half of all listings (the one category the rest of this
    module treats specially too — see rental_yield_by_district_rooms).
    Always returns exactly 4 rows (apartments x sale/rent, other x
    sale/rent), zero-filled if a bucket has no listings, so the chart layer
    never has to guess a missing combination.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_LISTING_COUNTS_SQL, {
        "excluded_ids": excluded,
        "apartment_labels": [_APARTMENT_SALE_LABEL, _APARTMENT_RENT_LABEL],
    })
    counts = {(row["listing_type"], row["bucket"]): row["n"] for row in cur.fetchall()}
    return [
        {"bucket": bucket, "listing_type": listing_type, "n": counts.get((listing_type, bucket), 0)}
        for bucket in ("apartments", "other")
        for listing_type in ("sale", "rent")
    ]


def listing_counts_by_property_type_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for listing_counts_by_property_type()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return listing_counts_by_property_type(cur)


# Below this on either side, a district is dropped from the ranked table
# entirely rather than scored: with too few listings, investment_score is
# noise, not signal. Verified against the live DB — without this cutoff,
# Багануур's single sale/rent pair (n_sale=1) outranks Хан-Уул's 4,308
# sale listings purely because the ranking treats every district equally
# regardless of sample size.
_MIN_SAMPLE_SIZE = 20


_DISTRICT_SALE_DISTRIBUTION_SQL = """
    WITH eligible_rent_groups AS (
        SELECT DISTINCT district, property_subtype, rooms
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND is_active
          AND listing_type = 'rent' AND property_type = %(rent_label)s
          AND district IS NOT NULL AND rooms IS NOT NULL
          AND price_negotiable IS NOT TRUE
          AND price > 0 AND price <= %(max_plausible_price)s
    )
    SELECT s.district,
           min(s.price) AS min_sale_price,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY s.price) AS median_sale_price,
           max(s.price) AS max_sale_price
    FROM listings s
    JOIN eligible_rent_groups r
      ON s.district = r.district
     AND s.property_subtype IS NOT DISTINCT FROM r.property_subtype
     AND s.rooms = r.rooms
    WHERE s.id != ALL(%(excluded_ids)s)
      AND s.is_active
      AND s.listing_type = 'sale' AND s.property_type = %(sale_label)s
      AND s.price_negotiable IS NOT TRUE
      AND s.price > 0 AND s.price <= %(max_plausible_price)s
    GROUP BY s.district
"""


def district_sale_price_distribution(
    cur: psycopg2.extensions.cursor,
) -> dict[str, dict[str, Any]]:
    """Min/median/max sale price for the same eligible apartment groups as yield."""
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_DISTRICT_SALE_DISTRIBUTION_SQL, {
        "excluded_ids": excluded,
        "sale_label": _APARTMENT_SALE_LABEL,
        "rent_label": _APARTMENT_RENT_LABEL,
        "max_plausible_price": _MAX_PLAUSIBLE_PRICE,
    })
    return {row["district"]: dict(row) for row in cur.fetchall()}


def investment_summary_by_district(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Week 6 dashboard input: one row per district, built on top of
    rental_yield_by_district_rooms() rather than a fresh query, so it always
    reflects the same match/exclusion logic as the room-level yield table.

    Room-count buckets are recombined with each bucket's own sample size as
    the weight (sum of price*n_sale over sum of n_sale, same for rent), not
    a naive average across room sizes — a district with mostly 2-room
    listings shouldn't be pulled toward a thin 5+-room bucket's price level.
    gross_rental_yield_pct is then recomputed from those recombined
    district-level price/rent figures, not averaged from the per-bucket
    yields directly, for the same reason. avg_price_per_sqm is recombined
    the same way, weighted separately by n_sale_with_sqm so a bucket with no
    area data doesn't distort it; None if no bucket in the district has any.

    roi_pct is the same number as gross_rental_yield_pct: annual rent over
    purchase price for an all-cash buyer. There's no financing, expense, or
    vacancy data in this DB to build a richer ROI on top of, so it's kept as
    an explicitly named alias rather than invented from assumptions — a
    dashboard/API consumer looking for "ROI" should still find it.

    Districts with n_sale < _MIN_SAMPLE_SIZE or n_rent < _MIN_SAMPLE_SIZE are
    dropped before ranking (see _MIN_SAMPLE_SIZE).

    investment_score (0-100) combines avg_sale_price and gross_rental_yield_pct
    by rank, not by blending their raw units: districts are ranked cheapest
    -> priciest and highest-yield -> lowest-yield, each rank converted to a
    0-100 scale (best = 100), then averaged 50/50. This is a simple,
    transparent MVP score — swap in a different blend once Week 6 shows what
    dashboard users actually weigh price vs. yield.
    """
    buckets = rental_yield_by_district_rooms(cur)
    distributions = district_sale_price_distribution(cur)

    totals: dict[str, dict[str, Any]] = {}
    for b in buckets:
        t = totals.setdefault(b["district"], {
            "n_sale": 0, "n_rent": 0, "n_sale_with_sqm": 0,
            "sale_price_sum": Decimal(0), "annual_rent_sum": Decimal(0),
            "sale_price_per_sqm_sum": Decimal(0),
        })
        t["n_sale"] += b["n_sale"]
        t["n_rent"] += b["n_rent"]
        t["sale_price_sum"] += b["avg_sale_price"] * b["n_sale"]
        t["annual_rent_sum"] += b["avg_annual_rent"] * b["n_rent"]
        # avg_sale_price_per_sqm can be NULL for a bucket with no area data;
        # weight its own sum/count separately so a gap doesn't skew avg_sale_price.
        if b["avg_sale_price_per_sqm"] is not None:
            t["sale_price_per_sqm_sum"] += b["avg_sale_price_per_sqm"] * b["n_sale"]
            t["n_sale_with_sqm"] += b["n_sale"]

    rows = []
    for district, t in totals.items():
        if t["n_sale"] < _MIN_SAMPLE_SIZE or t["n_rent"] < _MIN_SAMPLE_SIZE:
            continue
        avg_sale_price = t["sale_price_sum"] / t["n_sale"]
        avg_annual_rent = t["annual_rent_sum"] / t["n_rent"]
        gross_yield_pct = (avg_annual_rent / avg_sale_price) * 100
        avg_price_per_sqm = (
            t["sale_price_per_sqm_sum"] / t["n_sale_with_sqm"] if t["n_sale_with_sqm"] else None
        )
        rows.append({
            "district": district,
            "n_sale": t["n_sale"],
            "n_rent": t["n_rent"],
            "avg_sale_price": round(avg_sale_price, 2),
            "avg_price_per_sqm": round(avg_price_per_sqm, 2) if avg_price_per_sqm is not None else None,
            "gross_rental_yield_pct": round(gross_yield_pct, 2),
            "roi_pct": round(gross_yield_pct, 2),
            "min_sale_price": distributions[district]["min_sale_price"],
            "median_sale_price": distributions[district]["median_sale_price"],
            "max_sale_price": distributions[district]["max_sale_price"],
        })

    n = len(rows)
    if n > 1:
        cheapest_first = sorted(rows, key=lambda r: r["avg_sale_price"])
        price_rank = {r["district"]: i for i, r in enumerate(cheapest_first)}
        highest_yield_first = sorted(rows, key=lambda r: -r["gross_rental_yield_pct"])
        yield_rank = {r["district"]: i for i, r in enumerate(highest_yield_first)}
        for r in rows:
            price_score = 100 * (1 - price_rank[r["district"]] / (n - 1))
            yield_score = 100 * (1 - yield_rank[r["district"]] / (n - 1))
            r["investment_score"] = round((price_score + yield_score) / 2, 1)
    else:
        for r in rows:
            r["investment_score"] = 100.0

    rows.sort(key=lambda r: -r["investment_score"])
    return rows


def investment_summary_by_district_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for investment_summary_by_district()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return investment_summary_by_district(cur)


def monthly_delisting_trend(
    cur: psycopg2.extensions.cursor,
    listing_type: str | None = None,
    district: str | None = None,
) -> list[dict[str, Any]]:
    """Monthly soft-deletion counts over canonical Unegui listings.

    This is a lifecycle/liquidity observation, not proof that every removed ad
    was sold or rented: sellers can withdraw or replace an ad for other reasons.
    """
    if listing_type not in {None, "sale", "rent"}:
        raise ValueError(f"unsupported listing_type: {listing_type}")
    excluded = list(superseded_listing_ids(cur))
    cur.execute(
        """
        SELECT date_trunc('month', delisted_at)::date AS month,
               listing_type,
               district,
               count(*) AS n_delisted
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND source = 'unegui'
          AND NOT is_active
          AND delisted_at IS NOT NULL
          AND (%(listing_type)s IS NULL OR listing_type = %(listing_type)s)
          AND (%(district)s IS NULL OR district = %(district)s)
        GROUP BY 1, listing_type, district
        ORDER BY 1, listing_type, district
        """,
        {"excluded_ids": excluded, "listing_type": listing_type, "district": district},
    )
    return [dict(row) for row in cur.fetchall()]


def monthly_delisting_trend_conn(
    dsn: str, listing_type: str | None = None, district: str | None = None
) -> list[dict[str, Any]]:
    """Connection-owning wrapper for monthly_delisting_trend()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return monthly_delisting_trend(cur, listing_type, district)


_PRICE_HISTORY_UPSERT_SQL = """
    INSERT INTO price_history (snapshot_date, listing_type, property_type,
                                district, n_listings, avg_price, avg_price_per_sqm)
    VALUES (%(snapshot_date)s, %(listing_type)s, %(property_type)s,
            %(district)s, %(n_listings)s, %(avg_price)s, %(avg_price_per_sqm)s)
    ON CONFLICT (snapshot_date, listing_type, property_type, district)
    DO UPDATE SET n_listings = EXCLUDED.n_listings,
                  avg_price = EXCLUDED.avg_price,
                  avg_price_per_sqm = EXCLUDED.avg_price_per_sqm
"""


def snapshot_market_prices(cur: psycopg2.extensions.cursor, snapshot_date: date | None = None) -> int:
    """Record one price_history row per (listing_type, property_type,
    district) group for snapshot_date (default: today), so price trends can
    be charted over time without waiting on a separate historical dataset.

    Reuses average_price_by_group() rather than re-querying listings, so a
    snapshot always reflects the exact same canonical (non-superseded) set
    Week 5's other calculations use. Re-running on the same day upserts in
    place (see migration 008's UNIQUE constraint) rather than accumulating
    duplicate rows; running on a later day appends a new generation of rows,
    which is what lets the trend grow richer over time with no code changes.
    """
    snapshot_date = snapshot_date or date.today()
    groups = average_price_by_group(cur)
    for row in groups:
        cur.execute(_PRICE_HISTORY_UPSERT_SQL, {
            "snapshot_date": snapshot_date,
            "listing_type": row["listing_type"],
            "property_type": row["property_type"],
            "district": row["district"],
            "n_listings": row["n_listings"],
            "avg_price": row["avg_price"],
            "avg_price_per_sqm": row["avg_price_per_sqm"],
        })
    return len(groups)


def snapshot_market_prices_conn(dsn: str, snapshot_date: date | None = None) -> int:
    """Connection-owning wrapper for snapshot_market_prices()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return snapshot_market_prices(cur, snapshot_date)


_PRICE_TREND_SQL = """
    SELECT
        snapshot_date,
        sum(n_listings) AS n_listings,
        round((sum(avg_price * n_listings) / NULLIF(sum(n_listings), 0))::numeric, 2) AS avg_price,
        round((sum(avg_price_per_sqm * n_listings) / NULLIF(sum(n_listings), 0))::numeric, 2) AS avg_price_per_sqm
    FROM price_history
    WHERE listing_type = %(listing_type)s AND property_type = %(property_type)s
      AND (%(district)s IS NULL OR district = %(district)s)
    GROUP BY snapshot_date
    ORDER BY snapshot_date
"""


def price_trend(
    cur: psycopg2.extensions.cursor,
    listing_type: str = "sale",
    property_type: str = "Орон сууц зарна",
    district: str | None = None,
) -> list[dict[str, Any]]:
    """Overall price trend for one (listing_type, property_type) slice: one
    point per snapshot_date, with districts recombined by each snapshot's own
    n_listings weight (mirroring investment_summary_by_district's approach)
    rather than a naive average across districts.

    district: optional exact-match filter to a single district; None
    (default) recombines every district's own snapshot into one market-wide
    point per snapshot_date, same as before. Filtered, each point is just
    that one district's own price_history row for the date (the weighted
    sum/count formula still applies cleanly with a single row).

    Defaults to sale-side apartments — the closest analogue to the "average
    price / m²" headline figure a market dashboard usually leads with, and
    the category with the deepest, most reliable data (see
    yield_category_coverage). With only one snapshot on record, this returns
    a single point; it fills in as snapshot_market_prices() runs again over
    time, with no change needed here.
    """
    cur.execute(_PRICE_TREND_SQL, {
        "listing_type": listing_type,
        "property_type": property_type,
        "district": district,
    })
    return [dict(row) for row in cur.fetchall()]


def price_trend_conn(
    dsn: str,
    listing_type: str = "sale",
    property_type: str = "Орон сууц зарна",
    district: str | None = None,
) -> list[dict[str, Any]]:
    """Connection-owning wrapper for price_trend()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return price_trend(cur, listing_type, property_type, district)


# Below this, an apartment listing's area is more likely a scraper parsing
# failure than a real micro-unit: checked against the live DB, there's a
# cluster of listings with area_sqm 0-7 that are physically impossible for
# their own stated room count (a "2 өрөө" claiming 1m², a "3 өрөө" claiming
# 0m²) alongside a separate cluster of genuine tiny units (explicitly "мини"
# or "00 тоот" basement conversions) that all sit at 8m² and up. This floor
# keeps both the group median and individual listings clear of the first
# cluster without touching the second. (area_sqm=0 already yields a NULL
# price_per_sqm via the generated column's own CASE guard in db/schema.sql,
# so this floor's real job is the 1-7 range that guard doesn't catch.)
_MIN_AREA_SQM_FOR_DEAL = 10.0

# Unegui's own room-count category caps at "5+ өрөө" (property_subtype),
# so rooms=5 in this data is really "5 or more" -- it silently mixes true
# 5-room flats with 6+-room duplexes. Verified against the real DB: three
# of the "5+ өрөө" listings that scored as confident top deals (~49%, just
# under MAX_CONFIDENT_DEAL_PCT) were titled "6 өрөө" / "6 өрөө дуплекс",
# priced completely normally for their own size (~consistent ₮/m² across
# all three) -- they only looked underpriced against a median pulled up
# by smaller true-5-room units in the same bucket. Rooms 1-4 don't have
# this ambiguity: each is Unegui's own exact category, not an open range.
# Same "not comparable, don't approximate" call as yield_category_coverage.
_OPEN_ENDED_ROOMS = 5

# Confidence tiers, mirroring dedup's CANDIDATE_THRESHOLD/AUTO_RESOLVE_THRESHOLD
# structure but inverted: a MODERATE discount is more trustworthy than an
# extreme one. Real bargains rarely exceed ~50% below the comparable group's
# median; a wrong room count or property_type — putting a listing in the
# wrong comparison group entirely — routinely produces something that looks
# far more extreme than that. Guards against bad price/area data (the median
# baseline, the area floor) can't catch this, since a misclassified listing
# can otherwise look completely clean.
MIN_NOTABLE_DEAL_PCT = 10.0
MAX_CONFIDENT_DEAL_PCT = 50.0

# MIN_COMPARABLE_GROUP_SIZE (module-level, above) applies here too, at the
# finer (district, rooms, listing_type) grain this module uses: without it,
# a 2-listing group could put a listing in the confident "top_deal" tier off
# a "median" that's really just one other listing's price — no more
# trustworthy than a coin flip.

_MISCLASSIFICATION_REVIEW_REASON = "магадгүй ангилал буруу — шалгах шаардлагатай"

_DEAL_PERCENTAGES_SQL = """
    WITH group_medians AS (
        SELECT district, rooms, listing_type,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY price_per_sqm) AS group_median_price_per_sqm,
               count(*) AS n_comparable
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND is_active
          AND district IS NOT NULL AND rooms IS NOT NULL AND price_per_sqm IS NOT NULL
          AND area_sqm >= %(min_area_sqm)s
          AND rooms != %(open_ended_rooms)s
          AND price_negotiable IS NOT TRUE
          AND (%(district)s IS NULL OR district = %(district)s)
        GROUP BY district, rooms, listing_type
        HAVING count(*) >= %(min_group_size)s
    ),
    priced AS (
        SELECT
            l.id, l.complex_id, l.district, l.rooms, l.listing_type, l.property_type,
            l.price, l.price_per_sqm, l.area_sqm,
            round(gm.group_median_price_per_sqm::numeric, 2) AS group_median_price_per_sqm,
            gm.n_comparable,
            round((((gm.group_median_price_per_sqm - l.price_per_sqm)
                    / gm.group_median_price_per_sqm) * 100)::numeric, 2) AS deal_pct
        FROM listings l
        JOIN group_medians gm
          ON l.district = gm.district AND l.rooms = gm.rooms AND l.listing_type = gm.listing_type
        WHERE l.id != ALL(%(excluded_ids)s)
          AND l.is_active
          AND l.district IS NOT NULL AND l.rooms IS NOT NULL AND l.price_per_sqm IS NOT NULL
          AND l.area_sqm >= %(min_area_sqm)s
          AND l.rooms != %(open_ended_rooms)s
          AND l.price_negotiable IS NOT TRUE
          AND (%(district)s IS NULL OR l.district = %(district)s)
    )
    -- Classification runs on the already-rounded deal_pct (not the raw
    -- expression) so it always agrees with the value callers actually see —
    -- otherwise a row could round across a tier boundary (e.g. a raw value
    -- of 9.996 rounds to 10.00 for display but would classify as
    -- not_notable using the unrounded number) and disagree with
    -- classify_deal(deal_pct).
    SELECT *,
        CASE
            WHEN deal_pct > %(max_confident_pct)s THEN 'needs_review'
            WHEN deal_pct >= %(min_notable_pct)s THEN 'top_deal'
            ELSE 'not_notable'
        END AS deal_status
    FROM priced
    ORDER BY deal_pct DESC
"""


def classify_deal(deal_pct: float) -> str:
    """Confidence-tier classification for a deal_pct value — see
    MIN_NOTABLE_DEAL_PCT/MAX_CONFIDENT_DEAL_PCT. Kept as a standalone
    function (mirroring dedup.classify_pair) so the threshold logic is
    testable independent of a DB round-trip; deal_percentages()'s SQL
    computes the same classification directly (it already has the numbers
    in hand), and a test cross-checks the two never drift apart.
    """
    if deal_pct > MAX_CONFIDENT_DEAL_PCT:
        return "needs_review"
    if deal_pct >= MIN_NOTABLE_DEAL_PCT:
        return "top_deal"
    return "not_notable"


def deal_percentages(
    cur: psycopg2.extensions.cursor, district: str | None = None
) -> list[dict[str, Any]]:
    """How each listing's price/m² compares to its comparable group's
    median: (district, rooms, listing_type) — sale and rent never blended
    (same ~100x gap as everywhere else in this module), and rooms is part of
    the group for the same reason rental_yield_by_district_rooms uses it:
    a studio and a 5-room unit in the same district aren't comparable.

    district: optional exact-match filter to a single district; None
    (default) returns deals across every district. Since each group is
    already scoped to one district, filtering only narrows which groups get
    computed and returned — a filtered group's own median is built from
    exactly the same comparables as an unfiltered call, never a shrunken
    baseline (see the whole-market-baseline note below).

    Only ever populated for listings with rooms set — apartments, the one
    property_type with room-count data (see yield_category_coverage: every
    other category has rooms NULL for every row). Listings missing area
    (price_per_sqm NULL), below _MIN_AREA_SQM_FOR_DEAL, in the open-ended
    _OPEN_ENDED_ROOMS ("5+ өрөө") bucket, or marked price_negotiable are
    excluded from both sides of the comparison — a negotiable listing's
    price is a placeholder (e.g. "170 ₮ Үнэ тохирно"), not a real one, so
    it can neither have a sensible deal_pct itself nor belong in anyone
    else's group baseline. (A negotiable listing still gets a price
    estimate — see estimate_negotiable_price() — just never a deal_pct.)
    Groups smaller than MIN_COMPARABLE_GROUP_SIZE are dropped entirely
    (and every listing in them along with it): verified against the real
    DB that without this, a 2-listing group could put something in the
    confident tier off a "median" that's really just one other listing.

    Baseline is the group's MEDIAN price/m², not the mean: verified against
    the real DB (Сүхбаатар, 4-room rentals) that a single corrupted row
    (a "4 өрөө" listing with area_sqm=1) dragged the mean to more than 2x
    the median, making several genuinely-average-priced listings look like
    70-80% "deals" that weren't. Median shrugs off that kind of single-row
    corruption; mean doesn't.

    deal_pct is positive when a listing is CHEAPER than its group's median
    price/m² (a good deal) and negative when pricier — sorted best-deal-first
    by default. group_median_price_per_sqm is computed over canonical
    (non-superseded) listings only, and is the same for every listing in a
    group regardless of whatever district/property_type/price filters an API
    caller applies afterward — the comparison baseline must stay whole-market,
    not shrink to match a filtered view.

    deal_status classifies each row via classify_deal(): 'top_deal' for a
    plausible discount, 'needs_review' for one extreme enough that a wrong
    comparison group (bad room count, bad property_type) is a more likely
    explanation than a genuine bargain — carries deal_reason in that case.
    'not_notable' means the deviation isn't large enough to be interesting
    either way. n_comparable is the group's size, so a caller can judge how
    much to trust a given deal_pct regardless of tier.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_DEAL_PERCENTAGES_SQL, {
        "excluded_ids": excluded,
        "district": district,
        "min_group_size": MIN_COMPARABLE_GROUP_SIZE,
        "min_area_sqm": _MIN_AREA_SQM_FOR_DEAL,
        "open_ended_rooms": _OPEN_ENDED_ROOMS,
        "max_confident_pct": MAX_CONFIDENT_DEAL_PCT,
        "min_notable_pct": MIN_NOTABLE_DEAL_PCT,
    })
    rows = [dict(row) for row in cur.fetchall()]
    for row in rows:
        row["deal_reason"] = _MISCLASSIFICATION_REVIEW_REASON if row["deal_status"] == "needs_review" else None
    return rows


def deal_percentages_conn(dsn: str, district: str | None = None) -> list[dict[str, Any]]:
    """Connection-owning wrapper for deal_percentages()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return deal_percentages(cur, district)


# A complex is a much tighter comparison than a whole district. We require
# a larger discount before presenting a separate "complex-level opportunity"
# signal, while retaining the same 50% data-quality review ceiling.
MIN_COMPLEX_DEAL_PCT = 20.0

_COMPLEX_AVERAGE_PRICE_SQL = """
    SELECT
        l.complex_id,
        c.canonical_name AS complex_name,
        l.listing_type,
        l.property_type,
        count(*) AS n_listings,
        round(avg(l.price)::numeric, 2) AS avg_price,
        round(percentile_cont(0.5) WITHIN GROUP (ORDER BY l.price)::numeric, 2) AS median_price,
        round(avg(l.price_per_sqm)::numeric, 2) AS avg_price_per_sqm,
        round(percentile_cont(0.5) WITHIN GROUP (ORDER BY l.price_per_sqm)::numeric, 2)
            AS median_price_per_sqm,
        count(l.price_per_sqm) AS n_with_price_per_sqm
    FROM listings l
    JOIN complexes c ON c.id = l.complex_id
    WHERE l.id != ALL(%(excluded_ids)s)
      AND l.is_active
      AND l.complex_id IS NOT NULL
      AND l.listing_type IS NOT NULL
      AND l.property_type IS NOT NULL
      AND l.price IS NOT NULL
      AND l.price_negotiable IS NOT TRUE
      AND l.price <= %(max_plausible_price)s
      AND (%(complex_id)s IS NULL OR l.complex_id = %(complex_id)s)
    GROUP BY l.complex_id, c.canonical_name, l.listing_type, l.property_type
    HAVING count(*) >= %(min_group_size)s
    ORDER BY n_listings DESC, c.canonical_name, l.listing_type, l.property_type
"""


def complex_average_price(
    cur: psycopg2.extensions.cursor, complex_id: int | None = None
) -> list[dict[str, Any]]:
    """Price statistics within canonical complex + transaction + property type.

    Reuses every Phase 0 current-market guard: superseded duplicates,
    inactive rows, negotiable placeholders, prices above the verified 100B
    ceiling, and groups below MIN_COMPARABLE_GROUP_SIZE are excluded. Sale
    and rent, or apartments and garages in the same complex, are never mixed.
    Both mean and median are returned; callers should use the median for a
    per-listing deal badge because it resists one otherwise-valid extreme.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_COMPLEX_AVERAGE_PRICE_SQL, {
        "excluded_ids": excluded,
        "complex_id": complex_id,
        "max_plausible_price": _MAX_PLAUSIBLE_PRICE,
        "min_group_size": MIN_COMPARABLE_GROUP_SIZE,
    })
    return [dict(row) for row in cur.fetchall()]


def complex_average_price_conn(dsn: str, complex_id: int | None = None) -> list[dict[str, Any]]:
    """Connection-owning wrapper for complex_average_price()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return complex_average_price(cur, complex_id)


_COMPLEX_DEAL_PERCENTAGES_SQL = """
    WITH group_medians AS (
        SELECT complex_id, listing_type, property_type,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY price_per_sqm)
                   AS complex_median_price_per_sqm,
               count(*) AS n_comparable
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND is_active
          AND complex_id IS NOT NULL
          AND listing_type IS NOT NULL AND property_type IS NOT NULL
          AND price_per_sqm IS NOT NULL AND area_sqm >= %(min_area_sqm)s
          AND price_negotiable IS NOT TRUE
          AND price <= %(max_plausible_price)s
        GROUP BY complex_id, listing_type, property_type
        HAVING count(*) >= %(min_group_size)s
    ),
    priced AS (
        SELECT l.id, l.complex_id, c.canonical_name AS complex_name,
               l.district, l.rooms, l.listing_type, l.property_type,
               l.price, l.price_per_sqm, l.area_sqm,
               round(gm.complex_median_price_per_sqm::numeric, 2)
                   AS complex_median_price_per_sqm,
               gm.n_comparable AS complex_n_comparable,
               round((((gm.complex_median_price_per_sqm - l.price_per_sqm)
                       / gm.complex_median_price_per_sqm) * 100)::numeric, 2)
                   AS complex_deal_pct
        FROM listings l
        JOIN group_medians gm
          ON l.complex_id = gm.complex_id
         AND l.listing_type = gm.listing_type
         AND l.property_type = gm.property_type
        JOIN complexes c ON c.id = l.complex_id
        WHERE l.id != ALL(%(excluded_ids)s)
          AND l.is_active
          AND l.price_per_sqm IS NOT NULL AND l.area_sqm >= %(min_area_sqm)s
          AND l.price_negotiable IS NOT TRUE
          AND l.price <= %(max_plausible_price)s
    )
    SELECT *,
        CASE
            WHEN complex_deal_pct > %(max_confident_pct)s THEN 'needs_review'
            WHEN complex_deal_pct >= %(min_complex_deal_pct)s THEN 'top_deal'
            ELSE 'not_notable'
        END AS complex_deal_status
    FROM priced
    ORDER BY complex_deal_pct DESC
"""


def complex_deal_percentages(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Compare listings with the median price/m² inside their own complex.

    Groups are (complex_id, listing_type, property_type), with the same
    current-market/data-quality guards as complex_average_price(). A 20%
    discount is required for the complex-level top-deal signal; values above
    the existing 50% confidence ceiling remain needs_review, never a badge.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_COMPLEX_DEAL_PERCENTAGES_SQL, {
        "excluded_ids": excluded,
        "min_area_sqm": _MIN_AREA_SQM_FOR_DEAL,
        "max_plausible_price": _MAX_PLAUSIBLE_PRICE,
        "min_group_size": MIN_COMPARABLE_GROUP_SIZE,
        "min_complex_deal_pct": MIN_COMPLEX_DEAL_PCT,
        "max_confident_pct": MAX_CONFIDENT_DEAL_PCT,
    })
    rows = [dict(row) for row in cur.fetchall()]
    for row in rows:
        row["complex_deal_reason"] = (
            _MISCLASSIFICATION_REVIEW_REASON
            if row["complex_deal_status"] == "needs_review"
            else None
        )
    return rows


def complex_deal_percentages_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for complex_deal_percentages()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return complex_deal_percentages(cur)


_ESTIMATE_NEGOTIABLE_PRICE_SQL = """
    WITH group_medians AS (
        SELECT district, rooms, listing_type, property_type,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY price_per_sqm) AS group_median_price_per_sqm,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY price) AS group_median_price,
               count(*) AS n_comparable
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND is_active
          AND district IS NOT NULL AND rooms IS NOT NULL AND price_per_sqm IS NOT NULL
          AND area_sqm >= %(min_area_sqm)s
          AND rooms != %(open_ended_rooms)s
          AND price_negotiable IS NOT TRUE
        GROUP BY district, rooms, listing_type, property_type
        HAVING count(*) >= %(min_group_size)s
    )
    SELECT
        l.id, l.district, l.rooms, l.listing_type, l.property_type,
        l.price AS placeholder_price, l.price_raw, l.area_sqm,
        round(gm.group_median_price_per_sqm::numeric, 2) AS group_median_price_per_sqm,
        round(gm.group_median_price::numeric, 2) AS group_median_price,
        gm.n_comparable,
        CASE
            WHEN l.area_sqm IS NOT NULL AND l.area_sqm >= %(min_area_sqm)s
                THEN round((gm.group_median_price_per_sqm * l.area_sqm)::numeric, 2)
            ELSE round(gm.group_median_price::numeric, 2)
        END AS estimated_price,
        CASE
            WHEN l.area_sqm IS NOT NULL AND l.area_sqm >= %(min_area_sqm)s
                THEN round(gm.group_median_price_per_sqm::numeric, 2)
            ELSE NULL
        END AS estimated_price_per_sqm,
        CASE
            WHEN l.area_sqm IS NOT NULL AND l.area_sqm >= %(min_area_sqm)s THEN 'area_based'
            ELSE 'group_median_price'
        END AS estimate_basis
    FROM listings l
    JOIN group_medians gm
      ON l.district = gm.district AND l.rooms = gm.rooms
     AND l.listing_type = gm.listing_type AND l.property_type = gm.property_type
    WHERE l.id != ALL(%(excluded_ids)s)
      AND l.is_active
      AND l.price_negotiable IS TRUE
      AND l.district IS NOT NULL AND l.rooms IS NOT NULL
      AND l.rooms != %(open_ended_rooms)s
    ORDER BY l.district, l.rooms, l.listing_type
"""


def estimate_negotiable_price(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Price estimate for price_negotiable listings — a placeholder price
    (e.g. "170 ₮ Үнэ тохирно") is never a real one, so instead of treating
    it as data, this estimates what the listing would likely cost from its
    comparable group's real (non-negotiable) prices.

    Deliberately a separate function rather than an extension of
    deal_percentages(): built the same way as everywhere else in this
    module (group MEDIAN not mean, the area floor, the open-ended
    "5+ өрөө" bucket excluded, MIN_COMPARABLE_GROUP_SIZE) — but a
    negotiable listing must never appear in a deal ranking, confident or
    needs_review, since there's no real price to judge it against in the
    first place; estimation and deal-finding are different questions.
    Grouped by (district, rooms, listing_type, property_type) —
    property_type is redundant with rooms for apartments (the only
    rooms IS NOT NULL category, so property_type is already implied), but
    included for parity with a literal reading of the group key and in
    case that ever stops being true.

    Two estimation methods, in estimate_basis:
    - 'area_based': the listing's own area_sqm is known and clears the
      same _MIN_AREA_SQM_FOR_DEAL floor used elsewhere. estimated_price =
      group_median_price_per_sqm * this listing's area_sqm — preferred
      since it accounts for this specific unit's size.
    - 'group_median_price': area is missing or implausible (the same
      floor that would otherwise flag a parsing failure). Falls back to
      the group's own median total price, with estimated_price_per_sqm
      left None — deriving one from an untrusted area would just
      manufacture a second bad number from the first.

    Only ever produced for apartments in rooms 1-4 with a group of at
    least MIN_COMPARABLE_GROUP_SIZE non-negotiable, canonical comparables
    — the same categories deal_percentages() can score. Everything else
    (non-apartments, "5+ өрөө", thin groups) gets no estimate, same "not
    comparable, don't approximate" call made throughout this module.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_ESTIMATE_NEGOTIABLE_PRICE_SQL, {
        "excluded_ids": excluded,
        "min_area_sqm": _MIN_AREA_SQM_FOR_DEAL,
        "open_ended_rooms": _OPEN_ENDED_ROOMS,
        "min_group_size": MIN_COMPARABLE_GROUP_SIZE,
    })
    return [dict(row) for row in cur.fetchall()]


def estimate_negotiable_price_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for estimate_negotiable_price()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return estimate_negotiable_price(cur)


_LAST_SCRAPED_AT_SQL = """
    SELECT max(scraped_at) AS last_scraped_at
    FROM listings
    WHERE district = %(district)s
      AND id != ALL(%(excluded_ids)s)
      AND is_active
"""


def todays_opportunity(cur: psycopg2.extensions.cursor) -> dict[str, Any] | None:
    """"Which district looks like the best opportunity today" for a
    dashboard headline, built entirely from investment_summary_by_district()
    and deal_percentages() -- no separate scoring model, nothing invented.
    Returns None when investment_summary_by_district() has no district at
    all yet (e.g. a freshly-seeded DB the scraper hasn't populated enough
    of), which callers must render as "not available", never as a zeroed
    or placeholder result.

    The featured district is simply investment_summary_by_district()'s own
    top-ranked row (rows[0] -- already sorted by its documented, transparent
    investment_score) rather than a new ranking rule. Deliberately not
    returned here, though: investment_score is a 50/50 price-rank/yield-rank
    blend meant for sorting a table, not a number to headline on its own --
    surfacing it as an unlabeled score next to "today's opportunity" invites
    exactly the "AI score" misreading this function exists to avoid, so
    callers get only the real, individually-labeled component metrics
    (price, yield, deal share, sample sizes) that a reader can check
    against the district table themselves.

    top_deal_pct is share of that district's own deal_percentages() rows
    classified 'top_deal' -- a second, independently-thresholded comparable
    check (grouped by district+rooms+listing_type, not just district), so
    it can legitimately come back with zero comparable groups (None) even
    for a district that clears investment_summary_by_district's own
    n_sale/n_rent >= 20 gate, which is coarser. n_deals_analyzed is that
    group's own size, so a caller can judge how much to trust the
    percentage regardless.

    last_scraped_at is real -- max(scraped_at) over the district's own
    canonical listings -- never a guessed or "as of now" timestamp; None in
    the (currently impossible, since investment_summary_by_district already
    requires 20+ listings) edge case of no canonical listings at all.
    """
    ranked = investment_summary_by_district(cur)
    if not ranked:
        return None
    top = ranked[0]
    district = top["district"]

    deals = deal_percentages(cur, district=district)
    n_deals_analyzed = len(deals)
    top_deal_pct = (
        round(sum(1 for d in deals if d["deal_status"] == "top_deal") / n_deals_analyzed * 100, 1)
        if n_deals_analyzed > 0
        else None
    )

    excluded = list(superseded_listing_ids(cur))
    cur.execute(_LAST_SCRAPED_AT_SQL, {"district": district, "excluded_ids": excluded})
    last_scraped_at = cur.fetchone()["last_scraped_at"]

    return {
        "district": district,
        "n_sale": top["n_sale"],
        "n_rent": top["n_rent"],
        "avg_sale_price": top["avg_sale_price"],
        "avg_price_per_sqm": top["avg_price_per_sqm"],
        "gross_rental_yield_pct": top["gross_rental_yield_pct"],
        "top_deal_pct": top_deal_pct,
        "n_deals_analyzed": n_deals_analyzed,
        "last_scraped_at": last_scraped_at,
    }


def todays_opportunity_conn(dsn: str) -> dict[str, Any] | None:
    """Connection-owning wrapper for todays_opportunity()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return todays_opportunity(cur)
