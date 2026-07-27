"""Core market calculation queries over canonical (non-duplicate) listings.

Every query excludes matches.superseded_listing_ids() first, so an
auto-resolved duplicate group is counted once, not once per repost.
"""

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
