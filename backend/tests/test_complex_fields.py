from types import SimpleNamespace
from datetime import datetime, timezone

from app.api.routes.dashboard import _attach_computed_fields
from app.models.listing import (
    Complex,
    Listing,
    ListingComplexMatch,
    VerifiedComplexLocation,
)
from app.schemas.dashboard import ComplexPriceSummary


def test_attach_computed_fields_keeps_complex_comparison_independent() -> None:
    listing = SimpleNamespace()
    complex_deal = {
        "complex_name": "Buti Town",
        "complex_deal_pct": 22.5,
        "complex_deal_status": "top_deal",
        "complex_deal_reason": None,
        "complex_n_comparable": 24,
        "complex_median_price_per_sqm": 4_000_000,
    }

    result = _attach_computed_fields(listing, None, complex_deal, "Buti Town", None, None)

    assert result.deal_pct is None  # district comparison can be unavailable
    assert result.complex_name == "Buti Town"
    assert result.complex_deal_pct == 22.5
    assert result.complex_deal_status == "top_deal"
    assert result.complex_n_comparable == 24
    assert result.complex_median_price_per_sqm == 4_000_000.0


def test_complex_price_summary_schema_accepts_calculation_row() -> None:
    summary = ComplexPriceSummary.model_validate({
        "complex_id": 1,
        "complex_name": "Buti Town",
        "listing_type": "sale",
        "property_type": "Орон сууц зарна",
        "n_listings": 24,
        "avg_price": 300_000_000,
        "median_price": 290_000_000,
        "avg_price_per_sqm": 4_100_000,
        "median_price_per_sqm": 4_000_000,
        "n_with_price_per_sqm": 23,
    })
    assert summary.complex_name == "Buti Town"
    assert summary.n_listings == 24


def test_complex_options_and_listing_filter_use_same_canonical_name(client, db_session) -> None:
    now = datetime(2099, 2, 1, tzinfo=timezone.utc)
    complex_row = Complex(
        canonical_name="Phase 4 Test Complex",
        normalized_name="phase 4 test complex",
        aliases=[],
        created_at=now,
        updated_at=now,
    )
    db_session.add(complex_row)
    db_session.flush()
    listing = Listing(
        source="unegui",
        source_url="test://phase4-complex-filter",
        title="Phase 4 Test Complex байр",
        dedup_hash="phase4-complex-filter",
        complex_id=complex_row.id,
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
            confidence=0.99,
            evidence_text=listing.title,
            extractor_version="test-v1",
            review_status="approved",
            reviewer_note="test verified complex",
            reviewed_at=now,
            is_current=True,
        )
    )
    db_session.flush()

    options = client.get("/dashboard/complexes").json()
    assert {"id": complex_row.id, "canonical_name": complex_row.canonical_name} in options

    response = client.get(
        "/dashboard/listings",
        params={"complex_id": complex_row.id, "limit": 10},
    )
    assert response.status_code == 200
    rows = response.json()
    assert [row["id"] for row in rows] == [listing.id]
    assert rows[0]["complex_name"] == complex_row.canonical_name
    assert rows[0]["complex_verified"] is True


def test_listing_with_only_legacy_complex_pointer_is_not_verified(client, db_session) -> None:
    now = datetime(2099, 2, 2, tzinfo=timezone.utc)
    complex_row = Complex(
        canonical_name="Legacy Pointer Test Complex",
        normalized_name="legacy pointer test complex",
        aliases=[],
        created_at=now,
        updated_at=now,
    )
    db_session.add(complex_row)
    db_session.flush()
    listing = Listing(
        source="unegui",
        source_url="test://legacy-pointer-verification",
        title="Legacy complex байр",
        dedup_hash="legacy-pointer-verification",
        complex_id=complex_row.id,
        is_active=True,
        scraped_at=now,
        created_at=now,
        updated_at=now,
        photo_urls=[],
    )
    db_session.add(listing)
    db_session.flush()

    response = client.get(f"/listings/{listing.id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["complex_name"] == complex_row.canonical_name
    assert payload["complex_verified"] is False


def test_complex_review_queue_exposes_pending_evidence_read_only(client, db_session) -> None:
    now = datetime(2099, 2, 3, tzinfo=timezone.utc)
    complex_row = Complex(
        canonical_name="Review Queue Test Complex",
        normalized_name="review queue test complex",
        aliases=[],
        created_at=now,
        updated_at=now,
    )
    db_session.add(complex_row)
    db_session.flush()
    listing = Listing(
        source="unegui",
        source_url="test://complex-review-queue",
        title="Review Queue Test Complex хойно байр",
        dedup_hash="complex-review-queue",
        complex_id=complex_row.id,
        district="Хан-Уул",
        address="Хороо 15",
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
            relation="landmark",
            confidence=0.55,
            evidence_text=listing.title,
            extractor_version="test-v1",
            review_status="pending",
            reviewer_note="manual test queue",
            reviewed_at=None,
            is_current=True,
        )
    )
    db_session.flush()

    response = client.get(
        "/dashboard/complex-review-queue",
        params={"complex_id": complex_row.id, "relation": "landmark"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"] == [{
        "listing_id": listing.id,
        "complex_id": complex_row.id,
        "complex_name": complex_row.canonical_name,
        "matched_alias": None,
        "relation": "landmark",
        "confidence": 0.55,
        "evidence_text": listing.title,
        "district": "Хан-Уул",
        "address": "Хороо 15",
        "source_url": listing.source_url,
        "review_reason": "manual test queue",
        "can_approve": False,
        "approval_block_reason": "landmark_or_unknown_relation",
        "detected_at": payload["items"][0]["detected_at"],
    }]

    blocked = client.post(
        f"/dashboard/complex-review-queue/{listing.id}/decision",
        json={"decision": "approve"},
    )
    assert blocked.status_code == 409
    assert "landmark_or_unknown_relation" in blocked.json()["detail"]

    rejected = client.post(
        f"/dashboard/complex-review-queue/{listing.id}/decision",
        json={"decision": "reject"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["review_status"] == "rejected"
    assert rejected.json()["complex_id_after"] is None
    db_session.refresh(listing)
    assert listing.complex_id is None
    db_session.refresh(db_session.query(ListingComplexMatch).filter_by(listing_id=listing.id).one())
    assert db_session.query(ListingComplexMatch).filter_by(listing_id=listing.id).one().review_status == "rejected"


def test_complex_review_approve_requires_and_accepts_verified_location(client, db_session) -> None:
    now = datetime(2099, 2, 4, tzinfo=timezone.utc)
    complex_row = Complex(
        canonical_name="Review Approval Test Complex",
        normalized_name="review approval test complex",
        aliases=[],
        created_at=now,
        updated_at=now,
    )
    db_session.add(complex_row)
    db_session.flush()
    db_session.add(
        VerifiedComplexLocation(
            complex_id=complex_row.id,
            district="Хан-Уул",
            evidence_text="test registry evidence",
            registry_version="test-v1",
        )
    )
    listing = Listing(
        source="unegui",
        source_url="test://complex-review-approve",
        title="Review Approval Test Complex байр",
        dedup_hash="complex-review-approve",
        complex_id=complex_row.id,
        district="Хан-Уул",
        is_active=True,
        scraped_at=now,
        created_at=now,
        updated_at=now,
        photo_urls=[],
    )
    db_session.add(listing)
    db_session.flush()
    match = ListingComplexMatch(
        listing_id=listing.id,
        complex_id=complex_row.id,
        relation="unit",
        confidence=0.99,
        evidence_text=listing.title,
        extractor_version="test-v1",
        review_status="pending",
        reviewed_at=None,
        is_current=True,
    )
    db_session.add(match)
    db_session.flush()

    queue = client.get(
        "/dashboard/complex-review-queue", params={"complex_id": complex_row.id}
    ).json()
    assert queue["items"][0]["can_approve"] is True
    assert queue["items"][0]["approval_block_reason"] is None

    response = client.post(
        f"/dashboard/complex-review-queue/{listing.id}/decision",
        json={"decision": "approve"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "listing_id": listing.id,
        "complex_id": complex_row.id,
        "review_status": "approved",
        "complex_id_after": complex_row.id,
    }
    db_session.refresh(match)
    assert match.review_status == "approved"
    assert match.reviewed_at is not None
