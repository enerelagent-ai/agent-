from datetime import datetime, timezone

from app.models.listing import Listing
from app.api.routes.dashboard import _deal_candidate_ids
from app.api.routes import dashboard

# Far enough in the future that these synthetic rows always sort first in
# the endpoint's `scraped_at DESC` order, ahead of whatever real committed
# data also exists in this DB -- /listings has no district/filter param to
# otherwise isolate a test's own rows from it.
_FUTURE_SCRAPED_AT = datetime(2099, 1, 1, tzinfo=timezone.utc)


def test_deal_candidate_filter_keeps_needs_review_separate_from_top_deals() -> None:
    deals = {
        1: {"deal_status": "needs_review", "district": "A", "property_type": "Apartment", "complex_id": None, "price": 10},
        2: {"deal_status": "top_deal", "district": "A", "property_type": "Apartment", "complex_id": None, "price": 20},
        3: {"deal_status": "needs_review", "district": "B", "property_type": "Apartment", "complex_id": None, "price": 30},
    }

    for deal in deals.values():
        deal["listing_type"] = "sale"

    assert _deal_candidate_ids(deals, "needs_review", "sale", "A", None, None, None, None) == [1]
    assert _deal_candidate_ids(deals, "top_deal", "sale", "A", None, None, None, None) == [2]
    assert _deal_candidate_ids(deals, "top_deal", "rent", "A", None, None, None, None) == []


def _insert_tied_listings(db_session, n: int) -> list[int]:
    """n listings sharing one scraped_at -- the exact tie a batch insert
    produces in production and that the id tiebreaker exists for.

    created_at/updated_at/photo_urls are set explicitly rather than relying
    on db/schema.sql's column defaults: the SQLAlchemy model has no
    matching Python-side default for them, so an unset attribute is sent
    as an explicit NULL rather than omitted from the INSERT for the DB's
    own DEFAULT to fill in.
    """
    ids = []
    for i in range(n):
        listing = Listing(
            source="unegui",
            source_url=f"test://pagination-{i}",
            title="test",
            dedup_hash=f"test-pagination-hash-{i}",
            scraped_at=_FUTURE_SCRAPED_AT,
            created_at=_FUTURE_SCRAPED_AT,
            updated_at=_FUTURE_SCRAPED_AT,
            photo_urls=[],
        )
        db_session.add(listing)
        db_session.flush()  # assigns listing.id via the table's sequence
        ids.append(listing.id)
    return ids


def test_listings_pagination_has_no_duplicates_or_gaps_with_tied_scraped_at(
    client, db_session
) -> None:
    """Reproduces the bug CLAUDE.md's Known Issues documented: many rows
    sharing one scraped_at (a batch insert) with no tiebreaker means
    Postgres doesn't guarantee a stable order for the ties across separate
    offset-paged queries, so pages could overlap or skip rows. With id
    descending as the tiebreaker, the order is a fully deterministic total
    order (id is unique), so walking every page must reproduce the exact
    insertion order reversed -- newest (highest id) first -- with no id
    appearing twice and none missing."""
    inserted_ids = _insert_tied_listings(db_session, 30)
    expected_order = list(reversed(inserted_ids))

    page_1 = client.get("/listings", params={"limit": 10, "offset": 0}).json()
    page_2 = client.get("/listings", params={"limit": 10, "offset": 10}).json()
    page_3 = client.get("/listings", params={"limit": 10, "offset": 20}).json()

    all_ids = [row["id"] for row in page_1 + page_2 + page_3]

    assert len(all_ids) == 30
    assert len(set(all_ids)) == 30  # no id repeated across pages
    assert all_ids == expected_order  # exact, deterministic id-desc order


def test_listings_pagination_is_stable_across_repeated_calls(client, db_session) -> None:
    """The same offset/limit called twice must return identical rows in
    identical order -- without the id tiebreaker this isn't guaranteed for
    tied scraped_at values even within a single test run."""
    _insert_tied_listings(db_session, 15)

    first_call = client.get("/listings", params={"limit": 5, "offset": 5}).json()
    second_call = client.get("/listings", params={"limit": 5, "offset": 5}).json()

    assert [row["id"] for row in first_call] == [row["id"] for row in second_call]


def test_dashboard_listings_filters_sale_and_rent_without_hiding_browse_rows(
    client, db_session, monkeypatch
) -> None:
    """Transaction type is a browse concern. It must filter the result,
    while rows without an analytics classification remain visible."""
    monkeypatch.setattr(dashboard, "superseded_listing_ids_conn", lambda _dsn: set())
    monkeypatch.setattr(dashboard, "deal_percentages_conn", lambda _dsn: [])
    monkeypatch.setattr(dashboard, "complex_deal_percentages_conn", lambda _dsn: [])
    monkeypatch.setattr(dashboard, "estimate_negotiable_price_conn", lambda _dsn: [])
    monkeypatch.setattr(dashboard, "rental_yield_by_district_rooms_conn", lambda _dsn: [])

    rows = []
    for listing_type, property_type in (
        ("sale", "Орон сууц зарна"),
        ("rent", "Орон сууц түрээслүүлнэ"),
    ):
        row = Listing(
            source="unegui",
            source_url=f"test://transaction-filter-{listing_type}",
            title=f"test {listing_type}",
            listing_type=listing_type,
            property_type=property_type,
            district="TEST_TRANSACTION_CONTRACT",
            dedup_hash=f"test-transaction-filter-{listing_type}",
            is_active=True,
            scraped_at=_FUTURE_SCRAPED_AT,
            created_at=_FUTURE_SCRAPED_AT,
            updated_at=_FUTURE_SCRAPED_AT,
            photo_urls=[],
        )
        db_session.add(row)
        rows.append(row)
    db_session.flush()

    common = {"district": "TEST_TRANSACTION_CONTRACT", "limit": 2}
    sale = client.get(
        "/dashboard/listings", params={**common, "listing_type": "sale"}
    )
    rent = client.get(
        "/dashboard/listings", params={**common, "listing_type": "rent"}
    )

    assert sale.status_code == 200
    assert rent.status_code == 200
    assert [item["id"] for item in sale.json()] == [rows[0].id]
    assert [item["id"] for item in rent.json()] == [rows[1].id]
    assert sale.json()[0]["deal_status"] is None
    assert rent.json()[0]["deal_status"] is None


def test_dashboard_listings_rejects_unknown_listing_type(client) -> None:
    response = client.get("/dashboard/listings", params={"listing_type": "lease"})

    assert response.status_code == 422


def test_listing_detail_only_publishes_active_canonical_rows(
    client, db_session, monkeypatch
) -> None:
    rows = []
    for suffix, active in (("active", True), ("inactive", False), ("duplicate", True)):
        row = Listing(
            source="unegui",
            source_url=f"test://detail-{suffix}",
            title=f"detail {suffix}",
            listing_type="sale",
            property_type="Орон сууц зарна",
            dedup_hash=f"test-detail-{suffix}",
            is_active=active,
            scraped_at=_FUTURE_SCRAPED_AT,
            created_at=_FUTURE_SCRAPED_AT,
            updated_at=_FUTURE_SCRAPED_AT,
            photo_urls=[],
        )
        db_session.add(row)
        rows.append(row)
    db_session.flush()
    from app.api.routes import listings as listings_route

    monkeypatch.setattr(
        listings_route,
        "superseded_listing_ids_conn",
        lambda _dsn: {rows[2].id},
    )

    active = client.get(f"/listings/{rows[0].id}")
    inactive = client.get(f"/listings/{rows[1].id}")
    duplicate = client.get(f"/listings/{rows[2].id}")

    assert active.status_code == 200
    assert active.json()["id"] == rows[0].id
    assert inactive.status_code == 404
    assert duplicate.status_code == 404
