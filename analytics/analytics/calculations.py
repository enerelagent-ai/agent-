"""Core market calculation queries over canonical (non-duplicate) listings.

Every query excludes matches.superseded_listing_ids() first, so an
auto-resolved duplicate group is counted once, not once per repost.
"""

from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras

from analytics.matches import superseded_listing_ids
from analytics.db import normalize_dsn

# listing_type is included in the group-by even though only property_type
# and district were asked for: sale and rent prices differ by ~100x for the
# same property_type (see db/schema.sql's listing_type comment, and the
# Week 4 investigation) — blending them would make the average meaningless.
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
      AND listing_type IS NOT NULL
      AND property_type IS NOT NULL
      AND district IS NOT NULL
    GROUP BY listing_type, property_type, district
    ORDER BY listing_type, property_type, n_listings DESC
"""


def average_price_by_group(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Average price and price/m² per (listing_type, property_type, district)
    group, over canonical listings only.

    avg_price_per_sqm is computed over the stored generated column, so it
    only reflects listings that have both price and area_sqm; n_listings vs
    n_with_price_per_sqm shows how many of the group lack area data (common
    for land/object listings).
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_GROUP_STATS_SQL, {"excluded_ids": excluded})
    return [dict(row) for row in cur.fetchall()]


def average_price_by_group_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for average_price_by_group()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return average_price_by_group(cur)


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
               round(avg(price)::numeric, 2) AS avg_sale_price
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND listing_type = 'sale' AND property_type = %(sale_label)s
          AND district IS NOT NULL AND rooms IS NOT NULL
        GROUP BY district, property_subtype, rooms
    ),
    rent AS (
        SELECT district, property_subtype, rooms,
               count(*) AS n_rent,
               round(avg(price)::numeric, 2) AS avg_rent_price
        FROM listings
        WHERE id != ALL(%(excluded_ids)s)
          AND listing_type = 'rent' AND property_type = %(rent_label)s
          AND district IS NOT NULL AND rooms IS NOT NULL
        GROUP BY district, property_subtype, rooms
    )
    SELECT
        s.district, s.property_subtype, s.rooms,
        s.n_sale, s.avg_sale_price,
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


def rental_yield_by_district_rooms(cur: psycopg2.extensions.cursor) -> list[dict[str, Any]]:
    """Gross rental yield for apartments, matched sale-to-rent by (district,
    property_subtype, rooms) instead of a blunt property_type-level average,
    so a studio in one district isn't blended with a 5-room unit in another.

    Apartments are the only property_type with this granular breakdown
    (see the module-level comment above and yield_category_coverage()), so
    this only ever returns "Орон сууц" rows. avg_annual_rent assumes the
    stored rent price is monthly, which real-DB magnitudes confirm (e.g.
    2-room: ~232M avg sale vs ~2.08M avg monthly rent -> ~10.8% yield, a
    plausible gross residential yield). payback_years is avg_sale_price
    divided by avg_annual_rent — years of rent to recoup the purchase price
    at current averages, ignoring financing, vacancy, and expenses.
    """
    excluded = list(superseded_listing_ids(cur))
    cur.execute(_RENTAL_YIELD_SQL, {
        "excluded_ids": excluded,
        "sale_label": _APARTMENT_SALE_LABEL,
        "rent_label": _APARTMENT_RENT_LABEL,
    })
    return [dict(row) for row in cur.fetchall()]


def rental_yield_by_district_rooms_conn(dsn: str) -> list[dict[str, Any]]:
    """Connection-owning wrapper for rental_yield_by_district_rooms()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return rental_yield_by_district_rooms(cur)


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
    WHERE listing_type = %(listing_type)s AND property_type = %(label)s
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


# Below this on either side, a district is dropped from the ranked table
# entirely rather than scored: with too few listings, investment_score is
# noise, not signal. Verified against the live DB — without this cutoff,
# Багануур's single sale/rent pair (n_sale=1) outranks Хан-Уул's 4,308
# sale listings purely because the ranking treats every district equally
# regardless of sample size.
_MIN_SAMPLE_SIZE = 20


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
    yields directly, for the same reason.

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

    totals: dict[str, dict[str, Any]] = {}
    for b in buckets:
        t = totals.setdefault(b["district"], {
            "n_sale": 0, "n_rent": 0,
            "sale_price_sum": Decimal(0), "annual_rent_sum": Decimal(0),
        })
        t["n_sale"] += b["n_sale"]
        t["n_rent"] += b["n_rent"]
        t["sale_price_sum"] += b["avg_sale_price"] * b["n_sale"]
        t["annual_rent_sum"] += b["avg_annual_rent"] * b["n_rent"]

    rows = []
    for district, t in totals.items():
        if t["n_sale"] < _MIN_SAMPLE_SIZE or t["n_rent"] < _MIN_SAMPLE_SIZE:
            continue
        avg_sale_price = t["sale_price_sum"] / t["n_sale"]
        avg_annual_rent = t["annual_rent_sum"] / t["n_rent"]
        gross_yield_pct = (avg_annual_rent / avg_sale_price) * 100
        rows.append({
            "district": district,
            "n_sale": t["n_sale"],
            "n_rent": t["n_rent"],
            "avg_sale_price": round(avg_sale_price, 2),
            "gross_rental_yield_pct": round(gross_yield_pct, 2),
            "roi_pct": round(gross_yield_pct, 2),
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
