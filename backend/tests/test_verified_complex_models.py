from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.listing import Complex, ComplexAlias, Listing, ListingComplexMatch


def _listing() -> Listing:
    now = datetime.now(timezone.utc)
    return Listing(
        source="unegui",
        source_url="test://verified-complex-model",
        title="Тест хотхонд байр",
        photo_urls=[],
        dedup_hash="verified-complex-model",
        scraped_at=now,
        created_at=now,
        updated_at=now,
    )


def test_complex_match_keeps_evidence_separate_from_listing_pointer(db_session) -> None:
    complex_row = Complex(canonical_name="Verified Model", normalized_name="verified model", aliases=[])
    listing = _listing()
    db_session.add_all([complex_row, listing])
    db_session.flush()

    alias = ComplexAlias(
        complex_id=complex_row.id,
        alias="Verified Model",
        normalized_alias="verified model test alias",
        source="reviewed",
    )
    db_session.add(alias)
    db_session.flush()
    match = ListingComplexMatch(
        listing_id=listing.id,
        complex_id=complex_row.id,
        matched_alias_id=alias.id,
        relation="unit",
        confidence=0.99,
        evidence_text=listing.title,
        extractor_version="test-v1",
    )
    db_session.add(match)
    db_session.flush()

    assert listing.complex_id is None
    assert match.review_status == "pending"
    assert float(match.confidence) == 0.99


def test_reviewed_match_requires_review_timestamp(db_session) -> None:
    complex_row = Complex(canonical_name="Verified Constraint", normalized_name="verified constraint", aliases=[])
    listing = _listing()
    listing.source_url = "test://verified-complex-constraint"
    listing.dedup_hash = "verified-complex-constraint"
    db_session.add_all([complex_row, listing])
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                ListingComplexMatch(
                    listing_id=listing.id,
                    complex_id=complex_row.id,
                    relation="unit",
                    confidence=0.8,
                    evidence_text=listing.title,
                    extractor_version="test-v1",
                    review_status="approved",
                    reviewed_at=None,
                )
            )
            db_session.flush()
