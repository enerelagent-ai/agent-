from datetime import datetime, timezone

from app.api.routes import listings as listings_route
from app.models.listing import Listing


_NOW = datetime(2099, 3, 1, tzinfo=timezone.utc)


def _listing(suffix: str, **overrides) -> Listing:
    values = {
        "source": "unegui",
        "source_url": f"test://facets-{suffix}",
        "title": f"facets {suffix}",
        "listing_type": "sale",
        "property_type": "TEST FACET PROPERTY",
        "district": "TEST FACET DISTRICT",
        "rooms": 7,
        "price": 0.01,
        "price_negotiable": False,
        "dedup_hash": f"test-facets-{suffix}",
        "is_active": True,
        "scraped_at": _NOW,
        "created_at": _NOW,
        "updated_at": _NOW,
        "photo_urls": [],
    }
    values.update(overrides)
    return Listing(**values)


def test_listing_facets_use_active_canonical_transaction_slice(
    client, db_session, monkeypatch
) -> None:
    included = _listing("included")
    superseded = _listing("superseded", price=0.001)
    inactive = _listing("inactive", is_active=False, price=0.0001)
    wrong_transaction = _listing(
        "rent",
        listing_type="rent",
        property_type="TEST RENT FACET PROPERTY",
        district="TEST RENT FACET DISTRICT",
        price=0.00001,
    )
    negotiable = _listing(
        "negotiable",
        property_type="TEST NEGOTIABLE FACET PROPERTY",
        district="TEST NEGOTIABLE FACET DISTRICT",
        price=0.000001,
        price_negotiable=True,
    )
    db_session.add_all(
        [included, superseded, inactive, wrong_transaction, negotiable]
    )
    db_session.flush()
    monkeypatch.setattr(
        listings_route,
        "superseded_listing_ids_conn",
        lambda _dsn: {superseded.id},
    )

    response = client.get("/listings/facets", params={"listing_type": "sale"})

    assert response.status_code == 200
    payload = response.json()
    districts = {item["value"]: item["count"] for item in payload["districts"]}
    property_types = {
        item["value"]: item["count"] for item in payload["property_types"]
    }
    rooms = {item["value"]: item["count"] for item in payload["rooms"]}

    assert payload["listing_type"] == "sale"
    assert districts["TEST FACET DISTRICT"] == 1
    assert districts["TEST NEGOTIABLE FACET DISTRICT"] == 1
    assert "TEST RENT FACET DISTRICT" not in districts
    assert property_types["TEST FACET PROPERTY"] == 1
    assert property_types["TEST NEGOTIABLE FACET PROPERTY"] == 1
    assert "TEST RENT FACET PROPERTY" not in property_types
    assert rooms[7] >= 2
    assert payload["price"]["min"] == 0.01


def test_listing_facets_require_known_transaction_type(client) -> None:
    assert client.get("/listings/facets").status_code == 422
    assert (
        client.get("/listings/facets", params={"listing_type": "lease"}).status_code
        == 422
    )
