"""Integration tests for market calculation queries, run against the local
Postgres inside a transaction that is always rolled back. The `cur` fixture
(conftest.py) sees real committed data too, but synthetic districts below
use names that cannot collide with real Ulaanbaatar district data."""

from scraper.calculations import average_price_by_group
from scraper.matches import record_matches

_INSERT_SQL = """
    INSERT INTO listings (source, source_url, title, price, area_sqm,
                          district, listing_type, property_type, photo_urls,
                          dedup_hash)
    VALUES ('unegui', %(source_url)s, 'test', %(price)s, %(area_sqm)s,
            %(district)s, %(listing_type)s, %(property_type)s, '{}', 'test-hash')
    RETURNING id
"""


def _insert(cur, url, price, area, *, listing_type="sale",
            property_type="Орон сууц зарна", district="Тест дүүрэг") -> int:
    cur.execute(_INSERT_SQL, {
        "source_url": url, "price": price, "area_sqm": area,
        "district": district, "listing_type": listing_type, "property_type": property_type,
    })
    return cur.fetchone()["id"]


def _group(rows, *, listing_type, property_type, district):
    return next(
        r for r in rows
        if r["listing_type"] == listing_type
        and r["property_type"] == property_type
        and r["district"] == district
    )


def test_average_price_by_group_computes_correct_stats(cur) -> None:
    _insert(cur, "test://calc-a", 100_000_000, 50.0)
    _insert(cur, "test://calc-b", 200_000_000, 50.0)
    # different district -> must not leak into the group above
    _insert(cur, "test://calc-c", 999_000_000, 100.0, district="Өөр дүүрэг")

    rows = average_price_by_group(cur)
    group = _group(rows, listing_type="sale", property_type="Орон сууц зарна", district="Тест дүүрэг")
    assert group["n_listings"] == 2
    assert float(group["avg_price"]) == 150_000_000.0
    # price_per_sqm per row: 100M/50=2M, 200M/50=4M -> avg 3M
    assert float(group["avg_price_per_sqm"]) == 3_000_000.0
    assert group["n_with_price_per_sqm"] == 2


def test_sale_and_rent_are_never_blended_in_one_average(cur) -> None:
    _insert(cur, "test://calc-sale", 300_000_000, 50.0, listing_type="sale", district="Холимог дүүрэг")
    _insert(cur, "test://calc-rent", 1_500_000, 50.0, listing_type="rent", district="Холимог дүүрэг")

    rows = average_price_by_group(cur)
    sale_group = _group(rows, listing_type="sale", property_type="Орон сууц зарна", district="Холимог дүүрэг")
    rent_group = _group(rows, listing_type="rent", property_type="Орон сууц зарна", district="Холимог дүүрэг")
    assert sale_group["n_listings"] == 1 and float(sale_group["avg_price"]) == 300_000_000.0
    assert rent_group["n_listings"] == 1 and float(rent_group["avg_price"]) == 1_500_000.0


def test_missing_area_excluded_from_price_per_sqm_but_not_from_average_price(cur) -> None:
    _insert(cur, "test://calc-noarea", 50_000_000, None, district="Талбайгүй дүүрэг")

    rows = average_price_by_group(cur)
    group = _group(rows, listing_type="sale", property_type="Орон сууц зарна", district="Талбайгүй дүүрэг")
    assert group["n_listings"] == 1
    assert float(group["avg_price"]) == 50_000_000.0
    assert group["avg_price_per_sqm"] is None
    assert group["n_with_price_per_sqm"] == 0


def test_auto_resolved_duplicate_counted_once(cur) -> None:
    id_a = _insert(cur, "test://dupcalc-a", 100_000_000, 50.0, district="Дубль дүүрэг")
    id_b = _insert(cur, "test://dupcalc-b", 999_000_000, 50.0, district="Дубль дүүрэг")
    record_matches(cur, [(min(id_a, id_b), max(id_a, id_b), 0.95)])  # auto-resolve tier

    rows = average_price_by_group(cur)
    group = _group(rows, listing_type="sale", property_type="Орон сууц зарна", district="Дубль дүүрэг")
    assert group["n_listings"] == 1
    # tie on completeness/posted_at -> pick_canonical keeps the higher id (id_b)
    assert float(group["avg_price"]) == 999_000_000.0


def test_possible_duplicate_tier_does_not_reduce_the_count(cur) -> None:
    """A 0.60-0.80 match must not remove either listing from the average —
    only >=0.80 auto-resolves (see dedup.AUTO_RESOLVE_THRESHOLD)."""
    id_a = _insert(cur, "test://reviewcalc-a", 100_000_000, 50.0, district="Хянах дүүрэг")
    id_b = _insert(cur, "test://reviewcalc-b", 200_000_000, 50.0, district="Хянах дүүрэг")
    record_matches(cur, [(min(id_a, id_b), max(id_a, id_b), 0.65)])  # review tier

    rows = average_price_by_group(cur)
    group = _group(rows, listing_type="sale", property_type="Орон сууц зарна", district="Хянах дүүрэг")
    assert group["n_listings"] == 2
    assert float(group["avg_price"]) == 150_000_000.0


def test_real_data_smoke_check(cur) -> None:
    """Sanity check against the actual scraped dataset (visible inside the
    same rollback transaction): must run and return plausible aggregates."""
    rows = average_price_by_group(cur)
    assert len(rows) > 0
    total_grouped = sum(r["n_listings"] for r in rows)
    assert 0 < total_grouped <= 36_666
    for row in rows:
        assert row["avg_price"] is None or float(row["avg_price"]) > 0
