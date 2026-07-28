"""Integration tests for market calculation queries, run against the local
Postgres inside a transaction that is always rolled back. The `cur` fixture
(conftest.py) sees real committed data too, but synthetic districts below
use names that cannot collide with real Ulaanbaatar district data."""

from datetime import date

import pytest

from analytics.calculations import (
    MAX_CONFIDENT_DEAL_PCT,
    MIN_COMPARABLE_GROUP_SIZE,
    _MIN_AREA_SQM_FOR_DEAL,
    _OPEN_ENDED_ROOMS,
    average_price_by_group,
    classify_deal,
    deal_percentages,
    estimate_negotiable_price,
    investment_summary_by_district,
    listing_counts_by_property_type,
    price_trend,
    rental_yield_by_district_rooms,
    snapshot_market_prices,
    yield_category_coverage,
)
from analytics.matches import record_matches

_INSERT_SQL = """
    INSERT INTO listings (source, source_url, title, price, area_sqm,
                          district, listing_type, property_type,
                          property_subtype, rooms, photo_urls, dedup_hash)
    VALUES ('unegui', %(source_url)s, 'test', %(price)s, %(area_sqm)s,
            %(district)s, %(listing_type)s, %(property_type)s,
            %(property_subtype)s, %(rooms)s, '{}', 'test-hash')
    RETURNING id
"""


def _insert(cur, url, price, area, *, listing_type="sale",
            property_type="Орон сууц зарна", district="Тест дүүрэг",
            property_subtype=None, rooms=None) -> int:
    cur.execute(_INSERT_SQL, {
        "source_url": url, "price": price, "area_sqm": area,
        "district": district, "listing_type": listing_type, "property_type": property_type,
        "property_subtype": property_subtype, "rooms": rooms,
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


def _yield_row(rows, *, district, rooms):
    return next(r for r in rows if r["district"] == district and r["rooms"] == rooms)


def test_rental_yield_matches_by_district_and_rooms_not_by_category_average(cur) -> None:
    # Same district, two different room sizes, each with its own sale/rent pair.
    _insert(cur, "test://yield-1r-sale", 100_000_000, 30.0,
            district="Өгөөж дүүрэг", property_subtype="1 өрөө", rooms=1)
    _insert(cur, "test://yield-1r-rent", 1_000_000, 30.0, listing_type="rent",
            property_type="Орон сууц түрээслүүлнэ",
            district="Өгөөж дүүрэг", property_subtype="1 өрөө", rooms=1)
    _insert(cur, "test://yield-3r-sale", 400_000_000, 80.0,
            district="Өгөөж дүүрэг", property_subtype="3 өрөө", rooms=3)
    _insert(cur, "test://yield-3r-rent", 2_000_000, 80.0, listing_type="rent",
            property_type="Орон сууц түрээслүүлнэ",
            district="Өгөөж дүүрэг", property_subtype="3 өрөө", rooms=3)

    rows = rental_yield_by_district_rooms(cur)
    one_room = _yield_row(rows, district="Өгөөж дүүрэг", rooms=1)
    three_room = _yield_row(rows, district="Өгөөж дүүрэг", rooms=3)

    # 1-room: 1M/mo * 12 = 12M annual / 100M sale = 12%, payback 100M/12M = 8.3y
    assert float(one_room["gross_rental_yield_pct"]) == 12.0
    assert float(one_room["payback_years"]) == 8.3
    assert float(one_room["avg_sale_price_per_sqm"]) == pytest.approx(100_000_000 / 30, abs=0.01)
    # 3-room: 2M/mo * 12 = 24M annual / 400M sale = 6% — must not be blended
    # with the 1-room pair into a single category-level average.
    assert float(three_room["gross_rental_yield_pct"]) == 6.0
    assert float(three_room["avg_sale_price_per_sqm"]) == pytest.approx(400_000_000 / 80, abs=0.01)


def test_rental_yield_requires_both_sale_and_rent_present(cur) -> None:
    _insert(cur, "test://yield-onesided", 100_000_000, 30.0,
            district="Ганц тал дүүрэг", property_subtype="2 өрөө", rooms=2)

    rows = rental_yield_by_district_rooms(cur)
    assert all(r["district"] != "Ганц тал дүүрэг" for r in rows)


def test_rental_yield_excludes_auto_resolved_duplicate(cur) -> None:
    id_a = _insert(cur, "test://yield-dup-a", 100_000_000, 30.0,
                   district="Давхар дүүрэг", property_subtype="2 өрөө", rooms=2)
    id_b = _insert(cur, "test://yield-dup-b", 300_000_000, 30.0,
                   district="Давхар дүүрэг", property_subtype="2 өрөө", rooms=2)
    record_matches(cur, [(min(id_a, id_b), max(id_a, id_b), 0.95)])  # auto-resolve tier
    _insert(cur, "test://yield-dup-rent", 1_000_000, 30.0, listing_type="rent",
            property_type="Орон сууц түрээслүүлнэ",
            district="Давхар дүүрэг", property_subtype="2 өрөө", rooms=2)

    rows = rental_yield_by_district_rooms(cur)
    row = _yield_row(rows, district="Давхар дүүрэг", rooms=2)
    assert row["n_sale"] == 1
    # tie on completeness/posted_at -> pick_canonical keeps the higher id (id_b, 300M)
    assert float(row["avg_sale_price"]) == 300_000_000.0


def test_yield_category_coverage_apartments_calculable_others_are_not(cur) -> None:
    rows = yield_category_coverage(cur)
    by_category = {r["category"]: r for r in rows}

    apartments = by_category["Орон сууц (apartments)"]
    assert apartments["calculable"] is True
    assert apartments["reason"] is None
    assert apartments["n_sale"] > 0 and apartments["n_rent"] > 0

    land = by_category["Газар (land)"]
    assert land["calculable"] is False
    assert "subtype/rooms" in land["reason"]

    houses = by_category["Хашаа байшин (houses)"]
    assert houses["calculable"] is False
    assert "gers" in houses["reason"]

    ger = by_category["Монгол гэр (traditional ger)"]
    assert ger["calculable"] is False
    assert "folded into" in ger["reason"]

    hostel = by_category["Hostel/Хостел"]
    assert hostel["calculable"] is False
    assert "rent-only" in hostel["reason"]

    # every category must land in exactly one bucket, with a reason iff excluded
    assert all((r["reason"] is None) == r["calculable"] for r in rows)


def _district_row(rows, district):
    return next(r for r in rows if r["district"] == district)


def _insert_many(cur, url_prefix, n, price, area, **kwargs):
    for i in range(n):
        _insert(cur, f"{url_prefix}-{i}", price, area, **kwargs)


def test_investment_summary_recombines_weighted_avg_price_and_yield_per_district(cur) -> None:
    # 1-room bucket: 15 sales @100M, 10 rents @1M/mo
    _insert_many(cur, "test://inv-a-1r-sale", 15, 100_000_000, 30.0,
                 district="Инвест А", property_subtype="1 өрөө", rooms=1)
    _insert_many(cur, "test://inv-a-1r-rent", 10, 1_000_000, 30.0, listing_type="rent",
                 property_type="Орон сууц түрээслүүлнэ",
                 district="Инвест А", property_subtype="1 өрөө", rooms=1)
    # 2-room bucket: 5 sales @300M, 10 rents @2M/mo
    _insert_many(cur, "test://inv-a-2r-sale", 5, 300_000_000, 60.0,
                 district="Инвест А", property_subtype="2 өрөө", rooms=2)
    _insert_many(cur, "test://inv-a-2r-rent", 10, 2_000_000, 60.0, listing_type="rent",
                 property_type="Орон сууц түрээслүүлнэ",
                 district="Инвест А", property_subtype="2 өрөө", rooms=2)
    # total n_sale=20, n_rent=20 -> right at _MIN_SAMPLE_SIZE, must still be included

    rows = investment_summary_by_district(cur)
    row = _district_row(rows, "Инвест А")

    # weighted avg price: (100M*15 + 300M*5) / 20 = 150,000,000
    assert float(row["avg_sale_price"]) == pytest.approx(150_000_000.0, abs=0.01)
    # weighted price/sqm: (100M/30 * 15 + 300M/60 * 5) / 20 = 3,750,000
    assert float(row["avg_price_per_sqm"]) == pytest.approx(3_750_000.0, abs=0.01)
    # weighted annual rent: (1M*12*10 + 2M*12*10) / 20 = 18,000,000; yield = 18M/150M*100 = 12%
    assert float(row["gross_rental_yield_pct"]) == pytest.approx(12.0, abs=0.01)
    assert row["roi_pct"] == row["gross_rental_yield_pct"]
    assert row["n_sale"] == 20
    assert row["n_rent"] == 20


def test_investment_summary_drops_districts_below_min_sample_size(cur) -> None:
    # 19 sales, 19 rents -> one short of _MIN_SAMPLE_SIZE=20 on both sides
    _insert_many(cur, "test://inv-thin-sale", 19, 100_000_000, 30.0,
                 district="Нимгэн дүүрэг", property_subtype="1 өрөө", rooms=1)
    _insert_many(cur, "test://inv-thin-rent", 19, 1_000_000, 30.0, listing_type="rent",
                 property_type="Орон сууц түрээслүүлнэ",
                 district="Нимгэн дүүрэг", property_subtype="1 өрөө", rooms=1)

    rows = investment_summary_by_district(cur)
    assert all(r["district"] != "Нимгэн дүүрэг" for r in rows)


def test_investment_score_ranks_cheaper_higher_yield_district_above_pricier_lower_yield(cur) -> None:
    # Cheap and high-yield: 1-room, 20 sales @100M, 20 rents @1M/mo -> yield 12%
    _insert_many(cur, "test://inv-cheap-sale", 20, 100_000_000, 30.0,
                 district="Инвест Хямд", property_subtype="1 өрөө", rooms=1)
    _insert_many(cur, "test://inv-cheap-rent", 20, 1_000_000, 30.0, listing_type="rent",
                 property_type="Орон сууц түрээслүүлнэ",
                 district="Инвест Хямд", property_subtype="1 өрөө", rooms=1)
    # Expensive and low-yield: 1-room, 20 sales @500M, 20 rents @1M/mo -> yield 2.4%
    _insert_many(cur, "test://inv-costly-sale", 20, 500_000_000, 30.0,
                 district="Инвест Үнэтэй", property_subtype="1 өрөө", rooms=1)
    _insert_many(cur, "test://inv-costly-rent", 20, 1_000_000, 30.0, listing_type="rent",
                 property_type="Орон сууц түрээслүүлнэ",
                 district="Инвест Үнэтэй", property_subtype="1 өрөө", rooms=1)

    rows = investment_summary_by_district(cur)
    cheap = _district_row(rows, "Инвест Хямд")
    costly = _district_row(rows, "Инвест Үнэтэй")

    # cheaper AND higher-yield must outrank pricier AND lower-yield,
    # regardless of where real districts fall in the same ranking.
    assert cheap["investment_score"] > costly["investment_score"]
    assert 0.0 <= cheap["investment_score"] <= 100.0
    assert 0.0 <= costly["investment_score"] <= 100.0


def test_investment_summary_real_data_smoke_check(cur) -> None:
    """Sanity check against the actual scraped dataset: must run and return
    plausible aggregates for every real district with apartment yield data."""
    rows = investment_summary_by_district(cur)
    assert len(rows) > 0
    for row in rows:
        assert row["avg_sale_price"] > 0
        assert row["roi_pct"] == row["gross_rental_yield_pct"]
        assert 0.0 <= row["investment_score"] <= 100.0
        assert row["n_sale"] > 0 and row["n_rent"] > 0


# A clearly-fake date, distinct from any date a real snapshot run would use
# (today), so these tests never collide with the real price_history rows.
_TEST_SNAPSHOT_DATE = date(2020, 1, 1)


def _price_history_row(cur, *, listing_type, property_type, district, snapshot_date=_TEST_SNAPSHOT_DATE):
    cur.execute(
        "SELECT * FROM price_history WHERE snapshot_date = %s AND listing_type = %s"
        " AND property_type = %s AND district = %s",
        (snapshot_date, listing_type, property_type, district),
    )
    return cur.fetchone()


def _insert_price_history(cur, *, district, n_listings, avg_price, avg_price_per_sqm=None,
                           listing_type="sale", property_type="Орон сууц зарна",
                           snapshot_date=_TEST_SNAPSHOT_DATE) -> None:
    cur.execute(
        "INSERT INTO price_history (snapshot_date, listing_type, property_type,"
        " district, n_listings, avg_price, avg_price_per_sqm)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (snapshot_date, listing_type, property_type, district, n_listings, avg_price, avg_price_per_sqm),
    )


def test_snapshot_market_prices_inserts_a_row_per_group(cur) -> None:
    _insert(cur, "test://snap-a", 100_000_000, 50.0, district="Түүх дүүрэг")
    _insert(cur, "test://snap-b", 200_000_000, 50.0, district="Түүх дүүрэг")

    n = snapshot_market_prices(cur, snapshot_date=_TEST_SNAPSHOT_DATE)
    assert n > 0

    row = _price_history_row(cur, listing_type="sale", property_type="Орон сууц зарна", district="Түүх дүүрэг")
    assert row is not None
    assert row["n_listings"] == 2
    assert float(row["avg_price"]) == 150_000_000.0


def test_snapshot_market_prices_upserts_on_rerun_same_day(cur) -> None:
    _insert(cur, "test://snap-rerun-a", 100_000_000, 50.0, district="Дахин дүүрэг")
    snapshot_market_prices(cur, snapshot_date=_TEST_SNAPSHOT_DATE)

    # A second listing appears before the next run on the same day.
    _insert(cur, "test://snap-rerun-b", 300_000_000, 50.0, district="Дахин дүүрэг")
    snapshot_market_prices(cur, snapshot_date=_TEST_SNAPSHOT_DATE)

    cur.execute(
        "SELECT count(*) AS n FROM price_history WHERE snapshot_date = %s"
        " AND listing_type = 'sale' AND property_type = 'Орон сууц зарна' AND district = 'Дахин дүүрэг'",
        (_TEST_SNAPSHOT_DATE,),
    )
    assert cur.fetchone()["n"] == 1  # upserted, not duplicated

    row = _price_history_row(cur, listing_type="sale", property_type="Орон сууц зарна", district="Дахин дүүрэг")
    assert row["n_listings"] == 2
    assert float(row["avg_price"]) == 200_000_000.0


def test_price_trend_weights_districts_by_their_own_n_listings(cur) -> None:
    """price_trend aggregates across ALL districts for a slice, so seed
    price_history directly (not via snapshot_market_prices, which snapshots
    the whole DB and would mix thousands of real apartment listings from
    other districts into this same snapshot_date) to keep this isolated."""
    _insert_price_history(cur, district="Тренд А", n_listings=3, avg_price=100_000_000)
    _insert_price_history(cur, district="Тренд Б", n_listings=1, avg_price=500_000_000)

    rows = price_trend(cur, listing_type="sale", property_type="Орон сууц зарна")
    row = next(r for r in rows if r["snapshot_date"] == _TEST_SNAPSHOT_DATE)

    # weighted avg: (100M*3 + 500M*1) / 4 = 200,000,000 -- must not be a
    # naive (100M + 500M) / 2 = 300M average across the two districts.
    assert float(row["avg_price"]) == 200_000_000.0
    assert row["n_listings"] == 4


def test_price_trend_real_data_smoke_check(cur) -> None:
    """Once a real snapshot has been recorded, the default (sale, apartments)
    slice must return at least one plausible point."""
    rows = price_trend(cur)
    assert len(rows) > 0
    for row in rows:
        assert row["avg_price"] is None or float(row["avg_price"]) > 0


def _counts_by_key(cur):
    return {(r["bucket"], r["listing_type"]): r["n"] for r in listing_counts_by_property_type(cur)}


def test_listing_counts_by_property_type_buckets_and_counts_correctly(cur) -> None:
    before = _counts_by_key(cur)

    _insert(cur, "test://counts-apt-sale", 100_000_000, 50.0,
            listing_type="sale", property_type="Орон сууц зарна", district="Тоолол дүүрэг")
    _insert(cur, "test://counts-apt-rent", 1_000_000, 50.0,
            listing_type="rent", property_type="Орон сууц түрээслүүлнэ", district="Тоолол дүүрэг")
    _insert(cur, "test://counts-other-sale", 50_000_000, 50.0,
            listing_type="sale", property_type="Тест бусад зарна", district="Тоолол дүүрэг")
    _insert(cur, "test://counts-other-rent", 500_000, 50.0,
            listing_type="rent", property_type="Тест бусад түрээслүүлнэ", district="Тоолол дүүрэг")

    after = _counts_by_key(cur)
    assert after[("apartments", "sale")] == before[("apartments", "sale")] + 1
    assert after[("apartments", "rent")] == before[("apartments", "rent")] + 1
    assert after[("other", "sale")] == before[("other", "sale")] + 1
    assert after[("other", "rent")] == before[("other", "rent")] + 1


def test_listing_counts_by_property_type_excludes_superseded_duplicate(cur) -> None:
    before = _counts_by_key(cur)

    id_a = _insert(cur, "test://counts-dup-a", 100_000_000, 50.0,
                   property_type="Орон сууц зарна", district="Тоолол давхар дүүрэг")
    id_b = _insert(cur, "test://counts-dup-b", 300_000_000, 50.0,
                   property_type="Орон сууц зарна", district="Тоолол давхар дүүрэг")
    record_matches(cur, [(min(id_a, id_b), max(id_a, id_b), 0.95)])  # auto-resolve tier

    after = _counts_by_key(cur)
    assert after[("apartments", "sale")] == before[("apartments", "sale")] + 1  # not +2


def test_listing_counts_by_property_type_returns_exactly_four_rows(cur) -> None:
    rows = listing_counts_by_property_type(cur)
    keys = {(r["bucket"], r["listing_type"]) for r in rows}
    assert keys == {("apartments", "sale"), ("apartments", "rent"), ("other", "sale"), ("other", "rent")}
    assert all(r["n"] >= 0 for r in rows)


def _deal_row(rows, url_id):
    return next(r for r in rows if r["id"] == url_id)


def test_deal_percentages_computed_against_group_median(cur) -> None:
    # Group of 20 (MIN_COMPARABLE_GROUP_SIZE): 17 filler listings @ 3M/sqm,
    # plus 100M/150M/200M @ 50 sqm each -> price/sqm 2M, 3M, 4M. Median of
    # the 20 values stays exactly 3M (18 of them sit at 3M) -- equal to the
    # mean for this near-symmetric case; the median-vs-mean distinction only
    # bites with a skewing outlier, see test_deal_percentages_median_resists_outlier.
    _insert_many(cur, "test://deal-filler", 17, 150_000_000, 50.0,
                 district="Дил дүүрэг", rooms=2)
    id_a = _insert(cur, "test://deal-a", 100_000_000, 50.0, district="Дил дүүрэг", rooms=2)
    id_b = _insert(cur, "test://deal-b", 150_000_000, 50.0, district="Дил дүүрэг", rooms=2)
    id_c = _insert(cur, "test://deal-c", 200_000_000, 50.0, district="Дил дүүрэг", rooms=2)

    rows = deal_percentages(cur)
    row_a, row_b, row_c = (_deal_row(rows, i) for i in (id_a, id_b, id_c))

    assert float(row_a["group_median_price_per_sqm"]) == pytest.approx(3_000_000.0, abs=0.01)
    assert row_a["n_comparable"] == 20
    # cheapest -> best deal (positive), priciest -> worst (negative)
    assert float(row_a["deal_pct"]) == pytest.approx(33.33, abs=0.01)
    assert float(row_b["deal_pct"]) == pytest.approx(0.0, abs=0.01)
    assert float(row_c["deal_pct"]) == pytest.approx(-33.33, abs=0.01)
    assert row_a["deal_pct"] > row_b["deal_pct"] > row_c["deal_pct"]
    # 33.33% clears MIN_NOTABLE_DEAL_PCT but not MAX_CONFIDENT_DEAL_PCT
    assert row_a["deal_status"] == "top_deal"
    assert row_a["deal_reason"] is None
    assert row_b["deal_status"] == "not_notable"  # 0% isn't notable either way
    assert row_c["deal_status"] == "not_notable"  # priced above median, not a deal


def test_deal_percentages_median_resists_single_outlier(cur) -> None:
    """Verified against the real DB: a single corrupted row in a Сүхбаатар
    4-room rental group (area_sqm=1, so price/sqm came out ~40x too high)
    dragged that group's MEAN more than 2x above its median, making several
    normally-priced listings look like 70-80% "deals". This reproduces the
    same shape with a bad PRICE instead of a bad area (area alone is already
    caught by _MIN_AREA_SQM_FOR_DEAL, so this isolates the mean-vs-median
    fix specifically): 19 normal listings + 1 with a garbage low price.
    """
    normal_ids = [
        _insert(cur, f"test://deal-outlier-normal-{i}", 150_000_000, 50.0,
                district="Хэвийн дил дүүрэг", rooms=2)
        for i in range(19)
    ]  # price/sqm = 3,000,000 each; 19 + 1 outlier = 20, MIN_COMPARABLE_GROUP_SIZE
    outlier_id = _insert(cur, "test://deal-outlier-bad", 1_000_000, 50.0,
                          district="Хэвийн дил дүүрэг", rooms=2)  # price/sqm = 20,000 (typo-like)

    rows = deal_percentages(cur)
    normal_rows = [_deal_row(rows, i) for i in normal_ids]
    outlier_row = _deal_row(rows, outlier_id)

    # median of [3M x19, 20K] is 3M -- untouched by the one outlier (a mean
    # would be pulled down to ~2.85M, which would make every normal listing
    # look ~-5% i.e. overpriced, instead of the correct 0%).
    for row in normal_rows:
        assert float(row["group_median_price_per_sqm"]) == pytest.approx(3_000_000.0, abs=0.01)
        assert float(row["deal_pct"]) == pytest.approx(0.0, abs=0.01)
        assert row["deal_status"] == "not_notable"

    # the outlier itself is still an extreme deviation either way -- but the
    # confidence tier correctly keeps it OUT of the confident "top deal" list.
    assert float(outlier_row["deal_pct"]) > MAX_CONFIDENT_DEAL_PCT
    assert outlier_row["deal_status"] == "needs_review"
    assert outlier_row["deal_reason"] == "магадгүй ангилал буруу — шалгах шаардлагатай"


def test_deal_percentages_excludes_listings_without_rooms(cur) -> None:
    # No property_subtype/rooms data -- e.g. an office or land listing.
    _insert(cur, "test://deal-norooms", 100_000_000, 50.0,
            district="Дил тасархай дүүрэг", property_type="Оффис зарна", rooms=None)

    rows = deal_percentages(cur)
    assert all(r["district"] != "Дил тасархай дүүрэг" for r in rows)


def test_deal_percentages_excludes_listings_without_area(cur) -> None:
    ids_with_area = [
        _insert(cur, f"test://deal-area-a-{i}", 100_000_000, 50.0,
                district="Талбайгүй дил дүүрэг", rooms=3)
        for i in range(20)
    ]
    _insert(cur, "test://deal-area-b", 200_000_000, None,
            district="Талбайгүй дил дүүрэг", rooms=3)  # price_per_sqm NULL

    rows = deal_percentages(cur)
    group_rows = [r for r in rows if r["district"] == "Талбайгүй дил дүүрэг"]
    assert {r["id"] for r in group_rows} == set(ids_with_area)
    assert group_rows[0]["n_comparable"] == 20  # the no-area listing isn't in the group either


def test_deal_percentages_excludes_listings_below_min_area(cur) -> None:
    # area_sqm=2 for a "3 өрөө" is exactly the kind of parsing-failure
    # pattern _MIN_AREA_SQM_FOR_DEAL exists to catch (see its docstring).
    ids_real = [
        _insert(cur, f"test://deal-tinyarea-real-{i}", 100_000_000, 50.0,
                district="Жижиг талбай дил дүүрэг", rooms=3)
        for i in range(20)
    ]
    _insert(cur, "test://deal-tinyarea-bad", 100_000_000, 2.0,
            district="Жижиг талбай дил дүүрэг", rooms=3)

    rows = deal_percentages(cur)
    group_rows = [r for r in rows if r["district"] == "Жижиг талбай дил дүүрэг"]
    assert {r["id"] for r in group_rows} == set(ids_real)
    assert group_rows[0]["n_comparable"] == 20  # the tiny-area row isn't in the group either


def test_deal_percentages_excludes_negotiable_price_listings(cur) -> None:
    """price_negotiable=true listings carry a placeholder price (e.g. "170 ₮
    Үнэ тохирно" -- id 3039 on the real DB), not a real one. Verified this
    was previously flowing straight into deal_percentages() and scoring
    against real listings' median. Must be excluded from both sides: neither
    scored itself nor counted toward anyone else's group baseline. (It still
    gets a price *estimate* -- see estimate_negotiable_price() -- just never
    a deal_pct, since deal-finding and estimation are deliberately separate.)
    """
    ids_real = [
        _insert(cur, f"test://deal-negotiable-real-{i}", 150_000_000, 50.0,
                district="Тохиролцоот дил дүүрэг", rooms=2)
        for i in range(20)
    ]
    negotiable_id = _insert(cur, "test://deal-negotiable-bad", 170, 50.0,
                             district="Тохиролцоот дил дүүрэг", rooms=2)
    cur.execute("UPDATE listings SET price_negotiable = true WHERE id = %s", (negotiable_id,))

    rows = deal_percentages(cur)
    group_rows = [r for r in rows if r["district"] == "Тохиролцоот дил дүүрэг"]
    assert {r["id"] for r in group_rows} == set(ids_real)
    assert group_rows[0]["n_comparable"] == 20  # the negotiable listing isn't in the group either
    assert float(group_rows[0]["group_median_price_per_sqm"]) == pytest.approx(3_000_000.0, abs=0.01)


def test_deal_percentages_drops_groups_below_min_comparable_size(cur) -> None:
    # One short of MIN_COMPARABLE_GROUP_SIZE=20 -- the whole group (and every
    # listing in it) must be dropped entirely, not scored off a thin sample.
    _insert_many(cur, "test://deal-thin", 19, 150_000_000, 50.0,
                 district="Нимгэн дил дүүрэг", rooms=2)

    rows = deal_percentages(cur)
    assert all(r["district"] != "Нимгэн дил дүүрэг" for r in rows)


def test_deal_percentages_excludes_open_ended_rooms_bucket(cur) -> None:
    # Unegui's own category caps at "5+ өрөө" -- rooms=5 here really means
    # "5 or more", so it must not be treated as a comparable group at all
    # (verified against the real DB: 6-room duplexes tagged rooms=5 showed
    # up as false ~49% "deals" against a median skewed by smaller true
    # 5-room units in the same bucket).
    _insert(cur, "test://deal-5plus-a", 600_000_000, 200.0,
            district="Таван өрөө дүүрэг", rooms=5)
    _insert(cur, "test://deal-5plus-b", 900_000_000, 250.0,
            district="Таван өрөө дүүрэг", rooms=5)

    rows = deal_percentages(cur)
    assert all(r["district"] != "Таван өрөө дүүрэг" for r in rows)


def test_deal_percentages_keeps_sale_and_rent_groups_separate(cur) -> None:
    ids_sale = [
        _insert(cur, f"test://deal-sale-{i}", 300_000_000, 50.0,
                district="Хосгүй дил дүүрэг", rooms=2, listing_type="sale")
        for i in range(20)
    ]
    ids_rent = [
        _insert(cur, f"test://deal-rent-{i}", 1_500_000, 50.0, listing_type="rent",
                property_type="Орон сууц түрээслүүлнэ",
                district="Хосгүй дил дүүрэг", rooms=2)
        for i in range(20)
    ]

    rows = deal_percentages(cur)
    sale_rows = [r for r in rows if r["id"] in ids_sale]
    rent_rows = [r for r in rows if r["id"] in ids_rent]
    # each listing_type forms its own (district, rooms, listing_type) group
    assert len(sale_rows) == 20 and len(rent_rows) == 20
    assert sale_rows[0]["n_comparable"] == 20
    assert rent_rows[0]["n_comparable"] == 20
    assert all(float(r["deal_pct"]) == 0.0 for r in sale_rows)
    assert all(float(r["deal_pct"]) == 0.0 for r in rent_rows)


def test_deal_percentages_excludes_auto_resolved_duplicate_from_group_median(cur) -> None:
    _insert_many(cur, "test://deal-dup-filler", 18, 150_000_000, 50.0,
                 district="Дил давхар дүүрэг", rooms=2)
    id_a = _insert(cur, "test://deal-dup-a", 100_000_000, 50.0, district="Дил давхар дүүрэг", rooms=2)
    id_b = _insert(cur, "test://deal-dup-b", 300_000_000, 50.0, district="Дил давхар дүүрэг", rooms=2)
    record_matches(cur, [(min(id_a, id_b), max(id_a, id_b), 0.95)])  # auto-resolve tier
    id_c = _insert(cur, "test://deal-dup-c", 100_000_000, 50.0, district="Дил давхар дүүрэг", rooms=2)

    rows = deal_percentages(cur)
    group_rows = [r for r in rows if r["district"] == "Дил давхар дүүрэг"]
    # 18 filler + one of dup-a/dup-b (the other superseded) + dup-c = 20
    assert len(group_rows) == 20
    assert group_rows[0]["n_comparable"] == 20


def test_deal_percentages_real_data_smoke_check(cur) -> None:
    rows = deal_percentages(cur)
    assert len(rows) > 0
    for row in rows:
        assert row["rooms"] is not None
        assert row["rooms"] != _OPEN_ENDED_ROOMS
        assert row["area_sqm"] >= _MIN_AREA_SQM_FOR_DEAL
        assert row["n_comparable"] >= MIN_COMPARABLE_GROUP_SIZE
        # deal_status must always agree with what classify_deal() computes
        # independently from the same deal_pct -- SQL and Python must never drift.
        assert row["deal_status"] == classify_deal(float(row["deal_pct"]))
        assert (row["deal_reason"] is not None) == (row["deal_status"] == "needs_review")
    # sorted best-deal-first
    deal_pcts = [float(r["deal_pct"]) for r in rows]
    assert deal_pcts == sorted(deal_pcts, reverse=True)


def _make_negotiable(cur, district, rooms, *, area_sqm=60.0, listing_type="sale",
                      property_type="Орон сууц зарна", url="test://negotiable") -> int:
    listing_id = _insert(cur, url, 170, area_sqm, district=district, rooms=rooms,
                          listing_type=listing_type, property_type=property_type)
    cur.execute("UPDATE listings SET price_negotiable = true WHERE id = %s", (listing_id,))
    return listing_id


def _estimate_row(rows, listing_id):
    return next(r for r in rows if r["id"] == listing_id)


def test_estimate_negotiable_price_area_based(cur) -> None:
    # 20 filler listings, uniform 150M @ 50 sqm -> price/sqm median = 3M,
    # price median = 150M. Negotiable listing has its OWN area (60 sqm,
    # different from filler's 50) so area-based and group-median-price
    # fallback would disagree -- confirms which method actually ran.
    _insert_many(cur, "test://est-area-filler", 20, 150_000_000, 50.0,
                 district="Тохирсон дил дүүрэг", rooms=2)
    negotiable_id = _make_negotiable(cur, "Тохирсон дил дүүрэг", 2, area_sqm=60.0,
                                      url="test://est-area-negotiable")

    rows = estimate_negotiable_price(cur)
    row = _estimate_row(rows, negotiable_id)

    assert row["estimate_basis"] == "area_based"
    assert float(row["group_median_price_per_sqm"]) == pytest.approx(3_000_000.0, abs=0.01)
    assert float(row["estimated_price_per_sqm"]) == pytest.approx(3_000_000.0, abs=0.01)
    # 3,000,000 * 60 sqm = 180,000,000 -- NOT the filler's own 150M price
    assert float(row["estimated_price"]) == pytest.approx(180_000_000.0, abs=0.01)
    assert row["n_comparable"] == 20


def test_estimate_negotiable_price_falls_back_when_area_missing(cur) -> None:
    _insert_many(cur, "test://est-noarea-filler", 20, 150_000_000, 50.0,
                 district="Талбайгүй тохирсон дүүрэг", rooms=2)
    negotiable_id = _make_negotiable(cur, "Талбайгүй тохирсон дүүрэг", 2, area_sqm=None,
                                      url="test://est-noarea-negotiable")

    rows = estimate_negotiable_price(cur)
    row = _estimate_row(rows, negotiable_id)

    assert row["estimate_basis"] == "group_median_price"
    assert row["estimated_price_per_sqm"] is None  # never derived from an untrusted area
    assert float(row["estimated_price"]) == pytest.approx(150_000_000.0, abs=0.01)


def test_estimate_negotiable_price_falls_back_when_area_implausible(cur) -> None:
    # area_sqm=2 fails the same _MIN_AREA_SQM_FOR_DEAL floor deal_percentages() uses.
    _insert_many(cur, "test://est-tinyarea-filler", 20, 150_000_000, 50.0,
                 district="Жижиг тохирсон дүүрэг", rooms=2)
    negotiable_id = _make_negotiable(cur, "Жижиг тохирсон дүүрэг", 2, area_sqm=2.0,
                                      url="test://est-tinyarea-negotiable")

    rows = estimate_negotiable_price(cur)
    row = _estimate_row(rows, negotiable_id)

    assert row["estimate_basis"] == "group_median_price"
    assert row["estimated_price_per_sqm"] is None
    assert float(row["estimated_price"]) == pytest.approx(150_000_000.0, abs=0.01)


def test_estimate_negotiable_price_excludes_open_ended_rooms(cur) -> None:
    _insert_many(cur, "test://est-5plus-filler", 20, 600_000_000, 200.0,
                 district="Таван өрөө тохирсон дүүрэг", rooms=5)
    _make_negotiable(cur, "Таван өрөө тохирсон дүүрэг", 5, url="test://est-5plus-negotiable")

    rows = estimate_negotiable_price(cur)
    assert all(r["district"] != "Таван өрөө тохирсон дүүрэг" for r in rows)


def test_estimate_negotiable_price_excludes_listings_without_rooms(cur) -> None:
    _insert_many(cur, "test://est-norooms-filler", 20, 100_000_000, 50.0,
                 district="Тохирсон тасархай дүүрэг", property_type="Оффис зарна", rooms=None)
    _make_negotiable(cur, "Тохирсон тасархай дүүрэг", None,
                      property_type="Оффис зарна", url="test://est-norooms-negotiable")

    rows = estimate_negotiable_price(cur)
    assert all(r["district"] != "Тохирсон тасархай дүүрэг" for r in rows)


def test_estimate_negotiable_price_no_estimate_below_min_group_size(cur) -> None:
    # Only 19 real comparables -- one short of MIN_COMPARABLE_GROUP_SIZE.
    _insert_many(cur, "test://est-thin-filler", 19, 150_000_000, 50.0,
                 district="Нимгэн тохирсон дүүрэг", rooms=2)
    _make_negotiable(cur, "Нимгэн тохирсон дүүрэг", 2, url="test://est-thin-negotiable")

    rows = estimate_negotiable_price(cur)
    assert all(r["district"] != "Нимгэн тохирсон дүүрэг" for r in rows)


def test_estimate_negotiable_price_real_data_smoke_check(cur) -> None:
    rows = estimate_negotiable_price(cur)
    assert len(rows) > 0
    for row in rows:
        assert row["rooms"] is not None
        assert row["rooms"] != _OPEN_ENDED_ROOMS
        assert row["n_comparable"] >= MIN_COMPARABLE_GROUP_SIZE
        assert row["estimate_basis"] in ("area_based", "group_median_price")
        assert float(row["estimated_price"]) > 0
        if row["estimate_basis"] == "area_based":
            assert row["estimated_price_per_sqm"] is not None
        else:
            assert row["estimated_price_per_sqm"] is None
