"""Unit tests for the parser-dict -> listings-row mapping and dedup hash."""

from scraper.save import (
    compute_dedup_hash,
    known_urls,
    listing_row_from_parsed,
    normalize_dsn,
    parse_area_sqm,
    parse_price_negotiable,
    parse_rooms,
    recently_scraped,
)

SAMPLE_PARSED = {
    "url": "https://www.unegui.mn/adv/10103750_test/",
    "ad_id": 10103750,
    "title": "Тест зар",
    "description": "Төв талбайд ойр, бүрэн тохижсон.",
    "price": 99330.0,
    "price_raw": "99,330 ₮",
    "currency": "MNT",
    "location_raw": "Баянзүрх, Баянзүрх, Хороо 6",
    "district": "Баянзүрх",
    "sub_district": "Баянзүрх, Хороо 6",
    "listing_type": "rent",
    "property_category": "Орон сууц түрээслүүлнэ",
    "property_category_slug": "oron-suuts",
    "property_subcategory": "2 өрөө",
    "property_subcategory_slug": "2-r",
    "posted_raw": "Өчигдөр 21:32",
    "posted_at": "2026-07-21T21:32",
    "latitude": 47.91811,
    "longitude": 106.93199,
    "phones": ["+97683033091", "+97699112233"],
    "photo_urls": ["https://cdn1.unegui.mn/a.webp", "https://cdn1.unegui.mn/b.webp"],
    "specs": {"Талбай": "49 м²", "Шал": "Паркет"},
}


def test_parse_area_sqm_variants() -> None:
    assert parse_area_sqm("296 м²") == 296.0
    assert parse_area_sqm("69.85 м²") == 69.85
    assert parse_area_sqm("150 м² м²") == 150.0
    assert parse_area_sqm("38,5 м²") == 38.5
    assert parse_area_sqm("м²") is None
    assert parse_area_sqm(None) is None


def test_parse_price_negotiable_variants() -> None:
    assert parse_price_negotiable("2.8 Тэрбум ₮ Үнэ тохирно") is True
    assert parse_price_negotiable("7.9 сая ₮ 8.9 сая ₮ Үнэ тохирно") is True
    assert parse_price_negotiable("99,330 ₮") is False
    assert parse_price_negotiable(None) is None
    assert parse_price_negotiable("") is None


def test_parse_rooms_variants() -> None:
    assert parse_rooms("3 өрөө") == 3
    assert parse_rooms("5+ өрөө") == 5
    assert parse_rooms("Хажуу өрөө түрээслүүлнэ") is None
    assert parse_rooms(None) is None


def test_dedup_hash_is_deterministic_and_ignores_price() -> None:
    row = listing_row_from_parsed(SAMPLE_PARSED)
    assert row is not None
    repeat = listing_row_from_parsed(dict(SAMPLE_PARSED, price=123456.0))
    assert repeat is not None
    assert row["dedup_hash"] == repeat["dedup_hash"]


def test_dedup_hash_changes_with_location() -> None:
    row = listing_row_from_parsed(SAMPLE_PARSED)
    moved = listing_row_from_parsed(dict(SAMPLE_PARSED, district="Хан-Уул"))
    assert row is not None and moved is not None
    assert row["dedup_hash"] != moved["dedup_hash"]


def test_listing_row_mapping() -> None:
    row = listing_row_from_parsed(SAMPLE_PARSED)
    assert row is not None
    assert row["source"] == "unegui"
    assert row["source_url"] == SAMPLE_PARSED["url"]
    assert row["contact_phone"] == "+97683033091"  # first phone wins
    assert row["description"] == "Төв талбайд ойр, бүрэн тохижсон."
    assert row["posted_at"] == "2026-07-21T21:32"
    assert row["price_negotiable"] is False  # sample price_raw has no marker
    assert row["price_raw"] == "99,330 ₮"
    assert row["posted_raw"] == "Өчигдөр 21:32"
    assert row["specs"].adapted == SAMPLE_PARSED["specs"]  # full dict kept as JSONB
    assert row["area_sqm"] == 49.0
    assert row["rooms"] == 2
    assert row["listing_type"] == "rent"
    assert row["property_type"] == "Орон сууц түрээслүүлнэ"
    assert row["property_subtype"] == "2 өрөө"
    assert row["photo_urls"] == SAMPLE_PARSED["photo_urls"]
    assert row["address"] == "Баянзүрх, Баянзүрх, Хороо 6"
    assert row["lat"] == 47.91811 and row["lng"] == 106.93199


def test_unusable_records_are_skipped() -> None:
    assert listing_row_from_parsed({"url": "https://x/", "error": "challenge"}) is None
    assert listing_row_from_parsed({"title": "no url"}) is None


def test_recently_scraped_filters_by_window(cur) -> None:
    """Fresh rows are skipped, stale rows are re-scraped (integration, rolled back)."""
    for url, age in (("test://fresh", "0 seconds"), ("test://stale", "2 days")):
        cur.execute(
            """INSERT INTO listings (source, source_url, title, dedup_hash, scraped_at)
               VALUES ('unegui', %s, 't', 'x', now() - %s::interval)""",
            (url, age),
        )
    urls = ["test://fresh", "test://stale", "test://unknown"]
    assert recently_scraped(cur, urls, days=1.0) == {"test://fresh"}
    assert recently_scraped(cur, [], days=1.0) == set()


def test_known_urls_ignores_scraped_at_age(cur) -> None:
    """Unlike recently_scraped, existence alone counts, however old the row."""
    for url, age in (("test://known-fresh", "0 seconds"), ("test://known-old", "60 days")):
        cur.execute(
            """INSERT INTO listings (source, source_url, title, dedup_hash, scraped_at)
               VALUES ('unegui', %s, 't', 'x', now() - %s::interval)""",
            (url, age),
        )
    urls = ["test://known-fresh", "test://known-old", "test://known-unseen"]
    assert known_urls(cur, urls) == {"test://known-fresh", "test://known-old"}
    assert known_urls(cur, []) == set()


def test_normalize_dsn() -> None:
    assert normalize_dsn("postgresql+psycopg2://localhost:5432/postgres") == (
        "postgresql://localhost:5432/postgres"
    )
    assert normalize_dsn("postgresql://localhost/db") == "postgresql://localhost/db"
