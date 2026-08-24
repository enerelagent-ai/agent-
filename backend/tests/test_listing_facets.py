from datetime import datetime, timezone

from app.api.routes import listings as listings_route
from app.models.listing import Complex, Listing, ListingComplexMatch


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


def test_complex_facet_and_search_only_use_approved_current_unit_matches(
    client, db_session, monkeypatch
) -> None:
    approved_complex = Complex(
        canonical_name="TEST VERIFIED COMPLEX",
        normalized_name="test verified complex",
        aliases=[],
        created_at=_NOW,
        updated_at=_NOW,
    )
    pending_complex = Complex(
        canonical_name="TEST PENDING COMPLEX",
        normalized_name="test pending complex",
        aliases=[],
        created_at=_NOW,
        updated_at=_NOW,
    )
    db_session.add_all([approved_complex, pending_complex])
    db_session.flush()
    approved_listing = _listing("verified-complex", complex_id=approved_complex.id)
    pending_listing = _listing("pending-complex", complex_id=pending_complex.id)
    legacy_listing = _listing("legacy-complex", complex_id=approved_complex.id)
    db_session.add_all([approved_listing, pending_listing, legacy_listing])
    db_session.flush()
    db_session.add_all(
        [
            ListingComplexMatch(
                listing_id=approved_listing.id,
                complex_id=approved_complex.id,
                relation="unit",
                confidence=1.0,
                evidence_text=approved_listing.title,
                extractor_version="test",
                review_status="approved",
                reviewed_at=_NOW,
                is_current=True,
            ),
            ListingComplexMatch(
                listing_id=pending_listing.id,
                complex_id=pending_complex.id,
                relation="unit",
                confidence=0.9,
                evidence_text=pending_listing.title,
                extractor_version="test",
                review_status="pending",
                is_current=True,
            ),
        ]
    )
    db_session.flush()
    monkeypatch.setattr(listings_route, "superseded_listing_ids_conn", lambda _dsn: set())

    facets = client.get("/listings/facets", params={"listing_type": "sale"})
    assert facets.status_code == 200
    complex_ids = {item["id"] for item in facets.json()["complexes"]}
    assert approved_complex.id in complex_ids
    assert pending_complex.id not in complex_ids

    search = client.get(
        "/listings/search",
        params={"listing_type": "sale", "complex_id": approved_complex.id},
    )
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["items"]] == [approved_listing.id]
