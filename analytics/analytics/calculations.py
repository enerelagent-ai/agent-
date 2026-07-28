"""Core market calculation queries over canonical (non-duplicate) listings.

Every query excludes matches.superseded_listing_ids() first, so an
auto-resolved duplicate group is counted once, not once per repost.
"""

from datetime import date
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
               round(avg(price)::numeric, 2) AS avg_sale_price,
               round(avg(price_per_sqm)::numeric, 2) AS avg_sale_price_per_sqm
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
    avg_sale_price_per_sqm is the sale side's price/m² for the same bucket
    (rent side has no equivalent field — nothing here needs it).
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


_LISTING_COUNTS_SQL = """
    SELECT
        listing_type,
        CASE WHEN property_type = ANY(%(apartment_labels)s) THEN 'apartments' ELSE 'other' END AS bucket,
        count(*) AS n
    FROM listings
    WHERE id != ALL(%(excluded_ids)s)
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
    GROUP BY snapshot_date
    ORDER BY snapshot_date
"""


def price_trend(
    cur: psycopg2.extensions.cursor,
    listing_type: str = "sale",
    property_type: str = "Орон сууц зарна",
) -> list[dict[str, Any]]:
    """Overall price trend for one (listing_type, property_type) slice: one
    point per snapshot_date, with districts recombined by each snapshot's own
    n_listings weight (mirroring investment_summary_by_district's approach)
    rather than a naive average across districts.

    Defaults to sale-side apartments — the closest analogue to the "average
    price / m²" headline figure a market dashboard usually leads with, and
    the category with the deepest, most reliable data (see
    yield_category_coverage). With only one snapshot on record, this returns
    a single point; it fills in as snapshot_market_prices() runs again over
    time, with no change needed here.
    """
    cur.execute(_PRICE_TREND_SQL, {"listing_type": listing_type, "property_type": property_type})
    return [dict(row) for row in cur.fetchall()]


def price_trend_conn(
    dsn: str, listing_type: str = "sale", property_type: str = "Орон сууц зарна"
) -> list[dict[str, Any]]:
    """Connection-owning wrapper for price_trend()."""
    with psycopg2.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return price_trend(cur, listing_type, property_type)
