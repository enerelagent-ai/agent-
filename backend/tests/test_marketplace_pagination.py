from datetime import datetime, timezone

from app.api.routes import listings as listings_route
from app.models.listing import Listing


_TIED_AT = datetime(2099, 4, 1, tzinfo=timezone.utc)
_DISTRICT = "TEST CURSOR DISTRICT"


def _insert_tied_marketplace_rows(db_session, count: int) -> list[int]:
    ids = []
    for index in range(count):
        row = Listing(
            source="unegui",
            source_url=f"test://marketplace-cursor-{index}",
            title=f"cursor listing {index}",
            listing_type="sale",
            property_type="Орон сууц зарна",
            district=_DISTRICT,
            rooms=2,
            price=100_000_000 + index,
            price_negotiable=False,
            dedup_hash=f"test-marketplace-cursor-{index}",
            is_active=True,
            scraped_at=_TIED_AT,
            created_at=_TIED_AT,
            updated_at=_TIED_AT,
            photo_urls=[],
        )
        db_session.add(row)
        db_session.flush()
        ids.append(row.id)
    return ids


def test_marketplace_cursor_has_no_gaps_or_duplicates_for_tied_timestamps(
    client, db_session, monkeypatch
) -> None:
    inserted_ids = _insert_tied_marketplace_rows(db_session, 5)
    monkeypatch.setattr(
        listings_route, "superseded_listing_ids_conn", lambda _dsn: set()
    )
    params = {
        "listing_type": "sale",
        "district": _DISTRICT,
        "property_type": "Орон сууц зарна",
        "rooms": 2,
        "min_price": 100_000_000,
        "max_price": 200_000_000,
        "limit": 2,
    }

    pages = []
    cursor = None
    while True:
        request_params = {**params}
        if cursor is not None:
            request_params["cursor"] = cursor
        response = client.get("/listings/search", params=request_params)
        assert response.status_code == 200
        page = response.json()
        pages.append(page)
        cursor = page["next_cursor"]
        if cursor is None:
            break

    returned_ids = [item["id"] for page in pages for item in page["items"]]
    assert returned_ids == list(reversed(inserted_ids))
    assert len(returned_ids) == len(set(returned_ids)) == 5
    assert [page["has_more"] for page in pages] == [True, True, False]
    assert [len(page["items"]) for page in pages] == [2, 2, 1]


def test_marketplace_cursor_and_price_range_are_validated(client) -> None:
    invalid_cursor = client.get(
        "/listings/search",
        params={"listing_type": "sale", "cursor": "not-a-cursor"},
    )
    invalid_range = client.get(
        "/listings/search",
        params={"listing_type": "sale", "min_price": 2, "max_price": 1},
    )

    assert invalid_cursor.status_code == 422
    assert invalid_cursor.json()["detail"] == "Invalid marketplace cursor"
    assert invalid_range.status_code == 422
    assert invalid_range.json()["detail"] == "min_price cannot exceed max_price"
