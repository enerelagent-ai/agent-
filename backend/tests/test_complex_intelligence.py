from datetime import datetime, timezone

from app.api.routes import complexes as complexes_route
from app.models.listing import Complex, Listing, ListingComplexMatch, PublicAffordabilitySnapshot


def test_public_affordability_returns_latest_snapshot(client, db_session) -> None:
    db_session.add(PublicAffordabilitySnapshot(
        source="hotkhon.mn",
        data_as_of=datetime(2026, 8, 24).date(),
        source_url="https://hotkhon.mn/bolomj/",
        districts=["Хан-Уул", "Баянзүрх"],
        listings=[[80, 200, 0], [41, 155, 1]],
        rules={"loan_cap_mnt": 150_000_000, "min_downpayment_ratio": 0.3, "max_area_sqm": 80},
    ))
    db_session.flush()

    response = client.get("/complexes/public-affordability/latest")
    assert response.status_code == 200
    assert response.json()["data_as_of"] == "2026-08-24"
    assert response.json()["listings"] == [[80.0, 200.0, 0.0], [41.0, 155.0, 1.0]]


def test_complex_intelligence_only_exposes_approved_active_units(
    client, db_session, monkeypatch
) -> None:
    now = datetime(2099, 4, 1, tzinfo=timezone.utc)
    complex_row = Complex(
        canonical_name="TEST INTELLIGENCE COMPLEX",
        normalized_name="test intelligence complex",
        aliases=["TEST IC"],
        created_at=now,
        updated_at=now,
    )
    db_session.add(complex_row)
    db_session.flush()
    listing = Listing(
        source="unegui",
        source_url="test://complex-intelligence",
        title="TEST INTELLIGENCE COMPLEX 2 өрөө",
        price=200_000_000,
        area_sqm=50,
        listing_type="sale",
        property_type="Орон сууц зарна",
        district="Хан-Уул",
        lat=47.9,
        lng=106.9,
        complex_id=complex_row.id,
        dedup_hash="test-complex-intelligence",
        is_active=True,
        scraped_at=now,
        created_at=now,
        updated_at=now,
        photo_urls=[],
    )
    db_session.add(listing)
    db_session.flush()
    db_session.add(
        ListingComplexMatch(
            listing_id=listing.id,
            complex_id=complex_row.id,
            relation="unit",
            confidence=1.0,
            evidence_text=listing.title,
            extractor_version="test",
            review_status="approved",
            reviewed_at=now,
            is_current=True,
        )
    )
    db_session.flush()
    monkeypatch.setattr(complexes_route, "superseded_listing_ids_conn", lambda _dsn: set())

    response = client.get("/complexes")
    assert response.status_code == 200
    item = next(row for row in response.json() if row["id"] == complex_row.id)
    assert item["district"] == "Хан-Уул"
    assert item["active_listings"] == 1
    assert item["median_sale_price_per_sqm"] == 4_000_000
    assert item["location_kind"] == "listing_centroid"
    assert item["has_contour"] is False

    detail = client.get(f"/complexes/{complex_row.id}")
    assert detail.status_code == 200
    assert detail.json()["aliases"] == ["TEST IC"]
    assert detail.json()["median_sale_price"] == 200_000_000
